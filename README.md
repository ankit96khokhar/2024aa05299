# AI-Assisted Underwriting

Project workspace for AI-assisted underwriting experiments, including OCR, RAG, model development, backend APIs, frontend work, and evaluation.

## Project Structure

```text
.
├── backend/
├── data/
├── docker/
├── docs/
├── evaluation/
├── frontend/
├── models/
├── notebooks/
├── ocr/
└── rag/
```

## Requirements

- Python 3.11+
- Git
- Tesseract OCR installed on the system for `pytesseract`

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Installed Python Packages

- PyTorch
- transformers
- sentence-transformers
- fastapi
- uvicorn
- langchain
- faiss-cpu
- pytesseract
- easyocr
- pandas
- scikit-learn
- dvc

## Dataset Versioning

The synthetic underwriting dataset is tracked with DVC:

```bash
python data/generate_underwriting_samples.py
dvc add data/underwriting_samples.jsonl
git add data/underwriting_samples.jsonl.dvc data/.gitignore
```

Check dataset state:

```bash
dvc status
```

The current dataset contains 1000 JSONL samples across Hindi, Hinglish, and English, including clean text, noisy text, OCR-like mistakes, and intentionally missing fields.

## GitHub

Repository:

```text
git@github.com:ankit96khokhar/2024aa05299.git
```
