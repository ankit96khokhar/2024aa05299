# OCR Pipeline

Open-source OCR pipeline for extracting clean text from PDFs and images.

## Engines

- Tesseract via `pytesseract`
- EasyOCR via `easyocr`

PDF pages are rendered to images with `PyMuPDF`, then passed through the selected OCR engine.

## Generate Test Inputs

```bash
python ocr/generate_test_inputs.py
```

This creates synthetic, non-sensitive examples under `ocr/test_inputs/`:

- Aadhaar-like document
- GST document
- Bank statement
- Handwritten-note style document
- Hindi loan note
- Hinglish loan note
- Aadhaar-like PDF

## Run OCR

Image to plain text:

```bash
python -m ocr.pipeline ocr/test_inputs/aadhaar_like.png -o ocr/outputs/aadhaar_like.txt
```

PDF to plain text:

```bash
python -m ocr.pipeline ocr/test_inputs/aadhaar_like.pdf -o ocr/outputs/aadhaar_like_pdf.txt
```

EasyOCR:

```bash
python -m ocr.pipeline ocr/test_inputs/gst_document.png --engine easyocr --easyocr-language en
```

Hindi with Tesseract:

```bash
python -m ocr.pipeline ocr/test_inputs/hindi_loan_note.png --language-preset hindi
```

Hinglish with Tesseract:

```bash
python -m ocr.pipeline ocr/test_inputs/hinglish_loan_note.png --language-preset hinglish
```

Mixed Hindi and English with EasyOCR:

```bash
python -m ocr.pipeline ocr/test_inputs/hindi_loan_note.png --engine easyocr --language-preset mixed
```

Tesseract Hindi requires the `hin` trained data. On macOS:

```bash
brew install tesseract-lang
```

Check installed OCR languages:

```bash
tesseract --list-langs
```

## Output

The pipeline returns cleaned plain text with repeated whitespace removed and empty OCR lines filtered.
