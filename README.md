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

```
       
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

```
## ⚙️ Installation
### 1. Clone the repository
```bash
git clone https://github.com/yourusername/education-chatbot.git
cd education-chatbot

```
### 2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate     # MacOS/Linux
venv\Scripts\activate        # Windows
```
### 3. Install dependencies
```bash
Install dependencies
```
### 4. Set environment variables
```bash
OPENAI_API_KEY=your_key
DATABASE_URL=postgresql://user:pass@localhost:5432/chatbot
VECTOR_DB_URL=postgresql://user:pass@localhost:5432/chatbot
JWT_SECRET=your_secret
```
## 🖼️ Instructions

1. Upload learning materials

Vào trang Subject → Upload

Hệ thống sẽ:

Trích xuất văn bản

Chunking

Tạo embeddings

Lưu vào VectorDB

Sinh tóm tắt

Sinh câu hỏi ôn tập 

2. Ask questions and chat

Chọn môn học → Mở cuộc trò chuyện

Chat hiển thị streaming

Trả lời dựa trên nội dung tài liệu (không bịa).

Mỗi message được lưu trong DB.

3. Manage subjects/documents

Tạo môn học mới

Xem danh sách tài liệu

Xóa / cập nhật tài liệu

Xem lịch sử chat theo từng môn

## 🧠 RAG Pipeline Overview

Ingestion Pipeline

Upload PDF

Extract text & images

Chunking (350–450 tokens)

Generate embeddings

Store in VectorDB

Summaries + Question Generation

Chat Pipeline

Người dùng đặt câu hỏi

Retrieve + Rerank chunks

Tạo prompt chứa context

LLM trả lời (stream)

Lưu message vào DB

Evaluate RAG quality (RAGAS)



## 🧭 Next Steps
Thêm multimodal RAG (PDF hình ảnh → captioning → OCR).

Thêm Flashcard generation.

Thêm voice conversation mode.

Thêm LLM fine-tuning theo từng môn học.

Thêm RAG evaluation dashboard (RAGAS metrics).

Triển khai bản mobile React Native.

