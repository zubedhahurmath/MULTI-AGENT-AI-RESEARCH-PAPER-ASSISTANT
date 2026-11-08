# Multi-Agent AI Research Paper Assistant

An intelligent Multi-Agent AI web application that helps students, researchers, and academicians analyze research papers and generate useful outputs such as summaries, presentation slides, professional emails, and implementation code.

## 📌 Overview

The rapid growth of research publications makes it difficult and time-consuming to read, understand, and analyze multiple research papers.

The **Multi-Agent AI Research Paper Assistant** uses Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), and specialized AI agents to simplify research paper analysis.

The system accepts research papers in PDF format. A Manager Agent understands the user's request and coordinates different specialized agents to perform specific tasks.

## 🎯 Objectives

- Analyze research papers efficiently.
- Generate concise summaries of research papers.
- Extract important information and references.
- Generate presentation slides from research papers.
- Draft professional emails for sharing research findings.
- Generate implementation or starter code based on research methodologies.
- Provide context-aware answers using RAG.
- Reduce the manual effort required to understand research papers.

## 🌟 Key Features

1. **Manager Agent:** Coordinates all specialized agents and manages the complete workflow.
2. **PDF Processing Agent:** Extracts text, titles, authors, and structured sections from PDF documents using PyMuPDF.
3. **Summarizer Agent:** Generates detailed academic summaries covering problem statements, contributions, methodology, results, and limitations.
4. **PPT Generator Agent:** Creates downloadable PowerPoint presentations using python-pptx.
5. **Email Generator Agent:** Drafts professional emails for different purposes, including advisor briefings, peer discussions, and author inquiries.
6. **Code Generator Agent:** Generates Python prototype code and unit test demonstrations based on research methodologies.
7. **RAG System:** Retrieves relevant information from uploaded research papers to generate context-aware responses.

## 👥 Target Users

- Students
- Researchers
- Faculty Members
- Academicians
- Technical Learners

## 🤖 Multi-Agent System

The system consists of a Manager Agent and multiple specialized agents.

### 1. Manager Agent
Analyzes user requests, coordinates specialized agents, validates outputs, and manages the workflow.

### 2. PDF Processing Agent
Extracts and processes text and important information from uploaded research papers.

### 3. Summarizer Agent
Generates structured summaries of research papers.

### 4. Reference Agent
Extracts bibliographic information, authors, citations, keywords, and references.

### 5. Presentation Agent
Creates presentation slides based on research paper content.

### 6. Email Agent
Generates professional emails for communicating research findings.

### 7. Code Agent
Generates implementation or starter code based on the methodology described in research papers.

## 🔍 Retrieval-Augmented Generation (RAG)

The system uses RAG to provide context-aware responses based on uploaded research papers.

### RAG Workflow

```text
Research Paper PDF
       ↓
Text Extraction
       ↓
Text Processing
       ↓
Embeddings Generation
       ↓
Vector Database
       ↓
Relevant Information Retrieval
       ↓
Large Language Model (LLM)
       ↓
AI-Generated Output
```

## 🛠️ Technology Stack

- **Backend:** FastAPI
- **AI Framework:** LangGraph
- **LLM:** Google Gemini
- **PDF Processing:** PyMuPDF
- **Presentation Generation:** python-pptx
- **Database:** SQLite
- **Programming Language:** Python
- **Frontend:** HTML, CSS, JavaScript

## 📂 Project Structure

```text
Multi-Agent-AI-Research-Paper-Assistant/
├── app/
│   ├── agents/
│   ├── services/
│   ├── static/
│   ├── templates/
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── main.py
├── data/
│   ├── uploads/
│   └── presentations/
├── tests/
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## 🚀 Installation and Setup

1. Clone the repository:

```bash
git clone https://github.com/zubedhahurmath/MULTI-AGENT-AI-RESEARCH-PAPER-ASSISTANT.git
```

2. Navigate to the project directory:

```bash
cd MULTI-AGENT-AI-RESEARCH-PAPER-ASSISTANT
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

4. Configure the required environment variables in your `.env` file.

5. Run the application:

```bash
uvicorn app.main:app --reload
```

## 📌 Future Enhancements

- Support for multiple research paper uploads.
- Improved multi-agent collaboration.
- Advanced research comparison and analysis.
- Enhanced reference and citation management.
- More accurate research code generation.

---

**Developed as an Academic Project**

**Project Name:** Multi-Agent AI Research Paper Assistant