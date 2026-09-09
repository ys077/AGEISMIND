# Dataset Relationship Diagram — SYNTHETIC PROTOTYPE DATA

> **⚠ DISCLAIMER:** All data described in this document is **SYNTHETIC PROTOTYPE DATA**.
> It does NOT contain real citizen data, real bank account data, or data from any government portal.

---

## Overview

The six datasets form a connected graph that models the flow from a cybercrime complaint through financial transactions, account networks, and ultimately to candidate cash-withdrawal locations. Historical cases provide labeled training data for the future ML prediction pipeline.

---

## Entity-Relationship Diagram

```mermaid
erDiagram
    COMPLAINTS ||--o{ TRANSACTIONS : "has many"
    TRANSACTIONS }o--|| ACCOUNTS : "sender_account"
    TRANSACTIONS }o--|| ACCOUNTS : "receiver_account"
    ACCOUNTS ||--o{ ACCOUNT_RELATIONSHIPS : "source_account"
    ACCOUNTS ||--o{ ACCOUNT_RELATIONSHIPS : "target_account"
    WITHDRAWAL_LOCATIONS ||--o{ HISTORICAL_CASES : "withdrawal_zone"
    COMPLAINTS {
        string complaint_id PK
        date complaint_date
        string fraud_type
        float fraud_amount
        time complaint_time
        string victim_city
        float victim_latitude
        float victim_longitude
        string crime_category
        string source_channel
        string status
    }
    TRANSACTIONS {
        string transaction_id PK
        string complaint_id FK
        string sender_account FK
        string receiver_account FK
        float amount
        datetime transaction_time
        string transaction_type
        string transaction_status
    }
    ACCOUNTS {
        string account_id PK
        string account_type
        string city
        float latitude
        float longitude
        float account_risk_score
        int previous_case_count
        string account_status
    }
    ACCOUNT_RELATIONSHIPS {
        string relationship_id PK
        string source_account FK
        string target_account FK
        string relationship_type
        int transaction_count
        float total_amount
    }
    WITHDRAWAL_LOCATIONS {
        string location_id PK
        string location_name
        string city
        float latitude
        float longitude
        string location_type
        int atm_count
        float area_risk_baseline
    }
    HISTORICAL_CASES {
        string historical_case_id PK
        string fraud_type
        float fraud_amount
        int transaction_hour
        string city
        float account_risk
        int transaction_velocity
        float distance_to_location
        int atm_density
        float historical_similarity
        string withdrawal_zone FK
        string outcome
    }
```

---

## Relationship Descriptions

### 1. Complaints → Transactions
- **Join key:** `complaints.complaint_id` = `transactions.complaint_id`
- **Cardinality:** One complaint has many transactions (1:N)
- **Meaning:** Every cybercrime complaint is linked to one or more financial transactions that form the fraud trail.

### 2. Transactions → Accounts (Sender)
- **Join key:** `transactions.sender_account` = `accounts.account_id`
- **Cardinality:** Many transactions reference one sender account (N:1)
- **Meaning:** The account that initiated or sent the funds in each transaction.

### 3. Transactions → Accounts (Receiver)
- **Join key:** `transactions.receiver_account` = `accounts.account_id`
- **Cardinality:** Many transactions reference one receiver account (N:1)
- **Meaning:** The account that received the funds in each transaction.

### 4. Accounts → Account Relationships
- **Join keys:**
  - `account_relationships.source_account` = `accounts.account_id`
  - `account_relationships.target_account` = `accounts.account_id`
- **Cardinality:** One account can appear in many relationships (1:N on both sides)
- **Meaning:** Captures network links between accounts — mule chains, frequent transactors, shared devices, etc. These relationships are derived from transaction patterns and investigator annotations.

### 5. Withdrawal Locations → Historical Cases
- **Join key:** `historical_cases.withdrawal_zone` = `withdrawal_locations.location_id`
- **Cardinality:** One location can appear in many historical cases (1:N)
- **Meaning:** Each historical case records which withdrawal location was associated with the observed outcome.

### 6. Implicit Links (Shared Dimensions)
These columns enable cross-dataset analysis without direct foreign keys:

