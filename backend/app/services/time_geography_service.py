import math
from typing import List, Dict, Optional, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Complaint, Transaction, Account, WithdrawalLocation, HistoricalCase
from app.schemas.time_geography import (
    TimeGap, HourlyActivity, DailyActivity, TimePeriodActivity, TemporalIndicator, TemporalAnalysis,
    DistrictActivity, GeographicTransition, MovementSummary, GeographicConcentration, AccountGeography, GeographicAnalysis,
    WithdrawalCandidateFeature, HistoricalComparison, TemporalFeatures, GeographicFeatures, FeatureVector,
    TimeGeographyResponse, CandidateFeatureResponse
)
from app.services.money_flow_service import reconstruct_money_flow

def get_complaint_transactions(complaint_id: str, db: Session) -> List[Transaction]:
    return db.query(Transaction).filter(Transaction.complaint_id == complaint_id).all()

def get_complaint_accounts(complaint_id: str, db: Session) -> List[Account]:
    transactions = get_complaint_transactions(complaint_id, db)
    account_ids = set()
    for tx in transactions:
        account_ids.add(tx.sender_account)
        account_ids.add(tx.receiver_account)
    if not account_ids:
        return []
    return db.query(Account).filter(Account.account_id.in_(account_ids)).all()

# ==============================================================================
# TIME ANALYSIS
# ==============================================================================

def get_time_period(dt: datetime) -> str:
    hour = dt.hour
    if 0 <= hour < 6:
        return "NIGHT"
    elif 6 <= hour < 12:
        return "MORNING"
    elif 12 <= hour < 18:
        return "AFTERNOON"
    else:
        return "EVENING"

def analyze_temporal(complaint_id: str, db: Session) -> Optional[TemporalAnalysis]:
    transactions = get_complaint_transactions(complaint_id, db)
    if not transactions:
        return None

    # Sort successful transactions chronologically
    tx_count = len(transactions)
    successful_txs = sorted([t for t in transactions if t.transaction_status == 'Completed'], key=lambda x: x.transaction_time)
    
    if tx_count == 0:
        return TemporalAnalysis(
            transaction_count=0,
            time_gaps=TimeGap(minimum_gap_minutes=0, maximum_gap_minutes=0, average_gap_minutes=0, median_gap_minutes=0),
            hourly_activity=[], daily_activity=[], period_activity=[], indicators=[]
        )

    # Calculate gaps
    gaps_minutes = []
    for i in range(1, len(successful_txs)):
        prev_tx = successful_txs[i-1]
        curr_tx = successful_txs[i]
        diff = (curr_tx.transaction_time - prev_tx.transaction_time).total_seconds()
        gaps_minutes.append(max(0, diff / 60.0))

    if gaps_minutes:
        gaps_minutes.sort()
        min_gap = gaps_minutes[0]
        max_gap = gaps_minutes[-1]
        avg_gap = sum(gaps_minutes) / len(gaps_minutes)
        mid = len(gaps_minutes) // 2
        median_gap = (gaps_minutes[mid] + gaps_minutes[~mid]) / 2.0
    else:
        min_gap = max_gap = avg_gap = median_gap = 0.0

    time_gaps = TimeGap(
        minimum_gap_minutes=min_gap,
        maximum_gap_minutes=max_gap,
        average_gap_minutes=avg_gap,
        median_gap_minutes=median_gap
    )

    # Hourly Activity
    hourly_dict = {}
    for tx in transactions:
        hr = tx.transaction_time.hour
        amt = float(tx.amount)
        if hr not in hourly_dict:
            hourly_dict[hr] = {"count": 0, "amount": 0.0}
        hourly_dict[hr]["count"] += 1
        hourly_dict[hr]["amount"] += amt
    
    hourly_activity = [
        HourlyActivity(hour=hr, transaction_count=v["count"], total_amount=v["amount"])
        for hr, v in sorted(hourly_dict.items())
    ]

    # Daily Activity
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    daily_dict = {d: {"count": 0, "amount": 0.0} for d in days}
    for tx in transactions:
        day_name = days[tx.transaction_time.weekday()]
        daily_dict[day_name]["count"] += 1
        daily_dict[day_name]["amount"] += float(tx.amount)
        
    daily_activity = [
        DailyActivity(day_name=d, transaction_count=v["count"], total_amount=v["amount"])
        for d, v in daily_dict.items() if v["count"] > 0
    ]

    # Period Activity
    periods = {"NIGHT": 0, "MORNING": 0, "AFTERNOON": 0, "EVENING": 0}
    period_amt = {"NIGHT": 0.0, "MORNING": 0.0, "AFTERNOON": 0.0, "EVENING": 0.0}
    for tx in transactions:
        p = get_time_period(tx.transaction_time)
        periods[p] += 1
        period_amt[p] += float(tx.amount)
        
    period_activity = []
    for p, count in periods.items():
        if tx_count > 0:
            percentage = (count / tx_count) * 100
        else:
            percentage = 0.0
        period_activity.append(
            TimePeriodActivity(period=p, transaction_count=count, total_amount=period_amt[p], percentage=percentage)
        )

    # Indicators
    indicators = []
    if avg_gap > 0 and avg_gap < 10 and tx_count >= 3:
        indicators.append(TemporalIndicator(
            type="TEMPORAL_CLUSTER",
            severity="HIGH",
            description="Multiple transactions occurred within a very short average time gap (<10 mins).",
            evidence_transaction_ids=[t.transaction_id for t in successful_txs]
        ))

    night_pct = next((p.percentage for p in period_activity if p.period == "NIGHT"), 0.0)
    if night_pct > 30.0:
        indicators.append(TemporalIndicator(
            type="HIGH_NIGHT_ACTIVITY",
            severity="MEDIUM",
            description="High percentage of transactions occurred during nighttime hours.",
            evidence_transaction_ids=[t.transaction_id for t in successful_txs if get_time_period(t.transaction_time) == "NIGHT"]
        ))

    return TemporalAnalysis(
        transaction_count=tx_count,
        time_gaps=time_gaps,
        hourly_activity=hourly_activity,
        daily_activity=daily_activity,
        period_activity=period_activity,
        indicators=indicators
    )

