import json
import sys
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT_DIR / "data" / "underwriting_samples.jsonl"
TEST_INPUTS_DIR = ROOT_DIR / "ocr" / "test_inputs"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ocr.pipeline import LANGUAGE_PRESETS, extract_text


st.set_page_config(
    page_title="AI-Assisted Underwriting",
    page_icon="A",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def load_dataset() -> pd.DataFrame:
    if not DATASET_PATH.exists():
        return pd.DataFrame()
    records = [json.loads(line) for line in DATASET_PATH.read_text(encoding="utf-8").splitlines()]
    return pd.DataFrame(records)


def render_header() -> None:
    st.title("AI-Assisted Underwriting")
    st.caption("Local UI for OCR extraction and synthetic underwriting dataset review.")


def render_dataset_page() -> None:
    st.subheader("Dataset Explorer")
    df = load_dataset()
    if df.empty:
        st.warning("Dataset file not found. Generate it with `python data/generate_underwriting_samples.py`.")
        return

    metrics = st.columns(4)
    metrics[0].metric("Samples", f"{len(df):,}")
    metrics[1].metric("Languages", df["language"].nunique())
    metrics[2].metric("Missing-field rows", int(df["missing_fields"].map(bool).sum()))
    metrics[3].metric("Decisions", df["decision"].nunique())

    chart_cols = st.columns(3)
    with chart_cols[0]:
        st.caption("Language mix")
        st.bar_chart(df["language"].value_counts())
    with chart_cols[1]:
        st.caption("Decision mix")
        st.bar_chart(df["decision"].value_counts())
    with chart_cols[2]:
        st.caption("Noise types")
        st.bar_chart(df["noise_type"].value_counts())

    st.divider()
    filters = st.columns(4)
    language = filters[0].multiselect("Language", sorted(df["language"].dropna().unique()))
    decision = filters[1].multiselect("Decision", sorted(df["decision"].dropna().unique()))
    noise_type = filters[2].multiselect("Noise type", sorted(df["noise_type"].dropna().unique()))
    text_search = filters[3].text_input("Search text")

    filtered = df.copy()
    if language:
        filtered = filtered[filtered["language"].isin(language)]
    if decision:
        filtered = filtered[filtered["decision"].isin(decision)]
    if noise_type:
        filtered = filtered[filtered["noise_type"].isin(noise_type)]
    if text_search:
        filtered = filtered[filtered["input_text"].str.contains(text_search, case=False, na=False)]

    st.caption(f"Showing {len(filtered):,} of {len(df):,} samples")
    st.dataframe(
        filtered[
            [
                "sample_id",
                "language",
                "input_text",
                "income",
                "loan_amount",
                "business_type",
                "gst_registered",
                "credit_history",
                "decision",
                "noise_type",
            ]
        ],
        use_container_width=True,
        height=430,
    )


def list_test_inputs() -> list[Path]:
    if not TEST_INPUTS_DIR.exists():
        return []
    return sorted(path for path in TEST_INPUTS_DIR.iterdir() if path.is_file())


def run_ocr(input_path: Path, engine: str, language_preset: str, dpi: int) -> str:
    result = extract_text(
        input_path,
        engine=engine,
        language_preset=language_preset,
        dpi=dpi,
    )
    return result.clean_text


def render_ocr_page() -> None:
    st.subheader("OCR Workspace")
    left, right = st.columns([0.34, 0.66], gap="large")

    with left:
        st.markdown("#### Input")
        input_mode = st.radio("Source", ["Upload file", "Use test fixture"], horizontal=True)
        engine = st.selectbox("OCR engine", ["tesseract", "easyocr"])
        language_preset = st.selectbox("Language preset", sorted(LANGUAGE_PRESETS), index=0)
        dpi = st.slider("PDF render DPI", min_value=120, max_value=360, value=220, step=20)

        selected_path = None
        uploaded_file = None
        if input_mode == "Upload file":
            uploaded_file = st.file_uploader(
                "PDF or image",
                type=["pdf", "png", "jpg", "jpeg", "tif", "tiff", "bmp", "webp"],
            )
        else:
            fixtures = list_test_inputs()
            if fixtures:
                fixture = st.selectbox("Fixture", fixtures, format_func=lambda path: path.name)
                selected_path = fixture
            else:
                st.warning("No OCR fixtures found under `ocr/test_inputs`.")

        run_clicked = st.button("Run OCR", type="primary", use_container_width=True)

    with right:
        st.markdown("#### Clean Text Output")
        if run_clicked:
            try:
                if uploaded_file is not None:
                    suffix = Path(uploaded_file.name).suffix
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                        temp_file.write(uploaded_file.getbuffer())
                        selected_path = Path(temp_file.name)

                if selected_path is None:
                    st.warning("Choose or upload a document first.")
                    return

                with st.spinner("Running OCR..."):
                    clean_text = run_ocr(selected_path, engine, language_preset, dpi)

                st.text_area("Extracted text", clean_text, height=420)
                st.download_button(
                    "Download text",
                    clean_text,
                    file_name=f"{Path(selected_path).stem}_ocr.txt",
                    mime="text/plain",
                )
            except Exception as exc:
                st.error(str(exc))
        else:
            st.info("Select a document and click Run OCR.")

    st.divider()
    st.markdown("#### Quick Commands")
    st.code(
        "python -m ocr.pipeline ocr/test_inputs/hindi_loan_note.png --language-preset hindi\n"
        "python -m ocr.pipeline ocr/test_inputs/hinglish_loan_note.png --language-preset hinglish\n"
        "python -m ocr.pipeline ocr/test_inputs/aadhaar_like.pdf --language-preset english",
        language="bash",
    )


def render_about_page() -> None:
    st.subheader("Project Status")
    st.write("This local UI currently wraps:")
    st.markdown(
        "- Synthetic underwriting dataset generated under `data/`\n"
        "- DVC-tracked dataset pointer: `data/underwriting_samples.jsonl.dvc`\n"
        "- OCR pipeline under `ocr/` using Tesseract, EasyOCR, and PyMuPDF\n"
        "- Hindi, Hinglish, English, and mixed language OCR presets"
    )
    st.code("streamlit run frontend/streamlit_app.py", language="bash")


def main() -> None:
    render_header()
    page = st.sidebar.radio("Navigation", ["OCR Workspace", "Dataset Explorer", "About"])
    if page == "OCR Workspace":
        render_ocr_page()
    elif page == "Dataset Explorer":
        render_dataset_page()
    else:
        render_about_page()


if __name__ == "__main__":
    main()