| Shared Dimension | Datasets | Purpose |
|---|---|---|
| `city` | complaints, accounts, withdrawal_locations, historical_cases | Geographic co-location analysis |
| `fraud_type` | complaints, historical_cases | Pattern matching across current and past cases |
| `account_risk` / `account_risk_score` | accounts, historical_cases | Risk-based feature correlation |
| `atm_density` / `atm_count` | withdrawal_locations, historical_cases | Location feature matching |

---

## Data Flow for Prediction Pipeline

```mermaid
flowchart LR
    A["New Complaint"] --> B["Extract Transactions"]
    B --> C["Identify Involved Accounts"]
    C --> D["Map Account Relationships"]
    D --> E["Compute Features"]
    E --> F["Match Historical Cases"]
    F --> G["Rank Withdrawal Locations"]

    subgraph "Data Sources"
        H["complaints.csv"]
        I["transactions.csv"]
        J["accounts.csv"]
        K["account_relationships.csv"]
        L["withdrawal_locations.csv"]
        M["historical_cases.csv"]
    end

    A -.-> H
    B -.-> I
    C -.-> J
    D -.-> K
    G -.-> L
    F -.-> M
```

### Pipeline Steps

1. **New Complaint Received** — A complaint (e.g., CC1001) enters the system.
2. **Extract Transactions** — All transactions linked to the complaint are retrieved.
3. **Identify Involved Accounts** — Sender and receiver accounts from those transactions are mapped.
4. **Map Account Relationships** — The relationship network (mule chains, shared devices, etc.) is built from the account graph.
5. **Compute Features** — Features are computed: transaction velocity, timing patterns, geographic distances, risk scores, etc.
6. **Match Historical Cases** — Feature vectors are compared against historical cases to find similar past patterns.
7. **Rank Withdrawal Locations** — Candidate withdrawal locations are scored and ranked based on the ML model's predictions.

---

## CC1001 Demonstration Case — Data Connectivity

```mermaid
flowchart TD
    CC1001["CC1001\nUPI Fraud\n₹4,87,500"]

    CC1001 --> TXN90001["TXN90001\n₹1,50,000 UPI"]
    CC1001 --> TXN90002["TXN90002\n₹97,500 UPI"]
    CC1001 --> TXN90005["TXN90005\n₹1,00,000 UPI"]

    TXN90001 --> ACC100002["ACC100002\nMule 1 - Mumbai\nRisk: 0.78"]
    TXN90002 --> ACC100002
    TXN90005 --> ACC100005["ACC100005\nWallet - Mumbai\nRisk: 0.67"]

    ACC100002 --> TXN90003["TXN90003\n₹1,20,000 IMPS"]
    ACC100002 --> TXN90004["TXN90004\n₹80,000 NEFT"]

    TXN90003 --> ACC100003["ACC100003\nMule 2 - Pune\nRisk: 0.85"]
    TXN90004 --> ACC100004["ACC100004\nMule 3 - Delhi\nRisk: 0.91"]

    ACC100005 --> TXN90006["TXN90006\n₹60,000 UPI"]
    TXN90006 --> ACC100003

    ACC100003 --> TXN90007["TXN90007\n₹75,000 RTGS"]
    TXN90007 --> ACC100006["ACC100006\nMule 4 - Ahmedabad\nRisk: 0.72"]

    ACC100004 --> TXN90008["TXN90008\n₹10,000 ATM"]

    style CC1001 fill:#ff6b6b,color:#fff
    style ACC100002 fill:#ffa94d,color:#fff
    style ACC100003 fill:#ffa94d,color:#fff
    style ACC100004 fill:#ffa94d,color:#fff
    style ACC100005 fill:#ffd43b,color:#333
    style ACC100006 fill:#ffa94d,color:#fff
```

This diagram shows how CC1001's funds flow from the victim (ACC100001) through multiple mule accounts across Mumbai, Pune, Delhi, and Ahmedabad — creating a multi-city layering pattern that the prediction pipeline must analyze to identify probable cash-withdrawal locations.
