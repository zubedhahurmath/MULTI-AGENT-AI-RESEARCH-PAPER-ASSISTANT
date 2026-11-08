import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Paper, PaperMetadata, PaperSummary, GeneratedAsset, AgentLog

# In-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_create_paper_and_relationships(db_session):
    # 1. Create Paper
    paper = Paper(
        original_filename="sample_research.pdf",
        stored_filename="paper_123.pdf",
        file_path="/tmp/paper_123.pdf",
        file_size_bytes=10240,
        status="PENDING"
    )
    db_session.add(paper)
    db_session.commit()
    db_session.refresh(paper)

    assert paper.id is not None
    assert paper.status == "PENDING"

    # 2. Add Metadata
    metadata = PaperMetadata(
        paper_id=paper.id,
        title="Deep Reinforcement Learning in Robotics",
        authors="Alice Smith, Bob Jones",
        publication_year="2025",
        total_pages=10
    )
    db_session.add(metadata)
    db_session.commit()

    # 3. Add Summary
    summary = PaperSummary(
        paper_id=paper.id,
        tldr="A novel approach to robotic control using deep RL.",
        problem_statement="High dimensionality of state space.",
        methodology="Policy gradient with actor-critic.",
        experimental_results="Achieved 95% task success rate."
    )
    db_session.add(summary)

    # 4. Add Generated Asset
    asset = GeneratedAsset(
        paper_id=paper.id,
        asset_type="presentation",
        title="Slide Deck",
        file_path="/tmp/presentation_123.pptx"
    )
    db_session.add(asset)

    # 5. Add Log
    log = AgentLog(
        paper_id=paper.id,
        agent_name="Manager Agent",
        log_level="INFO",
        message="Workflow initialized successfully."
    )
    db_session.add(log)
    db_session.commit()

    # Verify query
    retrieved = db_session.query(Paper).filter(Paper.id == paper.id).first()
    assert retrieved is not None
    assert retrieved.metadata_rel.title == "Deep Reinforcement Learning in Robotics"
    assert retrieved.summary.tldr == "A novel approach to robotic control using deep RL."
    assert len(retrieved.assets) == 1
    assert len(retrieved.logs) == 1


def test_cascade_delete_paper(db_session):
    paper = Paper(
        original_filename="delete_test.pdf",
        stored_filename="paper_del.pdf",
        file_path="/tmp/paper_del.pdf",
        file_size_bytes=5000,
        status="PENDING"
    )
    db_session.add(paper)
    db_session.commit()

    metadata = PaperMetadata(paper_id=paper.id, title="Test Paper")
    db_session.add(metadata)
    db_session.commit()

    # Delete paper
    db_session.delete(paper)
    db_session.commit()

    # Verify child record was cascade deleted
    remaining_meta = db_session.query(PaperMetadata).filter(PaperMetadata.paper_id == paper.id).first()
    assert remaining_meta is None
