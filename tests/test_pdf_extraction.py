import os
import tempfile
import pytest
import pymupdf as fitz
from app.services.pdf_extractor import pdf_extractor_service


@pytest.fixture
def sample_pdf_path():
    """Generates a real, valid PDF document in a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, "test_paper.pdf")

    doc = fitz.open()
    doc.set_metadata({
        "title": "A Survey of Multi-Agent Systems in AI",
        "author": "Dr. Alan Turing, Ada Lovelace"
    })

    page = doc.new_page()
    text = (
        "A Survey of Multi-Agent Systems in AI\n\n"
        "ABSTRACT\n"
        "Multi-agent systems represent a paradigm shift in distributed intelligence. "
        "This paper explores coordination mechanisms and collective intelligence across autonomous agents.\n\n"
        "1. INTRODUCTION\n"
        "Autonomous agents operate in complex environments where coordination is paramount.\n\n"
        "2. METHODOLOGY\n"
        "We propose a hierarchical supervisor model where a central manager coordinates specialized worker agents.\n\n"
        "3. EXPERIMENTS\n"
        "We tested the framework against standard distributed benchmarks, achieving a 40% latency reduction.\n\n"
        "4. CONCLUSION\n"
        "Multi-agent architectures demonstrate superior modularity and reasoning efficiency.\n"
    )
    page.insert_text((50, 50), text, fontsize=11)
    doc.save(pdf_path)
    doc.close()

    yield pdf_path

    if os.path.exists(pdf_path):
        os.remove(pdf_path)


def test_extract_valid_paper(sample_pdf_path):
    result = pdf_extractor_service.extract_paper(sample_pdf_path)

    assert result["success"] is True
    assert result["is_scanned"] is False
    assert result["metadata"]["title"] == "A Survey of Multi-Agent Systems in AI"
    assert "Alan Turing" in result["metadata"]["authors"]
    assert result["metadata"]["total_pages"] == 1

    # Verify sections extracted
    sections = result["sections"]
    assert "abstract" in sections
    assert "Multi-agent systems represent a paradigm shift" in sections["abstract"]
    assert "methodology" in sections
    assert "hierarchical supervisor model" in sections["methodology"]
    assert "conclusion" in sections


def test_extract_invalid_pdf():
    # Create fake non-PDF file
    temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    temp_file.write(b"This is not a real PDF file header.")
    temp_file.close()

    try:
        result = pdf_extractor_service.extract_paper(temp_file.name)
        assert result["success"] is False
        assert "not a valid or readable PDF" in result["error"]
    finally:
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)


def test_extract_nonexistent_pdf():
    result = pdf_extractor_service.extract_paper("d:/non_existent_path/fake_paper.pdf")
    assert result["success"] is False