# ==============================================================================
# GEOGRAPHIC ANALYSIS
# ==============================================================================

def analyze_geography(complaint_id: str, db: Session) -> Optional[GeographicAnalysis]:
    accounts = get_complaint_accounts(complaint_id, db)
    if not accounts:
        return None
        
    transactions = get_complaint_transactions(complaint_id, db)
    successful_txs = sorted([t for t in transactions if t.transaction_status == 'Completed'], key=lambda x: x.transaction_time)
    
    acc_map = {a.account_id: a for a in accounts}

    # District Distribution for transactions
    district_tx_count = {}
    district_tx_amount = {}
    
    for tx in successful_txs:
        sender = acc_map.get(tx.sender_account)
        receiver = acc_map.get(tx.receiver_account)
        # Use receiver location as transaction location proxy where possible
        dist = receiver.district_id if receiver else (sender.district_id if sender else None)
        if dist:
            district_tx_count[dist] = district_tx_count.get(dist, 0) + 1
            district_tx_amount[dist] = district_tx_amount.get(dist, 0.0) + float(tx.amount)
            
    # Account geography
    acc_district_counts = {}
    for a in accounts:
        acc_district_counts[a.district_id] = acc_district_counts.get(a.district_id, 0) + 1

    district_distribution = []
    unique_tx_districts = set(district_tx_count.keys())
    for d in unique_tx_districts:
        district_distribution.append(
            DistrictActivity(
                district=d,
                transaction_count=district_tx_count.get(d, 0),
                account_count=acc_district_counts.get(d, 0),
                total_amount=district_tx_amount.get(d, 0.0)
            )
        )
        
    account_geo = AccountGeography(
        account_count_per_district=acc_district_counts,
        unique_account_districts=len(acc_district_counts)
    )

    # Geographic Movement and Transitions
    transitions = []
    total_distance_m = 0.0
    transitions_count = 0
    unique_dists_in_path = set()
    
    # We trace the geographic path of funds through the transactions
    for i in range(1, len(successful_txs)):
        prev_tx = successful_txs[i-1]
        curr_tx = successful_txs[i]
        
        prev_acc = acc_map.get(prev_tx.receiver_account) or acc_map.get(prev_tx.sender_account)
        curr_acc = acc_map.get(curr_tx.receiver_account) or acc_map.get(curr_tx.sender_account)
        
        if prev_acc and curr_acc:
            prev_dist = prev_acc.district_id
            curr_dist = curr_acc.district_id
            
            unique_dists_in_path.add(prev_dist)
            unique_dists_in_path.add(curr_dist)
            
            # PostGIS ST_Distance calculation
            # Use raw query or func.ST_Distance
            distance_scalar = db.query(func.ST_Distance(prev_acc.location, curr_acc.location)).scalar()
            dist_km = (distance_scalar / 1000.0) if distance_scalar else 0.0
            
            time_gap = (curr_tx.transaction_time - prev_tx.transaction_time).total_seconds() / 60.0
            speed_kmh = None
            if time_gap > 0 and dist_km > 0:
                speed_kmh = dist_km / (time_gap / 60.0)
                # Cap unrealistic speeds due to tiny time gaps
                if speed_kmh > 5000:
                    speed_kmh = None
                    
            transitions.append(GeographicTransition(
                previous_transaction_id=prev_tx.transaction_id,
                current_transaction_id=curr_tx.transaction_id,
                previous_district=prev_dist,
                current_district=curr_dist,
                distance_km=dist_km,
                time_gap_minutes=max(0.0, time_gap),
                speed_kmh=speed_kmh
            ))
            
            total_distance_m += (distance_scalar or 0.0)
            if prev_dist != curr_dist:
                transitions_count += 1

    total_dist_km = total_distance_m / 1000.0
    max_dist_km = max([t.distance_km for t in transitions], default=0.0)
    avg_dist_km = total_dist_km / len(transitions) if transitions else 0.0
    
    movement = MovementSummary(
        total_distance_km=total_dist_km,
        average_distance_km=avg_dist_km,
        maximum_distance_km=max_dist_km,
        district_transitions=transitions_count,
        unique_districts=len(unique_dists_in_path) if unique_dists_in_path else len(unique_tx_districts)
    )

    # Concentration
    dominant_dist = ""
    dom_pct = 0.0
    if district_tx_count:
        sorted_dists = sorted(district_tx_count.items(), key=lambda x: x[1], reverse=True)
        dominant_dist = sorted_dists[0][0]
        dom_pct = (sorted_dists[0][1] / len(successful_txs)) * 100.0 if successful_txs else 0.0
        
    concentration = GeographicConcentration(
        dominant_district=dominant_dist,
        dominant_district_percentage=dom_pct,
        unique_districts=len(unique_tx_districts)
    )

    return GeographicAnalysis(
        district_distribution=district_distribution,
        account_geography=account_geo,
        movement_summary=movement,
        transitions=transitions,
        concentration=concentration
    )

