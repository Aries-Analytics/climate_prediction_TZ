"""Data optimization utilities for chart rendering and large datasets."""

import numpy as np
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta


def downsample_timeseries(
    data: List[Dict[str, Any]], 
    max_points: int = 1000,
    date_field: str = "date",
    value_fields: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Downsample time series data to reduce number of points for chart rendering.
    
    Uses LTTB (Largest Triangle Three Buckets) algorithm for optimal visual representation.
    
    Args:
        data: List of data points with date and value fields
        max_points: Maximum number of points to return
        date_field: Name of the date field
        value_fields: List of value field names to preserve
        
    Returns:
        Downsampled data maintaining visual characteristics
    """
    if not data or len(data) <= max_points:
        return data
    
    if value_fields is None:
        # Auto-detect numeric fields
        value_fields = [k for k, v in data[0].items() 
                       if k != date_field and isinstance(v, (int, float))]
    
    # Sort by date
    sorted_data = sorted(data, key=lambda x: x[date_field])
    
    # Use LTTB algorithm for each value field
    result = []
    bucket_size = len(sorted_data) / max_points
    
    # Always include first point
    result.append(sorted_data[0])
    
    for i in range(1, max_points - 1):
        # Calculate bucket range
        bucket_start = int(i * bucket_size)
        bucket_end = int((i + 1) * bucket_size)
        
        if bucket_start >= len(sorted_data):
            break
            
        # Find point with largest triangle area
        max_area = -1
        max_idx = bucket_start
        
        # Previous point
        prev_point = result[-1]
        
        # Next bucket average (for triangle calculation)
        next_bucket_start = bucket_end
        next_bucket_end = min(int((i + 2) * bucket_size), len(sorted_data))
        
        if next_bucket_start < len(sorted_data):
            next_avg = {}
            for field in value_fields:
                values = [sorted_data[j].get(field, 0) 
                         for j in range(next_bucket_start, next_bucket_end)
                         if sorted_data[j].get(field) is not None]
                next_avg[field] = np.mean(values) if values else 0
            
            # Find point with largest area
            for j in range(bucket_start, bucket_end):
                if j >= len(sorted_data):
                    break
                    
                # Calculate triangle area for first value field
                if value_fields:
                    field = value_fields[0]
                    area = abs(
                        (prev_point.get(field, 0) - next_avg.get(field, 0)) *
                        (j - bucket_start) -
                        (prev_point.get(field, 0) - sorted_data[j].get(field, 0)) *
                        (next_bucket_start - bucket_start)
                    )
                    
                    if area > max_area:
                        max_area = area
                        max_idx = j
        
        result.append(sorted_data[max_idx])
    
    # Always include last point
    if len(sorted_data) > 0:
        result.append(sorted_data[-1])
    
    return result


def aggregate_by_time_window(
    data: List[Dict[str, Any]],
    window: str = "day",  # day, week, month
    date_field: str = "date",
    aggregation: str = "mean"  # mean, sum, min, max
) -> List[Dict[str, Any]]:
    """
    Aggregate data by time window to reduce data points.
    
    Args:
        data: List of data points
        window: Time window for aggregation (day, week, month)
        date_field: Name of the date field
        aggregation: Aggregation method
        
    Returns:
        Aggregated data
    """
    if not data:
        return []
    
    # Group by time window
    groups = {}
    
    for item in data:
        date = item[date_field]
        if isinstance(date, str):
            date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        
        # Determine window key
        if window == "day":
            key = date.date()
        elif window == "week":
            key = date.date() - timedelta(days=date.weekday())
        elif window == "month":
            key = date.replace(day=1).date()
        else:
            key = date.date()
        
        if key not in groups:
            groups[key] = []
        groups[key].append(item)
    
    # Aggregate each group
    result = []
    for key, group in sorted(groups.items()):
        aggregated = {date_field: key.isoformat()}
        
        # Get numeric fields
        numeric_fields = [k for k, v in group[0].items() 
                         if k != date_field and isinstance(v, (int, float))]
        
        for field in numeric_fields:
            values = [item.get(field) for item in group if item.get(field) is not None]
            
            if values:
                if aggregation == "mean":
                    aggregated[field] = np.mean(values)
                elif aggregation == "sum":
                    aggregated[field] = np.sum(values)
                elif aggregation == "min":
                    aggregated[field] = np.min(values)
                elif aggregation == "max":
                    aggregated[field] = np.max(values)
                else:
                    aggregated[field] = np.mean(values)
        
        result.append(aggregated)
    
    return result


def paginate_data(
    data: List[Any],
    page: int = 1,
    page_size: int = 100
) -> Tuple[List[Any], Dict[str, Any]]:
    """
    Paginate data for efficient loading.
    
    Args:
        data: List of data items
        page: Page number (1-indexed)
        page_size: Number of items per page
        
    Returns:
        Tuple of (paginated_data, pagination_metadata)
    """
    total_items = len(data)
    total_pages = (total_items + page_size - 1) // page_size
    
    # Validate page number
    page = max(1, min(page, total_pages if total_pages > 0 else 1))
    
    # Calculate slice indices
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_items)
    
    # Get page data
    page_data = data[start_idx:end_idx]
    
    # Create metadata
    metadata = {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1
    }
    
    return page_data, metadata


def optimize_for_chart(
    data: List[Dict[str, Any]],
    max_points: int = 1000,
    date_field: str = "date"
) -> List[Dict[str, Any]]:
    """
    Optimize data for chart rendering by downsampling if needed.
    
    Args:
        data: Raw data points
        max_points: Maximum points for chart
        date_field: Date field name
        
    Returns:
        Optimized data for chart rendering
    """
    if len(data) <= max_points:
        return data
    
    # Use downsampling for large datasets
    return downsample_timeseries(data, max_points, date_field)


def calculate_statistics(data: List[Dict[str, Any]], field: str) -> Dict[str, float]:
    """
    Calculate statistics for a numeric field.
    
    Args:
        data: List of data points
        field: Field name to calculate statistics for
        
    Returns:
        Dictionary with statistics (mean, median, std, min, max)
    """
    values = [item.get(field) for item in data if item.get(field) is not None]
    
    if not values:
        return {
            "mean": 0,
            "median": 0,
            "std": 0,
            "min": 0,
            "max": 0,
            "count": 0
        }
    
    return {
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "std": float(np.std(values)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "count": len(values)
    }
