#!/usr/bin/env python3
"""
Example usage of the Muse Bio AI Agent.
Demonstrates different scenarios and user types.
"""

import os
from musebio_agent import MuseBioAgent


def demo_donor_conversation():
    """Simulate a potential donor conversation."""
    print("\n" + "=" * 60)
    print("📋 DEMO: Potential Donor Conversation")
    print("=" * 60 + "\n")

    agent = MuseBioAgent()

    # Donor questions
    questions = [
        "Hi! I heard about Muse Bio and I'm interested in donating. What's this all about?",
        "What's the difference between the research study and commercial program?",
        "How much do you pay?",
        "I've never used a menstrual cup before. Is it hard?",
        "Am I eligible? I'm 28 and have an IUD.",
        "What if I get my IUD removed?",
    ]

    for q in questions:
        print(f"👤 Donor: {q}")
        response = agent.chat(q)
        print(f"\n🤖 Agent: {response}\n")
        print("-" * 40 + "\n")


def demo_investor_conversation():
    """Simulate a potential investor conversation."""
    print("\n" + "=" * 60)
    print("💰 DEMO: Potential Investor Conversation")
    print("=" * 60 + "\n")

    agent = MuseBioAgent()

    questions = [
        "Hi, I'm an angel investor interested in femtech. Can you tell me about Muse Bio?",
        "What stage is the company at?",
        "How can I get more information about investment opportunities?",
    ]

    for q in questions:
        print(f"👤 Investor: {q}")
        response = agent.chat(q)
        print(f"\n🤖 Agent: {response}\n")
        print("-" * 40 + "\n")


def demo_partner_conversation():
    """Simulate a potential partner conversation."""
    print("\n" + "=" * 60)
    print("🤝 DEMO: Potential Partner Conversation")
    print("=" * 60 + "\n")

    agent = MuseBioAgent()

    questions = [
        "Hello! I'm from a menstrual cup company and we're interested in partnerships.",
        "What types of partnerships are you looking for?",
        "We're a women-led sustainable product company. Would that be a fit?",
    ]

    for q in questions:
        print(f"👤 Partner: {q}")
        response = agent.chat(q)
        print(f"\n🤖 Agent: {response}\n")
        print("-" * 40 + "\n")


def demo_medical_boundary():
    """Demonstrate how the agent handles medical questions appropriately."""
    print("\n" + "=" * 60)
    print("⚕️ DEMO: Medical Boundary Handling")
    print("=" * 60 + "\n")

    agent = MuseBioAgent()

    questions = [
        "I've been having irregular periods and spotting between cycles. Is that endometriosis?",
        "Should I be worried about these symptoms?",
        "If I test positive for something, what treatment should I get?",
    ]

    for q in questions:
        print(f"👤 User: {q}")
        response = agent.chat(q)
        print(f"\n🤖 Agent: {response}\n")
        print("-" * 40 + "\n")


def interactive_mode():
    """Run in interactive mode."""
    print("\n" + "=" * 60)
    print("🧬 Muse Bio AI Agent - Interactive Mode")
    print("=" * 60)
    print("\nCommands:")
    print("  'quit' or 'exit' - End conversation")
    print("  'reset' - Start new conversation")
    print("  'demos' - Run all demos")
    print("-" * 60 + "\n")

    agent = MuseBioAgent()

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit']:
                print("\n👋 Thanks for chatting!")
                break

            if user_input.lower() == 'reset':
                agent.reset_conversation()
                print("\n🔄 Conversation reset!\n")
                continue

            if user_input.lower() == 'demos':
                run_all_demos()
                continue

            response = agent.chat(user_input)
            print(f"\nMuse Bio: {response}\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break


def run_all_demos():
    """Run all demonstration conversations."""
    demo_donor_conversation()
    demo_investor_conversation()
    demo_partner_conversation()
    demo_medical_boundary()


if __name__ == "__main__":
    import sys

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("⚠️  Error: ANTHROPIC_API_KEY environment variable not set.")
        print("   Please set it: export ANTHROPIC_API_KEY='your-key'")
        sys.exit(1)

    if len(sys.argv) > 1:
        if sys.argv[1] == "--demos":
            run_all_demos()
        elif sys.argv[1] == "--donor":
            demo_donor_conversation()
        elif sys.argv[1] == "--investor":
            demo_investor_conversation()
        elif sys.argv[1] == "--partner":
            demo_partner_conversation()
        elif sys.argv[1] == "--medical":
            demo_medical_boundary()
        else:
            print("Usage: python example_usage.py [--demos|--donor|--investor|--partner|--medical]")
    else:
        interactive_mode()
