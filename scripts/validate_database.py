"""
===============================================================================
DATABASE VALIDATION — SYNTHETIC PROTOTYPE DATA
===============================================================================

Validates the seeded PostgreSQL database against the expected CSV data.

Checks:
  1. Row counts match CSV counts
  2. CC1001 exists with 10 transactions and 6 related accounts
  3. All foreign keys are valid (no orphans)
  4. No duplicate primary keys
  5. Geographic coordinates are valid (within India bounds)
  6. PostGIS extension is enabled
  7. Spatial fields contain valid points

Usage:
    python scripts/validate_database.py

===============================================================================
"""

import csv
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make backend importable from project root
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from sqlalchemy import text, func, select, distinct  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.db.database import engine, SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    District,
    Location,
    Account,
    Complaint,
    Transaction,
    AccountRelationship,
    WithdrawalLocation,
    HistoricalCase,
    Prediction,
    PredictionFactor,
    InvestigationAction,
    AuditLog,
)

# ---------------------------------------------------------------------------
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PASS = "[PASS]"
FAIL = "[FAIL]"
errors: list[str] = []


def csv_count(filename: str) -> int:
    """Count rows in a CSV (excluding header)."""
    with open(RAW_DIR / filename, "r", encoding="utf-8") as f:
        return sum(1 for _ in csv.reader(f)) - 1


def check(label: str, passed: bool, detail: str = "") -> None:
    """Record a check result."""
    status = PASS if passed else FAIL
    msg = f"  {status} {label}"
    if detail:
        msg += f"  ({detail})"
    print(msg)
    if not passed:
        errors.append(label)


