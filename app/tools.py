import sqlite3
import pandas as pd
from langchain_core.tools import tool

@tool
def run_sqlite_query(query: str) -> str:
    """Run a sqlite query on the sales database. Use this to fetch data from the transactions table."""
    forbidden_keywords = ['drop', 'delete', 'update', 'insert', 'truncate']
    if any(keyword in query.lower() for keyword in forbidden_keywords):
        return "Error: Query contains forbidden keywords."
    try:
        conn = sqlite3.connect('sales.db')
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_string()
    except Exception as e:
        return f"Error executing query: {str(e)}"
