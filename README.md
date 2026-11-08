# Multi-Agent AI Research Paper Assistant

An intelligent, multi-agent web application built with **FastAPI**, **LangGraph**, **Google Gemini**, and **PyMuPDF** that ingests academic research papers in PDF format and orchestrates specialized AI agents to generate structured summaries, presentation slide decks, contextual professional emails, and reproducible implementation code.

---

## 🌟 Key Features

1. **Manager Agent**: Central orchestrator coordinating extraction, analysis, generation, and state persistence.
2. **PDF Processing Agent**: Fast extraction of text, titles, authors, and structured paper sections using PyMuPDF.
3. **Summarizer Agent**: In-depth academic synthesis covering Executive Summary, Problem Statement, Contributions, Methodology, Results, and Limitations.
4. **PPT Generator Agent**: Builds downloadable, formatted PowerPoint presentations (`.pptx`) using `python-pptx`.
5. **Email Generator Agent**: Drafts 3 professional personas (Advisor Briefing, Peer Discussion, and Author Inquiry).
6. **Code Generator Agent**: Synthesizes runnable Python prototype code with unit test demonstrations based on the paper's methodology.

---

## 📂 Project Structure

```text
Multi-Agent-AI-Research-Paper-Assistant/
├── app/
│   ├── agents/          # LangGraph multi-agent system definitions
│   ├── services/        # Low-level tools (PyMuPDF, python-pptx, Gemini API client)
│   ├── static/          # Frontend assets (CSS, JS, images)
│   ├── templates/       # HTML templates (Dashboard UI)
│   ├── config.py        # Application settings and environment management
│   ├── database.py      # SQLite connection and session management
│   ├── models.py        # SQLAlchemy database models
│   ├── schemas.py       # Pydantic validation schemas
│   └── main.py          # FastAPI server entry point
├── data/
│   ├── uploads/         # Uploaded research papers (PDF)
│   └── presentations/   # Generated PowerPoint decks (.pptx)
├── tests/               # Unit and integration test suite
├── .env.example         # Environment variables template
├── .gitignore           # Git ignore file
├── README.md            # Project documentation
└── requirements.txt     # Python dependencies
```

---

## 🚀 Quickstart Guide

*(To be updated upon backend and frontend implementation)*
