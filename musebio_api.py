#!/usr/bin/env python3
"""
Muse Bio AI Agent - Web API Version
A FastAPI-based web service for the Muse Bio conversational agent.
"""

import os
import base64
import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import anthropic

# Import from main agent module
from musebio_agent import (
    MuseBioAgent,
    PDF_RESOURCES,
    PDF_DIRECTORY,
    KNOWLEDGE_BASE_PATH
)


# Session storage (in production, use Redis or similar)
sessions: dict[str, dict] = {}
SESSION_TIMEOUT_HOURS = 24


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    session_id: str
    detected_user_type: Optional[str]
    suggested_pdfs: list[dict]
    timestamp: str


class PDFListResponse(BaseModel):
    """Response model for PDF list endpoint."""
    pdfs: list[dict]


class SessionInfo(BaseModel):
    """Response model for session info endpoint."""
    session_id: str
    created_at: str
    message_count: int
    detected_user_type: Optional[str]
    offered_pdfs: list[str]


def cleanup_old_sessions():
    """Remove sessions older than SESSION_TIMEOUT_HOURS."""
    cutoff = datetime.now() - timedelta(hours=SESSION_TIMEOUT_HOURS)
    expired = [
        sid for sid, data in sessions.items()
        if data.get("created_at", datetime.now()) < cutoff
    ]
    for sid in expired:
        del sessions[sid]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: verify knowledge base exists
    if not KNOWLEDGE_BASE_PATH.exists():
        print(f"⚠️  Warning: Knowledge base not found at {KNOWLEDGE_BASE_PATH}")
    else:
        print(f"✅ Knowledge base loaded from {KNOWLEDGE_BASE_PATH}")

    # Verify PDFs exist
    for pdf_key, pdf_info in PDF_RESOURCES.items():
        pdf_path = PDF_DIRECTORY / pdf_info["file"]
        if pdf_path.exists():
            print(f"✅ PDF found: {pdf_info['file']}")
        else:
            print(f"⚠️  PDF missing: {pdf_info['file']}")

    yield

    # Shutdown: cleanup
    sessions.clear()


# Initialize FastAPI app
app = FastAPI(
    title="Muse Bio AI Agent API",
    description="""
    AI-powered assistant for Muse Bio - helping potential donors, investors,
    and partners learn about menstrual blood stem cell donation programs.

    ## Features
    - Conversational AI powered by Claude
    - Automatic user type detection (donor/investor/partner)
    - Context-aware PDF recommendations
    - Session-based conversation history

    ## Usage
    1. Start a conversation with POST /chat
    2. Continue using the returned session_id
    3. Access recommended PDFs via GET /pdfs/{pdf_key}
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for web frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files directory
STATIC_DIR = Path(__file__).parent / "static"

# Mount static files for CSS and JS
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web chat interface."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    # Fallback to API info if no web interface
    return HTMLResponse(content="""
        <html>
            <head><title>Muse Bio API</title></head>
            <body>
                <h1>Muse Bio AI Agent API</h1>
                <p>Visit <a href="/docs">/docs</a> for API documentation.</p>
            </body>
        </html>
    """)


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "name": "Muse Bio AI Agent API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "chat": "POST /chat - Send a message to the agent",
            "pdfs": "GET /pdfs - List available PDF resources",
            "pdf_download": "GET /pdfs/{pdf_key} - Download a specific PDF",
            "session": "GET /session/{session_id} - Get session info",
            "health": "GET /health - Health check"
        },
        "contact": "muse@mycells.bio"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "knowledge_base_loaded": KNOWLEDGE_BASE_PATH.exists(),
        "active_sessions": len(sessions),
        "timestamp": datetime.now().isoformat()
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Send a message to the Muse Bio AI agent.

    - If no session_id provided, creates a new session
    - Returns the agent's response along with any suggested PDFs
    - Conversation history is maintained per session
    """
    # Clean up old sessions periodically
    background_tasks.add_task(cleanup_old_sessions)

    # Get or create session
    session_id = request.session_id or str(uuid.uuid4())

    if session_id not in sessions:
        # Create new session with agent instance
        try:
            agent = MuseBioAgent()
            sessions[session_id] = {
                "agent": agent,
                "created_at": datetime.now(),
                "message_count": 0
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize agent: {str(e)}")

    session = sessions[session_id]
    agent = session["agent"]

    # Process message
    try:
        response = agent.chat(request.message)
        session["message_count"] += 1

        # Find newly suggested PDFs (those just added to offered_pdfs)
        suggested_pdfs = []
        for pdf_key in agent.offered_pdfs:
            if pdf_key in PDF_RESOURCES:
                suggested_pdfs.append({
                    "key": pdf_key,
                    "file": PDF_RESOURCES[pdf_key]["file"],
                    "description": PDF_RESOURCES[pdf_key]["description"],
                    "download_url": f"/pdfs/{pdf_key}"
                })

        return ChatResponse(
            response=response,
            session_id=session_id,
            detected_user_type=agent.detected_user_type,
            suggested_pdfs=suggested_pdfs,
            timestamp=datetime.now().isoformat()
        )

    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Claude API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@app.get("/pdfs", response_model=PDFListResponse)
async def list_pdfs():
    """List all available PDF resources."""
    pdfs = []
    for pdf_key, pdf_info in PDF_RESOURCES.items():
        pdf_path = PDF_DIRECTORY / pdf_info["file"]
        pdfs.append({
            "key": pdf_key,
            "file": pdf_info["file"],
            "description": pdf_info["description"],
            "available": pdf_path.exists(),
            "download_url": f"/pdfs/{pdf_key}",
            "triggers": pdf_info["triggers"]
        })
    return PDFListResponse(pdfs=pdfs)


@app.get("/pdfs/{pdf_key}")
async def download_pdf(pdf_key: str):
    """Download a specific PDF resource."""
    if pdf_key not in PDF_RESOURCES:
        raise HTTPException(status_code=404, detail=f"PDF resource '{pdf_key}' not found")

    pdf_info = PDF_RESOURCES[pdf_key]
    pdf_path = PDF_DIRECTORY / pdf_info["file"]

    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail=f"PDF file not found: {pdf_info['file']}")

    # Read file and return with inline disposition for embedding
    with open(pdf_path, "rb") as f:
        content = f.read()

    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=\"{pdf_info['file']}\"",
        }
    )


