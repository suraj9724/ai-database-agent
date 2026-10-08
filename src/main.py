from agent.agent import DatabaseAgent


def main():

    agent = DatabaseAgent()

    questions = [
        # "Show me invoice INV-1001.",
        # "Show me all unpaid invoices.",
        # "How much revenue did we receive in September 2026?",
        # "What is the total outstanding amount?",
        # "Which customer has the highest invoice value?",
        # "How many invoices does TechNova Solutions have?",
        # "What is the average invoice value?",
        "Can you tell me how much money TechNova Solutions still owes us?",
    ]

    for question in questions:

        print("\n" + "=" * 60)
        print(f"USER: {question}")
        print("=" * 60)

        answer = agent.run(question)

        print(f"AGENT: {answer}")


if __name__ == "__main__":
    main()