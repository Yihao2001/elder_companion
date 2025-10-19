# app.py
import streamlit as st
import json
from module1 import NaturalLanguageToJSONPipeline
from PIL import Image

# ----------------------------
# Page Config
# ----------------------------
st.set_page_config(
    page_title="💙 Prescience Companion Listener",
    page_icon="💬",
    layout="wide"
)

# ----------------------------
# Load Logo
# ----------------------------
logo_path = r"C:\Users\Tay Han\OneDrive - National University of Singapore\Capstone\ElderlyCompanion\prescience_presbyrobotics_private_limited_logo.jpeg"
try:
    logo = Image.open(logo_path)
except Exception as e:
    logo = None
    st.warning(f"⚠️ Could not load logo image. ({e})")

# ----------------------------
# Global Styles (white + blue minimalist)
# ----------------------------
st.markdown("""
<style>
body {
    background-color: #ffffff;
    font-family: "Segoe UI", sans-serif;
    color: #1f2a44;
}

div[data-testid="stAppViewContainer"] {
    background-color: #ffffff;
    padding: 1rem 2rem;
}

/* Top header container */
.header-container {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 25px;
    margin-bottom: 30px;
}

/* Logo styling */
.header-logo {
    width: 200px;  /* 🔹 enlarged logo */
    height: auto;
    border-radius: 10px;
}

/* Brand title */
.header-title {
    font-size: 2rem;
    color: #1b4f72;
    margin: 0;
    padding-top: 10px;
}

/* Accent elements */
h1, h2, h3 {
    color: #1b4f72;
}

.stTextArea textarea {
    background-color: #f9f9f9;
    border: 2px solid #b3cde0;
    border-radius: 10px;
    color: #1f2a44;
    font-size: 1.1rem;
}
.stTextArea textarea:focus {
    border-color: #4a90e2;
    box-shadow: 0 0 0 2px rgba(74,144,226,0.2);
}

button[kind="primary"] {
    background-color: #4a90e2 !important;
    color: white !important;
    border-radius: 8px !important;
    font-size: 1.05rem !important;
    padding: 0.6rem 1.2rem !important;
}

hr {
    border: 0;
    height: 1px;
    background-color: #d0e2f2;
    margin: 30px 0;
}

footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ----------------------------
# Layout: Two Columns
# ----------------------------
left_col, right_col = st.columns([1.2, 1])  # left slightly wider

# ----------------------------
# LEFT COLUMN: Chat Input
# ----------------------------
with left_col:
    st.markdown("""
    <div style='text-align:left;'>
        <h1 style='color:#1b4f72;'>💙 Hello There!</h1>
        <p style='font-size:1.15rem; color:#2c3e50; line-height:1.6;'>
            I’m your friendly <b>Prescience Companion</b> — always here to listen,  
            comfort, and help you feel heard.<br><br>
            Just tell me what’s on your mind 🕊️
        </p>
    </div>
    """, unsafe_allow_html=True)

    user_input = st.text_area(
        "💬 What would you like to share today?",
        height=150,
        placeholder="For example: I felt dizzy after taking my medicine this morning.",
    )

    @st.cache_resource
    def load_pipeline():
        return NaturalLanguageToJSONPipeline()

    pipeline = load_pipeline()

    if st.button("💠 Share with Me"):
        if not user_input.strip():
            st.warning("Please tell me something first — I’m listening 💙")
        else:
            with st.spinner("Thinking carefully about what you said... ⏳"):
                try:
                    output = pipeline.run(user_input.strip())
                    st.session_state["structured_output"] = output
                    st.success("✅ Thank you for sharing that with me!")
                except Exception as e:
                    st.error("❌ Oh no! I had a bit of trouble understanding that. Please try again.")
                    st.exception(e)

# ----------------------------
# RIGHT COLUMN: Output
# ----------------------------
with right_col:
    st.markdown("### 🧩 My Understanding (Structured JSON)")
    if "structured_output" in st.session_state:
        output = st.session_state["structured_output"]
        st.json(output)
        st.download_button(
            label="💾 Save as JSON",
            data=json.dumps(output, indent=2, ensure_ascii=False),
            file_name="structured_output.json",
            mime="application/json"
        )
        st.caption("✨ Your message isn’t stored online — everything runs safely here.")
    else:
        st.info("Your structured understanding will appear here after you share your message 💬")

# ----------------------------
# Footer
# ----------------------------
st.markdown("""
<hr>
<p style='text-align:center; color:#5d6d7e; font-size:0.9rem;'>
💙 Built with care by <b>Prescience Presby Robotics</b> — making technology gentle, safe, and human.<br>
Your words matter. I’m always here to listen.
</p>
""", unsafe_allow_html=True)

# ----------------------------
# Header
# ----------------------------
if logo:
    st.markdown("<div class='header-container'>", unsafe_allow_html=True)
    st.image(logo, width=200)  # 🔹 bigger image

    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown("<h2 style='color:#1b4f72;'>Prescience Presbyrobotics</h2>", unsafe_allow_html=True)
