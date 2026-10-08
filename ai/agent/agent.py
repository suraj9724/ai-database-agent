import json

from ollama import Client

from agent.tools import (
    TOOL_DEFINITIONS,
    TOOL_FUNCTIONS,
)
from agent.validator import validate_financial_values


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

    def run(
        self, 
        user_message: str,
        history: list[dict] | None = None
    ) -> str:
        """
        Process a user request using an iterative tool-calling loop.

        The LLM can request multiple tools across multiple turns
        before producing the final answer.
        """

        # --------------------------------------------------
        # Start with previous conversation history if provided.
        # --------------------------------------------------

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
                    "6. NEVER perform arithmetic on financial values "
                    "returned by tools. Use the exact numbers returned "
                    "by the tools.\n"
                    "7. When listing database records, copy identifiers "
                    "and numeric values exactly as returned by the tool.\n"

                    "8. When the user asks which invoices make up a "
                    "customer's outstanding amount, use "
                    "get_customer_outstanding_details().\n"

                    "9. If a follow-up question refers to information "
                    "from the previous conversation, use the conversation "
                    "context to identify the customer or subject before "
                    "selecting a tool.\n"

                    "10. Do not search for invoices by amount when the "
                    "user asks which invoices make up an outstanding "
                    "balance. Retrieve the customer's outstanding "
                    "details instead.\n"
        ),
            }
        ]

        # Add previous conversation messages.
        if history:
            messages.extend(history)

        # Add the new user question.
        messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        # --------------------------------------------------
        # Keep asking the LLM what it wants to do until
        # it decides that it has enough information to answer.
        # --------------------------------------------------
        # --------------------------------------------------
        # Store all tool results produced during this run.
        #
        # These results are the source of truth when validating
        # the LLM's final response.
        # --------------------------------------------------

        tool_results = []
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

                final_answer = assistant_message["content"]

                # --------------------------------------------------
                # Validate financial values before returning the
                # answer to the user.
                # --------------------------------------------------

                is_valid, invalid_values = validate_financial_values(
                    final_answer,
                    tool_results,
                )

                if not is_valid:

                    print("\nVALIDATION FAILED")
                    print(f"Invalid financial values: {invalid_values}")

                    # Ask the LLM to correct its answer using the exact
                    # structured database results already returned by tools.
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "Your previous answer contained an incorrect "
                                "financial value.\n\n"
                                "Rewrite your answer using ONLY the exact "
                                "financial values from the tool results.\n"
                                "Do not calculate or modify any amount.\n"
                                "Do not mention this correction process.\n"
                                "Return only the final answer for the user."
                            ),
                        }
                    )

                    continue

                return final_answer

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
                # Keep the original structured result so we can
                # validate the LLM's final answer later.
                tool_results.append(result)
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
