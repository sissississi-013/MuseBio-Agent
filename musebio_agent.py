#!/usr/bin/env python3
"""
Muse Bio AI Agent
A conversational agent that helps potential donors, investors, and partners
learn about Muse Bio's menstrual blood stem cell programs.
"""

import os
import base64
from pathlib import Path
from typing import Optional
import anthropic

# Configuration
KNOWLEDGE_BASE_PATH = Path(__file__).parent / "muse_bio_ai_agent_kb_v4.md"
PDF_DIRECTORY = Path(__file__).parent

# PDF mappings - which PDFs to offer based on topic
# NOTE: Only the menstrual cup guide is shared publicly. Other documents (eligibility screening,
# consent forms, etc.) are confidential and information is provided verbally from the knowledge base.
PDF_RESOURCES = {
    "menstrual_cup_guide": {
        "file": "How_to_use_a_menstrual_cup.pdf",
        "description": "Complete Guide: How to Use a Menstrual Cup",
        "triggers": ["cup", "menstrual cup", "how to use", "insertion", "removal", "fold", "collect sample", "using a cup"]
    }
}

# User type detection keywords
USER_TYPE_KEYWORDS = {
    "donor": [
        "donate", "donation", "donor", "participate", "contribute", "menstrual",
        "cup", "sample", "blood", "period", "cycle", "collect", "eligible",
        "compensation", "gift card", "goodie bag", "$40", "$150", "research study",
        "commercial program", "stem cells"
    ],
    "investor": [
        "invest", "investor", "investment", "funding", "raise", "round",
        "equity", "valuation", "traction", "market", "revenue", "business model",
        "financial", "capital", "seed", "series", "pitch", "deck"
    ],
    "partner": [
        "partner", "partnership", "collaborate", "collaboration", "distribution",
        "marketing", "co-brand", "supplier", "femtech", "menstrual products",
        "pads", "tampons", "cups", "women-led", "sustainable", "research collaboration"
    ]
}


