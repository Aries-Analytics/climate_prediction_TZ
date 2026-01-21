"""
Validate trigger activation against known Tanzania climate events.

This script checks if insurance triggers correctly activate during documented
extreme weather events in Tanzania (2000-2023).
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Known extreme weather events in Tanzania (2000-2023)
# Sources: Tanzania Meteorological Authority, EM-DAT, ReliefWeb
KNOWN_EVENTS = {
    'floods': [
        {'year': 2006, 'month': 12, 'event': 'December 2006 floods', 'severity': 'severe'},
        {'year': 2018, 'month': 4, 'event': 'April 2018 floods (Dar es Salaam)', 'severity': 'severe'},
        {'year': 2019, 'month': 12, 'event': 'December 2019 floods', 'severity': 'moderate'},
        {'year': 2020, 'month': 3, 'event': 'March 2020 floods', 'severity': 'severe'},
        {'year': 2020, 'month': 4, 'event': 'April 2020 floods', 'severity': 'moderate'},
        {'year': 2022, 'month': 1, 'event': 'January 2022 floods', 'severity': 'severe'},
        {'year': 2022, 'month': 2, 'event': 'February 2022 floods', 'severity': 'severe'},
    ],
    'droughts': [
        {'year': 2005, 'month': 12, 'event': '2005-2006 drought', 'severity': 'severe'},
        {'year': 2006, 'month': 1, 'event': '2005-2006 drought', 'severity': 'severe'},
        {'year': 2016, 'month': 12, 'event': '2016-2017 drought (El Niño)', 'severity': 'severe'},
        {'year': 2017, 'month': 1, 'event': '2016-2017 drought (El Niño)', 'severity': 'severe'},
        {'year': 2017, 'month': 2, 'event': '2016-2017 drought (El Niño)', 'severity': 'moderate'},
    ]
}


def load_processed_data():
    """Load processed CHIRPS and NDVI data."""
    chirps_path = Path('outputs/processed/chirps_processed.csv')
    ndvi_path = Path('outputs/processed/ndvi_processed.csv')
    
    if not chirps_path.exists():
        raise FileNotFoundError(f"Processed CHIRPS data not found: {chirps_path}")
    
    if not ndvi_path.exists():
        raise FileNotFoundError(f"Processed NDVI data not found: {ndvi_path}")
    
    chirps_df = pd.read_csv(chirps_path)
    ndvi_df = pd.read_csv(ndvi_path)
    
    return chirps_df, ndvi_df


def validate_flood_events(df, known_floods):
    """
    Validate that flood triggers activate during known flood events.
    
    Returns:
        dict: Validation results with detection rates and details
    """
    print("\n" + "="*70)
    print("FLOOD EVENT VALIDATION")
    print("="*70)
    
    results = {
        'total_events': len(known_floods),
        'detected_events': 0,
        'missed_events': 0,
        'details': []
    }
    
    for event in known_floods:
        year = event['year']
        month = event['month']
        event_name = event['event']
        severity = event['severity']
        
        # Find matching record
        match = df[(df['year'] == year) & (df['month'] == month)]
        
        if len(match) == 0:
            print(f"\n⚠️  {event_name} ({year}-{month:02d})")
            print(f"    No data available for this period")
            results['details'].append({
                'event': event_name,
                'year': year,
                'month': month,
                'severity': severity,
                'detected': False,
                'reason': 'No data'
            })
            continue
        
        record = match.iloc[0]
        triggered = bool(record['flood_trigger'])
        confidence = record.get('flood_trigger_confidence', 0)
        rainfall = record['rainfall_mm']
        rainfall_7day = record['rainfall_7day']
        
        if triggered:
            results['detected_events'] += 1
            print(f"\n✓ {event_name} ({year}-{month:02d})")
            print(f"    Severity: {severity}")
            print(f"    Trigger: ACTIVATED (confidence: {confidence:.2f})")
            print(f"    Rainfall: {rainfall:.1f} mm (7-day: {rainfall_7day:.1f} mm)")
            
            results['details'].append({
                'event': event_name,
                'year': year,
                'month': month,
                'severity': severity,
                'detected': True,
                'confidence': confidence,
                'rainfall_mm': rainfall,
                'rainfall_7day': rainfall_7day
            })
        else:
            results['missed_events'] += 1
            print(f"\n✗ {event_name} ({year}-{month:02d})")
            print(f"    Severity: {severity}")
            print(f"    Trigger: NOT ACTIVATED")
            print(f"    Rainfall: {rainfall:.1f} mm (7-day: {rainfall_7day:.1f} mm)")
            print(f"    Note: May be due to monthly aggregation or event timing")
            
            results['details'].append({
                'event': event_name,
                'year': year,
                'month': month,
                'severity': severity,
                'detected': False,
                'rainfall_mm': rainfall,
                'rainfall_7day': rainfall_7day
            })
    
    # Calculate detection rate
    detection_rate = results['detected_events'] / results['total_events'] if results['total_events'] > 0 else 0
    results['detection_rate'] = detection_rate
    
    print(f"\n{'='*70}")
    print(f"FLOOD DETECTION SUMMARY")
    print(f"{'='*70}")
    print(f"Total known flood events: {results['total_events']}")
    print(f"Events detected: {results['detected_events']}")
    print(f"Events missed: {results['missed_events']}")
    print(f"Detection rate: {detection_rate:.1%}")
    
    return results


def validate_drought_events(df, known_droughts):
    """
    Validate that drought triggers activate during known drought events.
    
    Returns:
        dict: Validation results with detection rates and details
    """
    print("\n" + "="*70)
    print("DROUGHT EVENT VALIDATION")
    print("="*70)
    
    results = {
        'total_events': len(known_droughts),
        'detected_events': 0,
        'missed_events': 0,
        'details': []
    }
    
    for event in known_droughts:
        year = event['year']
        month = event['month']
        event_name = event['event']
        severity = event['severity']
        
        # Find matching record
        match = df[(df['year'] == year) & (df['month'] == month)]
        
        if len(match) == 0:
            print(f"\n⚠️  {event_name} ({year}-{month:02d})")
            print(f"    No data available for this period")
            results['details'].append({
                'event': event_name,
                'year': year,
                'month': month,
                'severity': severity,
                'detected': False,
                'reason': 'No data'
            })
            continue
        
        record = match.iloc[0]
        triggered = bool(record['drought_trigger'])
        confidence = record.get('drought_trigger_confidence', 0)
        spi = record['spi_30day']
        rainfall = record['rainfall_mm']
        
        if triggered:
            results['detected_events'] += 1
            print(f"\n✓ {event_name} ({year}-{month:02d})")
            print(f"    Severity: {severity}")
            print(f"    Trigger: ACTIVATED (confidence: {confidence:.2f})")
            print(f"    SPI-30: {spi:.2f}, Rainfall: {rainfall:.1f} mm")
            
            results['details'].append({
                'event': event_name,
                'year': year,
                'month': month,
                'severity': severity,
                'detected': True,
                'confidence': confidence,
                'spi_30day': spi,
                'rainfall_mm': rainfall
            })
        else:
            results['missed_events'] += 1
            print(f"\n✗ {event_name} ({year}-{month:02d})")
            print(f"    Severity: {severity}")
            print(f"    Trigger: NOT ACTIVATED")
            print(f"    SPI-30: {spi:.2f}, Rainfall: {rainfall:.1f} mm")
            print(f"    Note: SPI may not indicate drought at this specific location/month")
            
            results['details'].append({
                'event': event_name,
                'year': year,
                'month': month,
                'severity': severity,
                'detected': False,
                'spi_30day': spi,
                'rainfall_mm': rainfall
            })
    
    # Calculate detection rate
    detection_rate = results['detected_events'] / results['total_events'] if results['total_events'] > 0 else 0
    results['detection_rate'] = detection_rate
    
    print(f"\n{'='*70}")
    print(f"DROUGHT DETECTION SUMMARY")
    print(f"{'='*70}")
    print(f"Total known drought events: {results['total_events']}")
    print(f"Events detected: {results['detected_events']}")
    print(f"Events missed: {results['missed_events']}")
    print(f"Detection rate: {detection_rate:.1%}")
    
    return results


def generate_validation_report(flood_results, drought_results):
    """Generate a summary validation report."""
    print("\n" + "="*70)
    print("OVERALL VALIDATION SUMMARY")
    print("="*70)
    
    total_events = flood_results['total_events'] + drought_results['total_events']
    total_detected = flood_results['detected_events'] + drought_results['detected_events']
    overall_rate = total_detected / total_events if total_events > 0 else 0
    
    print(f"\nTotal known events validated: {total_events}")
    print(f"  - Flood events: {flood_results['total_events']}")
    print(f"  - Drought events: {drought_results['total_events']}")
    
    print(f"\nTotal events detected: {total_detected}")
    print(f"  - Floods detected: {flood_results['detected_events']}/{flood_results['total_events']} ({flood_results['detection_rate']:.1%})")
    print(f"  - Droughts detected: {drought_results['detected_events']}/{drought_results['total_events']} ({drought_results['detection_rate']:.1%})")
    
    print(f"\nOverall detection rate: {overall_rate:.1%}")
    
    # Assessment
    print(f"\n{'='*70}")
    print("ASSESSMENT")
    print("="*70)
    
    if overall_rate >= 0.70:
        print("✓ EXCELLENT: Triggers successfully detect most known extreme events")
    elif overall_rate >= 0.50:
        print("✓ GOOD: Triggers detect majority of known extreme events")
    elif overall_rate >= 0.30:
        print("⚠ FAIR: Triggers detect some known events, may need refinement")
    else:
        print("✗ POOR: Triggers miss most known events, calibration needs review")
    
    print("\nNotes:")
    print("- Monthly aggregated data may miss sub-monthly events")
    print("- Point location data may not capture regional events")
    print("- Some events may occur outside the specific location coordinates")
    print("- Detection rate >50% is considered acceptable for monthly data")
    
    return {
        'total_events': total_events,
        'total_detected': total_detected,
        'overall_detection_rate': overall_rate,
        'flood_results': flood_results,
        'drought_results': drought_results
    }


def main():
    """Main validation workflow."""
    print("="*70)
    print("KNOWN EVENT VALIDATION")
    print("="*70)
    print("\nValidating insurance triggers against documented extreme weather")
    print("events in Tanzania (2000-2023)")
    
    # Load data
    print("\nLoading processed data...")
    chirps_df, ndvi_df = load_processed_data()
    print(f"  CHIRPS: {len(chirps_df)} records")
    print(f"  NDVI: {len(ndvi_df)} records")
    
    # Validate flood events
    flood_results = validate_flood_events(chirps_df, KNOWN_EVENTS['floods'])
    
    # Validate drought events
    drought_results = validate_drought_events(chirps_df, KNOWN_EVENTS['droughts'])
    
    # Generate overall report
    overall_results = generate_validation_report(flood_results, drought_results)
    
    # Save results
    results_path = Path('outputs/validation_results.json')
    import json
    with open(results_path, 'w') as f:
        # Convert numpy types to native Python types for JSON serialization
        def convert_types(obj):
            if isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_types(item) for item in obj]
            return obj
        
        json.dump(convert_types(overall_results), f, indent=2)
    
    print(f"\n✓ Validation results saved to: {results_path}")
    
    return overall_results


if __name__ == '__main__':
    main()
