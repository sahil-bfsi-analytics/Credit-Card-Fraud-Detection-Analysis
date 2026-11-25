/* ==========================================================================
   CREDIT CARD FRAUD DATA ANALYSIS  |  Database: CCFDA  |  Table: cc
   Flags: Card_Present_Flag = 1/0
          Alert_Flag, Confirmed_Fraud_Flag, High_Risk_Merchant_Flag = 'Yes'/'No'
   ========================================================================== */


/* ==========================================================================
   1. TRANSACTION ANALYSIS
   ========================================================================== */

-- 1.1 Total Transactions                                   (Expected: 9,970)
SELECT COUNT(*) AS Total_Transactions
FROM cc;

-- 1.2 Total / Average Amount                  (Expected: 53,947,967.52 / 5,411.03)
SELECT
    CAST(SUM(Transaction_Amount) AS DECIMAL(18,2)) AS Total_Transaction_Amount,
    CAST(AVG(Transaction_Amount) AS DECIMAL(18,2)) AS Avg_Transaction_Amount
FROM cc;

-- 1.3 Approved / Declined                              (Expected: 9,605 / 365)
SELECT
    Transaction_Status,
    COUNT(*) AS Total
FROM cc
GROUP BY Transaction_Status;

-- 1.4 Approval Rate                                         (Expected: 96.34)
SELECT
    CAST(COUNT(CASE WHEN Transaction_Status = 'Approved' THEN 1 END) * 100.0
         / COUNT(*) AS DECIMAL(10,2)) AS Approval_Rate
FROM cc;


/* ==========================================================================
   2. FRAUD ANALYSIS
   ========================================================================== */

-- 2.1 Confirmed Fraud Count                                   (Expected: 150)
SELECT COUNT(*) AS Confirmed_Fraud_Count
FROM cc
WHERE Confirmed_Fraud_Flag = 'Yes';

-- 2.2 Fraud Rate                                            (Expected: 1.50)
SELECT
    CAST(COUNT(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1 END) * 100.0
         / COUNT(*) AS DECIMAL(10,2)) AS Fraud_Rate
FROM cc;

-- 2.3 Fraud Amount / Avg Fraud Amount         (Expected: 1,246,545.21 / 8,310.30)
SELECT
    CAST(SUM(Transaction_Amount) AS DECIMAL(18,2)) AS Total_Fraud_Amount,
    CAST(AVG(Transaction_Amount) AS DECIMAL(18,2)) AS Avg_Fraud_Amount
FROM cc
WHERE Confirmed_Fraud_Flag = 'Yes';

-- 2.4 Fraud Loss = Approved fraud with Lost / No Chargeback

SELECT
    CAST(SUM(Transaction_Amount) AS DECIMAL(18,2)) AS Fraud_Loss
FROM cc
WHERE Confirmed_Fraud_Flag = 'Yes'
  AND Transaction_Status = 'Approved'
  AND Chargeback_Status IN ('Lost', 'Not Applicable');

-- 2.5a Fraud Rate by Transaction Channel          (Expected: ATM 1.71 | Online 2.49 | POS 0.73)
SELECT
    Transaction_Channel,
    COUNT(*) AS Total_Transactions,
    SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1 ELSE 0 END) AS Fraud_Transactions,
    CAST(SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1.0 ELSE 0 END) * 100.0
         / COUNT(*) AS DECIMAL(10,2)) AS Fraud_Rate_Percentage
FROM cc
GROUP BY Transaction_Channel
ORDER BY Fraud_Rate_Percentage DESC;

-- 2.5b Fraud Rate by Merchant Category    (Expected top: Gift Cards 10.81, Money Transfer 8.77, Gaming 6.14)
SELECT
    Merchant_Category,
    COUNT(*) AS Total_Transactions,
    SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1 ELSE 0 END) AS Fraud_Transactions,
    CAST(SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1.0 ELSE 0 END) * 100.0
         / COUNT(*) AS DECIMAL(10,2)) AS Fraud_Rate_Percentage
FROM cc
GROUP BY Merchant_Category
ORDER BY Fraud_Rate_Percentage DESC;

-- 2.5c Fraud Rate by Domestic vs International
SELECT
    Domestic_International_Flag,
    COUNT(*) AS Total_Transactions,
    SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1 ELSE 0 END) AS Fraud_Transactions,
    CAST(SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1.0 ELSE 0 END) * 100.0
         / COUNT(*) AS DECIMAL(10,2)) AS Fraud_Rate_Percentage
