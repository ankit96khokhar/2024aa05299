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
LANGUAGE_PRESETS = {
    "english": {"tesseract": "eng", "easyocr": ["en"]},
    "hinglish": {"tesseract": "eng", "easyocr": ["en"]},
    "hindi": {"tesseract": "hin+eng", "easyocr": ["hi", "en"]},
    "mixed": {"tesseract": "hin+eng", "easyocr": ["hi", "en"]},
}


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
    installed_languages = set(pytesseract.get_languages(config=""))
    requested_languages = set(language.split("+"))
    missing_languages = requested_languages - installed_languages
    if missing_languages:
        missing = ", ".join(sorted(missing_languages))
        installed = ", ".join(sorted(installed_languages))
        raise RuntimeError(
            f"Tesseract language data missing: {missing}. Installed languages: {installed}. "
            "Install Hindi support with `brew install tesseract-lang` on macOS, "
            "or use EasyOCR with `--engine easyocr --language-preset hindi`."
        )

    processed = preprocess_image(image)
    config = "--oem 3 --psm 6"
    try:
        return pytesseract.image_to_string(processed, lang=language, config=config)
    except pytesseract.TesseractError as exc:
        if "Failed loading language" in str(exc) or "Error opening data file" in str(exc):
            raise RuntimeError(
                f"Tesseract language '{language}' is not installed. "
                "Install Hindi support with `brew install tesseract-lang` on macOS, "
                "or use EasyOCR with `--engine easyocr --language-preset hindi`."
            ) from exc
        raise


def ocr_with_easyocr(image: Image.Image, languages: list[str]) -> str:
    import easyocr

    reader = easyocr.Reader(languages, gpu=False)
    lines = reader.readtext(image, detail=0, paragraph=True)
    return "\n".join(lines)


def resolve_languages(
    language_preset: str,
    tesseract_language: str | None,
    easyocr_languages: list[str] | None,
) -> tuple[str, list[str]]:
    preset = LANGUAGE_PRESETS[language_preset]
    return (
        tesseract_language or preset["tesseract"],
        easyocr_languages or list(preset["easyocr"]),
    )


def extract_text(
    input_path: str | Path,
    engine: str = "tesseract",
    language_preset: str = "english",
    tesseract_language: str | None = None,
    easyocr_languages: list[str] | None = None,
    dpi: int = 220,
) -> OCRResult:
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(path)
    if language_preset not in LANGUAGE_PRESETS:
        allowed = ", ".join(sorted(LANGUAGE_PRESETS))
        raise ValueError(f"language_preset must be one of: {allowed}")

    resolved_tesseract_language, resolved_easyocr_languages = resolve_languages(
        language_preset,
        tesseract_language,
        easyocr_languages,
    )

    pages = []
    for page_number, image in iter_images(path, dpi=dpi):
        if engine == "tesseract":
            raw_text = ocr_with_tesseract(image, language=resolved_tesseract_language)
        elif engine == "easyocr":
            raw_text = ocr_with_easyocr(image, languages=resolved_easyocr_languages)
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
    parser.add_argument(
        "--language-preset",
        choices=sorted(LANGUAGE_PRESETS),
        default="english",
        help="Language preset for OCR. Use hindi or mixed for Devanagari Hindi.",
    )
    parser.add_argument("--tesseract-language", help="Override Tesseract lang, e.g. eng, hin, hin+eng")
    parser.add_argument("--easyocr-language", action="append", dest="easyocr_languages")
    parser.add_argument("--dpi", type=int, default=220)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        result = extract_text(
            args.input,
            engine=args.engine,
            language_preset=args.language_preset,
            tesseract_language=args.tesseract_language,
            easyocr_languages=args.easyocr_languages,
            dpi=args.dpi,
        )
    except RuntimeError as exc:
        raise SystemExit(f"ERROR: {exc}") from None

    if args.output:
        write_text(result, args.output)
    else:
        print(result.clean_text)


if __name__ == "__main__":
    main()
