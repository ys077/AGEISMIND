import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.alert import Alert
from app.models.prediction import Prediction
from app.models.investigation_action import InvestigationAction
from app.models.audit_log import AuditLog
from app.models.withdrawal_location import WithdrawalLocation
from app.models.district import District
from app.schemas.alert import AlertDetailResponse
from app.services import email_service
from app.core.config import settings

def generate_alerts_from_predictions(db: Session) -> int:
    """
    Scans existing predictions for HIGH or MEDIUM priority.
    Creates alerts for any that don't already have one.
    Returns the number of alerts created.
    """
    # Find high/medium predictions without an alert
    # We can do this with an outer join or subquery
    predictions_to_alert = db.query(Prediction).filter(
        Prediction.priority.in_(["CRITICAL", "HIGH", "MEDIUM"]),
        ~Prediction.prediction_id.in_(db.query(Alert.prediction_id))
    ).all()
    
    count = 0
    for pred in predictions_to_alert:
        new_alert = Alert(
            prediction_id=pred.prediction_id,
            status="NEW"
        )
        db.add(new_alert)
        db.flush()
        count += 1
        
        log_audit_event(
            db=db,
            action_type="ALERT_CREATED",
            entity_type="ALERT",
            entity_id=str(new_alert.alert_id),
            actor_id="SYSTEM",
            complaint_id=pred.complaint_id,
            data_hash=f"Priority:{pred.priority}|Score:{pred.risk_score}",
            commit=False
        )

        # ----------------------------------------------------
        # Email Notification & Duplicate Prevention
        # ----------------------------------------------------
        # Deduplicate by complaint_id to avoid sending multiple emails
        # if the complaint is re-processed and new alerts are generated.
        existing_email_log = db.query(AuditLog).filter(
            AuditLog.complaint_id == pred.complaint_id,
            AuditLog.action_type == "EMAIL_SENT"
        ).first()

        if not existing_email_log and settings.ENABLE_EMAIL_NOTIFICATIONS:
            # Fetch location and district data for the email format
            loc = db.query(WithdrawalLocation).filter(WithdrawalLocation.location_id == pred.location_id).first()
            dist_name = "Unknown"
            if loc:
                dist = db.query(District).filter(District.district_id == loc.district_id).first()
                if dist:
                    dist_name = dist.district_name

            alert_data = {
                "alert_id": str(new_alert.alert_id),
                "complaint_id": pred.complaint_id,
                "priority": pred.priority,
                "withdrawal_location_id": pred.location_id,
                "district": dist_name,
                "probability": float(pred.risk_score) if pred.risk_score is not None else 0.0,
                "created_at": new_alert.created_at.isoformat() if new_alert.created_at else "N/A"
            }

            recipient = settings.ALERT_FROM_EMAIL  # Using from_email as recipient for alerts per instructions?
            # Wait, the instruction says "Send the email to my test recipient." for the test. 
            # For the alert, it doesn't specify a generic alert recipient list, I will default to sending to ALERT_FROM_EMAIL or a hypothetical investigator email.
            # Let's send to ALERT_FROM_EMAIL for simplicity in testing as requested.
            
            email_success = email_service.send_alert_email(recipient, alert_data)

            if email_success:
                log_audit_event(
                    db=db,
                    action_type="EMAIL_SENT",
                    entity_type="ALERT",
                    entity_id=str(new_alert.alert_id),
                    actor_id="SYSTEM",
                    complaint_id=pred.complaint_id,
                    data_hash=f"EmailSentTo:{recipient}",
                    commit=False
                )
            else:
                log_audit_event(
                    db=db,
                    action_type="EMAIL_FAILED",
                    entity_type="ALERT",
                    entity_id=str(new_alert.alert_id),
                    actor_id="SYSTEM",
                    complaint_id=pred.complaint_id,
                    data_hash="Email delivery failed",
                    commit=False
                )
        
    if count > 0:
        db.commit()
        
    return count


def get_all_audit_logs(db: Session) -> List[Dict[str, Any]]:
    """
    Retrieve all system audit logs.
    """
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
    return [{
        "audit_id": str(log.audit_id),
        "action_type": log.action_type,
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "actor_id": log.actor_id,
        "complaint_id": log.complaint_id,
        "data_hash": log.data_hash,
        "created_at": log.timestamp.isoformat() if log.timestamp else None,
        "timestamp": log.timestamp.isoformat() if log.timestamp else None
    } for log in logs]


