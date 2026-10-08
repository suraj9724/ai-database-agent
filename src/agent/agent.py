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
        Process a user request using an iterative tool-calling loop.

        The LLM can request multiple tools across multiple turns
        before producing the final answer.
        """

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a business data assistant.\n\n"

                    "Use the available tools to answer questions "
                    "about invoices, customers, payments, revenue, "
                    "and outstanding amounts.\n\n"

                    "IMPORTANT RULES:\n"
                    "1. Never invent database information.\n"
                    "2. Only state facts returned by tools.\n"
                    "3. If the user asks for information that "
                    "requires multiple pieces of data, call all "
                    "necessary tools before answering.\n"
                    "4. Never create invoice numbers, amounts, "
                    "customers, dates, or other business data "
                    "yourself.\n"
                    "5. If the available tools cannot answer the "
                    "question, clearly say so.\n"
                    "6. NEVER perform arithmetic on financial values returned "
                    "by tools. Use the exact numbers returned by the tools. "
                    "Do not recalculate subtotal, GST, invoice total, outstanding "
                    "amount, payment amount, or any other financial value.\n"
                    "7. When listing database records, copy identifiers and "
                    "numeric values exactly as returned by the tool. "
                    "Never change, round, combine, or reconstruct them.\n"
                ),
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]

        # --------------------------------------------------
        # Keep asking the LLM what it wants to do until
        # it decides that it has enough information to answer.
        # --------------------------------------------------

        while True:

            response = self.client.chat(
                model=self.model,
                messages=messages,
                tools=TOOL_DEFINITIONS,
            )

            assistant_message = response["message"]

            # Add the assistant's message to the conversation.
            messages.append(assistant_message)

            # --------------------------------------------------
            # Check whether the LLM requested any tools.
            # --------------------------------------------------

            tool_calls = assistant_message.get(
                "tool_calls",
                [],
            )

            # No tool call means the LLM has produced
            # its final answer.
            if not tool_calls:
                return assistant_message["content"]

            # --------------------------------------------------
            # Execute every tool requested in this turn.
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

                # Temporary debugging while we learn the agent.
                print(
                    f"\nTOOL: {function_name}"
                )
                print(
                    f"ARGUMENTS: {arguments}"
                )

                if function is None:
                    result = {
                        "error": f"Unknown tool requested: {function_name}"
                    }
                else:
                    # --------------------------------------------------
                    # Execute the controlled Python function.
                    # --------------------------------------------------
                    try:
                        result = function(**arguments)
                    except Exception as e:
                        result = {"error": str(e)}

                print(
                    f"RESULT: {result}"
                )

                # --------------------------------------------------
                # Give the tool result back to the LLM.
                # --------------------------------------------------

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