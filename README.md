# Muse Bio AI Agent

An AI-powered conversational assistant for Muse Bio, built with the Anthropic Claude SDK. The agent helps potential donors, investors, and partners learn about Muse Bio's menstrual blood stem cell programs.

## Features

- **Intelligent Conversation**: Powered by Claude Sonnet for natural, context-aware responses
- **User Type Detection**: Automatically identifies donors, investors, or partners and adapts responses
- **Knowledge Base Integration**: References comprehensive company documentation for accurate answers
- **PDF Resource Recommendations**: Suggests relevant documents based on conversation context
- **Medical Boundary Compliance**: Strictly avoids medical advice per regulatory requirements
- **Web Interface**: Clean, responsive chat UI with inline PDF previews
- **Session Management**: Maintains conversation context across messages

## Project Structure

```
musebio/
├── musebio_agent.py              # Core agent implementation
├── musebio_api.py                # FastAPI web server
├── muse_bio_ai_agent_kb_v4.md    # Knowledge base
├── requirements.txt              # Python dependencies
├── TECHNICAL_DOCUMENTATION.md    # Detailed technical docs
├── static/
│   ├── index.html                # Web chat interface
│   ├── styles.css                # Muse Bio pink theme
│   ├── app.js                    # Frontend logic
│   └── logo.webp                 # Company logo
└── PDFs/
    ├── FM-0015__Informed_Consent_Form_(4).pdf
    ├── How_to_use_a_menstrual_cup.pdf
    ├── REF-0005__Donor_Eligibility_Screening_Risk_Factors.pdf
    ├── Sample_Collection_Instructions_Poster(1).pdf
    └── MUSE_BIO_COMPLETE_KB_v4.md.pdf
```

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/sissississi-013/MuseBio-Agent.git
cd MuseBio-Agent
```

### 2. Set Up Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Key

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

### 5. Run the Application

**Web Interface (Recommended):**
```bash
python3 musebio_api.py
```
Then open http://localhost:8000 in your browser.

**Command Line Interface:**
```bash
python3 musebio_agent.py
```

## Usage

### Web Interface

The web interface provides:
- Chat area with markdown-rendered responses
- Sidebar with quick start buttons for different user types
- PDF resources list with inline preview capability
- Session tracking and conversation reset

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web chat interface |
| `/chat` | POST | Send message to agent |
| `/pdfs` | GET | List available PDFs |
| `/pdfs/{key}` | GET | Download/view specific PDF |
| `/health` | GET | Server health check |
| `/session/{id}` | GET | Get session info |
| `/api` | GET | API documentation |

### Chat API Example

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about donating"}'
```

Response:
```json
{
  "response": "Hey there! I am excited you are interested...",
  "session_id": "abc-123",
  "detected_user_type": "donor",
  "suggested_pdfs": [...],
  "timestamp": "2026-02-05T10:00:00"
}
```

### Programmatic Usage

```python
from musebio_agent import MuseBioAgent

agent = MuseBioAgent()

# Start a conversation
response = agent.chat("Hi, I want to learn about donating")
print(response)

# Continue the conversation
response = agent.chat("What are the eligibility requirements?")
print(response)

# Check detected user type
print(agent.detected_user_type)  # "donor"

# Reset conversation
agent.reset_conversation()
```

## User Types

The agent adapts its responses based on detected user type:

### Donors
- Explains Research Study ($40/donation) vs Commercial Program ($150/donation)
- Details eligibility requirements (age 18-45, no IUD, etc.)
- Provides menstrual cup usage guidance
- Describes sample collection process

### Investors
- Directs to muse@mycells.bio with "Investor Inquiry" subject
- Shares public company information
- Maintains professional tone

### Partners
- Highlights partnership opportunities
- Lists target partner types (femtech, menstrual products, women-led companies)
- Directs to muse@mycells.bio with "Partnership Inquiry" subject

## PDF Resources

The agent automatically suggests relevant PDFs based on conversation topics:

| Resource | Triggers |
|----------|----------|
| Informed Consent Form | consent, sign up, enroll |
| Menstrual Cup Guide | cup, how to use, insertion |
| Eligibility Screening | eligibility, requirements, qualify |
| Sample Collection | collection, procedure, steps |

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key |

### Customization

**Modify PDF triggers** in `musebio_agent.py`:
```python
PDF_RESOURCES = {
    "your_key": {
        "file": "your_file.pdf",
        "description": "Description for users",
        "triggers": ["keyword1", "keyword2"]
    }
}
```

**Update knowledge base** by editing `muse_bio_ai_agent_kb_v4.md`

## Tech Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn
- **AI**: Anthropic Claude SDK (claude-sonnet-4-20250514)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Markdown**: marked.js for chat rendering

## Documentation

See [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) for detailed documentation including:
- System architecture diagrams
- Claude SDK deep dive
- Agent design patterns
- Security considerations
- Performance optimization

## Medical Disclaimer

Muse Bio is not a medical practice. This agent is programmed to never provide medical advice, diagnosis, or treatment recommendations. All medical questions are redirected to healthcare providers.

## Contact

- Email: muse@mycells.bio
- Website: https://mycells.bio
- Location: Frontier Tower, 995 Market St, San Francisco, CA 94103

## License

Proprietary - Muse Bio 2024
