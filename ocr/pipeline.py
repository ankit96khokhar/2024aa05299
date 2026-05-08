import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import fitz
import pytesseract
from PIL import Image, ImageOps


SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
SUPPORTED_PDF_EXTENSIONS = {".pdf"}


@dataclass
class OCRPageResult:
    page_number: int
    raw_text: str
    clean_text: str


@dataclass
class OCRResult:
    input_path: Path
    engine: str
    pages: list[OCRPageResult]

    @property
    def clean_text(self) -> str:
        return "\n\n".join(page.clean_text for page in self.pages if page.clean_text)


def clean_ocr_text(text: str) -> str:
    text = text.replace("\x0c", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip(" -|") for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines).strip()


def preprocess_image(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    image = image.convert("L")
    image = ImageOps.autocontrast(image)
    return image


def iter_images(input_path: Path, dpi: int = 220) -> Iterable[tuple[int, Image.Image]]:
    suffix = input_path.suffix.lower()
    if suffix in SUPPORTED_IMAGE_EXTENSIONS:
        with Image.open(input_path) as image:
            yield 1, image.copy()
        return

    if suffix in SUPPORTED_PDF_EXTENSIONS:
        with fitz.open(input_path) as document:
            zoom = dpi / 72
            matrix = fitz.Matrix(zoom, zoom)
            for page_index, page in enumerate(document, start=1):
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
                yield page_index, image
        return

    supported = ", ".join(sorted(SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_PDF_EXTENSIONS))
    raise ValueError(f"Unsupported input type: {input_path.suffix}. Supported: {supported}")


def ocr_with_tesseract(image: Image.Image, language: str = "eng") -> str:
    processed = preprocess_image(image)
    config = "--oem 3 --psm 6"
    return pytesseract.image_to_string(processed, lang=language, config=config)


def ocr_with_easyocr(image: Image.Image, languages: list[str]) -> str:
    import easyocr

    reader = easyocr.Reader(languages, gpu=False)
    lines = reader.readtext(image, detail=0, paragraph=True)
    return "\n".join(lines)


def extract_text(
    input_path: str | Path,
    engine: str = "tesseract",
    tesseract_language: str = "eng",
    easyocr_languages: list[str] | None = None,
    dpi: int = 220,
) -> OCRResult:
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(path)

    pages = []
    for page_number, image in iter_images(path, dpi=dpi):
        if engine == "tesseract":
            raw_text = ocr_with_tesseract(image, language=tesseract_language)
        elif engine == "easyocr":
            raw_text = ocr_with_easyocr(image, languages=easyocr_languages or ["en"])
        else:
            raise ValueError("engine must be 'tesseract' or 'easyocr'")

        pages.append(
            OCRPageResult(
                page_number=page_number,
                raw_text=raw_text,
                clean_text=clean_ocr_text(raw_text),
            )
        )

    return OCRResult(input_path=path, engine=engine, pages=pages)


def write_text(result: OCRResult, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(result.clean_text + "\n", encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract clean text from PDFs and images.")
    parser.add_argument("input", help="Input PDF or image path")
    parser.add_argument("-o", "--output", help="Output text path")
    parser.add_argument("--engine", choices=["tesseract", "easyocr"], default="tesseract")
    parser.add_argument("--tesseract-language", default="eng")
    parser.add_argument("--easyocr-language", action="append", dest="easyocr_languages")
    parser.add_argument("--dpi", type=int, default=220)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = extract_text(
        args.input,
        engine=args.engine,
        tesseract_language=args.tesseract_language,
        easyocr_languages=args.easyocr_languages,
        dpi=args.dpi,
    )
    if args.output:
        write_text(result, args.output)
    else:
        print(result.clean_text)


if __name__ == "__main__":
    main()
