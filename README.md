# 🤖 Education Q&A Chatbot – Intelligent Learning Assistant

## 📚 Contents
- [🔰 Introduction](#-introduction)
- [🏗️ Architecture](#-architecture)
- [📁 Folder Structure](#-folder-structure)
- [⚙️ Installation](#-installation)
  - [1. Clone the repository](#1-clone-the-repository)
  - [2. Create and activate virtual environment](#2-create-and-activate-virtual-environment)
  - [3. Install dependencies](#3-install-dependencies)
  - [4. Environment configuration](#4-environment-configuration)
- [🖼️ Instructions](#-instructions)
- [⚙️ CI/CD Pipeline](#-cicd-pipeline)
- [🧭 Next Steps](#-next-steps)

---

## 🔰 Introduction
The **Education Q&A Chatbot** is an intelligent learning assistant designed to help students interact with their uploaded study materials (PDFs containing text and images).  
Users can upload one or multiple documents for each course, and the chatbot will answer questions *only* based on the uploaded materials, similar to NotebookLM/ChatPDF.

This project incorporates modern ML techniques and a modular backend to ensure scalability, maintainability, and reproducibility.

---

## 🏗️ Architecture

```text
 ┌────────────────────────────────────────┐
 │                FRONTEND                │
 │   - Login / Register                   │
 │   - Upload PDF                         │
 │   - Subject Dashboard                  │
 │   - Chat UI (Streaming)                │
 └────────────────────────────────────────┘
                 │  REST / SSE
                 ▼
 ┌────────────────────────────────────────┐
 │              BACKEND API               │
 │ FastAPI:                               │
 │   /auth                                │
 │   /subjects                            │
 │   /documents                           │
 │   /conversations                       │
 │   /chat (sync + stream)                │
 └────────────────────────────────────────┘
                 │
                 ▼
 ┌────────────────────────────────────────┐
 │        RAG PIPELINE ENGINE             │
 │  - Text Extraction (PDF/Image)         │
 │  - Chunking                            │
 │  - Embeddings                          │
 │  - Vector Store Retrieval + Reranking  │
 │  - Summarizer                          │
 │  - Question Generator                  │
 │  - LLM Response (Streaming)            │
 └────────────────────────────────────────┘
                 │
                 ▼
 ┌───────────────────────────┐   ┌─────────────────────────┐
 │ Postgres (Relational DB)  │   │ Vector DB (pgvector)    │
 │ User / Subject / Document │   │ Chunk-level Embeddings  │
 │ Conversation / Messages   │   │ Metadata                │
 └───────────────────────────┘   └─────────────────────────┘
                 │
                 ▼
         ┌─────────────────┐
         │ Background Jobs │
         │   Celery/Redis  │
         │ - Embedding     │
         │ - Summaries     │
         │ - QG generation │
         └─────────────────┘

         
## 📁 Folder Structure
```text
education-chatbot/
│
├── backend/
│   ├── main.py
│   ├── api/
│   ├── services/
│   ├── rag/
│   ├── workers/
│   ├── models/
│   ├── database/
│   ├── utils/
│   └── tests/
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
│
├── data/
│   ├── uploads/
│   ├── processed/
│   └── embeddings/
│
├── scripts/
│
├── docs/
│
└── README.md

## ⚙️ Installation
