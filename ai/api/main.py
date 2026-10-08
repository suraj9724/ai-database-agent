from fastapi import FastAPI
from pydantic import BaseModel

from agent.agent import DatabaseAgent

from tools.conversation_tools import (
    create_conversation,
    save_message,
    get_conversation_history,
)

# --------------------------------------------------
# Create FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="AI Database Agent API"
)


# --------------------------------------------------
# Create the AI agent once when the API starts.
# --------------------------------------------------

agent = DatabaseAgent()


# --------------------------------------------------
# Store conversation history.
#
# Key   -> conversation ID
# Value -> list of previous messages
#
# This is intentionally simple for Project 4.
# Later we can move this to Redis/PostgreSQL.
# --------------------------------------------------



# --------------------------------------------------
# Request schema
# --------------------------------------------------

class ChatRequest(BaseModel):
    conversation_id: str
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

    # Make sure the conversation exists.
    create_conversation(
        request.conversation_id
    )

    # Load previous messages from PostgreSQL.
    history = get_conversation_history(
        request.conversation_id
    )

    # Run the AI agent with conversation history.
    answer = agent.run(
        user_message=request.message,
        history=history,
    )

    # Store the user's message.
    save_message(
        conversation_id=request.conversation_id,
        role="user",
        content=request.message,
    )

    # Store the AI response.
    save_message(
        conversation_id=request.conversation_id,
        role="assistant",
        content=answer,
    )

    return ChatResponse(
        answer=answer
    )