# ==============================================================================
# WITHDRAWAL CANDIDATES & HISTORICAL COMPARISON
# ==============================================================================

def analyze_withdrawal_candidates(complaint_id: str, db: Session) -> List[WithdrawalCandidateFeature]:
    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not complaint:
        return []
        
    transactions = get_complaint_transactions(complaint_id, db)
    successful_txs = sorted([t for t in transactions if t.transaction_status == 'Completed'], key=lambda x: x.transaction_time)
    accounts = get_complaint_accounts(complaint_id, db)
    acc_map = {a.account_id: a for a in accounts}
    
    # Identify latest activity location
    latest_acc = None
    if successful_txs:
        last_tx = successful_txs[-1]
        latest_acc = acc_map.get(last_tx.receiver_account) or acc_map.get(last_tx.sender_account)
        
    # Terminal accounts from Money Flow module
    money_flow = reconstruct_money_flow(complaint_id, db)
    terminal_accs = []
    if money_flow:
        terminal_ids = [a.account_id for a in money_flow.terminal_accounts]
        terminal_accs = [acc_map.get(tid) for tid in terminal_ids if acc_map.get(tid)]
        
    term_acc = terminal_accs[0] if terminal_accs else None
    
    # We calculate features for ALL withdrawal candidates to return descriptive stats
    candidates = db.query(WithdrawalLocation).all()
    features = []
    
    for c in candidates:
        dist_latest = 0.0
        dist_term = 0.0
        dist_victim = 0.0
        
        # Calculate distance from latest activity
        if latest_acc and latest_acc.location is not None and c.location is not None:
            dist_latest = db.query(func.ST_Distance(latest_acc.location, c.location)).scalar() or 0.0
            
        # Calculate distance from terminal account
        if term_acc and term_acc.location is not None and c.location is not None:
            dist_term = db.query(func.ST_Distance(term_acc.location, c.location)).scalar() or 0.0
            
        # Calculate distance from victim (using complaint location if available)
        if complaint.location is not None and c.location is not None:
            dist_victim = db.query(func.ST_Distance(complaint.location, c.location)).scalar() or 0.0
            
        # Historical cases nearby (approx match by district)
        hist_cases = db.query(HistoricalCase).filter(HistoricalCase.district_id == c.district_id).count()

        features.append(WithdrawalCandidateFeature(
            location_id=c.location_id,
            district=c.district_id,
            latitude=float(c.latitude),
            longitude=float(c.longitude),
            distance_from_latest_activity_km=dist_latest / 1000.0,
            distance_from_terminal_account_km=dist_term / 1000.0,
            distance_from_victim_km=dist_victim / 1000.0,
            district_match_latest_activity=(c.district_id == latest_acc.district_id) if latest_acc else False,
            district_match_terminal_account=(c.district_id == term_acc.district_id) if term_acc else False,
            historical_cases_nearby=hist_cases
        ))
        
    return features

