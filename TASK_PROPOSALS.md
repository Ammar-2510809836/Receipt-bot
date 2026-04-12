# Task Proposals from Codebase Review

## 1) Typo fix task
**Task:** Fix the model naming typo/inconsistency in `README.md` by replacing "Llama 3.2 Vision" with the actually configured model family (`llama-4-scout-17b-16e-instruct`).

**Why:** The intro says the bot uses "Llama 3.2 Vision", while the feature list and runtime configuration indicate Llama 4 Scout. This creates confusion for setup, expectations, and troubleshooting.

**Evidence:**
- `README.md` intro mentions "Llama 3.2 Vision".
- `README.md` feature section mentions `meta-llama/llama-4-scout-17b-16e-instruct`.
- `ai_engine.py` payload uses `meta-llama/llama-4-scout-17b-16e-instruct`.

**Acceptance criteria:**
- README consistently references the same model/version as code.
- No contradictory model names remain in docs.

---

## 2) Bug fix task
**Task:** Ensure invalid extracted dates are normalized before writing rows to Sheets in `add_transaction_to_sheet`.

**Why:** If `data['date']` is invalid (e.g., `31/12/2025`), code falls back to `datetime.now()` for worksheet routing, but still writes the original invalid `date_str` into the row. This causes sheet data quality issues and inconsistent date formatting.

**Evidence:**
- `google_services.py` falls back to `date_obj = datetime.now()` on parse failure.
- Later, row construction still uses `date_str` unchanged.

**Acceptance criteria:**
- On invalid input dates, row date value is rewritten to fallback ISO format (`YYYY-MM-DD`).
- Add unit test coverage for invalid date input path.

---

## 3) Code comment/documentation discrepancy task
**Task:** Align the Google credentials naming/documentation with actual OAuth usage (rename or clearly document `GOOGLE_SERVICE_ACCOUNT_JSON`).

**Why:** The variable name implies a Service Account file, but the flow in `google_services.py` uses OAuth client secrets (`InstalledAppFlow`). This discrepancy can mislead users and cause configuration errors.

**Evidence:**
- `config.py` expects `GOOGLE_SERVICE_ACCOUNT_JSON`.
- `google_services.py` uses OAuth InstalledAppFlow and comments about `credentials.json` fallback.
- `SETUP_GUIDE.md` notes this mismatch explicitly as a compatibility workaround.

**Acceptance criteria:**
- Naming and docs clearly describe OAuth client JSON, not service account credentials.
- README and setup docs match runtime behavior.

---

## 4) Test improvement task
**Task:** Add tests for monthly spend parsing edge cases in `get_monthly_spend`.

**Why:** Total parsing currently handles locale formats but can silently mis-handle values and row shapes; there is no test safety net.

**High-value cases to test:**
- Values with comma decimal (`"12,50"`).
- Values with thousands separators (`"1,234.56"`, `"1 234,56"`).
- Empty/malformed rows and missing columns.
- Worksheet-not-found path returning `0.0`.

**Acceptance criteria:**
- New automated tests validate numeric normalization and resilience to malformed rows.
- Tests run in CI/local without requiring live Google API calls (mock gspread client/workbook).
