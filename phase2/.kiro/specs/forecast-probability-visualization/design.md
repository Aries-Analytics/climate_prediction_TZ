# Design Document

## Overview

This design addresses critical visualization issues in the Forecast Probability Timeline chart. The current implementation incorrectly renders forecast probability data as scattered dots at 100% instead of continuous trend lines showing probability distributions over time. Additionally, a legend interaction bug causes the legend to disappear when users double-click to isolate series, with no recovery mechanism.

The root causes are:
1. **Data Structure Mismatch**: The chart receives forecast data with sparse date coverage, causing Plotly to render disconnected markers instead of lines
2. **Missing Line Mode Configuration**: The scatter plot mode is set to 'lines+markers' but the data structure doesn't support continuous line rendering
3. **Legend Configuration Gap**: Plotly's default legend behavior allows hiding all items, which removes the legend entirely from the DOM
4. **State Management Issue**: No mechanism exists to track or restore legend visibility state

## Architecture

### Component Structure

```
ForecastDashboard (Container)
├── Chart (Plotly Wrapper)
│   └── react-plotly.js
├── Data Preparation Layer
│   ├── timelineData (forecast series)
│   └── historicalData (actual events)
└── State Management
    ├── forecasts
    ├── historicalTriggers
    ├── filters (type, horizon)
    └── legendState (new)
```

### Data Flow

```
API Response → Data Transformation → Chart Configuration → Plotly Rendering
     ↓              ↓                      ↓                    ↓
  Forecasts    Group by type/horizon   Trace objects      Interactive chart
                Sort chronologically    + Layout config    + Legend controls
```

## Components and Interfaces

### 1. Enhanced Chart Data Preparation

**Purpose**: Transform forecast API responses into properly structured Plotly traces with continuous line rendering

**Interface**:
```typescript
interface ForecastTrace {
  x: string[]           // Sorted dates
  y: number[]           // Probability values [0-1]
  error_y: ErrorBar     // Confidence intervals
  type: 'scatter'
  mode: 'lines+markers' | 'markers'  // Conditional based on data density
  name: string          // e.g., "drought (3mo)"
  line: LineStyle
  marker: MarkerStyle
  visible: boolean | 'legendonly'  // Legend state
  hovertemplate: string
  customdata: any[][]
}

interface ErrorBar {
  type: 'data'
  symmetric: false
  array: number[]       // Upper bound deltas
  arrayminus: number[]  // Lower bound deltas
  color: string
  thickness: number
  width: number
}
```

**Key Changes**:
- Sort forecast data by `targetDate` before creating traces
- Use `mode: 'lines+markers'` only when 2+ consecutive dates exist
- Use `mode: 'markers'` for single-point series
- Set `connectgaps: false` to avoid connecting non-consecutive data

### 2. Legend State Management

**Purpose**: Prevent legend disappearance and provide reset functionality

**Interface**:
```typescript
interface LegendState {
  [seriesName: string]: boolean | 'legendonly'
}

interface ChartControls {
  onResetView: () => void
  legendState: LegendState
  onLegendClick: (seriesName: string) => void
}
```

**Implementation Strategy**:
- Track visibility state for each series in React state
- Configure Plotly with `showlegend: true` (always)
- Use `visible: true | false | 'legendonly'` on traces
- Add "Reset View" button to restore all series

### 3. Plotly Configuration Updates

**Layout Configuration**:
```typescript
const layout = {
  height: 500,
  xaxis: {
    title: 'Target Date',
    type: 'date',
    autorange: true
  },
  yaxis: {
    title: 'Trigger Probability',
    tickformat: '.0%',
    range: [0, 1],
    fixedrange: false
  },
  hovermode: 'closest',
  legend: {
    orientation: 'h',
    y: -0.2,
    x: 0,
    xanchor: 'left',
    bgcolor: 'rgba(255,255,255,0.9)',
    bordercolor: '#ccc',
    borderwidth: 1,
    // Prevent legend from disappearing
    itemclick: 'toggle',      // Single click toggles
    itemdoubleclick: 'toggleothers'  // Double click isolates
  },
  // ... rest of layout
}
```

**Config Options**:
```typescript
const config = {
  responsive: true,
  displayModeBar: true,
  displaylogo: false,
  modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
  // Ensure legend interactions work properly
  editable: false,
  scrollZoom: true
}
```

## Data Models

### Forecast Data Structure

**Current API Response**:
```typescript
interface Forecast {
  id: number
  forecastDate: string      // When forecast was made
  targetDate: string        // Date being predicted
  horizonMonths: number     // 3, 4, 5, or 6
  triggerType: string       // 'drought' | 'flood' | 'crop_failure'
  probability: number       // 0.0 to 1.0
  confidenceLower: number   // Lower CI bound
  confidenceUpper: number   // Upper CI bound
  modelVersion: string
  createdAt: string
}
```

**Transformed Chart Data**:
```typescript
interface ChartSeries {
  triggerType: string
  horizonMonths: number
  dataPoints: Array<{
    date: string
    probability: number
    confidenceLower: number
    confidenceUpper: number
  }>
}
```

