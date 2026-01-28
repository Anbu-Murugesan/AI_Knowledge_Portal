import traceback
from pydantic import BaseModel
from typing import List, Dict, Any, Callable, Optional


class WorkflowState(BaseModel):
    request_id: str
    query: str

    selected_tool: str = "rss"
    selected_blog: Optional[str] = None

    status: str = "initialized"
    retrieved_docs: List[Dict[str, Any]] = []
    retrieved_text: str = ""
    generated_post: Any = ""
    sources: List[Dict[str, str]] = []
    error: Optional[str] = None


class NodeSpec(BaseModel):
    id: str
    func: Callable[..., WorkflowState]
    run_with_query: bool = False


class StateGraph:
    def __init__(self, nodes: List[NodeSpec], edges: List[tuple], start_node: str):
        self.nodes_map = {n.id: n for n in nodes}
        self.edges = edges
        self.start_node = start_node

    def run(self, state: WorkflowState):
        current = self.start_node
        visited = set()
        while current:
            if current in visited:
                state.status = "error"
                state.error = f"cycle detected at node {current}"
                return state
            visited.add(current)
            node = self.nodes_map.get(current)
            if node is None:
                state.status = "error"
                state.error = f"node {current} not found"
                return state
            try:
                if node.run_with_query:
                    state = node.func(state.query, state)
                else:
                    state = node.func(state)
            except Exception as e:
                state.status = "error"
                state.error = f"node execution error: {repr(e)}\n{traceback.format_exc()}"
                return state

            outgoing = [t for (f, t) in self.edges if f == current]
            if not outgoing:
                break
            current = outgoing[0]
        return state
