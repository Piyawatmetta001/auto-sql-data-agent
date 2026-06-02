import os
from dotenv import load_dotenv
from typing import TypedDict, List, Annotated
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from app.tools import run_sqlite_query
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langgraph.graph.message import add_messages

load_dotenv()

# Define the state for the agent with a reducer
class AgentState(TypedDict):
    # 'add_messages' will append new messages to the existing list instead of overwriting
    messages: Annotated[List[BaseMessage], add_messages]

# Initialize tools
tools = [run_sqlite_query]
tool_nodes = ToolNode(tools)

# Initialize the Groq model
# Note: Ensure GROQ_API_KEY is in your .env
model = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
model_with_tools = model.bind_tools(tools)

system_prompt = SystemMessage(content="""You are an expert Data Analyst and SQL Developer.
Your task is to answer questions about sales data by generating precise SQLite queries.

Database Schema:
- Table: 'transactions'
- Columns: 
    - 'id' (INTEGER): Unique ID
    - 'product_name' (TEXT): Name of the product
    - 'category' (TEXT): Category of the product (e.g., Electronics, Accessories)
    - 'amount' (REAL): The price or sales amount (Important: Use this for 'highest', 'top', 'total' calculations)
    - 'sales_date' (DATE): Date of transaction (YYYY-MM-DD)

SQL Guidelines:
1. For 'Top 5' or 'Highest', use 'ORDER BY amount DESC LIMIT 5'.
2. For 'Total sales', use 'SUM(amount)'.
3. Always check the column names correctly before writing the query.
4. Output only the final answer based on the data provided by the tool.

Always use the 'run_sqlite_query' tool to fetch data before answering.""")

def call_model(state: AgentState):
    print(f"--- Calling Model with {len(state['messages'])} messages ---")
    messages = [system_prompt] + state["messages"]
    response = model_with_tools.invoke(messages)
    print(f"--- Model Response: {response.content[:50]}... (Tool calls: {getattr(response, 'tool_calls', [])}) ---")
    return {"messages": [response]}

def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    print(f"--- Checking if should continue. Last message: {type(last_message)} ---")
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        print(f"--- Continuing to Action (Tool calls found) ---")
        return "continue"
    print("--- Ending Workflow ---")
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
