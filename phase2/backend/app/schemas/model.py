from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, Dict, Any

class ModelMetricsBase(BaseModel):
    model_name: str
    experiment_id: Optional[str] = None
    r2_score: Optional[float] = None
    rmse: Optional[float] = None
    mae: Optional[float] = None
    mape: Optional[float] = None
    training_date: datetime
    data_start_date: Optional[date] = None
    data_end_date: Optional[date] = None
    hyperparameters: Optional[Dict[str, Any]] = None

class ModelMetricsCreate(ModelMetricsBase):
    pass

class ModelMetricsResponse(ModelMetricsBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ModelPredictionBase(BaseModel):
    model_name: str
    prediction_date: date
    target_date: date
    predicted_value: Optional[float] = None
    actual_value: Optional[float] = None
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None

class ModelPredictionCreate(ModelPredictionBase):
    pass

class ModelPredictionResponse(ModelPredictionBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class FeatureImportance(BaseModel):
    feature_name: str
    importance: float
    rank: int

class ModelComparison(BaseModel):
    models: list[ModelMetricsResponse]
    best_model: str
    comparison_metric: str

class DriftStatus(BaseModel):
    model_name: str
    is_drifting: bool
    drift_score: float
    threshold: float
    recommendation: str