FROM cc
GROUP BY Domestic_International_Flag;

-- 2.6 Fraud by Amount Group
SELECT
    CASE
        WHEN Transaction_Amount < 1000  THEN '< 1K'
        WHEN Transaction_Amount < 10000 THEN '1K - 10K'
        WHEN Transaction_Amount < 50000 THEN '10K - 50K'
        ELSE '50K+'
    END AS Fraud_Amount_Group,
    COUNT(*) AS Fraud_Transactions,
    CAST(SUM(Transaction_Amount) AS DECIMAL(18,2)) AS Total_Fraud_Amount
FROM cc
WHERE Confirmed_Fraud_Flag = 'Yes'
GROUP BY
    CASE
        WHEN Transaction_Amount < 1000  THEN '< 1K'
        WHEN Transaction_Amount < 10000 THEN '1K - 10K'
        WHEN Transaction_Amount < 50000 THEN '10K - 50K'
        ELSE '50K+'
    END;

-- 2.7 Fraud by Time of Day
WITH FraudData AS
(
    SELECT
        CASE
            WHEN DATEPART(HOUR, Transaction_DateTime) < 6  THEN 'Night'
            WHEN DATEPART(HOUR, Transaction_DateTime) < 12 THEN 'Morning'
            WHEN DATEPART(HOUR, Transaction_DateTime) < 18 THEN 'Afternoon'
            ELSE 'Evening'
        END AS Time_Of_Day,
        Transaction_Amount
    FROM cc
    WHERE Confirmed_Fraud_Flag = 'Yes'
)
SELECT
    Time_Of_Day,
    COUNT(*) AS Fraud_Transactions,
    CAST(SUM(Transaction_Amount) AS DECIMAL(18,2)) AS Total_Fraud_Amount
FROM FraudData
GROUP BY Time_Of_Day
ORDER BY
    CASE Time_Of_Day
        WHEN 'Night'     THEN 1
        WHEN 'Morning'   THEN 2
        WHEN 'Afternoon' THEN 3
        WHEN 'Evening'   THEN 4
    END;

-- 2.8 Fraud by Customer Spending Behaviour (fraud transactions only)
--     (Expected: <1x 67 | 1x-2x 28 | 2x-5x 33 | 5x+ 22)
WITH SpendingData AS
(
    SELECT
        Transaction_ID,
        Transaction_Amount,
        Customer_Avg_Amount_30D,
        Transaction_Amount / NULLIF(Customer_Avg_Amount_30D, 0) AS Spending_Ratio
    FROM cc
    WHERE Confirmed_Fraud_Flag = 'Yes'
)
SELECT
    CASE
        WHEN Spending_Ratio < 1 THEN 'Below Avg (<1x)'
        WHEN Spending_Ratio < 2 THEN '1x - 2x'
        WHEN Spending_Ratio < 5 THEN '2x - 5x'
        ELSE '5x+'
    END AS Spending_Behaviour,
    COUNT(*) AS Fraud_Transactions,
    CAST(SUM(Transaction_Amount) AS DECIMAL(18,2)) AS Total_Fraud_Amount,
    CAST(AVG(Spending_Ratio) AS DECIMAL(10,2)) AS Avg_Spending_Ratio
FROM SpendingData
WHERE Spending_Ratio IS NOT NULL
GROUP BY
    CASE
        WHEN Spending_Ratio < 1 THEN 'Below Avg (<1x)'
        WHEN Spending_Ratio < 2 THEN '1x - 2x'
        WHEN Spending_Ratio < 5 THEN '2x - 5x'
        ELSE '5x+'
    END;


/* ==========================================================================
   3. FRAUD MONITORING ANALYSIS
   ========================================================================== */

-- 3.1 Total Alerts                                            (Expected: 445)
SELECT COUNT(*) AS Total_Alerts
FROM cc
WHERE Alert_Flag = 'Yes';

-- 3.2 Confirmed Fraud Alerts                                   (Expected: 72)
SELECT COUNT(*) AS Confirmed_Fraud_Alerts
FROM cc
WHERE Alert_Flag = 'Yes' AND Confirmed_Fraud_Flag = 'Yes';

-- 3.3 False Positive Count                                    (Expected: 373)
SELECT COUNT(*) AS False_Positive_Count
FROM cc
WHERE Alert_Flag = 'Yes' AND Confirmed_Fraud_Flag = 'No';

