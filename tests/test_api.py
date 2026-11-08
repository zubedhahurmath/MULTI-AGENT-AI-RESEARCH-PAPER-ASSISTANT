import os
import io
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, SessionLocal
from app.models import Paper, GeneratedAsset

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "Multi-Agent AI Research Paper Assistant" in data["app_name"]
    assert "gemini_configured" in data


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200


def test_upload_valid_pdf_no_autoprocess():
    # Construct minimal valid PDF bytes
    valid_pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"

    response = client.post(
        "/api/upload?auto_process=false",
        files={"file": ("test_paper.pdf", io.BytesIO(valid_pdf_bytes), "application/pdf")}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["paper_id"] is not None
    assert data["original_filename"] == "test_paper.pdf"
    assert data["status"] == "PENDING"


def test_upload_invalid_extension():
    response = client.post(
        "/api/upload",
        files={"file": ("document.txt", io.BytesIO(b"Hello world"), "text/plain")}
    )
    assert response.status_code == 400
    assert "Only PDF research papers" in response.json()["detail"]


def test_upload_invalid_magic_bytes():
    # Has .pdf extension but fake contents
    response = client.post(
        "/api/upload",
        files={"file": ("fake.pdf", io.BytesIO(b"Not a PDF header"), "application/pdf")}
    )
    assert response.status_code == 400
    assert "standard PDF header bytes" in response.json()["detail"]


def test_get_paper_status():
    # Insert dummy paper into DB
    db = SessionLocal()
    paper = Paper(
        original_filename="status_test.pdf",
        stored_filename=f"status_{uuid.uuid4().hex[:8]}.pdf",
        file_path="/tmp/status_123.pdf",
        file_size_bytes=1024,
        status="PROCESSING"
    )
    db.add(paper)
    db.commit()
    paper_id = paper.id
    db.close()

    response = client.get(f"/api/status/{paper_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["paper_id"] == paper_id
    assert data["status"] == "PROCESSING"


def test_get_paper_results():
    db = SessionLocal()
    paper = Paper(
        original_filename="results_test.pdf",
        stored_filename=f"results_{uuid.uuid4().hex[:8]}.pdf",
        file_path="/tmp/results_123.pdf",
        file_size_bytes=1024,
        status="COMPLETED"
    )
    db.add(paper)
    db.commit()
    paper_id = paper.id
    db.close()

    response = client.get(f"/api/results/{paper_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["paper_id"] == paper_id
    assert data["status"] == "COMPLETED"


def test_download_asset_security_and_success():
    from app.config import settings

    # Create dummy presentation file in allowed directory
    test_ppt_path = settings.PRESENTATION_DIR / "test_download.pptx"
    test_ppt_path.write_bytes(b"PK\x03\x04Dummy PPTX Content")

    db = SessionLocal()
    unique_name = f"dl_{uuid.uuid4().hex[:8]}.pdf"
    paper = Paper(
        original_filename="dl_test.pdf",
        stored_filename=unique_name,
        file_path="/tmp/dl_123.pdf",
        file_size_bytes=1024,
        status="COMPLETED"
    )
    db.add(paper)
    db.commit()
    paper_id = paper.id

    asset = GeneratedAsset(
        paper_id=paper_id,
        asset_type="presentation",
        title="Download Test PPT",
        file_path=str(test_ppt_path)
    )
    db.add(asset)
    db.commit()
    asset_id = asset.id
    db.close()

    # Test authorized download
    response = client.get(f"/api/download/{asset_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.presentationml.presentation"

    # Test path traversal attack prevention
    db = SessionLocal()
    forbidden_asset = GeneratedAsset(
        paper_id=paper_id,
        asset_type="presentation",
        title="Malicious Asset",
        file_path="C:/Windows/System32/drivers/etc/hosts"
    )
    db.add(forbidden_asset)
    db.commit()
    forbidden_id = forbidden_asset.id
    db.close()

    response_forbidden = client.get(f"/api/download/{forbidden_id}")
    assert response_forbidden.status_code == 403

    # Clean up test file
    if test_ppt_path.exists():
        test_ppt_path.unlink()
