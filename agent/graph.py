# import json
# from datetime import date
# # from langchain_groq import ChatGroq
# from langchain_openai import ChatOpenAI
# from langgraph.graph import StateGraph, START, END
# from langgraph.prebuilt import tools_condition, ToolNode
# from langgraph.checkpoint.memory import MemorySaver
# from langchain_core.messages import SystemMessage
# from langchain_mcp_adapters.tools import load_mcp_tools

# from config import config
# from agent.state import AgentState
# from agent.prompts import SYSTEM_PROMPT

# # Import tools file to ensure they are registered with FastMCP
# import mcp_server.tools 

# async def create_agent_graph(mcp_session):
#     # 1. Load Tools from MCP Session
#     # This magic function converts FastMCP tools into LangChain tools
#     tools = await load_mcp_tools(mcp_session)
    
#     # 2. Initialize Groq (Llama 3)
#     # llm = ChatGroq(
#     #     model=config.GROQ_MODEL,
#     #     api_key=config.GROQ_API_KEY,
#     #     temperature=0.0
#     # ).bind_tools(tools)

#     # 2. Initialize OpenAI (GPT-4o) <-- CHANGED
#     llm = ChatOpenAI(
#         model=config.OPENAI_MODEL,
#         api_key=config.OPENAI_API_KEY,
#         temperature=0.0
#     ).bind_tools(tools)

#     # 3. Define the Chatbot Logic
#     async def chatbot_node(state: AgentState):
#         sys_msg = SystemMessage(content=SYSTEM_PROMPT.format(current_date=date.today()))
#         messages = [sys_msg] + state["messages"]

#         response = await llm.ainvoke(messages)

#         # Extract patient_id from tool calls in history
#         patient_id = state.get("patient_id")

#         for msg in reversed(state["messages"]):
#             if msg.type == "tool":
#                 try:
#                     content = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
#                     if content.get("success") and content.get("patient_id"):
#                         patient_id = content["patient_id"]
#                         break
#                 except:
#                     continue

#         return {
#             "messages": [response],
#             "patient_id": patient_id  # This persists across turns!
#         }

#     # 4. Build Graph
#     workflow = StateGraph(AgentState)
#     workflow.add_node("agent", chatbot_node)
#     workflow.add_node("tools", ToolNode(tools))

#     workflow.add_edge(START, "agent")
#     workflow.add_conditional_edges("agent", tools_condition)
#     workflow.add_edge("tools", "agent")

#     return workflow.compile(checkpointer=MemorySaver())

import json
from datetime import date
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage
from langchain_mcp_adapters.tools import load_mcp_tools

from config import config
from agent.state import AgentState
from agent.prompts import SYSTEM_PROMPT

async def create_agent_graph(mcp_session):
    tools = await load_mcp_tools(mcp_session)
    
    # Higher temp for slightly more natural, less robotic responses
    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        api_key=config.OPENAI_API_KEY,
        temperature=0.6 
    ).bind_tools(tools)

    async def chatbot_node(state: AgentState):
        messages = state["messages"]
        patient_id = state.get("patient_id")
        patient_name = state.get("patient_name")

        # Aggressively extract patient name from latest successful tool call
        for msg in reversed(messages[-10:]):  # look back last 10 messages
            if msg.type == "tool":
                try:
                    content = msg.content
                    if isinstance(content, str):
                        content = json.loads(content)
                    if content.get("success") and content.get("patient_name"):
                        patient_name = content["patient_name"]
                        patient_id = content["patient_id"]
                        break
                    if content.get("success") and content.get("patient_id"):
                        # fallback lookup
                        for pid, data in DUMMY_PATIENTS.items():
                            if data.get("patient_id") == content["patient_id"]:
                                patient_name = data["first_name"]
                                patient_id = pid
                                break
                except:
                    continue

        system_content = SYSTEM_PROMPT.format(current_date=date.today())
        if patient_name:
            system_content += f"\n\nCURRENT PATIENT: {patient_name} (ID: {patient_id})"

        system_msg = SystemMessage(content=system_content)

        response = await llm.ainvoke([system_msg] + messages)

        return {
            "messages": [response],
            "patient_id": patient_id or state.get("patient_id"),
            "patient_name": patient_name or state.get("patient_name"),
        }

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", chatbot_node)
    workflow.add_node("tools", ToolNode(tools))

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")

    return workflow.compile(checkpointer=MemorySaver())