-- 3.4 False Positive Rate = FP / all legitimate txns       (Expected: 3.80)
SELECT
    CAST(SUM(CASE WHEN Alert_Flag = 'Yes' AND Confirmed_Fraud_Flag = 'No' THEN 1 ELSE 0 END) * 100.0
         / NULLIF(SUM(CASE WHEN Confirmed_Fraud_Flag = 'No' THEN 1 ELSE 0 END), 0)
         AS DECIMAL(10,2)) AS False_Positive_Rate
FROM cc;
-- 3.5 Alert-to-Fraud Conversion Rate                        (Expected: 16.18)
SELECT
    CAST(SUM(CASE WHEN Alert_Flag = 'Yes' AND Confirmed_Fraud_Flag = 'Yes' THEN 1 ELSE 0 END) * 100.0
         / NULLIF(SUM(CASE WHEN Alert_Flag = 'Yes' THEN 1 ELSE 0 END), 0)
         AS DECIMAL(10,2)) AS Alert_To_Fraud_Conversion_Rate
FROM cc;

-- 3.6 Fraud Detection Rate                                  (Expected: 48.00)
SELECT
    CAST(SUM(CASE WHEN Alert_Flag = 'Yes' AND Confirmed_Fraud_Flag = 'Yes' THEN 1 ELSE 0 END) * 100.0
         / NULLIF(SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1 ELSE 0 END), 0)
         AS DECIMAL(10,2)) AS Fraud_Detection_Rate
FROM cc;


/* ==========================================================================
   4. CHARGEBACK ANALYSIS
   ========================================================================== */

-- 4.1 Total Chargebacks Filed                                 (Expected: 106)
SELECT COUNT(*) AS Total_Chargebacks_Filed
FROM cc
WHERE Chargeback_Status <> 'Not Applicable';

-- 4.2 Chargeback Amount                                (Expected: 510,116.06)
SELECT CAST(SUM(Transaction_Amount) AS DECIMAL(18,2)) AS Chargeback_Amount
FROM cc
WHERE Chargeback_Status <> 'Not Applicable';

-- 4.3 Chargeback Success Rate = Won / (Won + Lost)          (Expected: 40.85)
SELECT
    CAST(SUM(CASE WHEN Chargeback_Status = 'Won' THEN 1 ELSE 0 END) * 100.0
         / NULLIF(SUM(CASE WHEN Chargeback_Status IN ('Won','Lost') THEN 1 ELSE 0 END), 0)
         AS DECIMAL(10,2)) AS Chargeback_Success_Rate
FROM cc;

-- 4.4 Chargeback Status Analysis    (Expected: Lost 42, Won 29, Pending 21, Filed 14)
SELECT
    Chargeback_Status,
    COUNT(*) AS Total_Chargebacks,
    CAST(SUM(Transaction_Amount) AS DECIMAL(18,2)) AS Total_Amount
FROM cc
WHERE Chargeback_Status <> 'Not Applicable'
GROUP BY Chargeback_Status
ORDER BY Total_Chargebacks DESC;


/* ==========================================================================
   5. CUSTOMER BEHAVIOUR ANALYSIS
   ========================================================================== */

-- 5.1 Customers with Multiple Suspicious Transactions (2+ alerts)
--     (Expected: 101 customers; 42 of them with 3+ alerts)
SELECT
    Customer_ID,
    COUNT(*) AS Suspicious_Transactions,
    SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1 ELSE 0 END) AS Confirmed_Fraud,
    CAST(SUM(Transaction_Amount) AS DECIMAL(18,2)) AS Suspicious_Amount
FROM cc
WHERE Alert_Flag = 'Yes'
GROUP BY Customer_ID
HAVING COUNT(*) >= 2
ORDER BY Suspicious_Transactions DESC, Suspicious_Amount DESC;

-- 5.2 Unusual Transaction Frequency (1H >= 3 or 24H >= 5)
SELECT
    Transaction_ID, Customer_ID, Transaction_DateTime, Transaction_Amount,
    Transaction_Count_1H, Transaction_Count_24H, Confirmed_Fraud_Flag
FROM cc
WHERE Transaction_Count_1H >= 3 OR Transaction_Count_24H >= 5
ORDER BY Transaction_Count_1H DESC, Transaction_Count_24H DESC;

-- 5.3 Frequency vs Fraud Rate
SELECT
    Transaction_Count_1H,
    COUNT(*) AS Total_Transactions,
    SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1 ELSE 0 END) AS Fraud_Transactions,
    CAST(SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1.0 ELSE 0 END) * 100.0
         / COUNT(*) AS DECIMAL(10,2)) AS Fraud_Rate
