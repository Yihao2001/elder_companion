from typing import Dict, Any
from module_2.graph_flow import build_classification_graph


class RouterGraph:
    def __init__(self):
        self.graph = build_classification_graph()

    def invoke(self, input_state: Dict[str, Any]) -> Dict[str, Any]:
        return self.graph.invoke(input_state)

    # Optional: add streaming support
    def stream(self, input_state: Dict[str, Any]):
        return self.graph.stream(input_state)