# ===========================================================================
# MAIN
# ===========================================================================
def main() -> int:
    print("=" * 60)
    print("  DATABASE VALIDATION")
    print("  AI-Driven Cybercrime Cash Withdrawal Prediction System")
    print("=" * 60)
    print()

    session = SessionLocal()

    try:
        # ==================================================================
        # 1. PostgreSQL connectivity
        # ==================================================================
        pg_version = session.execute(text("SELECT version()")).scalar()
        print(f"  PostgreSQL: {PASS}")
        print(f"    {pg_version[:60]}...")
        print()

        # ==================================================================
        # 2. PostGIS extension
        # ==================================================================
        try:
            postgis_ver = session.execute(text("SELECT PostGIS_Version()")).scalar()
            check("PostGIS extension enabled", True, postgis_ver)
        except Exception:
            check("PostGIS extension enabled", False, "PostGIS not found")

        print()

        # ==================================================================
        # 3. Row counts vs CSV
        # ==================================================================
        print("  --- Row Counts ---")
        count_checks = [
            ("districts.csv", District, "districts"),
            ("locations.csv", Location, "locations"),
            ("complaints.csv", Complaint, "complaints"),
            ("transactions.csv", Transaction, "transactions"),
            ("accounts.csv", Account, "accounts"),
            ("account_relationships.csv", AccountRelationship, "relationships"),
            ("withdrawal_locations.csv", WithdrawalLocation, "withdrawal locations"),
            ("historical_cases.csv", HistoricalCase, "historical cases"),
        ]

        for csv_file, model, label in count_checks:
            expected = csv_count(csv_file)
            actual = session.query(func.count()).select_from(model).scalar()
            check(
                f"{label}: {actual}",
                actual == expected,
                f"expected {expected}",
            )

        # Empty tables check removed because modules are now implemented

        print()

        # ==================================================================
        # 4. CC1001 demonstration case
        # ==================================================================
        print("  --- CC1001 Demonstration Case ---")

        cc1001_exists = session.query(Complaint).filter_by(
            complaint_id="CC1001"
        ).first()
        check("CC1001 exists", cc1001_exists is not None)

        cc1001_txn_count = session.query(func.count()).select_from(
            Transaction
        ).filter_by(complaint_id="CC1001").scalar()
        check(
            f"CC1001 transactions: {cc1001_txn_count}",
            cc1001_txn_count == 10,
            "expected 10",
        )

        # Distinct accounts involved in CC1001 transactions
        sender_q = session.query(
            distinct(Transaction.sender_account)
        ).filter_by(complaint_id="CC1001")
        receiver_q = session.query(
            distinct(Transaction.receiver_account)
        ).filter_by(complaint_id="CC1001")
        cc1001_accounts = set(
            [r[0] for r in sender_q.all()] + [r[0] for r in receiver_q.all()]
        )
        check(
            f"CC1001 accounts: {len(cc1001_accounts)}",
            len(cc1001_accounts) == 6,
            "expected 6",
        )

        # CC1001 relationships
        cc1001_rels = session.query(func.count()).select_from(
            AccountRelationship
        ).filter(
            (AccountRelationship.source_account.in_(cc1001_accounts)) |
            (AccountRelationship.target_account.in_(cc1001_accounts))
        ).scalar()
        check(
            f"CC1001 relationships: {cc1001_rels}",
            cc1001_rels >= 4,
            "expected >= 4",
        )

        print()

        # ==================================================================
        # 5. Foreign key integrity
        # ==================================================================
        print("  --- Foreign Key Integrity ---")

        # Transactions → complaints
        orphan_txn_complaints = session.execute(text("""
            SELECT COUNT(*) FROM transactions t
            LEFT JOIN complaints c ON t.complaint_id = c.complaint_id
            WHERE c.complaint_id IS NULL
        """)).scalar()
        check("Transactions -> complaints FK", orphan_txn_complaints == 0,
              f"{orphan_txn_complaints} orphans")

        # Transactions → accounts (sender)
        orphan_senders = session.execute(text("""
            SELECT COUNT(*) FROM transactions t
            LEFT JOIN accounts a ON t.sender_account = a.account_id
            WHERE a.account_id IS NULL
        """)).scalar()
        check("Transactions -> accounts (sender) FK", orphan_senders == 0,
              f"{orphan_senders} orphans")

        # Transactions → accounts (receiver)
        orphan_receivers = session.execute(text("""
            SELECT COUNT(*) FROM transactions t
            LEFT JOIN accounts a ON t.receiver_account = a.account_id
            WHERE a.account_id IS NULL
        """)).scalar()
        check("Transactions -> accounts (receiver) FK", orphan_receivers == 0,
              f"{orphan_receivers} orphans")

        # Account relationships → accounts (source)
        orphan_rel_src = session.execute(text("""
            SELECT COUNT(*) FROM account_relationships ar
            LEFT JOIN accounts a ON ar.source_account = a.account_id
            WHERE a.account_id IS NULL
        """)).scalar()
        check("Relationships -> accounts (source) FK", orphan_rel_src == 0,
              f"{orphan_rel_src} orphans")

        # Account relationships → accounts (target)
        orphan_rel_tgt = session.execute(text("""
            SELECT COUNT(*) FROM account_relationships ar
            LEFT JOIN accounts a ON ar.target_account = a.account_id
            WHERE a.account_id IS NULL
        """)).scalar()
        check("Relationships -> accounts (target) FK", orphan_rel_tgt == 0,
              f"{orphan_rel_tgt} orphans")

        # Historical cases → withdrawal_locations
        orphan_hc = session.execute(text("""
            SELECT COUNT(*) FROM historical_cases hc
            LEFT JOIN withdrawal_locations wl ON hc.withdrawal_zone = wl.location_id
            WHERE wl.location_id IS NULL
        """)).scalar()
        check("Historical cases -> withdrawal_locations FK", orphan_hc == 0,
              f"{orphan_hc} orphans")

        print()

        # ==================================================================
        # 6. Duplicate IDs
        # ==================================================================
        print("  --- Duplicate ID Checks ---")

        dup_checks = [
            ("accounts", "account_id"),
            ("complaints", "complaint_id"),
            ("transactions", "transaction_id"),
            ("account_relationships", "relationship_id"),
            ("withdrawal_locations", "location_id"),
            ("historical_cases", "historical_case_id"),
        ]
        for table, pk_col in dup_checks:
            dup_count = session.execute(text(f"""
                SELECT COUNT(*) FROM (
                    SELECT {pk_col}, COUNT(*) as cnt
                    FROM {table}
                    GROUP BY {pk_col}
                    HAVING COUNT(*) > 1
                ) sub
            """)).scalar()
            check(f"No duplicate {pk_col}", dup_count == 0,
                  f"{dup_count} duplicates" if dup_count else "NONE")

        print()

        # ==================================================================
        # 7. Geographic coordinate validity
        # ==================================================================
        print("  --- Geographic Coordinates ---")

        invalid_acc_coords = session.execute(text("""
            SELECT COUNT(*) FROM accounts
            WHERE latitude < 6.0 OR latitude > 37.0
               OR longitude < 68.0 OR longitude > 98.0
        """)).scalar()
        check("Account coordinates valid (India bounds)", invalid_acc_coords == 0,
              f"{invalid_acc_coords} invalid" if invalid_acc_coords else "NONE")

        invalid_loc_coords = session.execute(text("""
            SELECT COUNT(*) FROM withdrawal_locations
            WHERE latitude < 6.0 OR latitude > 37.0
               OR longitude < 68.0 OR longitude > 98.0
        """)).scalar()
        check("Location coordinates valid (India bounds)", invalid_loc_coords == 0,
              f"{invalid_loc_coords} invalid" if invalid_loc_coords else "NONE")

        invalid_comp_coords = session.execute(text("""
            SELECT COUNT(*) FROM complaints
            WHERE victim_latitude < 6.0 OR victim_latitude > 37.0
               OR victim_longitude < 68.0 OR victim_longitude > 98.0
        """)).scalar()
        check("Complaint coordinates valid (India bounds)", invalid_comp_coords == 0,
              f"{invalid_comp_coords} invalid" if invalid_comp_coords else "NONE")

        print()

        # ==================================================================
        # 8. PostGIS spatial field validation
        # ==================================================================
        print("  --- Spatial Field Validation ---")

        for table, label, field in [
            ("districts", "District", "geometry"),
            ("locations", "Location", "geometry"),
            ("accounts", "Account", "location"),
            ("complaints", "Complaint", "location"),
            ("withdrawal_locations", "Withdrawal Location", "location"),
        ]:
            null_locations = session.execute(text(f"""
                SELECT COUNT(*) FROM {table} WHERE {field} IS NULL
            """)).scalar()
            valid_points = session.execute(text(f"""
                SELECT COUNT(*) FROM {table}
                WHERE ST_IsValid({field}::geometry) = true
            """)).scalar()
            total = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            check(
                f"{label} spatial points",
                null_locations == 0 and valid_points == total,
                f"{valid_points}/{total} valid, {null_locations} NULL",
            )

        print()

        # ==================================================================
        # SUMMARY
        # ==================================================================
        print("=" * 60)
        if errors:
            print(f"  DATABASE STATUS: {FAIL}  ({len(errors)} check(s) failed)")
            for e in errors:
                print(f"    - {e}")
        else:
            print(f"  DATABASE STATUS: {PASS}")
        print()
        print("  [!] ALL DATA IS SYNTHETIC PROTOTYPE DATA.")
        print("=" * 60)

        return 0 if not errors else 1

    except Exception as e:
        print(f"\n  [ERROR] Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
