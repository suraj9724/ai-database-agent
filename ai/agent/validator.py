import re
from typing import Any


def extract_money_values(text: str) -> list[float]:
    """
    Extract monetary values from an LLM response.

    Examples:
        $100,300.00 -> 100300.00
        $35,400      -> 35400.00

    This is only used for validation. It does not calculate
    or modify any financial values.
    """

    matches = re.findall(
    r"\$\s*([\d,]+(?:\.\d+)?)",
    text,
)

    values = []

    for match in matches:
        try:
            values.append(
                float(match.replace(",", ""))
            )
        except ValueError:
            continue

    return values


def collect_tool_values(tool_results: list[Any]) -> set[float]:
    """
    Collect numeric financial values returned by tools.

    We recursively inspect dictionaries/lists because tool
    responses can contain nested invoice/customer/payment data.
    """

    values = set()

    def collect(value):
        if isinstance(value, dict):

            for key, item in value.items():

                # Only treat fields that represent financial
                # amounts as financial values.
                if key in {
                    "amount",
                    "total",
                    "subtotal",
                    "gst",
                    "outstanding_amount",
                    "payment_amount",
                    "total_received",
                    "total_unpaid_amount",
                    "revenue",
                    "total_amount",
                    "amount_paid",
                }:
                    if isinstance(item, (int, float)):
                        values.add(float(item))

                collect(item)

        elif isinstance(value, list):

            for item in value:
                collect(item)

    for result in tool_results:
        collect(result)

    return values


def validate_financial_values(
    answer: str,
    tool_results: list[Any],
) -> tuple[bool, list[float]]:
    """
    Check whether monetary values mentioned by the LLM
    actually exist in the tool results.

    Returns:
        (True, []) if everything is valid.

        (False, invalid_values) if the LLM introduced
        financial values that were not returned by tools.
    """

    answer_values = extract_money_values(answer)

    allowed_values = collect_tool_values(tool_results)

    invalid_values = [
        value
        for value in answer_values
        if value not in allowed_values
    ]

    return (
        len(invalid_values) == 0,
        invalid_values,
    )