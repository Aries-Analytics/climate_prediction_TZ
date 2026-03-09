import pytest
from datetime import datetime, date
from app.models.model_metric import ModelMetric
from app.models.model_prediction import ModelPrediction
from app.services import model_service

@pytest.fixture
def sample_model_metrics(db):
    """Create sample model metrics"""
    metrics = [
        ModelMetric(
            model_name="model_a",
            r2_score=0.85,
            rmse=2.5,
            mae=1.8,
            mape=0.12,
            training_date=datetime.now(),
            experiment_id="exp_001"
        ),
        ModelMetric(
            model_name="model_b",
            r2_score=0.78,
            rmse=3.2,
            mae=2.1,
            mape=0.15,
            training_date=datetime.now(),
            experiment_id="exp_002"
        )
    ]
    
    for metric in metrics:
        db.add(metric)
    db.commit()
    
    return metrics

def test_get_model_metrics(db, sample_model_metrics):
    """Test getting model metrics"""
    metrics = model_service.get_model_metrics(db, "model_a")
    
    assert metrics is not None
    assert metrics.model_name == "model_a"
    assert metrics.r2_score == 0.85

def test_get_all_models(db, sample_model_metrics):
    """Test getting all models"""
    models = model_service.get_all_models(db)
    
    assert len(models) == 2
    assert any(m.model_name == "model_a" for m in models)
    assert any(m.model_name == "model_b" for m in models)

def test_compare_models(db, sample_model_metrics):
    """Test model comparison"""
    comparison = model_service.compare_models(db, ["model_a", "model_b"], "r2_score")
    
    assert comparison is not None
    assert len(comparison.models) == 2
    assert comparison.best_model == "model_a"  # Higher R² is better
    assert comparison.comparison_metric == "r2_score"

def test_models_list_endpoint(client, auth_headers, sample_model_metrics):
    """Test models list endpoint"""
    response = client.get("/api/models", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_model_metrics_endpoint(client, auth_headers, sample_model_metrics):
    """Test model metrics endpoint"""
    response = client.get("/api/models/model_a/metrics", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["modelName"] == "model_a"
    assert data["r2Score"] == 0.85

def test_model_not_found(client, auth_headers):
    """Test getting metrics for nonexistent model"""
    response = client.get("/api/models/nonexistent/metrics", headers=auth_headers)
    
    assert response.status_code == 404
