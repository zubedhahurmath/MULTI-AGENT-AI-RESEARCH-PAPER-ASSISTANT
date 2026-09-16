# MULTI-AGENT AI RESEARCH PAPER ASSISTANT

A Multi-Agent AI system that helps students, researchers, and academicians analyze research papers and generate useful outputs such as summaries, references, presentations, emails, and implementation code.

## 📌 Overview

The rapid growth of research publications makes it difficult and time-consuming to read, understand, and analyze multiple research papers.

The **Multi-Agent AI Research Paper Assistant** uses **Large Language Models (LLMs)** and **Retrieval-Augmented Generation (RAG)** to simplify research paper analysis.

The system accepts one or more research papers in PDF format. A Manager Agent understands the user's request and coordinates specialized AI agents to perform different tasks.

## 🎯 Objectives

- Analyze research papers efficiently.
- Generate concise summaries of research papers.
- Extract important references and bibliographic information.
- Generate presentation slides from research papers.
- Draft professional emails for sharing research findings.
- Generate basic implementation or starter code when applicable.
- Provide context-aware answers using Retrieval-Augmented Generation.
- Reduce the manual effort required to understand research papers.

## 👥 Target Users

- Students
- Researchers
- Faculty Members
- Academicians
- Technical learners

## 🤖 Multi-Agent System

The system consists of a Manager Agent and multiple specialized agents.

### 1. Manager Agent

The Manager Agent analyzes the user's request and coordinates the other agents.

### 2. Summary Agent

Generates concise summaries of different sections of the research paper.

### 3. Reference Agent

Extracts information such as:

- Authors
- Citations
- Keywords
- Bibliography
- References

### 4. Presentation Agent

Creates presentation slides based on the content of the research paper.

### 5. Email Agent

Generates professional emails for sharing research findings.

### 6. Code Agent

Generates basic implementation or starter code related to the methodology described in the research paper, whenever applicable.

## 🔍 Retrieval-Augmented Generation (RAG)

The system uses RAG to provide context-aware responses from uploaded research papers.

The basic workflow is:

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
LLM
       ↓
AI-Generated Output