class MuseBioAgent:
    """Muse Bio conversational agent using Claude SDK."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the agent with Claude client and knowledge base."""
        self.client = anthropic.Anthropic(api_key=api_key)
        self.knowledge_base = self._load_knowledge_base()
        self.conversation_history = []
        self.detected_user_type = None
        self.offered_pdfs = set()  # Track which PDFs we've already offered

    def _load_knowledge_base(self) -> str:
        """Load the knowledge base markdown file."""
        try:
            with open(KNOWLEDGE_BASE_PATH, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Warning: Knowledge base not found at {KNOWLEDGE_BASE_PATH}")
            return ""

    def _detect_user_type(self, message: str) -> Optional[str]:
        """Detect if user is a donor, investor, or partner based on message."""
        message_lower = message.lower()
        scores = {"donor": 0, "investor": 0, "partner": 0}

        for user_type, keywords in USER_TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    scores[user_type] += 1

        # Return the type with highest score if any matches found
        max_score = max(scores.values())
        if max_score > 0:
            return max(scores, key=scores.get)
        return None

    def _find_relevant_pdfs(self, message: str) -> list[dict]:
        """Find PDFs relevant to the user's message."""
        message_lower = message.lower()
        relevant = []

        for pdf_key, pdf_info in PDF_RESOURCES.items():
            # Skip if we've already offered this PDF in this conversation
            if pdf_key in self.offered_pdfs:
                continue

            for trigger in pdf_info["triggers"]:
                if trigger in message_lower:
                    relevant.append({
                        "key": pdf_key,
                        "file": pdf_info["file"],
                        "description": pdf_info["description"]
                    })
                    break

        return relevant

    def _get_pdf_path(self, filename: str) -> Path:
        """Get full path to a PDF file."""
        return PDF_DIRECTORY / filename

    def _build_system_prompt(self) -> str:
        """Build the system prompt including the knowledge base."""
        user_type_context = ""
        if self.detected_user_type:
            type_contexts = {
                "donor": """
The user appears to be a potential DONOR. Focus on:
- Explaining the two programs (Research Study vs Commercial Donation)
- Eligibility requirements and what to expect
- The sample collection process and menstrual cup usage
- Compensation details ($40 for research, $150 for commercial)
- Making them feel comfortable and excited about participating
- Offering relevant PDF guides when they ask about specific procedures""",

                "investor": """
The user appears to be a potential INVESTOR. Focus on:
- Directing them to email muse@mycells.bio with "Investor Inquiry" in subject
- Briefly explaining what Muse Bio does (MenSCs for cosmetic ingredients)
- Mentioning the team (CEO Juliette Humer, COO Tommy Kronmark, team of 6)
- Noting current stage (building phase, no products on market yet)
- Being professional while maintaining friendly tone
- NOT sharing confidential business details""",

                "partner": """
The user appears to be a potential PARTNER. Focus on:
- Types of partnerships Muse Bio is interested in:
  * Menstrual product companies (pads, tampons, cups)
  * Femtech and women's health tech companies
  * Women-led companies
  * Sustainable/environmental organizations
  * Research institutions
- Directing them to email muse@mycells.bio with "Partnership Inquiry" in subject
- Being enthusiastic about collaboration opportunities"""
            }
            user_type_context = type_contexts.get(self.detected_user_type, "")

        return f"""You are the Muse Bio AI Assistant - a friendly, knowledgeable helper for Muse Bio, a biotech company working with menstrual blood-derived stem cells (MenSCs).

## CRITICAL MEDICAL BOUNDARIES - READ FIRST

MUSE BIO IS NOT A MEDICAL PRACTICE. You CANNOT and DO NOT provide medical advice, diagnosis, or treatment.

NEVER:
- Diagnose any medical condition
- Interpret test results or symptoms
- Recommend treatments or medications
- Tell someone whether they should see a doctor for a specific symptom
- Say "you probably have X condition" or "that sounds like Y"
- Say "we provide care" - WE ARE NOT A MEDICAL PRACTICE

ALWAYS redirect medical questions to healthcare providers with responses like:
- "That's a great question for your healthcare provider! We're not a medical practice and can't provide medical advice."
- "For questions about your health, symptoms, or medications, please consult with your healthcare provider."

## TONE & STYLE

Talk like a friendly, knowledgeable friend - NOT a corporate robot!
- Use warm, conversational language
- Be enthusiastic about the science without being over-the-top
- Use contractions naturally (you're, we're, it's, don't)
- Show empathy and understanding
- Make people feel comfortable and excited

## USER TYPE CONTEXT
{user_type_context}

## KNOWLEDGE BASE

Use the following knowledge base to answer questions accurately. Reference specific details from here:

{self.knowledge_base}

## IMPORTANT GUIDELINES

1. For DONORS:
   - Explain both programs clearly (Research Study: $40, no blood tests vs Commercial: $150, requires blood/urine tests)
   - Be clear about eligibility (18-45, menstruates regularly, no IUD, no diagnosed endometriosis)
   - Explain menstrual cup usage cheerfully
   - Mention location: Frontier Tower, 995 Market St, San Francisco
   - Contact: muse@mycells.bio

2. For INVESTORS:
   - Direct to email muse@mycells.bio with "Investor Inquiry" subject line
   - Share only public information about company
   - Be professional but friendly

3. For PARTNERS:
   - Mention partnership types we're interested in
   - Direct to email muse@mycells.bio with "Partnership Inquiry" subject line
   - Be enthusiastic about collaboration

4. When users ask about specific procedures (cup usage, collection, eligibility):
   - Provide detailed help from the knowledge base
   - Mention that relevant PDF guides are available if the system notes them

5. NEVER make up information not in the knowledge base
6. If unsure, direct them to email muse@mycells.bio or say you'll need to check with the team
"""

    def _format_pdf_offer(self, pdfs: list[dict]) -> str:
        """Format a message offering relevant PDF resources."""
        if not pdfs:
            return ""

        offers = []
        for pdf in pdfs:
            offers.append(f"📄 **{pdf['description']}** - `{pdf['file']}`")
            self.offered_pdfs.add(pdf["key"])

        if len(offers) == 1:
            return f"\n\n---\n💡 **Helpful Resource:** I have a PDF that might help!\n{offers[0]}\n\nWould you like me to tell you more about what's in it, or you can find it in the musebio folder!"
        else:
            offer_list = "\n".join(offers)
            return f"\n\n---\n💡 **Helpful Resources:** I have some PDFs that might help!\n{offer_list}\n\nLet me know if you'd like more details about any of these!"

    def chat(self, user_message: str) -> str:
        """
        Process a user message and return the agent's response.

        Args:
            user_message: The user's input message

        Returns:
            The agent's response string
        """
        # Detect user type if not already detected
        if not self.detected_user_type:
            self.detected_user_type = self._detect_user_type(user_message)

        # Find relevant PDFs for this message
        relevant_pdfs = self._find_relevant_pdfs(user_message)

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Build messages for API call
        messages = self.conversation_history.copy()

        # Make API call
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=self._build_system_prompt(),
            messages=messages
        )

        # Extract response text
        assistant_message = response.content[0].text

        # Add PDF offers if relevant
        if relevant_pdfs:
            assistant_message += self._format_pdf_offer(relevant_pdfs)

        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

    def reset_conversation(self):
        """Reset the conversation history and user type detection."""
        self.conversation_history = []
        self.detected_user_type = None
        self.offered_pdfs = set()

    def get_pdf_content_base64(self, pdf_key: str) -> Optional[str]:
        """
        Get a PDF file's content as base64 string.
        Useful for sending PDFs via API or embedding.

        Args:
            pdf_key: Key from PDF_RESOURCES dict

        Returns:
            Base64 encoded string of PDF content, or None if not found
        """
        if pdf_key not in PDF_RESOURCES:
            return None

        pdf_path = self._get_pdf_path(PDF_RESOURCES[pdf_key]["file"])

        try:
            with open(pdf_path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except FileNotFoundError:
            return None


def main():
    """Run the Muse Bio agent in interactive mode."""
    print("=" * 60)
    print("🧬 Welcome to Muse Bio AI Assistant!")
    print("=" * 60)
    print()
    print("I'm here to help you learn about Muse Bio's menstrual")
    print("blood stem cell donation programs.")
    print()
    print("I can help with:")
    print("  • Information for potential DONORS")
    print("  • Information for INVESTORS")
    print("  • Information for PARTNERS")
    print()
    print("Type 'quit' or 'exit' to end the conversation.")
    print("Type 'reset' to start a new conversation.")
    print("-" * 60)
    print()

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("⚠️  Warning: ANTHROPIC_API_KEY environment variable not set.")
        print("   Please set it before running: export ANTHROPIC_API_KEY='your-key'")
        print()
        return

    agent = MuseBioAgent()

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit']:
                print("\n👋 Thanks for chatting! Visit mycells.bio to learn more.")
                break

            if user_input.lower() == 'reset':
                agent.reset_conversation()
                print("\n🔄 Conversation reset! How can I help you today?\n")
                continue

            response = agent.chat(user_input)
            print(f"\nMuse Bio: {response}\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except anthropic.APIError as e:
            print(f"\n❌ API Error: {e}\n")


if __name__ == "__main__":
    main()
