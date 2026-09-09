# Data Dictionary — SYNTHETIC PROTOTYPE DATA

> **⚠ DISCLAIMER:** All data described in this document is **SYNTHETIC PROTOTYPE DATA**.
> It does NOT contain real citizen data, real bank account data, or data from any government portal.
> The synthetic data layer is designed to be replaceable by an authorized real API in production.

---

## 1. `complaints.csv`

Records of cybercrime complaints filed by victims.

| Column | Data Type | Description | Example | Links To |
|---|---|---|---|---|
| `complaint_id` | `string` (PK) | Unique complaint identifier | `CC1001` | `transactions.complaint_id` |
| `complaint_date` | `date` (YYYY-MM-DD) | Date the complaint was filed | `2026-07-15` | — |
| `fraud_type` | `string` | Category of fraud committed | `UPI Fraud` | `historical_cases.fraud_type` |
| `fraud_amount` | `float` | Total reported fraud amount (INR) | `487500.00` | — |
| `complaint_time` | `time` (HH:MM:SS) | Time the complaint was registered | `14:32:00` | — |
| `victim_city` | `string` | City where the victim is located | `Mumbai` | `accounts.city`, `withdrawal_locations.city` |
| `victim_latitude` | `float` | Latitude of victim's approximate location | `19.0760` | — |
| `victim_longitude` | `float` | Longitude of victim's approximate location | `72.8777` | — |
| `crime_category` | `string` | Broader crime classification | `Online Financial Fraud` | — |
| `source_channel` | `string` | How the complaint was received | `Helpline 1930` | — |
| `status` | `string` | Current investigation status | `Under Investigation` | — |

---

## 2. `transactions.csv`

Financial transactions linked to cybercrime complaints.

| Column | Data Type | Description | Example | Links To |
|---|---|---|---|---|
| `transaction_id` | `string` (PK) | Unique transaction identifier | `TXN90001` | — |
| `complaint_id` | `string` (FK) | Complaint this transaction belongs to | `CC1001` | `complaints.complaint_id` |
| `sender_account` | `string` (FK) | Account that sent the funds | `ACC100001` | `accounts.account_id` |
| `receiver_account` | `string` (FK) | Account that received the funds | `ACC100002` | `accounts.account_id` |
| `amount` | `float` | Transaction amount (INR) | `150000.00` | — |
| `transaction_time` | `datetime` (YYYY-MM-DD HH:MM:SS) | When the transaction occurred | `2026-07-14 22:15:00` | — |
| `transaction_type` | `string` | Transfer method used | `UPI` | — |
| `transaction_status` | `string` | Outcome of the transaction | `Completed` | — |

**Valid `transaction_type` values:** UPI, NEFT, RTGS, IMPS, ATM Withdrawal, Card Payment

**Valid `transaction_status` values:** Completed, Pending, Failed, Reversed

---

## 3. `accounts.csv`

Synthetic bank/wallet accounts involved in fraud cases.

| Column | Data Type | Description | Example | Links To |
|---|---|---|---|---|
| `account_id` | `string` (PK) | Unique account identifier | `ACC100001` | `transactions.sender_account`, `transactions.receiver_account`, `account_relationships.source_account`, `account_relationships.target_account` |
| `account_type` | `string` | Type of financial account | `Savings` | — |
| `city` | `string` | City where the account is registered | `Mumbai` | `complaints.victim_city`, `withdrawal_locations.city` |
| `latitude` | `float` | Latitude of account holder's location | `19.0821` | — |
| `longitude` | `float` | Longitude of account holder's location | `72.8810` | — |
| `account_risk_score` | `float` (0.0–1.0) | Computed risk score for the account | `0.78` | `historical_cases.account_risk` |
| `previous_case_count` | `integer` | Number of past fraud cases involving this account | `3` | — |
| `account_status` | `string` | Current operational status | `Under Monitoring` | — |

**Valid `account_type` values:** Savings, Current, Jan Dhan, Wallet, Business

**Valid `account_status` values:** Active, Frozen, Suspended, Under Monitoring, Closed

---

## 4. `account_relationships.csv`

