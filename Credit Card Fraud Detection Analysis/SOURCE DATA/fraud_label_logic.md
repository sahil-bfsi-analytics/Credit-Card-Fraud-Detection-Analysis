# Synthetic Fraud-Label Generation Logic

## Three classes kept distinct
- **Legitimate:** `Confirmed_Fraud_Flag = No`, no alert.
- **Suspicious (not confirmed):** `Alert_Flag = Yes` and `Confirmed_Fraud_Flag = No` (outcome Legitimate Transaction, Under Investigation or Not Investigated).
- **Confirmed fraud:** `Confirmed_Fraud_Flag = Yes`; `Investigation_Outcome = Confirmed Fraud`. This includes fraud attempts the bank declined.

## How fraud cases were created
Exactly 150 confirmed-fraud transactions were generated from seven scenarios, never at random:

| Scenario | Rows | Typical pattern |
|---|---:|---|
| Card testing burst | 32 | 3-5 small online attempts within minutes, often high-risk merchants, new device, foreign IP |
| International card-not-present | 28 | Foreign merchant and IP, amount several times the customer's normal, often at night |
| Account takeover (online) | 22 | New device, domestic merchants, 1-3 purchases, amounts above normal (some near normal) |
| Lost/stolen card POS spree | 22 | 2-4 quick POS purchases, often in a distant city after a recent normal transaction |
| ATM cash-out | 14 | Large withdrawals at night, in a distant city or abroad |
| Low-value online fraud | 16 | Small amounts, sometimes on the customer's usual device, mostly looks normal |
| Skimmed POS in home area | 16 | Normal-looking amounts, swipe entry, home city |

Not every fraud looks obvious: some use the customer's own device or a domestic IP, and low-value fraud is included.

## Alerts (not the same as fraud)
Each transaction gets a risk score from observable signals: amount vs the customer's 30-day average, short-term transaction counts, international merchant, foreign IP, new device, high-risk merchant, fast long-distance movement, night time and ATM abroad, plus random noise. 
Fraud also gets a small bump for signals not present as columns. An alert is then drawn from that score, so:
- some fraud is **not** alerted (found later via customer dispute);
- many legitimate transactions **are** alerted (travel, large purchases, new devices, bursts).

## After the alert
- **Status:** fraud is declined more often when alerted, but some fraud is declined without an alert (e.g. limit or insufficient funds). Some alerted legitimate transactions are declined (code 59 etc.).
- **Investigation:** confirmed fraud is always `Confirmed Fraud`. Alerted legitimate transactions are mostly cleared; recent ones are more likely still `Under Investigation`. Un-alerted legitimate rows are `Not Investigated`, except a few customer disputes.
- **Chargebacks:** only approved transactions can have one. Not all fraud is charged back (ATM cash fraud and a share of card fraud are `Not Applicable`). Status depends on age (recent = Filed/Pending; older = mostly Won/Lost). Online-authenticated fraud is less likely to be won. A small number of legitimate disputes exist and are mostly lost.
- **Declined transactions** never carry a chargeback.

These are synthetic proportions, not real bank rates.
