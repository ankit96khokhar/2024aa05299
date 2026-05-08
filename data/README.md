# Underwriting Dataset

Synthetic underwriting samples for multilingual loan-underwriting experiments.

## Files

- `underwriting_samples.jsonl`: 1000 JSONL records tracked by DVC.

## Schema

Each row includes underwriting signals such as:

- `sample_id`
- `language`
- `input_text`
- `income`
- `loan_amount`
- `business_type`
- `gst_registered`
- `existing_loans`
- `credit_history`
- `monthly_expenses`
- `bank_balance`
- `employment_type`
- `decision`
- `noise_type`
- `missing_fields`

Some records intentionally omit selected fields to simulate incomplete applications.
