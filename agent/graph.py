# agent/graph.py
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

# =============================================================================
# STATE DEFINITION
# =============================================================================
class AgentState(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    patient_id: Optional[str]
    patient_name: Optional[str]
    
    # Optional flags for flow control (populated by logic or LLM if needed)
    new_patient: Optional[bool]
    pending_name: Optional[dict]
    pending_dob: Optional[bool]

# =============================================================================
# GRAPH BUILDER
# =============================================================================
async def create_agent_graph(mcp_session):
    # 1. Load Tools (includes lookup_patient, register_patient, etc.)
    tools = await load_mcp_tools(mcp_session)
    
    # 2. Initialize LLM
    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        api_key=config.OPENAI_API_KEY,
        temperature=0.6 
    ).bind_tools(tools)

    # 3. Define the Chatbot Node
    async def chatbot_node(state: AgentState):
        messages = state["messages"]
        
        # Load existing identity from state
        patient_id = state.get("patient_id")
        patient_name = state.get("patient_name")

        # ---------------------------------------------------------------------
        # CRITICAL: Identity Recovery Logic
        # If we don't have the ID yet, check the tool history.
        # We look for successful 'lookup_patient' OR 'register_patient' calls.
        # ---------------------------------------------------------------------
        if not patient_id:
            for msg in reversed(messages):
                if msg.type == "tool":
                    try:
                        # Parse tool output
                        content = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                        
                        if isinstance(content, dict) and content.get("success"):
                            # Check if this tool gave us an ID (works for lookup AND register)
                            p_id = content.get("patient_id")
                            p_name = content.get("patient_name")
                            
                            if p_id and p_name:
                                patient_id = p_id
                                patient_name = p_name
                                # Stop searching once found
                                break
                    except Exception:
                        continue

        # 4. Build System Prompt
        # We format the date and inject the identity if known
        sys_prompt = SYSTEM_PROMPT.format(current_date=date.today())
        
        if patient_id and patient_name:
            # Identity Injection: Keeps the LLM focused on the current user
            sys_prompt += (
                f"\n\nCURRENT PATIENT CONTEXT:\n"
                f"Name: {patient_name}\n"
                f"ID: {patient_id}\n"
                f"(Identity Verified - Do NOT ask for name/DOB again. Proceed to booking.)"
            )
        
        # 5. Invoke LLM
        # Prepend System Message to the conversation history
        messages_with_prompt = [SystemMessage(content=sys_prompt)] + messages
        response = await llm.ainvoke(messages_with_prompt)

        # 6. Return State Updates
        # We ensure patient_id/name are persisted to the next turn
        return {
            "messages": [response],
            "patient_id": patient_id,
            "patient_name": patient_name
        }

    # 4. Define Workflow
    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent", chatbot_node)
    workflow.add_node("tools", ToolNode(tools))

    workflow.add_edge(START, "agent")
    
    # Conditional edge: If LLM calls a tool -> go to "tools", else END
    workflow.add_conditional_edges("agent", tools_condition)
    
    # Return from tools back to agent to interpret result
    workflow.add_edge("tools", "agent")

    return workflow.compile(checkpointer=MemorySaver())