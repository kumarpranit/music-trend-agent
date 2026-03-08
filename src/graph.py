from langgraph.graph import END, StateGraph

from src.agents.analyst import run_analyst_agent
from src.agents.collector import run_collector_agent
from src.agents.reporter import run_reporter_agent
from src.state import MusicState


def build_graph():
    graph = StateGraph(MusicState)

    graph.add_node("collector", run_collector_agent)
    graph.add_node("analyst", run_analyst_agent)
    graph.add_node("reporter", run_reporter_agent)

    graph.set_entry_point("collector")

    graph.add_edge("collector", "analyst")
    graph.add_edge("analyst", "reporter")
    graph.add_edge("reporter", END)

    return graph.compile()