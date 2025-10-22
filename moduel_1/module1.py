import re
import uuid
import json
from dotenv import load_dotenv
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

import spacy
from spacy.matcher import Matcher
from pydantic import BaseModel, Field, ValidationError
import google.generativeai as genai

from module_3.utils.logger import logger

# -----------------------------
# Gemini API Config
# -----------------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# -----------------------------
# Data Models
# -----------------------------
class Entity(BaseModel):
    text: str
    label: str
    start: int
    end: int
    confidence: float = 1.0


class EntityCollection(BaseModel):
    conversation_id: str
    timestamp: str
    raw_text: str
    sentences: List[str]
    entities: List[Entity]

    def to_endpoint_json(self) -> Dict[str, Any]:
        """Convert to downstream endpoint JSON."""
        return {
            "conversation_id": self.conversation_id,
            "input": [{"role": "user", "content": self.raw_text}],
            "sentences": self.sentences,
            "entities": [e.dict() for e in self.entities],
            "pos_tagged_text": self.raw_text,  # include POS-tagged version
        }


class FinalStructuredOutput(BaseModel):
    """Final JSON schema for LLM output."""
    conversation_id: str
    input: List[Dict[str, Any]]
    sentences: List[str]
    entities: List[Entity]
    contextual_tags: Optional[Dict[str, Any]] = Field(default=None)
    pos_tagged_text: Optional[str] = None


