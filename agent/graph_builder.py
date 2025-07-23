from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import (
    gather_financials_node,
    analyze_data_node,
    research_competitors_node,
    compare_performance_node,
    collect_feedback_node,
    research_critique_node,
    write_report_node,
    should_continue
)

def build_graph():
    builder = StateGraph(AgentState)
    builder.set_entry_point("gather_financials")
    builder.add_node("gather_financials", gather_financials_node)
    builder.add_node("analyze_data", analyze_data_node)
    builder.add_node("research_competitors", research_competitors_node)
    builder.add_node("compare_performance", compare_performance_node)
    builder.add_node("collect_feedback", collect_feedback_node)
    builder.add_node("research_critique", research_critique_node)
    builder.add_node("write_report", write_report_node)
    builder.add_conditional_edges("compare_performance", should_continue, {
        END: END,
        "collect_feedback": "collect_feedback",
    })
    builder.add_edge("gather_financials", "analyze_data")
    builder.add_edge("analyze_data", "research_competitors")
    builder.add_edge("research_competitors", "compare_performance")
    builder.add_edge("collect_feedback", "research_critique")
    builder.add_edge("research_critique", "compare_performance")
    builder.add_edge("compare_performance", "write_report")
    return builder.compile()

graph = build_graph()
