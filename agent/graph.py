import json
from datetime import date
# from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage
from langchain_mcp_adapters.tools import load_mcp_tools

from config import config
from agent.state import AgentState
from agent.prompts import SYSTEM_PROMPT

# Import tools file to ensure they are registered with FastMCP
import mcp_server.tools 

async def create_agent_graph(mcp_session):
    # 1. Load Tools from MCP Session
    # This magic function converts FastMCP tools into LangChain tools
    tools = await load_mcp_tools(mcp_session)
    
    # 2. Initialize Groq (Llama 3)
    # llm = ChatGroq(
    #     model=config.GROQ_MODEL,
    #     api_key=config.GROQ_API_KEY,
    #     temperature=0.0
    # ).bind_tools(tools)

    # 2. Initialize OpenAI (GPT-4o) <-- CHANGED
    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        api_key=config.OPENAI_API_KEY,
        temperature=0.0
    ).bind_tools(tools)

    # 3. Define the Chatbot Logic
    async def chatbot_node(state: AgentState):
        # Inject dynamic date into prompt
        sys_msg = SystemMessage(content=SYSTEM_PROMPT.format(current_date=date.today()))
        
        # Invoke LLM
        messages = [sys_msg] + state["messages"]
        response = await llm.ainvoke(messages)
        
        # State Update Logic (Capture patient_id from tool outputs)
        patient_id = state.get("patient_id")
        
        # If the last message was a tool response, check if it returned a patient_id
        if len(state["messages"]) > 0 and state["messages"][-1].type == "tool":
            try:
                content = json.loads(state["messages"][-1].content)
                if isinstance(content, dict) and content.get("success") and "patient_id" in content:
                    patient_id = content["patient_id"]
            except:
                pass # Ignore parse errors
                
        return {"messages": [response], "patient_id": patient_id}

    # 4. Build Graph
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", chatbot_node)
    workflow.add_node("tools", ToolNode(tools))

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")

    return workflow.compile(checkpointer=MemorySaver())