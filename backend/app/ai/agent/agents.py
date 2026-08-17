from dataclasses import dataclass

from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field
from ai.agent.data_research_agent import data_research_agent
from ai.agent.oa_assistant import oa_assistant
from ai.agent.multi_agent import supervisor_agent


DEFAULT_AGENT = "data-research-agent"


class AgentInfo(BaseModel):
    """Info about an available agent."""

    key: str = Field(
        description="Agent key.",
        examples=["data-research-agent"],
    )
    description: str = Field(
        description="Description of the agent.",
        examples=["A tool-using data research agent."],
    )


@dataclass
class Agent:
    description: str
    graph: CompiledStateGraph


agents: dict[str, Agent] = {
    "data-research-agent": Agent(
        description="A LangGraph agent for retrieval, SQL analysis, and calculator-driven research.",
        graph=data_research_agent,
    ),
    "oa-assistant": Agent(description="A legacy HR assistant example.", graph=oa_assistant),
    "multi-agent-supervisor": Agent(description="A supervisor-based multi-agent example.", graph=supervisor_agent),
}


def get_agent(agent_id: str) -> CompiledStateGraph:
    """Get agent by agent_id."""
    return agents[agent_id].graph


def get_all_agent_info() -> list[AgentInfo]:
    return [
        AgentInfo(key=agent_id, description=agent.description) for agent_id, agent in agents.items()
    ]