### Historical Trigger Data

```typescript
interface TriggerEvent {
  id: number
  date: string
  triggerType: string
  confidence: number
  severity: number
}

interface HistoricalMarker {
  x: string[]
  y: number[]  // Always 1.0 (100%)
  type: 'scatter'
  mode: 'markers'
  marker: {
    symbol: 'x'
    size: 12
    color: string
  }
  name: string
  showlegend: boolean
}
```

## Correctne
ss Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Property 1: Multi-point series render as lines
*For any* forecast series with 2 or more chronologically sorted data points, the resulting Plotly trace should have mode set to 'lines+markers' and x/y arrays should be in chronological order
**Validates: Requirements 1.1**

Property 2: Single-point series render as markers only
*For any* forecast series with exactly 1 data point, the resulting Plotly trace should have mode set to 'markers' (not 'lines+markers')
**Validates: Requirements 1.2**

Property 3: Horizon differentiation through line styles
*For any* trigger type with multiple forecast horizons, each horizon's trace should have a unique line dash style (solid, dash, dot, or dashdot)
**Validates: Requirements 1.4**

Property 4: Series visibility preservation
*For any* series with data points, the trace should have a visible property that is never undefined, ensuring the series can be toggled via legend
**Validates: Requirements 1.5**

Property 5: Legend persistence across interactions
*For any* sequence of legend click events (single or double), the legend element should remain present in the DOM with showlegend: true
**Validates: Requirements 2.5**

Property 6: Gap handling in sparse data
*For any* forecast series with non-consecutive dates (gaps > 1 day), the trace should have connectgaps set to false to avoid drawing lines across missing data
**Validates: Requirements 3.1**

Property 7: Empty series exclusion
*For any* combination of trigger type and horizon with zero data points, no trace should be created in the chart data array
**Validates: Requirements 3.2**

Property 8: Historical marker differentiation
*For any* historical trigger event, the trace should use marker symbol 'x' and the legend label should include "(actual)" to distinguish from forecasts
**Validates: Requirements 3.4**

Property 9: Filter consistency
*For any* filter combination (trigger type and/or horizon), all traces in the resulting chart data should match the filter criteria
**Validates: Requirements 3.5**

Property 10: Error bar presence
*For any* forecast data point with confidence intervals, the trace should have an error_y object with array and arrayminus properties containing the correct delta values
**Validates: Requirements 4.1**

Property 11: Array length consistency
*For any* trace in the chart data, the lengths of x, y, and customdata arrays should be equal
**Validates: Requirements 5.2**

## Error Handling

### Data Validation Errors

**Scenario**: API returns forecasts with invalid probability values (< 0 or > 1)
**Handling**: 
- Filter out invalid data points during transformation
- Log warning with forecast ID and invalid value
- Continue rendering valid data points

**Scenario**: Forecast data has mismatched array lengths (x.length !== y.length)
**Handling**:
- Truncate arrays to shortest length
- Log error with series name and array lengths
- Render truncated data to avoid Plotly errors

### Chart Rendering Errors

**Scenario**: Plotly throws error during render (e.g., invalid trace configuration)
**Handling**:
- Catch error in React error boundary
- Display user-friendly error message: "Unable to render chart. Please try refreshing."
- Log full error details to console for debugging

**Scenario**: Legend interaction causes unexpected state
**Handling**:
- Validate legend state before applying to traces
- Reset to default state (all visible) if invalid
- Log warning about state reset

### Network Errors

**Scenario**: Forecast API request fails
**Handling**:
- Display existing cached data if available
- Show error alert: "Failed to fetch latest forecasts"
- Provide retry button

**Scenario**: Historical triggers API request fails
**Handling**:
- Render forecast data without historical markers
- Log warning about missing historical data
- Do not block chart rendering

## Testing Strategy

### Unit Testing

**Framework**: Jest + React Testing Library

**Test Coverage**:
1. Data transformation functions
   - `prepareForecastTraces()` - transforms API data to Plotly traces
   - `prepareHistoricalMarkers()` - transforms trigger events to markers
   - `filterForecastData()` - applies trigger type and horizon filters
   - `sortChronologically()` - sorts data points by date

2. Utility functions
   - `determineTraceMode()` - returns 'lines+markers' or 'markers' based on data density
   - `calculateErrorBars()` - computes error bar arrays from confidence intervals
   - `validateTraceData()` - checks array length consistency

3. Component rendering
   - Chart renders with valid forecast data
   - Chart renders with empty data (shows empty state)
   - Chart renders with mixed forecast and historical data
   - Legend remains visible after interactions

**Example Unit Test**:
```typescript
describe('prepareForecastTraces', () => {
  it('should create line traces for multi-point series', () => {
    const forecasts = [
      { targetDate: '2024-01-01', triggerType: 'drought', horizonMonths: 3, probability: 0.2 },
      { targetDate: '2024-01-15', triggerType: 'drought', horizonMonths: 3, probability: 0.3 }
    ]
    const traces = prepareForecastTraces(forecasts)
    expect(traces[0].mode).toBe('lines+markers')
    expect(traces[0].x).toEqual(['2024-01-01', '2024-01-15'])
  })
})
```