def analyze_historical_comparison(complaint_id: str, db: Session) -> List[HistoricalComparison]:
    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not complaint:
        return []
        
    # Find historical cases with same fraud type
    similar_cases = db.query(HistoricalCase).filter(HistoricalCase.fraud_type == complaint.fraud_type).limit(20).all()
    
    comparisons = []
    for hc in similar_cases:
        dist_m = 0.0
        if complaint.location is not None and hc.longitude is not None and hc.latitude is not None:
            # Calculate distance using PostGIS
            dist_scalar = db.query(func.ST_Distance(
                complaint.location, 
                func.ST_SetSRID(func.ST_MakePoint(hc.longitude, hc.latitude), 4326)
            )).scalar()
            if dist_scalar:
                dist_m = float(dist_scalar)
            
        comparisons.append(HistoricalComparison(
            historical_case_id=hc.historical_case_id,
            district=hc.district_id,
            city=hc.city,
            crime_type=hc.fraud_type,
            distance_from_current_activity_km=dist_m / 1000.0,
            withdrawal_location_id=hc.withdrawal_zone
        ))
        
    # Sort by distance
    comparisons.sort(key=lambda x: x.distance_from_current_activity_km)
    return comparisons

# ==============================================================================
# MAIN API
# ==============================================================================

def generate_time_geography_analysis(complaint_id: str, db: Session) -> Optional[TimeGeographyResponse]:
    temp = analyze_temporal(complaint_id, db)
    if not temp:
        return None
        
    geo = analyze_geography(complaint_id, db)
    candidates = analyze_withdrawal_candidates(complaint_id, db)
    historical = analyze_historical_comparison(complaint_id, db)
    
    # Build ML-ready feature vector
    night_pct = next((p.percentage for p in temp.period_activity if p.period == "NIGHT"), 0.0)
    eve_pct = next((p.percentage for p in temp.period_activity if p.period == "EVENING"), 0.0)
    
    temp_feat = TemporalFeatures(
        transaction_count=temp.transaction_count,
        average_gap_minutes=temp.time_gaps.average_gap_minutes,
        minimum_gap_minutes=temp.time_gaps.minimum_gap_minutes,
        maximum_gap_minutes=temp.time_gaps.maximum_gap_minutes,
        night_percentage=night_pct,
        evening_percentage=eve_pct
    )
    
    geo_feat = GeographicFeatures(
        unique_districts=geo.movement_summary.unique_districts,
        district_transitions=geo.movement_summary.district_transitions,
        total_distance_km=geo.movement_summary.total_distance_km,
        average_distance_km=geo.movement_summary.average_distance_km,
        maximum_distance_km=geo.movement_summary.maximum_distance_km
    )
    
    vec = FeatureVector(
        temporal_features=temp_feat,
        geographic_features=geo_feat
    )
    
    return TimeGeographyResponse(
        complaint_id=complaint_id,
        temporal_analysis=temp,
        geographic_analysis=geo,
        withdrawal_candidate_features=candidates,
        historical_comparison=historical,
        feature_vector=vec
    )
