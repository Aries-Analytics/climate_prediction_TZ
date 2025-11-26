"""Test script to verify recommendations API response"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.database import SessionLocal
from app.services.forecast_service import get_recommendations
import json

db = SessionLocal()

try:
    # Get recommendations
    forecasts_with_recs = get_recommendations(db, min_probability=0.3)
    
    print(f"Total forecasts with recommendations: {len(forecasts_with_recs)}")
    print("\n" + "="*60)
    
    for forecast in forecasts_with_recs[:3]:  # Show first 3
        print(f"\nForecast ID: {forecast.id}")
        print(f"Trigger Type: {forecast.trigger_type}")
        print(f"Probability: {forecast.probability}")
        print(f"Number of recommendations: {len(forecast.recommendations)}")
        
        for rec in forecast.recommendations:
            print(f"\n  Recommendation ID: {rec.id}")
            print(f"  Priority: {rec.priority}")
            print(f"  Text: {rec.recommendation_text[:80]}...")
            print(f"  Timeline: {rec.action_timeline}")
    
    # Test serialization
    print("\n" + "="*60)
    print("Testing Pydantic serialization...")
    
    from app.schemas.forecast import ForecastWithRecommendations as ForecastSchema
    
    if forecasts_with_recs:
        schema_obj = ForecastSchema.model_validate(forecasts_with_recs[0])
        json_data = schema_obj.model_dump(by_alias=True)
        
        print(f"\nSerialized forecast keys: {list(json_data.keys())}")
        print(f"Recommendations count: {len(json_data.get('recommendations', []))}")
        
        if json_data.get('recommendations'):
            rec = json_data['recommendations'][0]
            print(f"\nFirst recommendation keys: {list(rec.keys())}")
            print(f"Recommendation text: {rec.get('recommendationText', 'MISSING')[:80]}...")
            print(f"Action timeline: {rec.get('actionTimeline', 'MISSING')}")
            print(f"Priority: {rec.get('priority', 'MISSING')}")
        
        print("\n" + "="*60)
        print("Full JSON output:")
        print(json.dumps(json_data, indent=2, default=str))
        
finally:
    db.close()
