from fastapi import FastAPI
from pydantic import BaseModel

from agent.agent import DatabaseAgent


# --------------------------------------------------
# Create FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="AI Database Agent API",
)


# --------------------------------------------------
# Create the agent once when the API starts.
#
# We don't want to create a new Ollama client
# for every request.
# --------------------------------------------------

agent = DatabaseAgent()


# --------------------------------------------------
# Request schema
# --------------------------------------------------

class ChatRequest(BaseModel):
    message: str


# --------------------------------------------------
# Response schema
# --------------------------------------------------

class ChatResponse(BaseModel):
    answer: str


# --------------------------------------------------
# Chat endpoint
# --------------------------------------------------

@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    # Send the user's question to the AI agent.
    answer = agent.run(request.message)

    # Return a clean JSON response to the frontend.
    return ChatResponse(
        answer=answer
    )