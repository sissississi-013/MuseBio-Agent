#!/usr/bin/env python3
"""
Test script to verify Muse Bio AI Agent setup.
Run this to check that all dependencies and files are correctly configured.
"""

import os
import sys
from pathlib import Path


def check_python_version():
    """Check Python version is 3.10+."""
    print("Checking Python version...", end=" ")
    if sys.version_info >= (3, 10):
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
        return True
    else:
        print(f"❌ Python {sys.version_info.major}.{sys.version_info.minor} (need 3.10+)")
        return False


def check_dependencies():
    """Check required packages are installed."""
    print("\nChecking dependencies...")
    required = {
        "anthropic": "anthropic",
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "pydantic": "pydantic",
    }

    all_ok = True
    for name, package in required.items():
        try:
            __import__(package)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name} (run: pip install {name})")
            all_ok = False

    return all_ok


def check_api_key():
    """Check Anthropic API key is set."""
    print("\nChecking API key...", end=" ")
    if os.environ.get("ANTHROPIC_API_KEY"):
        key = os.environ["ANTHROPIC_API_KEY"]
        masked = key[:10] + "..." + key[-4:] if len(key) > 14 else "***"
        print(f"✅ Set ({masked})")
        return True
    else:
        print("❌ ANTHROPIC_API_KEY not set")
        print("   Set it with: export ANTHROPIC_API_KEY='your-key'")
        return False


def check_files():
    """Check required files exist."""
    print("\nChecking files...")
    base_dir = Path(__file__).parent

    files = {
        "Knowledge Base": "muse_bio_ai_agent_kb_v4.md",
        "Main Agent": "musebio_agent.py",
        "Web API": "musebio_api.py",
        "Requirements": "requirements.txt",
    }

    pdfs = {
        "Informed Consent": "FM-0015__Informed_Consent_Form_(4).pdf",
        "Cup Guide": "How_to_use_a_menstrual_cup.pdf",
        "Eligibility Screening": "REF-0005__Donor_Eligibility_Screening_Risk_Factors.pdf",
        "Collection Instructions": "Sample_Collection_Instructions_Poster(1).pdf",
        "Complete KB PDF": "MUSE_BIO_COMPLETE_KB_v4.md.pdf",
    }

    all_ok = True

    print("  Core files:")
    for name, filename in files.items():
        path = base_dir / filename
        if path.exists():
            print(f"    ✅ {name}: {filename}")
        else:
            print(f"    ❌ {name}: {filename} NOT FOUND")
            all_ok = False

    print("  PDF resources:")
    for name, filename in pdfs.items():
        path = base_dir / filename
        if path.exists():
            size_kb = path.stat().st_size / 1024
            print(f"    ✅ {name}: {filename} ({size_kb:.1f} KB)")
        else:
            print(f"    ⚠️  {name}: {filename} NOT FOUND (optional)")

    return all_ok


def check_knowledge_base():
    """Check knowledge base content."""
    print("\nChecking knowledge base content...")
    kb_path = Path(__file__).parent / "muse_bio_ai_agent_kb_v4.md"

    if not kb_path.exists():
        print("  ❌ Knowledge base file not found")
        return False

    with open(kb_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for key sections
    sections = [
        "CRITICAL: MEDICAL BOUNDARIES",
        "Company Overview",
        "Program Comparison",
        "Research Study Program",
        "Commercial Donation Program",
        "Sample Collection Process",
        "Eligibility Requirements",
        "For Potential Investors",
        "For Potential Partners",
    ]

    print("  Key sections:")
    all_ok = True
    for section in sections:
        if section in content:
            print(f"    ✅ {section}")
        else:
            print(f"    ❌ {section} NOT FOUND")
            all_ok = False

    lines = content.count('\n')
    words = len(content.split())
    print(f"\n  📊 Stats: {lines:,} lines, {words:,} words")

    return all_ok


def test_agent_import():
    """Test that the agent can be imported."""
    print("\nTesting agent import...")
    try:
        from musebio_agent import MuseBioAgent, PDF_RESOURCES
        print(f"  ✅ MuseBioAgent class imported")
        print(f"  ✅ {len(PDF_RESOURCES)} PDF resources configured")
        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False


def test_agent_initialization():
    """Test that the agent can be initialized (requires API key)."""
    print("\nTesting agent initialization...")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("  ⏭️  Skipped (no API key)")
        return True

    try:
        from musebio_agent import MuseBioAgent
        agent = MuseBioAgent()
        print("  ✅ Agent initialized successfully")

        # Check knowledge base loaded
        if agent.knowledge_base:
            kb_preview = agent.knowledge_base[:100].replace('\n', ' ')
            print(f"  ✅ Knowledge base loaded: '{kb_preview}...'")
        else:
            print("  ⚠️  Knowledge base empty")

        return True
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        return False


def run_all_checks():
    """Run all setup checks."""
    print("=" * 60)
    print("🧬 Muse Bio AI Agent - Setup Verification")
    print("=" * 60)

    results = {
        "Python Version": check_python_version(),
        "Dependencies": check_dependencies(),
        "API Key": check_api_key(),
        "Files": check_files(),
        "Knowledge Base": check_knowledge_base(),
        "Agent Import": test_agent_import(),
        "Agent Init": test_agent_initialization(),
    }

    print("\n" + "=" * 60)
    print("📋 Summary")
    print("=" * 60)

    all_passed = True
    for check, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("🎉 All checks passed! You're ready to go.")
        print("\nNext steps:")
        print("  1. Run interactive mode: python musebio_agent.py")
        print("  2. Run web API: python musebio_api.py")
        print("  3. Run demos: python example_usage.py --demos")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")

    return all_passed


if __name__ == "__main__":
    success = run_all_checks()
    sys.exit(0 if success else 1)
