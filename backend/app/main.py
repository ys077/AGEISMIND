from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import health, complaints, withdrawal_locations, historical_cases, cases, analysis, money_flow, network_analysis, time_geography, predictions, explainability, risk_heatmap, alerts, dashboard, notifications

app = FastAPI(
    title="Cybercrime Cash Withdrawal Prediction System Mock API",
    description="Mock API layer over Tamil Nadu synthetic PostgreSQL data. ALL DATA IS SYNTHETIC PROTOTYPE DATA.",
    version="1.0.0",
)

# Set up CORS
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router, prefix="/api")
app.include_router(complaints.router, prefix="/api")
app.include_router(withdrawal_locations.router, prefix="/api")
app.include_router(historical_cases.router, prefix="/api")
app.include_router(cases.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(money_flow.router, prefix="/api")
app.include_router(network_analysis.router, prefix="/api")
app.include_router(time_geography.router, prefix="/api")
app.include_router(predictions.router, prefix="/api")
app.include_router(explainability.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(notifications.router, prefix="/api/notifications")
app.include_router(risk_heatmap.router, prefix="/api/risk-heatmap", tags=["Risk Heatmap"])

@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": "Welcome to the Cybercrime Cash Withdrawal Prediction System API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "note": "ALL DATA IS SYNTHETIC PROTOTYPE DATA."
    }