Relationships and linkages between accounts (derived from transaction patterns and investigator annotations).

| Column | Data Type | Description | Example | Links To |
|---|---|---|---|---|
| `relationship_id` | `string` (PK) | Unique relationship identifier | `REL9001` | — |
| `source_account` | `string` (FK) | Originating account in the relationship | `ACC100001` | `accounts.account_id` |
| `target_account` | `string` (FK) | Destination account in the relationship | `ACC100002` | `accounts.account_id` |
| `relationship_type` | `string` | Nature of the relationship | `Mule Chain` | — |
| `transaction_count` | `integer` | Number of transactions between the pair | `2` | — |
| `total_amount` | `float` | Sum of all transactions between the pair (INR) | `247500.00` | — |

**Valid `relationship_type` values:** Frequent Transactor, Mule Chain, Beneficiary, Co-holder, Shared Device, Common IP

---

## 5. `withdrawal_locations.csv`

Candidate cash-withdrawal locations (ATMs, branches, clusters).

| Column | Data Type | Description | Example | Links To |
|---|---|---|---|---|
| `location_id` | `string` (PK) | Unique location identifier | `LOC2001` | `historical_cases.withdrawal_zone` |
| `location_name` | `string` | Human-readable location label | `Mumbai ATM Cluster 1` | — |
| `city` | `string` | City of the location | `Mumbai` | `complaints.victim_city`, `accounts.city` |
| `latitude` | `float` | Latitude of the location | `19.0820` | — |
| `longitude` | `float` | Longitude of the location | `72.8855` | — |
| `location_type` | `string` | Category of the location | `ATM Cluster` | — |
| `atm_count` | `integer` | Number of ATMs at this location | `8` | `historical_cases.atm_density` |
| `area_risk_baseline` | `float` (0.0–1.0) | Baseline crime risk of the area | `0.65` | — |

**Valid `location_type` values:** ATM Cluster, Bank Branch, Business District, Market Area, Residential Hub

---

## 6. `historical_cases.csv`

Historical fraud case feature vectors for ML training. Each row is a past case with observed features and factual outcome.

| Column | Data Type | Description | Example | Links To |
|---|---|---|---|---|
| `historical_case_id` | `string` (PK) | Unique historical case identifier | `HC3001` | — |
| `fraud_type` | `string` | Type of fraud in this case | `UPI Fraud` | `complaints.fraud_type` |
| `fraud_amount` | `float` | Reported fraud amount (INR) | `250000.00` | — |
| `transaction_hour` | `integer` (0–23) | Hour of key transaction | `22` | — |
| `city` | `string` | City where the case occurred | `Mumbai` | `complaints.victim_city`, `accounts.city` |
| `account_risk` | `float` (0.0–1.0) | Risk score of the primary account | `0.85` | `accounts.account_risk_score` |
| `transaction_velocity` | `integer` | Number of transactions per day | `12` | — |
| `distance_to_location` | `float` | Distance (km) from account to withdrawal location | `5.3` | — |
| `atm_density` | `integer` | Number of ATMs near the withdrawal location | `8` | `withdrawal_locations.atm_count` |
| `historical_similarity` | `float` (0.0–1.0) | Similarity score to known fraud patterns | `0.72` | — |
| `withdrawal_zone` | `string` (FK) | Location where withdrawal occurred | `LOC2005` | `withdrawal_locations.location_id` |
| `outcome` | `string` | What actually happened (factual observation) | `Withdrawal Detected` | — |

**Valid `outcome` values:** Withdrawal Detected, Withdrawal Attempted, No Activity

> **Note:** The `outcome` column records factual observations from past cases. It does **not** encode predictions or probability scores. Future ML models will use these features and outcomes for training.

---

## Key Conventions

- **PK** = Primary Key (unique identifier for this dataset)
- **FK** = Foreign Key (references a PK in another dataset)
- All monetary amounts are in **Indian Rupees (INR)**
- All coordinates use **WGS 84 (decimal degrees)**, bounded within India (~6°N–37°N, ~68°E–98°E)
- All dates use **ISO 8601** format (`YYYY-MM-DD`)
- All times use **24-hour** format (`HH:MM:SS`)