# -----------------------------
# Preprocessing
# -----------------------------
class TextPreprocessor:
    """Cleans elderly speech before NLP: casing, fillers, en-SG removal, typo normalization."""

    _FILLERS = [
        r"\buh+\b", r"\bum+\b", r"\bah+\b", r"\bhmm+\b", r"\byou know\b",
        r"\blike\b", r"\bkind of\b", r"\bsort of\b",
    ]
    _EN_SG = [r"\blah\b", r"\bleh\b", r"\blor\b", r"\bmeh\b", r"\bsia\b", r"\bhor\b"]

    def __init__(self, keep_case: bool = True):
        self.keep_case = keep_case

    def sentence_segment(self, text: str) -> List[str]:
        segs = re.split(r"(?<=[\.\!\?])\s+", text.strip())
        segs = [s.strip() for s in segs if s.strip()]
        return segs if segs else [text.strip()]

    def normalize(self, text: str) -> str:
        t = text.strip()
        if not self.keep_case:
            t = t.lower()
        for pat in self._FILLERS + self._EN_SG:
            t = re.sub(pat, "", t, flags=re.IGNORECASE)
        t = re.sub(r"\bI\'m\b", "I am", t)
        t = re.sub(r"\bcan\'t\b", "cannot", t)
        t = re.sub(r"\bwon\'t\b", "will not", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def process(self, text: str) -> Dict[str, Any]:
        cleaned = self.normalize(text)
        sentences = self.sentence_segment(cleaned)
        return {"cleaned": cleaned, "sentences": sentences}


# -----------------------------
# NER + POS + INTERROGATIVE Extraction
# -----------------------------
class NER_POS_Extractor:
    """Extracts both NER and POS, and embeds POS tags directly in text."""

    INTERROGATIVE_WORDS = {"what", "how", "when", "where", "why", "who", "whom", "whose"}

    def __init__(self, model: str = "en_core_web_lg"):
        self.nlp = spacy.load(model)

    def embed_pos_in_text(self, text: str) -> str:
        doc = self.nlp(text)
        pos_embedded_text = text
        for token in reversed(doc):
            pos_tag = "ACTION" if token.pos_ == "VERB" else token.pos_
            pos_embedded_text = (
                pos_embedded_text[:token.idx + len(token.text)]
                + f" <{pos_tag}>"
                + pos_embedded_text[token.idx + len(token.text):]
            )
        return pos_embedded_text

    def extract(self, cleaned_text: str, sentences: List[str]) -> EntityCollection:
        doc = self.nlp(cleaned_text)
        entities: List[Entity] = []

        # 1. NER entities
        for ent in doc.ents:
            entities.append(
                Entity(
                    text=ent.text,
                    label=f"NER_{ent.label_}",
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=1.0,
                )
            )

        # 2. INTERROGATIVE words
        for token in doc:
            if token.text.lower() in self.INTERROGATIVE_WORDS:
                entities.append(
                    Entity(
                        text=token.text,
                        label="INTERROGATIVE",
                        start=token.idx,
                        end=token.idx + len(token.text),
                        confidence=1.0,
                    )
                )

        # 3. Embed POS tags
        pos_embedded_text = self.embed_pos_in_text(cleaned_text)

        return EntityCollection(
            conversation_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            raw_text=pos_embedded_text,
            sentences=sentences,
            entities=entities,
        )


# -----------------------------
# Gemini Postprocessor
# -----------------------------
class GeminiPostProcessor:
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash-lite"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def parse(self, collection: EntityCollection) -> Dict[str, Any]:
        logger.info(f"Raw POS-tagged text: {collection.raw_text}")
        system_prompt = """You are an assistant that converts elderly conversation into structured JSON.
        The language used may be Singlish-based; understand its nuances.
        The schema must look like this:
        {
            "conversation_id": "...",
            "input": [{"role": "user", "content": "..."}],
            "sentences": [...],
            "entities": [
                {"text": "...", "label": "ACTIVITY/FOOD/DATE/EVENT/FACILITY/ACTION/INTERROGATIVE", "start": ..., "end": ...}
            ]
        }
        """

        user_prompt = f"""
        Conversation text (POS-tagged):
        {collection.raw_text}

        NER hints:
        {json.dumps([e.dict() for e in collection.entities if e.label.startswith("NER_")], indent=2)}

        Additional hints (Interrogative words, verbs, etc.):
        {json.dumps([e.dict() for e in collection.entities if e.label == "INTERROGATIVE"], indent=2)}
        """

        response = self.model.generate_content([system_prompt, user_prompt])
        result_text = response.text.strip()

        # Clean output
        if result_text.startswith("```json"):
            result_text = result_text[7:-3].strip()

        match = re.search(r"\{.*\}", result_text, re.DOTALL)
        if match:
            result_text = match.group(0)

        try:
            return json.loads(result_text)
        except Exception as e:
            logger.error(f"Invalid JSON from Gemini: {e}")
            return {"error": f"Invalid JSON from Gemini: {e}", "raw": result_text}


# -----------------------------
# Full Pipeline
# -----------------------------
class NaturalLanguageToJSONPipeline:
    def __init__(self):
        self.pre = TextPreprocessor()
        self.extractor = NER_POS_Extractor()
        self.llm = GeminiPostProcessor(api_key=GEMINI_API_KEY)

    def run(self, text: str) -> Dict[str, Any]:
        logger.info("Beginning preprocessing...")
        prep = self.pre.process(text)

        cleaned, sentences = prep["cleaned"], prep["sentences"]
        logger.info("Starting NER+POS extraction...")
        collection = self.extractor.extract(cleaned, sentences)

        logger.info("Sending to Gemini for structured parsing...")
        structured = self.llm.parse(collection)

        # Inject POS-tagged text
        if isinstance(structured, dict):
            structured["pos_tagged_text"] = collection.raw_text

        logger.info("Validating output schema...")
        try:
            validated = FinalStructuredOutput(**structured)
            return validated.dict()
        except ValidationError as e:
            logger.error("Validation failed during schema validation.")
            return {"error": "Validation failed", "details": e.errors(), "raw": structured}


# -----------------------------
# Example Run
# -----------------------------
if __name__ == "__main__":
    text = "What should I eat today ah"

    pipeline = NaturalLanguageToJSONPipeline()
    output = pipeline.run(text)

    print("\n======== FINAL JSON OUTPUT ========")
    print(json.dumps(output, indent=2, ensure_ascii=False))
