import os
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# -------------------------------------------------------------------
# 1. DATABASE SETUP & CONNECTION MANAGEMENT
# -------------------------------------------------------------------
DATABASE_URL = "sqlite:///./backend_app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Schema Tables
class IncidentDB(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), default="LOW")
    created_at = Column(DateTime, default=datetime.utcnow)

class PredictionDB(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    input_val = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    prediction_label = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AlertDB(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    triggered_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------------------------------------------
# 2. AI/ML MODEL INTEGRATION MODULE
# -------------------------------------------------------------------
class MachineLearningModel:
    """Wrapper for AI/ML Model inference integration."""
    def predict(self, feature_value: float) -> dict:
        # Example model inference computation
        score = min(max(feature_value / 100.0, 0.0), 1.0)
        label = "HIGH_RISK" if score >= 0.75 else "NORMAL"
        return {"risk_score": score, "label": label}

ml_model = MachineLearningModel()

# -------------------------------------------------------------------
# 3. FASTAPI APPLICATION & FRONTEND CORS SETTINGS
# -------------------------------------------------------------------
app = FastAPI(title="OM Backend Service API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Enable communication with frontend web apps
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request / Response Schemas
class PredictionRequest(BaseModel):
    feature_value: float = Field(..., example=88.5)

class PredictionResponse(BaseModel):
    id: int
    risk_score: float
    prediction_label: str
    alert_triggered: bool

class IncidentCreate(BaseModel):
    title: str
    description: str
    severity: str = Field(default="LOW", example="HIGH")

class IncidentResponse(BaseModel):
    id: int
    title: str
    description: str
    severity: str
    created_at: datetime
    class Config:
        orm_mode = True

# -------------------------------------------------------------------
# 4. BACKEND ALERT SYSTEM LOGIC
# -------------------------------------------------------------------
def trigger_alert_system(db: Session, alert_type: str, message: str) -> AlertDB:
    """Executes backend alert dispatch and logs the alert to the database."""
    alert_entry = AlertDB(alert_type=alert_type, message=message)
    db.add(alert_entry)
    db.commit()
    db.refresh(alert_entry)
    
    # Business logic for downstream notifications (e.g., WebSockets, Email, SMS)
    print(f"[SYSTEM ALERT ACTIVE]: {alert_type} - {message}")
    return alert_entry

# -------------------------------------------------------------------
# 5. API ENDPOINTS (PREDICTION & INCIDENT REPORTING)
# -------------------------------------------------------------------
@app.post("/api/v1/predict", response_model=PredictionResponse)
def execute_prediction(payload: PredictionRequest, db: Session = Depends(get_db)):
    """Accepts frontend data, passes it to the AI model, logs results, and triggers alerts."""
    # 1. Run AI/ML Prediction
    ml_result = ml_model.predict(payload.feature_value)
    
    # 2. Save prediction results to DB
    prediction_record = PredictionDB(
        input_val=payload.feature_value,
        risk_score=ml_result["risk_score"],
        prediction_label=ml_result["label"]
    )
    db.add(prediction_record)
    db.commit()
    db.refresh(prediction_record)
    
    # 3. Backend Alert logic check
    alert_flag = False
    if ml_result["risk_score"] >= 0.75:
        trigger_alert_system(
            db=db,
            alert_type="CRITICAL_RISK_PREDICTION",
            message=f"Model calculated an elevated risk score: {ml_result['risk_score']}"
        )
        alert_flag = True

    # 4. Return results back to frontend
    return PredictionResponse(
        id=prediction_record.id,
        risk_score=prediction_record.risk_score,
        prediction_label=prediction_record.prediction_label,
        alert_triggered=alert_flag
    )

@app.post("/api/v1/incidents", response_model=IncidentResponse)
def create_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    """Saves new incident reports to the database and evaluates alert conditions."""
    new_incident = IncidentDB(
        title=incident.title,
        description=incident.description,
        severity=incident.severity.upper()
    )
    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)

    # Incident Alert evaluation
    if new_incident.severity in ["HIGH", "CRITICAL"]:
        trigger_alert_system(
            db=db,
            alert_type="INCIDENT_SEVERITY_ALERT",
            message=f"Incident #{new_incident.id} logged with critical severity level: {new_incident.severity}"
        )

    return new_incident

@app.get("/api/v1/incidents", response_model=List[IncidentResponse])
def get_incident_reports(db: Session = Depends(get_db)):
    """Fetches all reported incidents stored in the database."""
    return db.query(IncidentDB).all()
  