@app.get("/pdfs/{pdf_key}/base64")
async def get_pdf_base64(pdf_key: str):
    """Get a PDF as base64-encoded string (useful for embedding)."""
    if pdf_key not in PDF_RESOURCES:
        raise HTTPException(status_code=404, detail=f"PDF resource '{pdf_key}' not found")

    pdf_info = PDF_RESOURCES[pdf_key]
    pdf_path = PDF_DIRECTORY / pdf_info["file"]

    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail=f"PDF file not found: {pdf_info['file']}")

    try:
        with open(pdf_path, 'rb') as f:
            content = base64.b64encode(f.read()).decode('utf-8')
        return {
            "key": pdf_key,
            "file": pdf_info["file"],
            "description": pdf_info["description"],
            "content_base64": content,
            "mime_type": "application/pdf"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading PDF: {str(e)}")


@app.get("/session/{session_id}", response_model=SessionInfo)
async def get_session_info(session_id: str):
    """Get information about a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    agent = session["agent"]

    return SessionInfo(
        session_id=session_id,
        created_at=session["created_at"].isoformat(),
        message_count=session["message_count"],
        detected_user_type=agent.detected_user_type,
        offered_pdfs=list(agent.offered_pdfs)
    )


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and its conversation history."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del sessions[session_id]
    return {"message": "Session deleted successfully"}


@app.post("/session/{session_id}/reset")
async def reset_session(session_id: str):
    """Reset a session's conversation while keeping the same session ID."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    session["agent"].reset_conversation()
    session["message_count"] = 0

    return {"message": "Session reset successfully", "session_id": session_id}


# Quick start commands for different user types
QUICK_START_PROMPTS = {
    "donor": "Hi! I'm interested in donating. Can you tell me about the programs?",
    "investor": "Hello, I'm interested in learning about investment opportunities at Muse Bio.",
    "partner": "Hi there! I represent a femtech company and I'm interested in partnership opportunities."
}


@app.get("/quickstart/{user_type}")
async def quickstart(user_type: str, background_tasks: BackgroundTasks):
    """
    Start a conversation with a predefined prompt for a specific user type.

    User types: donor, investor, partner
    """
    if user_type not in QUICK_START_PROMPTS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid user type. Choose from: {list(QUICK_START_PROMPTS.keys())}"
        )

    request = ChatRequest(message=QUICK_START_PROMPTS[user_type])
    return await chat(request, background_tasks)


if __name__ == "__main__":
    import uvicorn

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("⚠️  Warning: ANTHROPIC_API_KEY environment variable not set.")
        print("   Please set it before running: export ANTHROPIC_API_KEY='your-key'")
        print()

    print("🧬 Starting Muse Bio AI Agent API...")
    print("   Documentation: http://localhost:8000/docs")
    print("   Health check:  http://localhost:8000/health")
    print()

    uvicorn.run(app, host="0.0.0.0", port=8000)
