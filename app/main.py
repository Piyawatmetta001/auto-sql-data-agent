from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.database import init_mock_db
from langchain_core.messages import HumanMessage
import uvicorn

# We import app_agent inside a function or after FastAPI init to be safe, 
# but top-level should be fine if there are no circular imports.
from app.agent import app_agent

app = FastAPI(title="Autonomous AI Data Agent")

@app.on_event("startup")
def startup_event():
    init_mock_db()

class QueryRequest(BaseModel):
    query: str

@app.post("/analyze")
async def analyze_data(request: QueryRequest):
    print(f"--- Received Request: {request.query} ---")
    try:
        # Initialize state with the user's query
        inputs = {"messages": [HumanMessage(content=request.query)]}
        
        print("--- Invoking Agent ---")
        # Run the agent with a recursion limit to prevent infinite loops
        result = app_agent.invoke(inputs, config={"recursion_limit": 10})
        print("--- Agent Execution Finished ---")
        
        # Get the last message from the result
        final_message = result["messages"][-1]
        
        return {
            "status": "success", 
            "response": final_message.content
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5432)
