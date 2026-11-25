# Dataset Generation Methodology

**All data is synthetic.** It does not come from, and does not represent, any real bank, customer or card. No real card numbers, CVV, PIN or OTP are used.

## How it was built
1. **Reproducible script.** `generate_cc_fraud_dataset.py` (fixed random seed) generates everything, so IDs, dates and fraud logic are consistent.
2. **Customers (650).** Each has a home city, a spending tier (low / mid / high), 1-2 accounts, 1-3 card tokens, 1-2 usual devices and an online-usage preference. Activity is skewed, so some customers have many transactions and others only a few. Some customers take domestic trips and a few take international trips, which creates *legitimate* international and distant-location spending.
3. **Merchants (~1,800).** Created on demand by country, city and category, then reused. High-risk status is a property of the merchant (more likely for Gaming, Gift Cards, Money Transfer; occasionally for Jewellery, Electronics, E-commerce).
4. **Legitimate transactions (9,820).** Channel, category, amount (scaled to the customer's tier), time of day, device, IP and entry mode follow realistic patterns. About 17% of transactions are short follow-up purchases, which gives natural bursts. A small share are legitimate high-value purchases, foreign online purchases and VPN-style IPs.
5. **Fraud transactions (150).** Generated from seven scenarios (see `fraud_label_logic.md`) and attached to existing customers' cards.
6. **Behaviour columns.** `Customer_Avg_Amount_30D`, `Transaction_Count_1H/24H`, `Time_Since_Last_Transaction_Min` and `Distance_From_Previous_Transaction_KM` are computed from each customer's earlier transactions only (no future data). Counts and averages include declined attempts. For a customer's first transaction in the dataset (or when there is nothing in the 30-day window) a simulated pre-period baseline is used.
7. **Alerts, status, chargebacks, investigation.** Assigned after the behaviour columns, using risk signals plus randomness (see the fraud logic file).
8. **Data-quality issues.** Injected last into a copy; the untouched data is kept separately.

## Key design decisions
- **10,000 rows = 9,970 unique + 30 duplicates.** You asked for exactly 10,000 rows *and* some duplicate records. The main CSV has exactly 10,000 rows; after removing the 30 exact duplicates you have 9,970 unique transactions, of which 150 are confirmed fraud (about 1.5%).
- **Currency.** All amounts are in INR. Foreign spend is already converted.
- **Date range.** 01-May-2026 to 31-Oct-2026 (all valid timestamps fall inside it).
- **Billing country.** India for all customers, so Domestic/International depends on `Merchant_Country`.
- **Alert time.** With exactly 31 columns there is no alert-time column. `Alert_Flag` represents a real-time flag at authorization, so alert time equals `Transaction_DateTime`. Investigation outcome and chargeback status are post-transaction results, aged against a snapshot date of 10-Nov-2026.
- **Structural blanks.** `Terminal_ID` is blank for Online; `Device_ID` and `IP_Country` are blank for POS/ATM. These are by design, not errors.

## Metric definitions (for your own calculations)
The dataset has no recovery or loss columns, so derive them from existing fields. Suggested synthetic assumptions:
- **Fraudulent transaction amount / gross fraud exposure:** amount of all confirmed-fraud rows, including declined attempts.
- **Approved fraud amount:** confirmed fraud with `Transaction_Status = Approved` (the money that actually left the customer's account).
- **Recovered chargeback amount:** approved fraud with `Chargeback_Status = Won`.
- **Actual fraud loss (assumption):** approved fraud amount minus recovered chargeback amount. Rows that are Filed, Pending, Lost or Not Applicable are treated as unrecovered at the snapshot date.
- **Chargeback success rate:** Won / (Won + Lost).
- **False positive:** `Alert_Flag = Yes` and `Confirmed_Fraud_Flag = No`.

No KPI has been calculated for you.
