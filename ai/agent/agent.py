import json
import re

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

    def _extract_tool_calls_from_content(self, content: str) -> list[dict]:
        """
        Fallback parser for models (like Llama 3.2 3B) that occasionally output
        tool calls as text or malformed JSON in message.content instead of
        populating the structured message.tool_calls field.
        """
        if not content or not isinstance(content, str):
            return []

        text = content.strip()
        text = re.sub(r"^<\|python_tag\|>", "", text).strip()

        # Unwrap markdown code fence if wrapped
        fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fence_match:
            text = fence_match.group(1).strip()

        # Fix common Llama 3.2 malformed JSON syntax:
        # missing colon and/or missing closing quote on parameters/arguments
        # Example: {"name":"foo","parameters{"customer_name":"BlueSky"}}
        text_fixed = re.sub(r'"(parameters|arguments)"?\s*\{', r'"\1": {', text)

        # 1. Direct JSON parse
        try:
            data = json.loads(text_fixed)
            if isinstance(data, dict) and "name" in data:
                name = data["name"]
                if name in TOOL_FUNCTIONS:
                    args = data.get("parameters") or data.get("arguments") or {}
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except Exception:
                            pass
                    return [{"function": {"name": name, "arguments": args}}]
        except Exception:
            pass

        # 2. Regex fallback for JSON-like structures
        match = re.search(r'\{\s*"name"\s*:\s*"([a-zA-Z0-9_]+)"', text_fixed)
        if match:
            name = match.group(1)
            if name in TOOL_FUNCTIONS:
                p_match = re.search(
                    r'"(?:parameters|arguments)"\s*:\s*(\{.*?\})', text_fixed, re.DOTALL
                )
                args = {}
                if p_match:
                    try:
                        args = json.loads(p_match.group(1))
                    except Exception:
                        pass
                return [{"function": {"name": name, "arguments": args}}]

        # 3. Python-style function call: func_name(arg="val", ...)
        fn_match = re.match(r"^([a-zA-Z0-9_]+)\s*\((.*)\)$", text, re.DOTALL)
        if fn_match:
            name = fn_match.group(1)
            if name in TOOL_FUNCTIONS:
                raw_args = fn_match.group(2).strip()
                args = {}
                for pair in re.finditer(r'([a-zA-Z0-9_]+)\s*=\s*(["\'])(.*?)\2', raw_args):
                    args[pair.group(1)] = pair.group(3)
                return [{"function": {"name": name, "arguments": args}}]

        return []

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

                    "11. Always call tools using function calling. "
                    "Never output raw JSON, parameters, or tool call syntax directly "
                    "in the response message text.\n"
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
        validation_retries = 0
        MAX_VALIDATION_RETRIES = 2   
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

            # If the model produced a tool call in content instead of tool_calls,
            # extract and execute it.
            if not tool_calls and assistant_message.get("content"):
                parsed_calls = self._extract_tool_calls_from_content(
                    assistant_message["content"]
                )
                if parsed_calls:
                    tool_calls = parsed_calls
                    assistant_message["tool_calls"] = tool_calls

            # No tool call means the LLM has produced
            # its final answer.
            if not tool_calls:

                final_answer = assistant_message["content"]

                # Guard against raw tool call string leaking as final answer
                if final_answer and final_answer.strip().startswith('{"name":'):
                    print("\nWARNING: Unexecuted tool call detected in content, retrying...")
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "Please call the tool using function calling to get the data, "
                                "do not print raw JSON."
                            ),
                        }
                    )
                    continue

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

                    validation_retries += 1

                    # --------------------------------------------------
                    # Stop retrying if the model continues producing
                    # incorrect financial values.
                    # --------------------------------------------------

                    if validation_retries > MAX_VALIDATION_RETRIES:

                        return (
                            "I was unable to generate a reliable response "
                            "from the database results. Please try the "
                            "question again."
                        )

                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "Your previous answer contained incorrect "
                                "financial values.\n\n"

                                "Use ONLY the exact financial values returned "
                                "by the database tools.\n\n"

                                "The correct values are already present in "
                                "the tool results in this conversation.\n\n"

                                "Do not calculate, estimate, round, modify, "
                                "or reconstruct any financial value.\n\n"

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
