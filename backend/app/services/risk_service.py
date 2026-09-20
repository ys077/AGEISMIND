"""
Authoritative risk service for the AGEISMIND application.
Provides a single source of truth for risk-level classification across
both prediction engines and user interfaces.
"""

RISK_THRESHOLDS = {
    "CRITICAL": 0.75,
    "HIGH": 0.50,
    "MEDIUM": 0.25
}

def get_risk_level(probability: float) -> str:
    """
    Authoritative risk classification used system-wide.
    Returns one of: CRITICAL, HIGH, MEDIUM, LOW based on the probability.
    """
    if probability >= RISK_THRESHOLDS["CRITICAL"]:
        return "CRITICAL"
    if probability >= RISK_THRESHOLDS["HIGH"]:
        return "HIGH"
    if probability >= RISK_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    return "LOW"