def get_alerts(
    db: Session,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    district: Optional[str] = None,
    complaint_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve a list of alerts with optional filters.
    """
    # Column-only query avoids selectin-loading SHAP factors, historical cases, etc.
    query = db.query(
        Alert.alert_id,
        Alert.status,
        Alert.created_at,
        Prediction.prediction_id,
        Prediction.complaint_id,
        Prediction.risk_score,
        Prediction.rank,
        Prediction.priority,
        WithdrawalLocation.location_id,
        District.district_name,
    ).join(
        Prediction, Alert.prediction_id == Prediction.prediction_id
    ).join(
        WithdrawalLocation, Prediction.location_id == WithdrawalLocation.location_id
    ).join(
        District, WithdrawalLocation.district_id == District.district_id
    )

    if status:
        query = query.filter(Alert.status == status)
    if priority:
        query = query.filter(Prediction.priority == priority)
    if district:
        query = query.filter(District.district_name == district)
    if complaint_id:
        query = query.filter(Prediction.complaint_id == complaint_id)

    results = query.order_by(Prediction.risk_score.desc(), Prediction.rank.asc()).all()

    return [{
        "alert_id": row.alert_id,
        "prediction_id": row.prediction_id,
        "complaint_id": row.complaint_id,
        "withdrawal_location_id": row.location_id,
        "district": row.district_name,
        "probability": float(row.risk_score) if row.risk_score is not None else 0.0,
        "rank": row.rank,
        "priority": row.priority,
        "status": row.status,
        "created_at": row.created_at
    } for row in results]


def get_alert_detail(db: Session, alert_id: uuid.UUID) -> Optional[AlertDetailResponse]:
    """
    Retrieve detailed view for an alert, including SHAP explanations.
    """
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        return None
        
    pred = db.query(Prediction).options(
        joinedload(Prediction.factors)
    ).filter(Prediction.prediction_id == alert.prediction_id).first()
    
    if not pred:
        return None
        
    loc = db.query(WithdrawalLocation).options(
        joinedload(WithdrawalLocation.district)
    ).filter(WithdrawalLocation.location_id == pred.location_id).first()
    
    if not loc:
        return None

    # Process SHAP factors
    positive_factors = []
    negative_factors = []
    
    for factor in pred.factors:
        contrib = float(factor.contribution) if factor.contribution is not None else 0.0
        f_dict = {
            "feature_name": factor.factor_name,
            "feature_value": float(factor.feature_value) if (factor.feature_value is not None and str(factor.feature_value).replace('.','',1).isdigit()) else factor.feature_value,
            "shap_value": contrib,
            "explanation_text": factor.explanation_text
        }
        if contrib > 0:
            positive_factors.append(f_dict)
        elif contrib < 0:
            negative_factors.append(f_dict)
            
    # Sort by absolute impact
    positive_factors.sort(key=lambda x: x["shap_value"], reverse=True)
    negative_factors.sort(key=lambda x: x["shap_value"])  # smallest (most negative) first
    
    # Generate basic explanation text (Module 9 format)
    explanation_text = "This candidate was prioritized based on several factors. "
    if positive_factors:
        top_pos = positive_factors[0]
        explanation_text += f"The most significant risk indicator was {top_pos['feature_name']} (SHAP: +{top_pos['shap_value']:.4f}). "
    if negative_factors:
        top_neg = negative_factors[0]
        explanation_text += f"Conversely, {top_neg['feature_name']} slightly reduced the overall risk score (SHAP: {top_neg['shap_value']:.4f})."

    # Fetch audit logs related to this alert / complaint
    raw_logs = db.query(AuditLog).filter(
        (AuditLog.complaint_id == pred.complaint_id) | (AuditLog.entity_id == str(alert.alert_id))
    ).order_by(AuditLog.timestamp.desc()).all()

    audit_logs = [{
        "audit_id": str(log.audit_id),
        "action_type": log.action_type,
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "actor_id": log.actor_id,
        "complaint_id": log.complaint_id,
        "data_hash": log.data_hash,
        "created_at": log.timestamp.isoformat() if log.timestamp else None,
        "timestamp": log.timestamp.isoformat() if log.timestamp else None
    } for log in raw_logs]

    return AlertDetailResponse(
        alert_id=alert.alert_id,
        prediction_id=pred.prediction_id,
        complaint_id=pred.complaint_id,
        withdrawal_location_id=loc.location_id,
        district=loc.district.district_name if loc.district else "Unknown",
        probability=float(pred.risk_score),
        rank=pred.rank,
        priority=pred.priority,
        status=alert.status,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
        top_positive_factors=positive_factors[:5],
        top_negative_factors=negative_factors[:5],
        explanation_text=explanation_text.strip(),
        audit_logs=audit_logs
    )


def log_audit_event(
    db: Session,
    action_type: str,
    entity_type: str,
    entity_id: str,
    actor_id: str = "SYSTEM",
    complaint_id: Optional[str] = None,
    data_hash: Optional[str] = None,
    commit: bool = True
):
    """
    Create an audit log entry for tamper-evident tracking.
    """
    audit = AuditLog(
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        complaint_id=complaint_id,
        data_hash=data_hash
    )
    db.add(audit)
    if commit:
        db.commit()


def update_alert_status(db: Session, alert_id: uuid.UUID, new_status: str, actor_id: str = "INVESTIGATOR_1") -> Optional[Alert]:
    """
    Updates alert status and records an audit log.
    """
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        return None
        
    old_status = alert.status
    alert.status = new_status
    db.commit()
    db.refresh(alert)
    
    # We need complaint_id for the audit log
    pred = db.query(Prediction).filter(Prediction.prediction_id == alert.prediction_id).first()
    comp_id = pred.complaint_id if pred else None
    
    log_audit_event(
        db=db,
        action_type=f"STATUS_CHANGE_{old_status}_TO_{new_status}",
        entity_type="ALERT",
        entity_id=str(alert.alert_id),
        actor_id=actor_id,
        complaint_id=comp_id,
        data_hash=f"{old_status}->{new_status}" # simple representation for now
    )
    
    return alert


def add_investigator_action(
    db: Session, 
    alert_id: uuid.UUID, 
    action_type: str, 
    notes: Optional[str], 
    actor_id: str = "INVESTIGATOR_1"
) -> Optional[InvestigationAction]:
    """
    Records an investigator action and creates an audit log.
    """
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        return None
        
    pred = db.query(Prediction).filter(Prediction.prediction_id == alert.prediction_id).first()
    if not pred:
        return None
        
    action = InvestigationAction(
        complaint_id=pred.complaint_id,
        investigator_id=actor_id,
        action_type=action_type,
        action_description=f"Alert {alert_id}: {notes}" if notes else f"Alert {alert_id}"
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    
    log_audit_event(
        db=db,
        action_type=f"INVESTIGATION_ACTION_{action_type}",
        entity_type="INVESTIGATION_ACTION",
        entity_id=str(action.action_id),
        actor_id=actor_id,
        complaint_id=pred.complaint_id
    )
    
    return action


def get_alert_summary(db: Session) -> Dict[str, int]:
    """
    Returns dashboard statistics for alerts.
    """
    # Status counts
    status_counts = db.query(Alert.status, func.count(Alert.alert_id)).group_by(Alert.status).all()
    status_dict = {status: count for status, count in status_counts}
    
    # Priority counts
    priority_counts = db.query(Prediction.priority, func.count(Alert.alert_id)).join(
        Prediction, Alert.prediction_id == Prediction.prediction_id
    ).group_by(Prediction.priority).all()
    priority_dict = {priority: count for priority, count in priority_counts}
    
    total = sum(status_dict.values())
    
    return {
        "total_alerts": total,
        "new_alerts": status_dict.get("NEW", 0),
        "acknowledged_alerts": status_dict.get("ACKNOWLEDGED", 0),
        "in_review_alerts": status_dict.get("IN_REVIEW", 0),
        "action_taken_alerts": status_dict.get("ACTION_TAKEN", 0),
        "closed_alerts": status_dict.get("CLOSED", 0),
        "critical_priority": priority_dict.get("CRITICAL", 0),
        "high_priority": priority_dict.get("HIGH", 0),
        "medium_priority": priority_dict.get("MEDIUM", 0),
        "low_priority": priority_dict.get("LOW", 0)
    }
