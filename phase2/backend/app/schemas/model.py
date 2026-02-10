from pydantic import BaseModel, Field, ConfigDict
from datetime import date, datetime
from typing import Optional, Dict, Any

class ModelMetricsBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    model_name: str = Field(..., serialization_alias="modelName")
    experiment_id: Optional[str] = Field(None, serialization_alias="experimentId")
    r2_score: Optional[float] = Field(None, serialization_alias="r2Score")
    rmse: Optional[float] = None
    mae: Optional[float] = None
    mape: Optional[float] = None
    training_date: datetime = Field(..., serialization_alias="trainingDate")
    data_start_date: Optional[date] = Field(None, serialization_alias="dataStartDate")
    data_end_date: Optional[date] = Field(None, serialization_alias="dataEndDate")
    hyperparameters: Optional[Dict[str, Any]] = None
    
    # Cross-validation metrics (more reliable)
    cv_r2_mean: Optional[float] = Field(None, serialization_alias="cvR2Mean")
    cv_r2_std: Optional[float] = Field(None, serialization_alias="cvR2Std")
    cv_r2_ci_lower: Optional[float] = Field(None, serialization_alias="cvR2CiLower")
    cv_r2_ci_upper: Optional[float] = Field(None, serialization_alias="cvR2CiUpper")
    cv_rmse_mean: Optional[float] = Field(None, serialization_alias="cvRmseMean")
    cv_rmse_std: Optional[float] = Field(None, serialization_alias="cvRmseStd")
    cv_mae_mean: Optional[float] = Field(None, serialization_alias="cvMaeMean")
    cv_mae_std: Optional[float] = Field(None, serialization_alias="cvMaeStd")
    cv_n_splits: Optional[int] = Field(None, serialization_alias="cvNSplits")
    
    # Feature selection info
    n_features: Optional[int] = Field(None, serialization_alias="nFeatures")
    feature_to_sample_ratio: Optional[float] = Field(None, serialization_alias="featureToSampleRatio")
    
    # Sample counts (from training data)
    n_train_samples: Optional[int] = Field(None, serialization_alias="trainingSamples")
    n_val_samples: Optional[int] = Field(None, serialization_alias="valSamples")
    n_test_samples: Optional[int] = Field(None, serialization_alias="testSamples")

class ModelMetricsCreate(ModelMetricsBase):
    pass

class ModelMetricsResponse(ModelMetricsBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    id: int
    created_at: datetime = Field(..., serialization_alias="createdAt")

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
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    id: int
    created_at: datetime = Field(..., serialization_alias="createdAt")

class FeatureImportance(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    feature_name: str = Field(..., serialization_alias="featureName")
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
