from fastapi import FastAPI
from pydantic import BaseModel

from agent.agent import DatabaseAgent


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

conversations: dict[str, list[dict]] = {}


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

    # Get existing conversation history.
    history = conversations.get(
        request.conversation_id,
        []
    )

    # Run the agent with the previous conversation.
    answer = agent.run(
        user_message=request.message,
        history=history,
    )

    # Store the user's message.
    history.append(
        {
            "role": "user",
            "content": request.message,
        }
    )

    # Store the assistant's response.
    history.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )

    # Save the updated conversation.
    conversations[request.conversation_id] = history

    return ChatResponse(
        answer=answer
    )