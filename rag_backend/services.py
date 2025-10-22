from moduel_1.module1 import NaturalLanguageToJSONPipeline
from module_2.router_graph import RouterGraph
from module_2.states import FlowRequest, FlowResponse
from module_3.session_context import SessionContext
from module_3.offline_graph import OfflineGraph
from module_3.online_graph import OnlineGraph


class Services:
    def __init__(self, 
            pipeline: NaturalLanguageToJSONPipeline,
            router: RouterGraph,
            session_ctx: SessionContext,
            offline_graph: OfflineGraph,
            online_graph: OnlineGraph
        ):
        self.pipeline = pipeline
        self.router = router
        self.session_ctx = session_ctx
        self.offline_graph = offline_graph
        self.online_graph = online_graph