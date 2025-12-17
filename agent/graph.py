import json
from datetime import date
from typing import Annotated, List, Optional
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from config import config
from agent.prompts import SYSTEM_PROMPT

class AgentState(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    patient_id: Optional[str]
    patient_name: Optional[str]
    # Removed manual "usage" field; handled by callbacks now

async def create_agent_graph(mcp_session):
    tools = await load_mcp_tools(mcp_session)
    
    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        api_key=config.OPENAI_API_KEY,
        temperature=0.6
    ).bind_tools(tools)

    async def chatbot_node(state: AgentState):
        messages = state["messages"]
        patient_id = state.get("patient_id")
        patient_name = state.get("patient_name")

        # --- Identity Recovery Logic ---
        if not patient_id:
            for msg in reversed(messages):
                if msg.type == "tool":
                    try:
                        content = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                        if isinstance(content, dict) and content.get("success"):
                            p_id = content.get("patient_id")
                            p_name = content.get("patient_name")
                            if p_id and p_name:
                                patient_id = p_id
                                patient_name = p_name
                                break
                    except Exception:
                        continue

        # --- Dynamic System Prompt ---
        sys_prompt = SYSTEM_PROMPT.format(current_date=date.today())
        
        if patient_id and patient_name:
            sys_prompt += (
                f"\n\nCURRENT PATIENT CONTEXT:\n"
                f"Name: {patient_name}\n"
                f"ID: {patient_id}\n"
                f"(Identity Verified - Treat 'Hello' as a casual mid-conversation greeting.)"
            )

        messages_with_prompt = [SystemMessage(content=sys_prompt)] + messages
        response = await llm.ainvoke(messages_with_prompt)
        
        # We simply return the state. The CallbackHandler in main.py tracks the tokens.
        return {
            "messages": [response],
            "patient_id": patient_id,
            "patient_name": patient_name
        }

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", chatbot_node)
    workflow.add_node("tools", ToolNode(tools))
    
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")

    return workflow.compile(checkpointer=MemorySaver())