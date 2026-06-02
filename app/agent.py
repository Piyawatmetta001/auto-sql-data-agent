import os
from dotenv import load_dotenv
from typing import TypedDict, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from app.tools import run_sqlite_query
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage

load_dotenv()

# Define the state for the agent
class AgentState(TypedDict):
    message: List[BaseMessage]

# Initialize tools
tools = [run_sqlite_query]
tool_nodes = ToolNode(tools)

# Initialize the Gemini model
# Note: Ensure GOOGLE_API_KEY is in your .env
model = ChatGoogleGenerativeAI(model="gemini-3.1-flash-live-preview", temperature=0)
model_with_tools = model.bind_tools(tools)

system_prompt = SystemMessage(content="""You are a helpful assistant for analyzing sales data. 
You have access to a SQL tool for the 'transactions' table which has columns: 'id', 'product_name', 'category', 'amount', 'sales_date'.
Always use the 'run_sqlite_query' tool to fetch data before answering questions about sales.""")

def call_model(state: AgentState):
    messages = [system_prompt] + state["message"]
    response = model_with_tools.invoke(messages)
    return {"message": [response]}

def should_continue(state: AgentState):
    last_message = state["message"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"
    return "end"

# Build the graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("action", tool_nodes)

workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "action",
        "end": END
    }
)
workflow.add_edge("action", "agent")

app_agent = workflow.compile()