### Property-Based Testing

**Framework**: fast-check (JavaScript property testing library)

**Property Tests**:

Each property test will run a minimum of 100 iterations with randomly generated data to verify correctness across a wide range of inputs.

**Test 1: Multi-point series mode**
- **Feature: forecast-probability-visualization, Property 1: Multi-point series render as lines**
- Generate: Random forecast arrays with 2-10 data points per series
- Verify: All resulting traces have mode 'lines+markers' and sorted x arrays

**Test 2: Single-point series mode**
- **Feature: forecast-probability-visualization, Property 2: Single-point series render as markers only**
- Generate: Random forecast arrays with exactly 1 data point per series
- Verify: All resulting traces have mode 'markers'

**Test 3: Horizon line style uniqueness**
- **Feature: forecast-probability-visualization, Property 3: Horizon differentiation through line styles**
- Generate: Random forecasts with all 4 horizons for same trigger type
- Verify: Each horizon has unique dash style

**Test 4: Array length consistency**
- **Feature: forecast-probability-visualization, Property 11: Array length consistency**
- Generate: Random forecast data with varying numbers of points
- Verify: For all traces, x.length === y.length === customdata.length

**Test 5: Empty series filtering**
- **Feature: forecast-probability-visualization, Property 7: Empty series exclusion**
- Generate: Random forecast data including some empty series
- Verify: No traces exist for series with zero data points

**Test 6: Filter correctness**
- **Feature: forecast-probability-visualization, Property 9: Filter consistency**
- Generate: Random forecast data and random filter combinations
- Verify: All traces match the applied filters

**Example Property Test**:
```typescript
import fc from 'fast-check'

describe('Property: Array length consistency', () => {
  it('should maintain equal array lengths across all traces', () => {
    fc.assert(
      fc.property(
        fc.array(fc.record({
          targetDate: fc.date(),
          triggerType: fc.constantFrom('drought', 'flood', 'crop_failure'),
          horizonMonths: fc.constantFrom(3, 4, 5, 6),
          probability: fc.float({ min: 0, max: 1 }),
          confidenceLower: fc.float({ min: 0, max: 1 }),
          confidenceUpper: fc.float({ min: 0, max: 1 })
        }), { minLength: 1, maxLength: 50 }),
        (forecasts) => {
          const traces = prepareForecastTraces(forecasts)
          return traces.every(trace => 
            trace.x.length === trace.y.length &&
            trace.x.length === trace.customdata.length
          )
        }
      ),
      { numRuns: 100 }
    )
  })
})
```

### Integration Testing

**Scope**: Test full component with mocked API responses

**Test Scenarios**:
1. Load dashboard with forecast data → verify chart renders with correct number of series
2. Click legend item → verify series toggles visibility
3. Double-click legend item → verify only that series is visible
4. Click "Reset View" button → verify all series become visible
5. Change filter dropdown → verify chart updates with filtered data
6. Toggle "Show Historical Events" → verify markers appear/disappear

### Manual Testing Checklist

- [ ] Chart displays continuous lines for multi-date series
- [ ] Chart displays individual markers for single-date series
- [ ] Legend remains visible after single-click interactions
- [ ] Legend remains visible after double-click interactions
- [ ] "Reset View" button restores all series
- [ ] Error bars display correctly with semi-transparent styling
- [ ] Hover tooltips show date, probability, and confidence interval
- [ ] Historical markers use 'x' symbol and appear on top of lines
- [ ] Filters update chart without errors
- [ ] Chart is responsive and resizes properly

## Implementation Notes

### Performance Considerations

1. **Data Transformation**: Perform grouping and sorting once during data preparation, not on every render
2. **Memoization**: Use `useMemo` for expensive computations like trace preparation
3. **Trace Count**: Limit to 12 series maximum (3 trigger types × 4 horizons) to maintain performance
4. **Historical Markers**: Limit to most recent 100 events to avoid rendering slowdown

### Accessibility

1. **Color Blindness**: Use distinct line styles (dash patterns) in addition to colors
2. **Keyboard Navigation**: Ensure legend items are keyboard accessible
3. **Screen Readers**: Add aria-labels to chart container and controls
4. **High Contrast**: Ensure sufficient contrast between lines and background

### Browser Compatibility

- Tested on: Chrome 120+, Firefox 120+, Safari 17+, Edge 120+
- Plotly.js version: 2.26.0 or higher
- React version: 18.2.0 or higher

### Future Enhancements

1. **Zoom Persistence**: Save zoom/pan state in URL query params
2. **Series Comparison**: Add ability to compare specific horizons side-by-side
3. **Confidence Interval Toggle**: Allow users to show/hide error bars
4. **Export Data**: Add button to export visible series data as CSV
5. **Animation**: Animate line drawing when data updates