FROM cc
GROUP BY Transaction_Count_1H
ORDER BY Transaction_Count_1H;

-- 5.4 High-Value Transaction Analysis (50K+ or more than 5x the customer's 30-day average)
SELECT
    CASE
        WHEN Transaction_Amount >= 50000 THEN '50K+'
        WHEN Transaction_Amount > 5 * Customer_Avg_Amount_30D THEN '5x Above Customer Avg'
        ELSE 'Normal'
    END AS High_Value_Group,
    COUNT(*) AS Total_Transactions,
    SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1 ELSE 0 END) AS Fraud_Transactions,
    CAST(SUM(Transaction_Amount) AS DECIMAL(18,2)) AS Total_Amount
FROM cc
GROUP BY
    CASE
        WHEN Transaction_Amount >= 50000 THEN '50K+'
        WHEN Transaction_Amount > 5 * Customer_Avg_Amount_30D THEN '5x Above Customer Avg'
        ELSE 'Normal'
    END;

-- 5.5 Geographic Behaviour: IP Country vs Billing Country
--     (Online rows only, because POS/ATM transactions have no IP)   (Expected: Mismatch 150 / fraud 71 | Match 3,779 / fraud 27)
SELECT
    CASE WHEN IP_Country <> Billing_Country THEN 'IP Country Mismatch'
         ELSE 'IP Country Match' END AS IP_Check,
    COUNT(*) AS Total_Transactions,
    SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1 ELSE 0 END) AS Fraud_Transactions,
    CAST(SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1.0 ELSE 0 END) * 100.0
         / COUNT(*) AS DECIMAL(10,2)) AS Fraud_Rate
FROM cc
WHERE Transaction_Channel = 'Online'
GROUP BY CASE WHEN IP_Country <> Billing_Country THEN 'IP Country Mismatch'
              ELSE 'IP Country Match' END;

-- 5.6 Geographic Behaviour: Fraud by Merchant Country
SELECT
    Merchant_Country,
    COUNT(*) AS Total_Transactions,
    SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1 ELSE 0 END) AS Fraud_Transactions
FROM cc
GROUP BY Merchant_Country
ORDER BY Fraud_Transactions DESC;

-- 5.7 Customer Spending Behaviour vs Fraud Rate (all transactions)
WITH Spending AS
(
    SELECT *,
           Transaction_Amount / NULLIF(Customer_Avg_Amount_30D, 0) AS Spending_Ratio
    FROM cc
)
SELECT
    CASE
        WHEN Spending_Ratio < 1 THEN 'Below Avg (<1x)'
        WHEN Spending_Ratio < 2 THEN '1x - 2x'
        WHEN Spending_Ratio < 5 THEN '2x - 5x'
        ELSE '5x+'
    END AS Spending_Behaviour,
    COUNT(*) AS Total_Transactions,
    SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1 ELSE 0 END) AS Fraud_Transactions,
    CAST(SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1.0 ELSE 0 END) * 100.0
         / COUNT(*) AS DECIMAL(10,2)) AS Fraud_Rate
FROM Spending
WHERE Spending_Ratio IS NOT NULL
GROUP BY
    CASE
        WHEN Spending_Ratio < 1 THEN 'Below Avg (<1x)'
        WHEN Spending_Ratio < 2 THEN '1x - 2x'
        WHEN Spending_Ratio < 5 THEN '2x - 5x'
        ELSE '5x+'
    END;


/* ==========================================================================
   6. CREDIT CARD FRAUD PATTERNS
   ========================================================================== */

-- 6.1 Transaction Behaviour: Card Entry Mode wise
SELECT
    Card_Entry_Mode,
    COUNT(*) AS Total_Transactions,
    SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1 ELSE 0 END) AS Fraud_Transactions,
    CAST(SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1.0 ELSE 0 END) * 100.0
         / COUNT(*) AS DECIMAL(10,2)) AS Fraud_Rate
FROM cc
GROUP BY Card_Entry_Mode
ORDER BY Fraud_Rate DESC;

-- 6.2 Fraudulent Transaction Amounts (summary)
SELECT
    COUNT(*) AS Fraud_Transactions,
    CAST(SUM(Transaction_Amount) AS DECIMAL(18,2)) AS Total_Fraud_Amount,
    CAST(AVG(Transaction_Amount) AS DECIMAL(18,2)) AS Avg_Fraud_Amount,
    MIN(Transaction_Amount) AS Min_Fraud_Amount,
    MAX(Transaction_Amount) AS Max_Fraud_Amount
