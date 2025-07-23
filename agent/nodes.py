import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from tavily import TavilyClient
import pandas as pd
from io import StringIO

from .state import AgentState, Queries
from .prompts import *

load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
tavily_key = os.getenv("TAVILY_API_KEY")
model = ChatOpenAI(api_key=openai_key, model="gpt-4o-mini")
tavily = TavilyClient(api_key=tavily_key)

def gather_financials_node(state: AgentState):
    csv_file = state["csv_file"]
    df = pd.read_csv(StringIO(csv_file))
    financial_data_str = df.to_string(index=False)
    combined_content = f"{state['task']}\n\nHere is the financial data:\n\n{financial_data_str}"
    messages = [SystemMessage(content=GATHER_FINANCIALS_PROMPT), HumanMessage(content=combined_content)]
    response = model.invoke(messages)
    return {"financial_data": response.content}

def analyze_data_node(state: AgentState):
    messages = [SystemMessage(content=ANALYZE_DATA_PROMPT), HumanMessage(content=state["financial_data"])]
    response = model.invoke(messages)
    return {"analysis": response.content}

def research_competitors_node(state: AgentState):
    content = state["content"] or []
    for competitor in state["competitors"]:
        queries = model.with_structured_output(Queries).invoke([
            SystemMessage(content=RESEARCH_COMPETITORS_PROMPT),
            HumanMessage(content=competitor),
        ])
        for q in queries.queries:
            response = tavily.search(query=q, max_results=2)
            for r in response["results"]:
                content.append(r["content"])
    return {"content": content}

def compare_performance_node(state: AgentState):
    content = "\n\n".join(state["content"] or [])
    user_message = HumanMessage(content=f"{state['task']}\n\nHere is the financial analysis:\n\n{state['analysis']}")
    messages = [
        SystemMessage(content=COMPETE_PERFORMANCE_PROMPT.format(content=content)),
        user_message,
    ]
    response = model.invoke(messages)
    return {
        "comparison": response.content,
        "revision_number": state.get("revision_number", 1) + 1,
    }

def collect_feedback_node(state: AgentState):
    messages = [SystemMessage(content=FEEDBACK_PROMPT), HumanMessage(content=state["comparison"])]
    response = model.invoke(messages)
    return {"feedback": response.content}

def research_critique_node(state: AgentState):
    queries = model.with_structured_output(Queries).invoke([
        SystemMessage(content=RESEARCH_CRITIQUE_PROMPT),
        HumanMessage(content=state["feedback"]),
    ])
    content = state["content"] or []
    for q in queries.queries:
        response = tavily.search(query=q, max_results=2)
        for r in response["results"]:
            content.append(r["content"])
    return {"content": content}

def write_report_node(state: AgentState):
    messages = [SystemMessage(content=WRITE_REPORT_PROMPT), HumanMessage(content=state["comparison"])]
    response = model.invoke(messages)
    return {"report": response.content}

def should_continue(state):
    from langgraph.graph import END
    return END if state["revision_number"] > state["max_revisions"] else "collect_feedback"
