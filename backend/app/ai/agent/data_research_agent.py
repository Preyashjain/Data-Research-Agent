from __future__ import annotations

import json
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, MessagesState, StateGraph

from ai.llm import get_model, settings
from ai.tools.research_tools import calculator_tool, retrieval_tool, sql_data_tool


class ResearchState(MessagesState):
    question: str
    selected_tool: str | None
    tool_results: list[dict]
    intermediate: list[str]
    final_answer: str | None


def _extract_question(state: ResearchState) -> str:
    messages = state.get("messages", [])
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return str(msg.content)
    return ""


def _route_question(question: str) -> str:
    q = question.lower()
    if any(keyword in q for keyword in ["document", "architecture", "deployment", "playbook", "handbook", "describe", "what does"]):
        return "retrieval"
    if any(keyword in q for keyword in ["calculate", "percent", "percentage", "average", "median", "sum", "difference", "growth"]):
        return "calculator"
    if any(keyword in q for keyword in ["average", "revenue", "profit", "customers", "compare", "growth", "percentage", "metric", "dataset", "year", "region", "quarter", "conversion"]):
        return "sql"
    return "retrieval"


async def initialize_question(state: ResearchState, config: RunnableConfig) -> ResearchState:
    question = _extract_question(state)
    return {"question": question, "selected_tool": _route_question(question), "intermediate": [f"Question captured: {question[:120]}"]}


async def router_node(state: ResearchState, config: RunnableConfig) -> ResearchState:
    question = state.get("question") or _extract_question(state)
    selected_tool = _route_question(question)
    return {"selected_tool": selected_tool, "intermediate": [f"Selected tool: {selected_tool}"]}


async def retrieval_node(state: ResearchState, config: RunnableConfig) -> ResearchState:
    query = state["question"]
    response = await retrieval_tool.ainvoke({"query": query})
    return {"tool_results": [{"tool": "retrieval_tool", "result": response}], "intermediate": ["Retrieved documentation context."]}


async def sql_node(state: ResearchState, config: RunnableConfig) -> ResearchState:
    question = state["question"]
    response = await sql_data_tool.ainvoke({"question": question})
    return {"tool_results": [{"tool": "sql_data_tool", "result": response}], "intermediate": ["Executed safe SQL analysis."]}


async def calculator_node(state: ResearchState, config: RunnableConfig) -> ResearchState:
    question = state["question"]
    lowered = question.lower()
    try:
        if "percentage" in lowered or "percent" in lowered:
            values = []
            for token in question.replace("%", " ").split():
                try:
                    values.append(float(token))
                except ValueError:
                    pass
            if len(values) >= 2:
                response = calculator_tool.invoke({"values": values[-2:], "operation": "percent_change"})
            else:
                response = {"error": "No numeric values found for percentage calculation."}
        else:
            response = {"error": "Calculator was not needed for this question."}
    except Exception as exc:
        response = {"error": f"Calculator failure: {exc}"}
    return {"tool_results": [{"tool": "calculator_tool", "result": response}], "intermediate": ["Computed numeric summary."]}


async def resolve_answer(state: ResearchState, config: RunnableConfig) -> ResearchState:
    model = get_model(config["configurable"].get("model", settings.DEFAULT_MODEL))
    tool_results = state.get("tool_results", [])
    context = "\n".join(json.dumps(item, default=str) for item in tool_results)
    system_prompt = (
        "You are the Data Research Agent. Answer using the supplied evidence. "
        "Be explicit about whether the evidence came from retrieval, SQL, or calculator tools. "
        "If there is not enough evidence, say so instead of guessing."
    )
    response = await model.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Question: {state['question']}\n\nEvidence:\n{context}"),
    ])
    return {"final_answer": response.content}


agent = StateGraph(ResearchState)
agent.add_node("initialize", initialize_question)
agent.add_node("router", router_node)
agent.add_node("retrieval", retrieval_node)
agent.add_node("sql", sql_node)
agent.add_node("calculator", calculator_node)
agent.add_node("finalize", resolve_answer)

agent.set_entry_point("initialize")
agent.add_edge("initialize", "router")
agent.add_conditional_edges(
    "router",
    lambda state: state["selected_tool"],
    {
        "retrieval": "retrieval",
        "sql": "sql",
        "calculator": "calculator",
    },
)
agent.add_edge("retrieval", "finalize")
agent.add_edge("sql", "finalize")
agent.add_edge("calculator", "finalize")
agent.add_edge("finalize", END)

data_research_agent = agent.compile(checkpointer=MemorySaver())
data_research_agent.name = "data-research-agent"