FROM cc
WHERE Confirmed_Fraud_Flag = 'Yes';

-- 6.3 Suspicious Transaction Activity (combined risk signals)
SELECT
    CASE
        WHEN Alert_Flag = 'Yes' AND High_Risk_Merchant_Flag = 'Yes' THEN 'Alert + High Risk Merchant'
        WHEN Alert_Flag = 'Yes'                                     THEN 'Alert Only'
        WHEN High_Risk_Merchant_Flag = 'Yes'                        THEN 'High Risk Merchant Only'
        ELSE 'No Risk Signal'
    END AS Risk_Signal,
    COUNT(*) AS Total_Transactions,
    SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1 ELSE 0 END) AS Fraud_Transactions,
    CAST(SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1.0 ELSE 0 END) * 100.0
         / COUNT(*) AS DECIMAL(10,2)) AS Fraud_Rate
FROM cc
GROUP BY
    CASE
        WHEN Alert_Flag = 'Yes' AND High_Risk_Merchant_Flag = 'Yes' THEN 'Alert + High Risk Merchant'
        WHEN Alert_Flag = 'Yes'                                     THEN 'Alert Only'
        WHEN High_Risk_Merchant_Flag = 'Yes'                        THEN 'High Risk Merchant Only'
        ELSE 'No Risk Signal'
    END;

-- 6.4 Merchant Risk: High Risk Merchant Flag vs Fraud   (Expected: 532 txns, 46 fraud)
SELECT
    High_Risk_Merchant_Flag,
    COUNT(*) AS Total_Transactions,
    SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1 ELSE 0 END) AS Fraud_Transactions,
    CAST(SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1.0 ELSE 0 END) * 100.0
         / COUNT(*) AS DECIMAL(10,2)) AS Fraud_Rate
FROM cc
GROUP BY High_Risk_Merchant_Flag;

-- 6.5 Merchant Risk: Top 10 Merchant Categories by Fraud Rate
SELECT TOP 10
    Merchant_Category,
    COUNT(*) AS Total_Transactions,
    SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1 ELSE 0 END) AS Fraud_Transactions,
    CAST(SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1.0 ELSE 0 END) * 100.0
         / COUNT(*) AS DECIMAL(10,2)) AS Fraud_Rate
FROM cc
GROUP BY Merchant_Category
ORDER BY Fraud_Rate DESC;

-- 6.6 Domestic vs International                    (Expected: International 348, fraud 69)
SELECT
    Domestic_International_Flag,
    COUNT(*) AS Total_Transactions,
    SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1 ELSE 0 END) AS Fraud_Transactions,
    CAST(SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1.0 ELSE 0 END) * 100.0
         / COUNT(*) AS DECIMAL(10,2)) AS Fraud_Rate,
    CAST(SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN Transaction_Amount ELSE 0 END)
         AS DECIMAL(18,2)) AS Fraud_Amount
FROM cc
GROUP BY Domestic_International_Flag;

-- 6.7 Transaction Channel Risk
SELECT
    Transaction_Channel,
    COUNT(*) AS Total_Transactions,
    SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1 ELSE 0 END) AS Fraud_Transactions,
    CAST(SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN 1.0 ELSE 0 END) * 100.0
         / COUNT(*) AS DECIMAL(10,2)) AS Fraud_Rate,
    CAST(SUM(CASE WHEN Confirmed_Fraud_Flag = 'Yes' THEN Transaction_Amount ELSE 0 END)
         AS DECIMAL(18,2)) AS Fraud_Amount
FROM cc
GROUP BY Transaction_Channel
ORDER BY Fraud_Rate DESC;

-- 6.8 Fraud Alerts: Monthly Trend
SELECT
    FORMAT(Transaction_DateTime, 'yyyy-MM') AS Txn_Month,
    SUM(CASE WHEN Alert_Flag = 'Yes' THEN 1 ELSE 0 END) AS Total_Alerts,
    SUM(CASE WHEN Alert_Flag = 'Yes' AND Confirmed_Fraud_Flag = 'Yes' THEN 1 ELSE 0 END) AS Confirmed_Fraud_Alerts,
    SUM(CASE WHEN Alert_Flag = 'Yes' AND Confirmed_Fraud_Flag = 'No'  THEN 1 ELSE 0 END) AS False_Positives
