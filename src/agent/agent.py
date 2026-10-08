import json

from ollama import Client

from agent.tools import (
    TOOL_DEFINITIONS,
    TOOL_FUNCTIONS,
)


class DatabaseAgent:

    def __init__(
        self,
        model: str = "llama3.2:3b",
    ):
        """
        Initialize the Ollama client.

        The model can be changed later without changing
        the rest of the agent architecture.
        """

        self.model = model

        self.client = Client(
            host="http://localhost:11434"
        )

    def run(self, user_message: str) -> str:
        """
        Process a user request.

        The agent may:
            1. Ask the LLM what tool to use.
            2. Execute that tool.
            3. Give the result back to the LLM.
            4. Return the final natural-language answer.
        """

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a business data assistant. "
                    "Use the available tools to answer questions "
                    "about invoices, customers, payments, revenue, "
                    "and outstanding amounts. "
                    "Never invent database information. "
                    "If database information is required, use a tool."
                ),
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]

        # --------------------------------------------------
        # Ask the LLM what it wants to do.
        # --------------------------------------------------

        response = self.client.chat(
            model=self.model,
            messages=messages,
            tools=TOOL_DEFINITIONS,
        )

        assistant_message = response["message"]

        # Add the LLM response to the conversation.
        messages.append(assistant_message)

        # --------------------------------------------------
        # Check whether the LLM requested a tool.
        # --------------------------------------------------

        tool_calls = assistant_message.get("tool_calls", [])

        if not tool_calls:
            # The LLM answered without needing the database.
            return assistant_message["content"]

        # --------------------------------------------------
        # Execute every requested tool.
        # --------------------------------------------------

        for tool_call in tool_calls:

            function_name = tool_call["function"]["name"]

            arguments = tool_call["function"].get(
                "arguments",
                {},
            )

            # Ollama may return arguments as a JSON string.
            if isinstance(arguments, str):
                arguments = json.loads(arguments)

            function = TOOL_FUNCTIONS.get(function_name)

            if function is None:
                raise ValueError(
                    f"Unknown tool requested: {function_name}"
                )

            # Execute our controlled Python function.
            result = function(**arguments)

            # Send the tool result back to the LLM.
            messages.append(
                {
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(
                        result,
                        default=str,
                    ),
                }
            )

        # --------------------------------------------------
        # Ask the LLM to turn the database result into
        # a natural-language answer.
        # --------------------------------------------------

        final_response = self.client.chat(
            model=self.model,
            messages=messages,
            tools=TOOL_DEFINITIONS,
        )

        return final_response["message"]["content"]