import json
import random
from pathlib import Path


RANDOM_SEED = 202405299
OUTPUT_PATH = Path(__file__).with_name("underwriting_samples.jsonl")
SAMPLE_COUNT = 1000

BUSINESS_TYPES = [
    "retail",
    "kirana",
    "manufacturing",
    "services",
    "transport",
    "food_stall",
    "online_seller",
    "tailoring",
    "wholesale",
    "agriculture",
]

EMPLOYMENT_TYPES = [
    "salaried",
    "self_employed",
    "business_owner",
    "gig_worker",
    "contract_worker",
]

CREDIT_HISTORY = ["excellent", "good", "average", "thin_file", "poor", "unknown"]
LANGUAGES = ["hindi", "hinglish", "english"]
NOISE_TYPES = ["clean", "noisy_text", "ocr_like", "missing_fields"]


def decide(income, loan_amount, existing_loans, credit_history, monthly_expenses, bank_balance, gst_registered):
    debt_ratio = existing_loans / max(income, 1)
    expense_ratio = monthly_expenses / max(income, 1)
    loan_income_ratio = loan_amount / max(income, 1)

    score = 0
    if income >= 60000:
        score += 2
    elif income >= 35000:
        score += 1
    else:
        score -= 1

    if loan_income_ratio <= 5:
        score += 2
    elif loan_income_ratio <= 9:
        score += 1
    else:
        score -= 2

    if credit_history in {"excellent", "good"}:
        score += 2
    elif credit_history in {"average", "thin_file"}:
        score += 0
    else:
        score -= 2

    if debt_ratio <= 0.25:
        score += 1
    elif debt_ratio > 0.5:
        score -= 2

    if expense_ratio <= 0.55:
        score += 1
    elif expense_ratio > 0.75:
        score -= 1

    if bank_balance >= monthly_expenses:
        score += 1

    if gst_registered:
        score += 1

    if score >= 5:
        return "Approve"
    if score <= 0:
        return "Reject"
    return "Review"


def format_amount(amount):
    if amount >= 100000:
        lakh = amount / 100000
        return f"{lakh:g} lakh"
    return str(amount)


def make_input_text(language, income, loan_amount, business_type, gst_registered, existing_loans, credit_history, monthly_expenses, bank_balance, employment_type):
    gst_text = "GST registered" if gst_registered else "not GST registered"
    if language == "hindi":
        return (
            f"Meri mahine ki aamdani {income} hai, mujhe {format_amount(loan_amount)} ka loan chahiye. "
            f"Mera kaam {business_type} hai, {gst_text}, existing loan EMI {existing_loans}, "
            f"credit history {credit_history}, monthly kharcha {monthly_expenses}, bank balance {bank_balance}, "
            f"employment {employment_type}."
        )
    if language == "hinglish":
        return (
            f"Meri monthly income {income} hai aur mujhe {format_amount(loan_amount)} ka loan chahiye. "
            f"Business type {business_type}, GST status {gst_text}, current EMI {existing_loans}, "
            f"credit history {credit_history}, expenses {monthly_expenses}, bank balance {bank_balance}, "
            f"employment type {employment_type}."
        )
    return (
        f"My monthly income is {income} and I need a loan of {loan_amount}. "
        f"Business type is {business_type}, GST status is {gst_text}, existing loan EMI is {existing_loans}, "
        f"credit history is {credit_history}, monthly expenses are {monthly_expenses}, bank balance is {bank_balance}, "
        f"employment type is {employment_type}."
    )


def add_noisy_text(text, rng):
    replacements = {
        "monthly": "mnthly",
        "income": "incm",
        "loan": "loan!!",
        "business": "biz",
        "registered": "regd",
        "balance": "bal",
        "expenses": "expns",
        "credit": "crdt",
    }
    for source, target in replacements.items():
        if source in text and rng.random() < 0.45:
            text = text.replace(source, target)
    if rng.random() < 0.5:
        text = text.lower()
    if rng.random() < 0.35:
        text = f"{text} pls check asap"
    return text


def add_ocr_mistakes(text, rng):
    replacements = {
        "0": "O",
        "1": "I",
        "5": "S",
        "8": "B",
        "income": "incorne",
        "loan": "Ioan",
        "GST": "6ST",
        "balance": "baIance",
        "monthly": "rnonthly",
    }
    for source, target in replacements.items():
        if source in text and rng.random() < 0.5:
            text = text.replace(source, target)
    if rng.random() < 0.3:
        text = text.replace(" ", "  ")
    return text


def make_record(index, rng):
    language = LANGUAGES[index % len(LANGUAGES)]
    noise_type = NOISE_TYPES[(index // len(LANGUAGES)) % len(NOISE_TYPES)]

    income = rng.randrange(15000, 180001, 1000)
    loan_amount = rng.randrange(50000, 2000001, 10000)
    business_type = rng.choice(BUSINESS_TYPES)
    gst_registered = rng.choice([True, False])
    existing_loans = rng.randrange(0, 90001, 1000)
    credit_history = rng.choice(CREDIT_HISTORY)
    monthly_expenses = rng.randrange(8000, min(income + 20000, 140000), 1000)
    bank_balance = rng.randrange(1000, 500001, 1000)
    employment_type = rng.choice(EMPLOYMENT_TYPES)
    decision = decide(
        income,
        loan_amount,
        existing_loans,
        credit_history,
        monthly_expenses,
        bank_balance,
        gst_registered,
    )
    input_text = make_input_text(
        language,
        income,
        loan_amount,
        business_type,
        gst_registered,
        existing_loans,
        credit_history,
        monthly_expenses,
        bank_balance,
        employment_type,
    )

    missing_fields = []
    if noise_type == "noisy_text":
        input_text = add_noisy_text(input_text, rng)
    elif noise_type == "ocr_like":
        input_text = add_ocr_mistakes(input_text, rng)

    record = {
        "sample_id": f"UW-{index + 1:04d}",
        "language": language,
        "input_text": input_text,
        "income": income,
        "loan_amount": loan_amount,
        "business_type": business_type,
        "gst_registered": gst_registered,
        "existing_loans": existing_loans,
        "credit_history": credit_history,
        "monthly_expenses": monthly_expenses,
        "bank_balance": bank_balance,
        "employment_type": employment_type,
        "decision": decision,
        "noise_type": noise_type,
        "missing_fields": missing_fields,
    }

    if noise_type == "missing_fields":
        removable = [
            "income",
            "loan_amount",
            "business_type",
            "gst_registered",
            "existing_loans",
            "credit_history",
            "monthly_expenses",
            "bank_balance",
            "employment_type",
        ]
        for field in rng.sample(removable, rng.randint(1, 3)):
            record.pop(field)
            missing_fields.append(field)

    return record


def main():
    rng = random.Random(RANDOM_SEED)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as output_file:
        for index in range(SAMPLE_COUNT):
            record = make_record(index, rng)
            output_file.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
