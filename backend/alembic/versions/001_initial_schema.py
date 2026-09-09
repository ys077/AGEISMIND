"""Initial schema — all 10 tables with PostGIS

Revision ID: 001
Revises: None
Create Date: 2026-09-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Enable PostGIS extension
    # ------------------------------------------------------------------
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # ------------------------------------------------------------------
    # 1. accounts (no FK dependencies)
    # ------------------------------------------------------------------
    op.create_table(
        "accounts",
        sa.Column("account_id", sa.String(20), primary_key=True),
        sa.Column("account_type", sa.String(50), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("latitude", sa.Numeric(9, 4), nullable=False),
        sa.Column("longitude", sa.Numeric(9, 4), nullable=False),
        sa.Column("account_risk_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("previous_case_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("account_status", sa.String(50), nullable=False),
        sa.Column(
            "location",
            geoalchemy2.types.Geography(
                geometry_type="POINT", srid=4326, spatial_index=False,
            ),
            nullable=True,
        ),
    )
    op.create_index("ix_accounts_city", "accounts", ["city"])
    op.create_index(
        "idx_accounts_location", "accounts", ["location"],
        postgresql_using="gist",
    )

    # ------------------------------------------------------------------
    # 2. complaints (no FK dependencies)
    # ------------------------------------------------------------------
    op.create_table(
        "complaints",
        sa.Column("complaint_id", sa.String(20), primary_key=True),
        sa.Column("complaint_date", sa.Date, nullable=False),
        sa.Column("fraud_type", sa.String(100), nullable=False),
        sa.Column("fraud_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("complaint_time", sa.Time, nullable=False),
        sa.Column("victim_city", sa.String(100), nullable=False),
        sa.Column("victim_latitude", sa.Numeric(9, 4), nullable=False),
        sa.Column("victim_longitude", sa.Numeric(9, 4), nullable=False),
        sa.Column("crime_category", sa.String(100), nullable=False),
        sa.Column("source_channel", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column(
            "location",
            geoalchemy2.types.Geography(
                geometry_type="POINT", srid=4326, spatial_index=False,
            ),
            nullable=True,
        ),
    )
    op.create_index("ix_complaints_fraud_type", "complaints", ["fraud_type"])
    op.create_index("ix_complaints_victim_city", "complaints", ["victim_city"])
    op.create_index(
        "idx_complaints_location", "complaints", ["location"],
        postgresql_using="gist",
    )

    # ------------------------------------------------------------------
    # 3. transactions (FKs → complaints, accounts x2)
    # ------------------------------------------------------------------
    op.create_table(
        "transactions",
        sa.Column("transaction_id", sa.String(20), primary_key=True),
        sa.Column(
            "complaint_id", sa.String(20),
            sa.ForeignKey("complaints.complaint_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "sender_account", sa.String(20),
            sa.ForeignKey("accounts.account_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "receiver_account", sa.String(20),
            sa.ForeignKey("accounts.account_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("transaction_time", sa.DateTime(timezone=False), nullable=False),
        sa.Column("transaction_type", sa.String(50), nullable=False),
        sa.Column("transaction_status", sa.String(50), nullable=False),
    )
    op.create_index("ix_transactions_complaint_id", "transactions", ["complaint_id"])
    op.create_index("ix_transactions_sender_account", "transactions", ["sender_account"])
    op.create_index("ix_transactions_receiver_account", "transactions", ["receiver_account"])
    op.create_index("ix_transactions_transaction_time", "transactions", ["transaction_time"])

    # ------------------------------------------------------------------
    # 4. account_relationships (FKs → accounts x2)
    # ------------------------------------------------------------------
    op.create_table(
        "account_relationships",
        sa.Column("relationship_id", sa.String(20), primary_key=True),
        sa.Column(
            "source_account", sa.String(20),
            sa.ForeignKey("accounts.account_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_account", sa.String(20),
            sa.ForeignKey("accounts.account_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("relationship_type", sa.String(50), nullable=False),
        sa.Column("transaction_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Numeric(15, 2), nullable=False),
    )
    op.create_index("ix_account_relationships_source", "account_relationships", ["source_account"])
    op.create_index("ix_account_relationships_target", "account_relationships", ["target_account"])

    # ------------------------------------------------------------------
    # 5. withdrawal_locations (no FK dependencies)
    # ------------------------------------------------------------------
    op.create_table(
        "withdrawal_locations",
        sa.Column("location_id", sa.String(20), primary_key=True),
        sa.Column("location_name", sa.String(200), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("latitude", sa.Numeric(9, 4), nullable=False),
        sa.Column("longitude", sa.Numeric(9, 4), nullable=False),
        sa.Column("location_type", sa.String(50), nullable=False),
        sa.Column("atm_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("area_risk_baseline", sa.Numeric(5, 2), nullable=False),
        sa.Column(
            "location",
            geoalchemy2.types.Geography(
                geometry_type="POINT", srid=4326, spatial_index=False,
            ),
            nullable=True,
        ),
    )
    op.create_index("ix_withdrawal_locations_city", "withdrawal_locations", ["city"])
    op.create_index(
        "idx_withdrawal_locations_location", "withdrawal_locations", ["location"],
        postgresql_using="gist",
    )

    # ------------------------------------------------------------------
    # 6. historical_cases (FK → withdrawal_locations)
    # ------------------------------------------------------------------
    op.create_table(
        "historical_cases",
        sa.Column("historical_case_id", sa.String(20), primary_key=True),
        sa.Column("fraud_type", sa.String(100), nullable=False),
        sa.Column("fraud_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("transaction_hour", sa.Integer, nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("account_risk", sa.Numeric(5, 2), nullable=False),
        sa.Column("transaction_velocity", sa.Integer, nullable=False),
        sa.Column("distance_to_location", sa.Numeric(10, 2), nullable=False),
        sa.Column("atm_density", sa.Integer, nullable=False),
        sa.Column("historical_similarity", sa.Numeric(5, 2), nullable=False),
        sa.Column(
            "withdrawal_zone", sa.String(20),
            sa.ForeignKey("withdrawal_locations.location_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("outcome", sa.String(50), nullable=False),
    )
    op.create_index("ix_historical_cases_fraud_type", "historical_cases", ["fraud_type"])

    # ------------------------------------------------------------------
    # 7. predictions (FKs → complaints, withdrawal_locations)
    # ------------------------------------------------------------------
    op.create_table(
        "predictions",
        sa.Column("prediction_id", sa.Uuid, primary_key=True),
        sa.Column(
            "complaint_id", sa.String(20),
            sa.ForeignKey("complaints.complaint_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "location_id", sa.String(20),
            sa.ForeignKey("withdrawal_locations.location_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("risk_score", sa.Numeric(7, 4), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("rank", sa.Integer, nullable=False),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_predictions_complaint_id", "predictions", ["complaint_id"])

    # ------------------------------------------------------------------
    # 8. prediction_factors (FK → predictions)
    # ------------------------------------------------------------------
    op.create_table(
        "prediction_factors",
        sa.Column("factor_id", sa.Uuid, primary_key=True),
        sa.Column(
            "prediction_id", sa.Uuid,
            sa.ForeignKey("predictions.prediction_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("factor_name", sa.String(100), nullable=False),
        sa.Column("contribution", sa.Numeric(7, 4), nullable=False),
        sa.Column("direction", sa.String(20), nullable=False),
    )
    op.create_index("ix_prediction_factors_prediction_id", "prediction_factors", ["prediction_id"])

    # ------------------------------------------------------------------
    # 9. investigation_actions (FK → complaints)
    # ------------------------------------------------------------------
    op.create_table(
        "investigation_actions",
        sa.Column("action_id", sa.Uuid, primary_key=True),
        sa.Column(
            "complaint_id", sa.String(20),
            sa.ForeignKey("complaints.complaint_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("investigator_id", sa.String(50), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("action_description", sa.Text, nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_investigation_actions_complaint_id", "investigation_actions", ["complaint_id"])

    # ------------------------------------------------------------------
    # 10. audit_logs (FK → complaints, nullable)
    # ------------------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column("audit_id", sa.Uuid, primary_key=True),
        sa.Column(
            "complaint_id", sa.String(20),
            sa.ForeignKey("complaints.complaint_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(50), nullable=False),
        sa.Column("data_hash", sa.String(256), nullable=True),
        sa.Column(
            "timestamp", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
        sa.Column("actor_id", sa.String(50), nullable=True),
    )
    op.create_index("ix_audit_logs_complaint_id", "audit_logs", ["complaint_id"])


def downgrade() -> None:
    # Drop in reverse order of creation (children before parents)
    op.drop_table("audit_logs")
    op.drop_table("investigation_actions")
    op.drop_table("prediction_factors")
    op.drop_table("predictions")
    op.drop_table("historical_cases")
    op.drop_table("withdrawal_locations")
    op.drop_table("account_relationships")
    op.drop_table("transactions")
    op.drop_table("complaints")
    op.drop_table("accounts")
    op.execute("DROP EXTENSION IF EXISTS postgis")
