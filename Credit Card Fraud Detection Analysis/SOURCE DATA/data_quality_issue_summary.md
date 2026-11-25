# Data Quality Issue Summary

All issues were injected programmatically into `credit_card_transactions_synthetic.csv`. The untouched generated data is preserved in `credit_card_transactions_clean_reference.csv` (answer key - open it only after you finish your own cleaning). Every injected issue is listed row-by-row in `data_quality_issue_log.csv`.

- Rows in main CSV: **10,000** (includes 30 duplicate rows, so 9,970 unique transactions)
- Rows affected by at least one injected issue: **320** (3.2% of rows; each issue was placed on a different row)
- `Transaction_ID` and `Confirmed_Fraud_Flag` were deliberately left untouched, and no confirmed-fraud row was corrupted.

| Issue type | Records affected | Column(s) |
|---|---:|---|
| Date Format Inconsistency (2-digit year) | 4 | Transaction_DateTime |
| Date Format Inconsistency (DD/MM/YYYY) | 10 | Transaction_DateTime |
| Date Format Inconsistency (time missing) | 6 | Transaction_DateTime |
| Duplicate Record | 30 | (entire row) |
| Impossible Date | 4 | Transaction_DateTime |
| Inconsistent Channel Spelling/Case | 35 | Transaction_Channel |
| Inconsistent Country Name | 30 | Billing_Country, IP_Country, Merchant_Country |
| Inconsistent Status Label | 17 | Transaction_Status |
| Incorrect Card_Present_Flag | 15 | Card_Present_Flag |
| Incorrect Data Type | 35 | Distance_From_Previous_Transaction_KM, Transaction_Amount, Transaction_Count_24H |
| Invalid Amount (Negative) | 8 | Transaction_Amount |
| Invalid Amount (Non-numeric) | 5 | Transaction_Amount |
| Invalid Amount (Outlier > 200,000) | 6 | Transaction_Amount |
| Invalid Amount (Zero) | 6 | Transaction_Amount |
| Missing Value | 101 | Customer_Avg_Amount_30D, Device_ID, IP_Country, Merchant_City, Merchant_ID, Terminal_ID, Transaction_DateTime |
| Status Conflicts With Response Code | 8 | Transaction_Status |

## Notes on blanks that are NOT errors

- `Terminal_ID` is blank by design for Online transactions; `Device_ID` and `IP_Country` are blank by design for POS/ATM transactions.
- Injected missing values are the blanks that appear where the channel says a value should exist (e.g. an Online row with no `Device_ID`, or a POS row with no `Terminal_ID`).

## Other things to check (not counted above)

- `Authorization_Response_Code` is stored as text (e.g. `00`, `05`); Excel may drop the leading zero on open.
- `Customer_Avg_Amount_30D`, `Transaction_Count_*`, `Time_Since_Last_Transaction_Min` and `Distance_...` are computed from the generated history; see the methodology file for how first-in-dataset transactions were handled.