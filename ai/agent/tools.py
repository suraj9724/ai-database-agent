from tools.invoice_tools import (
    get_invoice,
    search_invoices,
    search_invoices_above_amount,
    get_customer_invoices,
    get_highest_invoice,
)

from tools.customer_tools import search_customer

from tools.payment_tools import (
    get_revenue,
    get_outstanding_amount,
    get_customer_outstanding_by_name,
    get_customer_outstanding_details,
    get_total_unpaid_amount,
    get_customer_payments,
    get_customer_with_highest_outstanding,
    get_highest_invoice_for_customer,
)


# --------------------------------------------------
# Tool definitions exposed to the LLM
# --------------------------------------------------
#
# These descriptions tell the LLM:
#
# 1. What the tool does
# 2. When it should use it
# 3. What arguments it needs
#
# The LLM does NOT receive database credentials
# or SQL queries.
# --------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_invoice",
            "description": (
                "Get complete information about a specific "
                "invoice using its invoice number."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "invoice_number": {
                        "type": "string",
                        "description": "The invoice number, such as INV-1001.",
                    }
                },
                "required": ["invoice_number"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "search_invoices",
            "description": (
                "Find invoices by payment status. "
                "Use this for paid, unpaid, or partially paid invoices."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": [
                            "paid",
                            "unpaid",
                            "partially_paid",
                        ],
                        "description": "Invoice payment status.",
                    }
                },
                "required": ["status"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "search_invoices_above_amount",
            "description": (
                "Find invoices whose total is greater than "
                "a specified amount."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "Minimum invoice total.",
                    }
                },
                "required": ["amount"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "search_customer",
            "description": (
                "Search for customers using their name."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Customer name or partial name.",
                    }
                },
                "required": ["customer_name"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "get_revenue",
            "description": (
                "Calculate revenue received between two dates. "
                "Revenue is based on actual payments received."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format.",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format.",
                    },
                },
                "required": [
                    "start_date",
                    "end_date",
                ],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "get_outstanding_amount",
            "description": (
                "Calculate the total amount still outstanding "
                "across all invoices."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },  
    {
        "type": "function",
        "function": {
            "name": "get_customer_outstanding_by_name",
            "description": (
                "Calculate the outstanding amount owed by a "
                "specific customer. Use this when the user asks "
                "how much a particular customer owes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": (
                            "The name of the customer."
                        ),
                    }
                },
                "required": ["customer_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
        "name": "get_customer_invoices",
        "description": (
            "Get all invoices belonging to a specific customer. "
            "Use this when the user asks about a customer's "
            "invoices or wants to know which invoices belong "
            "to that customer."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "Customer name.",
                }
            },
            "required": ["customer_name"],
        },
    },
},
    {
    "type": "function",
    "function": {
        "name": "get_customer_outstanding_details",
        "description": (
            "Get the outstanding amount owed by a specific "
            "customer AND the invoices belonging to that customer. "
            "Use this when the user asks how much a customer owes "
            "and/or which invoices make up the amount."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "Customer name.",
                }
            },
            "required": ["customer_name"],
        },
    },
},
    {
    "type": "function",
    "function": {
        "name": "get_highest_invoice",
        "description": (
            "Find the single invoice with the highest total value. "
            "Use this when the user asks which customer has the "
            "highest invoice or which invoice is the largest."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
},
    {
    "type": "function",
    "function": {
        "name": "get_total_unpaid_amount",
        "description": (
            "Calculate the total value of all unpaid invoices. "
            "Use this when the user asks for the total value "
            "or total amount of unpaid invoices."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
},
    {
        "type": "function",
        "function": {
            "name": "get_customer_payments",
            "description": (
                "Calculate how much money has been received from "
                "a specific customer. Use this when the user asks "
                "how much a particular customer has paid or how "
                "much was received from that customer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Customer name.",
                    }
                },
                "required": ["customer_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_with_highest_outstanding",
            "description": (
                "Find the customer with the highest total outstanding balance across all invoices. "
                "Use this when the user asks which customer owes the most money, who has the "
                "largest debt/outstanding amount, or which customer to prioritize for collections."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_highest_invoice_for_customer",
            "description": (
                "Find the single invoice with the highest outstanding balance for a specific "
                "customer. Use this when the user asks for a customer's largest unpaid invoice, "
                "highest open balance, or which invoice has the most debt for that customer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "The customer's name (e.g. 'TechNova Solutions').",
                    },
                    "customer_id": {
                        "type": "integer",
                        "description": "The customer ID if known.",
                    },
                },
                "required": [],
            },
        },
    },
]


# --------------------------------------------------
# Map tool names to actual Python functions.
# --------------------------------------------------

TOOL_FUNCTIONS = {
    "get_invoice": get_invoice,
    "search_invoices": search_invoices,
    "search_invoices_above_amount": search_invoices_above_amount,
    "search_customer": search_customer,
    "get_revenue": get_revenue,
    "get_outstanding_amount": get_outstanding_amount,
    "get_customer_outstanding_by_name": get_customer_outstanding_by_name,
    "get_customer_invoices": get_customer_invoices,
    "get_customer_outstanding_details": get_customer_outstanding_details,
    "get_highest_invoice": get_highest_invoice,
    "get_total_unpaid_amount": get_total_unpaid_amount,
    "get_customer_payments": get_customer_payments,
    "get_customer_with_highest_outstanding": get_customer_with_highest_outstanding,
    "get_highest_invoice_for_customer": get_highest_invoice_for_customer,
}