FROM cc
GROUP BY FORMAT(Transaction_DateTime, 'yyyy-MM')
ORDER BY Txn_Month;

-- 6.9 False Positives by Channel
--     (Expected FP: ATM 23, Online 178, POS 172)
SELECT
    Transaction_Channel,
    SUM(CASE WHEN Alert_Flag = 'Yes' THEN 1 ELSE 0 END) AS Total_Alerts,
    SUM(CASE WHEN Alert_Flag = 'Yes' AND Confirmed_Fraud_Flag = 'No' THEN 1 ELSE 0 END) AS False_Positives,
    -- FP / all legitimate transactions in that channel (same definition as 3.4)
    CAST(SUM(CASE WHEN Alert_Flag = 'Yes' AND Confirmed_Fraud_Flag = 'No' THEN 1.0 ELSE 0 END) * 100.0
         / NULLIF(SUM(CASE WHEN Confirmed_Fraud_Flag = 'No' THEN 1 ELSE 0 END), 0)
         AS DECIMAL(10,2)) AS False_Positive_Rate,
    -- FP / total alerts in that channel
    CAST(SUM(CASE WHEN Alert_Flag = 'Yes' AND Confirmed_Fraud_Flag = 'No' THEN 1.0 ELSE 0 END) * 100.0
         / NULLIF(SUM(CASE WHEN Alert_Flag = 'Yes' THEN 1 ELSE 0 END), 0)
         AS DECIMAL(10,2)) AS False_Positive_Share_Of_Alerts
FROM cc
GROUP BY Transaction_Channel;

-- 6.10 Chargebacks vs Fraud
SELECT
    Confirmed_Fraud_Flag,
    Chargeback_Status,
    COUNT(*) AS Total_Transactions,
    CAST(SUM(Transaction_Amount) AS DECIMAL(18,2)) AS Total_Amount
FROM cc
WHERE Chargeback_Status <> 'Not Applicable'
GROUP BY Confirmed_Fraud_Flag, Chargeback_Status
ORDER BY Confirmed_Fraud_Flag, Chargeback_Status;

-- 6.11 Fraud Investigation Outcomes
--      (Expected: Not Investigated 9441, Legitimate 355, Confirmed Fraud 150, Under Investigation 24)
SELECT
    Investigation_Outcome,
    COUNT(*) AS Total_Transactions,
    CAST(SUM(Transaction_Amount) AS DECIMAL(18,2)) AS Total_Amount,
    CAST(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () AS DECIMAL(10,2)) AS Pct_Of_Total
FROM cc
GROUP BY Investigation_Outcome
ORDER BY Total_Transactions DESC;


/* ==========================================================================
   7. FINANCIAL LOSS PREVENTION
   ========================================================================== */

-- 7.1 Where did the fraud money go (Recovery Status)
SELECT
    CASE
        WHEN Transaction_Status = 'Declined'          THEN '0. Prevented (Declined)'
        WHEN Chargeback_Status = 'Won'                THEN '1. Recovered (Chargeback Won)'
        WHEN Chargeback_Status IN ('Filed','Pending') THEN '2. Recovery In Progress'
        WHEN Chargeback_Status = 'Lost'               THEN '3. Lost (Chargeback Lost)'
        ELSE '4. Lost (No Chargeback Filed)'
    END AS Recovery_Status,
    COUNT(*) AS Fraud_Transactions,
    CAST(SUM(Transaction_Amount) AS DECIMAL(18,2)) AS Fraud_Amount
FROM cc
WHERE Confirmed_Fraud_Flag = 'Yes'
GROUP BY
    CASE
        WHEN Transaction_Status = 'Declined'          THEN '0. Prevented (Declined)'
        WHEN Chargeback_Status = 'Won'                THEN '1. Recovered (Chargeback Won)'
        WHEN Chargeback_Status IN ('Filed','Pending') THEN '2. Recovery In Progress'
        WHEN Chargeback_Status = 'Lost'               THEN '3. Lost (Chargeback Lost)'
        ELSE '4. Lost (No Chargeback Filed)'
    END
ORDER BY Recovery_Status;
-- 7.2 Missed Fraud (fraud occurred but no alert was raised)             (Expected: 78)
SELECT
    COUNT(*) AS Missed_Fraud_Transactions,
    CAST(SUM(Transaction_Amount) AS DECIMAL(18,2)) AS Missed_Fraud_Amount
FROM cc
WHERE Confirmed_Fraud_Flag = 'Yes' AND Alert_Flag = 'No';