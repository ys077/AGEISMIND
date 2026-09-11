from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Complaint, Transaction, Account, HistoricalCase, WithdrawalLocation

class FeatureEngineer:
    def __init__(self, db: Session):
        self.db = db

    def _get_historical_candidate_frequencies(self) -> Dict[str, int]:
        """Calculates withdrawal frequency per candidate zone based on historical cases."""
        frequencies = self.db.query(
            HistoricalCase.withdrawal_zone, 
            func.count(HistoricalCase.historical_case_id)
        ).group_by(HistoricalCase.withdrawal_zone).all()
        return {zone: count for zone, count in frequencies}

    def generate_features_for_complaint(
        self, 
        complaint: Complaint, 
        transactions: List[Transaction], 
        accounts: List[Account], 
        candidates: List[WithdrawalLocation],
        historical_frequencies: Optional[Dict[str, int]] = None
    ) -> pd.DataFrame:
        """
        Generates candidate-level features for a given complaint.
        For N candidates, returns N rows of features.
        """
        # --- Base Features (Complaint & Transaction Level) ---
        amount = float(complaint.fraud_amount)
        tx_count = len(transactions)
        successful_txs = [tx for tx in transactions if tx.transaction_status.lower() == "completed"]
        successful_tx_count = len(successful_txs)
        
        amounts = [float(tx.amount) for tx in transactions]
        total_amount = sum(amounts) if amounts else 0.0
        avg_amount = total_amount / tx_count if tx_count > 0 else 0.0
        max_amount = max(amounts) if amounts else 0.0
        min_amount = min(amounts) if amounts else 0.0
        
        unique_senders = len(set(tx.sender_account for tx in transactions))
        unique_receivers = len(set(tx.receiver_account for tx in transactions))

        from app.services.time_geography_service import analyze_temporal, analyze_geography
        time_analysis = analyze_temporal(complaint.complaint_id, self.db)
        geo_analysis = analyze_geography(complaint.complaint_id, self.db)
        
        # Determine complaint/case core location
        complaint_lat = float(complaint.victim_latitude) if complaint.victim_latitude else 0.0
        complaint_lon = float(complaint.victim_longitude) if complaint.victim_longitude else 0.0
        complaint_district = complaint.district_id

        # Terminal account district
        terminal_district = "UNKNOWN"
        if geo_analysis.district_distribution:
            # Most active district
            sorted_districts = sorted(geo_analysis.district_distribution, key=lambda x: x.transaction_count, reverse=True)
            terminal_district = sorted_districts[0].district
            
        avg_tx_gap = time_analysis.time_gaps.average_gap_minutes
        max_tx_gap = time_analysis.time_gaps.maximum_gap_minutes
        min_tx_gap = time_analysis.time_gaps.minimum_gap_minutes

        # Activity periods
        night_pct = 0.0
        morning_pct = 0.0
        afternoon_pct = 0.0
        evening_pct = 0.0
        for period in time_analysis.period_activity:
            if period.period == "NIGHT": night_pct = period.percentage
            elif period.period == "MORNING": morning_pct = period.percentage
            elif period.period == "AFTERNOON": afternoon_pct = period.percentage
            elif period.period == "EVENING": evening_pct = period.percentage

        # --- Candidate-level Expansion ---
        feature_rows = []
        
        for candidate in candidates:
            # Candidate specific features
            candidate_lat = float(candidate.latitude)
            candidate_lon = float(candidate.longitude)
            
            # Simple Euclidean approx for distance (Module 7 uses PostGIS, but we need fast features here too)
            # In production, use ST_Distance
            dist_from_complaint = ((candidate_lat - complaint_lat)**2 + (candidate_lon - complaint_lon)**2)**0.5
            same_district_as_victim = 1 if candidate.district_id == complaint_district else 0
            same_district_as_terminal = 1 if candidate.district_id == terminal_district else 0
            
            hist_freq = historical_frequencies.get(candidate.location_id, 0) if historical_frequencies else 0
            
            # Encode Fraud Type
            # One-hot encodings for common fraud types
            ft = complaint.fraud_type.lower()
            is_upi = 1 if "upi" in ft else 0
            is_phishing = 1 if "phishing" in ft else 0
            is_sim_swap = 1 if "sim" in ft else 0
            is_job = 1 if "job" in ft else 0
            is_investment = 1 if "investment" in ft else 0
            is_card = 1 if "card" in ft else 0
            
            row = {
                # Identifiers (will be dropped before training)
                "complaint_id": complaint.complaint_id,
                "candidate_location_id": candidate.location_id,
                "district_id": candidate.district_id,
                
                # Transaction base
                "amount": amount,
                "tx_count": tx_count,
                "successful_tx_count": successful_tx_count,
                "total_amount": total_amount,
                "avg_amount": avg_amount,
                "max_amount": max_amount,
                "min_amount": min_amount,
                "unique_senders": unique_senders,
                "unique_receivers": unique_receivers,
                
                # Fraud type OHE
                "is_upi": is_upi,
                "is_phishing": is_phishing,
                "is_sim_swap": is_sim_swap,
                "is_job": is_job,
                "is_investment": is_investment,
                "is_card": is_card,
                
                # Temporal
                "avg_tx_gap": avg_tx_gap,
                "max_tx_gap": max_tx_gap,
                "min_tx_gap": min_tx_gap,
                "night_pct": night_pct,
                "morning_pct": morning_pct,
                "afternoon_pct": afternoon_pct,
                "evening_pct": evening_pct,
                
                # Geographic / Candidate
                "candidate_atm_count": candidate.atm_count,
                "candidate_area_risk": float(candidate.area_risk_baseline),
                "dist_from_complaint_deg": dist_from_complaint,
                "same_district_as_victim": same_district_as_victim,
                "same_district_as_terminal": same_district_as_terminal,
                
                # Historical
                "historical_frequency": hist_freq
            }
            feature_rows.append(row)
            
        return pd.DataFrame(feature_rows)

    def generate_features_for_historical_case(
        self, 
        case: HistoricalCase, 
        candidates: List[WithdrawalLocation],
        historical_frequencies: Optional[Dict[str, int]] = None
    ) -> pd.DataFrame:
        """
        Generates candidate-level features for a historical case (for training).
        Mocking transaction features from case aggregates.
        """
        amount = float(case.fraud_amount)
        tx_count = case.transaction_velocity
        
        # Fraud Type OHE
        ft = case.fraud_type.lower()
        is_upi = 1 if "upi" in ft else 0
        is_phishing = 1 if "phishing" in ft else 0
        is_sim_swap = 1 if "sim" in ft else 0
        is_job = 1 if "job" in ft else 0
        is_investment = 1 if "investment" in ft else 0
        is_card = 1 if "card" in ft else 0
        
        # Temporal
        night_pct = 1.0 if 0 <= case.transaction_hour < 6 else 0.0
        morning_pct = 1.0 if 6 <= case.transaction_hour < 12 else 0.0
        afternoon_pct = 1.0 if 12 <= case.transaction_hour < 18 else 0.0
        evening_pct = 1.0 if 18 <= case.transaction_hour < 24 else 0.0
        
        feature_rows = []
        for candidate in candidates:
            # Candidate specific
            candidate_lat = float(candidate.latitude)
            candidate_lon = float(candidate.longitude)
            
            case_lat = float(case.latitude)
            case_lon = float(case.longitude)
            
            dist_from_complaint = ((candidate_lat - case_lat)**2 + (candidate_lon - case_lon)**2)**0.5
            same_district_as_victim = 1 if candidate.district_id == case.district_id else 0
            
            hist_freq = historical_frequencies.get(candidate.location_id, 0) if historical_frequencies else 0
            
            # Label
            is_target = 1 if candidate.location_id == case.withdrawal_zone else 0
            
            row = {
                "historical_case_id": case.historical_case_id,
                "candidate_location_id": candidate.location_id,
                "district_id": candidate.district_id,
                
                # Base
                "amount": amount,
                "tx_count": tx_count,
                "successful_tx_count": tx_count,  # Approximate for historical
                "total_amount": amount,
                "avg_amount": amount / tx_count if tx_count > 0 else amount,
                "max_amount": amount,
                "min_amount": amount / tx_count if tx_count > 0 else amount,
                "unique_senders": 1,
                "unique_receivers": 1,
                
                "is_upi": is_upi,
                "is_phishing": is_phishing,
                "is_sim_swap": is_sim_swap,
                "is_job": is_job,
                "is_investment": is_investment,
                "is_card": is_card,
                
                "avg_tx_gap": 0.0,
                "max_tx_gap": 0.0,
                "min_tx_gap": 0.0,
                "night_pct": night_pct,
                "morning_pct": morning_pct,
                "afternoon_pct": afternoon_pct,
                "evening_pct": evening_pct,
                
                "candidate_atm_count": candidate.atm_count,
                "candidate_area_risk": float(candidate.area_risk_baseline),
                "dist_from_complaint_deg": dist_from_complaint,
                "same_district_as_victim": same_district_as_victim,
                "same_district_as_terminal": same_district_as_victim, # Approx
                
                "historical_frequency": hist_freq,
                
                # Target Label
                "is_target": is_target
            }
            feature_rows.append(row)
            
        return pd.DataFrame(feature_rows)
