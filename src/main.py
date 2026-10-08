from tools.invoice_tools import (
    get_invoice,
    search_invoices,
    search_invoices_above_amount,
)

from tools.customer_tools import search_customer

from tools.payment_tools import (
    get_revenue,
    get_outstanding_amount,
)


def main():

    print("\n--- GET INVOICE ---")

    print(
        get_invoice("INV-1001")
    )


    print("\n--- UNPAID INVOICES ---")

    print(
        search_invoices("unpaid")
    )


    print("\n--- INVOICES ABOVE 40000 ---")

    print(
        search_invoices_above_amount(40000)
    )


    print("\n--- SEARCH CUSTOMER ---")

    print(
        search_customer("TechNova")
    )


    print("\n--- SEPTEMBER REVENUE ---")

    print(
        get_revenue(
            "2026-09-01",
            "2026-09-30",
        )
    )


    print("\n--- OUTSTANDING ---")

    print(
        get_outstanding_amount()
    )


if __name__ == "__main__":
    main()