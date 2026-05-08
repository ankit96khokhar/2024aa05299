from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUTPUT_DIR = Path(__file__).parent / "test_inputs"


DOCUMENTS = {
    "aadhaar_like": [
        "AADHAAR-LIKE ID SAMPLE",
        "Name: Rohan Sharma",
        "DOB: 12/08/1993",
        "Gender: Male",
        "Address: Pune, Maharashtra",
        "Masked Aadhaar: XXXX XXXX 4321",
    ],
    "gst_document": [
        "GST REGISTRATION SAMPLE",
        "Legal Name: Sharma Retail Traders",
        "GSTIN: 27ABCDE1234F1Z5",
        "Business Type: Retail",
        "Registration Date: 14/07/2021",
        "Status: Active",
    ],
    "bank_statement": [
        "BANK STATEMENT SAMPLE",
        "Account Holder: Priya Verma",
        "Statement Month: March 2026",
        "Opening Balance: 45000",
        "Salary Credit: 78000",
        "Loan EMI Debit: 12000",
        "Closing Balance: 92000",
    ],
    "handwritten_note": [
        "HANDWRITTEN NOTE STYLE SAMPLE",
        "Monthly income approx 45000",
        "Need business loan 300000",
        "Kirana shop, GST not registered",
        "Existing EMI 5000",
    ],
    "hindi_loan_note": [
        "हिंदी ऋण आवेदन नमूना",
        "नाम: रोहन शर्मा",
        "मासिक आय: 45000",
        "ऋण राशि: 300000",
        "व्यवसाय: किराना दुकान",
        "GST पंजीकृत: नहीं",
    ],
    "hinglish_loan_note": [
        "HINGLISH LOAN NOTE SAMPLE",
        "Meri monthly income 45000 hai",
        "Mujhe 3 lakh ka loan chahiye",
        "Business: kirana shop",
        "GST registered: nahi",
        "Existing EMI: 5000",
    ],
}


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc",
        "/System/Library/Fonts/Supplemental/DevanagariMT.ttc",
        "/System/Library/Fonts/Supplemental/ITFDevanagari.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_image(lines: list[str], output_path: Path, handwritten: bool = False) -> None:
    image = Image.new("RGB", (1100, 760), "white")
    draw = ImageDraw.Draw(image)
    title_font = load_font(42)
    body_font = load_font(32 if not handwritten else 34)

    y = 70
    for index, line in enumerate(lines):
        font = title_font if index == 0 else body_font
        x = 75 + ((index % 2) * 8 if handwritten else 0)
        draw.text((x, y), line, fill="black", font=font)
        y += 78 if index == 0 else 64

    if handwritten:
        for offset in range(0, 5):
            draw.line((70, 160 + offset * 86, 980, 166 + offset * 86), fill=(230, 230, 230), width=1)

    image.save(output_path)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    first_image = None
    for name, lines in DOCUMENTS.items():
        image_path = OUTPUT_DIR / f"{name}.png"
        make_image(lines, image_path, handwritten=name == "handwritten_note")
        if first_image is None:
            first_image = Image.open(image_path).convert("RGB")

    pdf_path = OUTPUT_DIR / "aadhaar_like.pdf"
    if first_image:
        first_image.save(pdf_path, "PDF", resolution=100)


if __name__ == "__main__":
    main()
