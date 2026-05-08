# Streamlit UI

Local UI for the OCR pipeline and synthetic underwriting dataset.

## Run

```bash
source .venv/bin/activate
streamlit run frontend/streamlit_app.py
```

Then open:

```text
http://localhost:8501
```

## Features

- Upload PDF/image documents and extract clean text.
- Use built-in Aadhaar-like, GST, bank statement, Hindi, and Hinglish test fixtures.
- Select OCR engine: Tesseract or EasyOCR.
- Select language preset: English, Hindi, Hinglish, or mixed.
- Browse the 1000-sample underwriting dataset and filter by language, decision, noise type, or search text.
