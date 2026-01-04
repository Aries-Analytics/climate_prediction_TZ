/**
 * Utility functions for preparing forecast data for Plotly chart rendering
 */

interface Forecast {
  id: number
  forecastDate: string
  targetDate: string
  horizonMonths: number
  triggerType: string
  probability: number
  confidenceLower: number
  confidenceUpper: number
  modelVersion: string
  createdAt: string
}

interface TriggerEvent {
  id: number
  date: string
  triggerType: string
  confidence: number
  severity: number
}

interface ForecastTrace {
  x: string[]
  y: number[]
  error_y: {
    type: 'data'
    symmetric: false
    array: number[]
    arrayminus: number[]
    color: string
    thickness: number
    width: number
  }
  type: 'scatter'
  mode: 'lines+markers' | 'markers'
  name: string
  line: {
    color: string
    width: number
    dash: 'solid' | 'dash' | 'dot' | 'dashdot'
  }
  marker: {
    size: number
    color: string
    line: {
      color: string
      width: number
    }
  }
  hovertemplate: string
  customdata: [number, number][]
  connectgaps: boolean
}

interface HistoricalMarker {
  x: string[]
  y: number[]
  type: 'scatter'
  mode: 'markers'
  name: string
  marker: {
    symbol: 'x'
    size: number
    color: string
    line: {
      color: string
      width: number
    }
  }
  hovertemplate: string
  showlegend: boolean
}

const getTriggerTypeColor = (triggerType: string): string => {
  const colors: Record<string, string> = {
    drought: '#ff9800',
    flood: '#2196f3',
    crop_failure: '#f44336'
  }
  return colors[triggerType] || '#9e9e9e'
}

const getHorizonLineStyle = (horizon: number): 'solid' | 'dash' | 'dot' | 'dashdot' => {
  const styles: Record<number, 'solid' | 'dash' | 'dot' | 'dashdot'> = {
    3: 'solid',
    4: 'dash',
    5: 'dot',
    6: 'dashdot'
  }
  return styles[horizon] || 'solid'
}

/**
 * Groups forecasts by trigger type and horizon, then sorts chronologically
 */
const groupAndSortForecasts = (forecasts: Forecast[]): Map<string, Forecast[]> => {
  const grouped = new Map<string, Forecast[]>()
  
  forecasts.forEach(forecast => {
    const key = `${forecast.triggerType}|${forecast.horizonMonths}`
    if (!grouped.has(key)) {
      grouped.set(key, [])
    }
    grouped.get(key)!.push(forecast)
  })
  
  // Sort each group chronologically by targetDate
  grouped.forEach((group, key) => {
    group.sort((a, b) => new Date(a.targetDate).getTime() - new Date(b.targetDate).getTime())
  })
  
  return grouped
}

/**
 * Validates and filters forecast data
 * Removes forecasts with invalid probability values
 */
const validateForecasts = (forecasts: Forecast[]): Forecast[] => {
  return forecasts.filter(f => {
    // Validate probability is in [0, 1] range
    if (f.probability < 0 || f.probability > 1) {
      console.warn(`Invalid probability value ${f.probability} for forecast ${f.id}. Skipping.`)
      return false
    }
    
    // Validate confidence intervals
    if (f.confidenceLower < 0 || f.confidenceLower > 1) {
      console.warn(`Invalid confidenceLower value ${f.confidenceLower} for forecast ${f.id}. Skipping.`)
      return false
    }
    
    if (f.confidenceUpper < 0 || f.confidenceUpper > 1) {
      console.warn(`Invalid confidenceUpper value ${f.confidenceUpper} for forecast ${f.id}. Skipping.`)
      return false
    }
    
    // Validate confidence interval ordering
    if (f.confidenceLower > f.probability || f.confidenceUpper < f.probability) {
      console.warn(`Invalid confidence interval for forecast ${f.id}. Probability ${f.probability} not within [${f.confidenceLower}, ${f.confidenceUpper}]. Skipping.`)
      return false
    }
    
    return true
  })
}

/**
 * Prepares forecast traces for Plotly chart rendering
 * Groups forecasts by trigger type and horizon, applies distinct styling,
 * and configures hover templates
 * 
 * @param forecasts - Array of forecast data from API
 * @returns Array of Plotly trace objects ready for rendering
 */
export const prepareForecastTraces = (forecasts: Forecast[]): ForecastTrace[] => {
  // Validate and filter forecasts
  const validForecasts = validateForecasts(forecasts)
  
  if (validForecasts.length < forecasts.length) {
    console.warn(`Filtered out ${forecasts.length - validForecasts.length} invalid forecasts`)
  }
  
  const grouped = groupAndSortForecasts(validForecasts)
  const traces: ForecastTrace[] = []
  
  grouped.forEach((group, key) => {
    // Skip empty series
    if (group.length === 0) {
      return
    }
    
    const [triggerType, horizonStr] = key.split('|')
    const horizon = parseInt(horizonStr)
    
    // Determine mode based on data point count
    const mode = group.length >= 2 ? 'lines+markers' : 'markers'
    
    // Extract data arrays
    const x = group.map(f => f.targetDate)
    const y = group.map(f => f.probability)
    const customdata = group.map(f => [f.confidenceLower, f.confidenceUpper] as [number, number])
    
    // Calculate error bars
    const errorArray = group.map(f => f.confidenceUpper - f.probability)
    const errorArrayMinus = group.map(f => f.probability - f.confidenceLower)
    
    // Validate array lengths
    if (x.length !== y.length || x.length !== customdata.length) {
      console.error(`Array length mismatch for series ${key}: x=${x.length}, y=${y.length}, customdata=${customdata.length}`)
      return
    }
    
    // Format trigger type name for display
    const triggerTypeDisplay = triggerType.replace('_', ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
    
    const trace: ForecastTrace = {
      x,
      y,
      error_y: {
        type: 'data',
        symmetric: false,
        array: errorArray,
        arrayminus: errorArrayMinus,
        color: 'rgba(0,0,0,0.15)',
        thickness: 1.5,
        width: 4
      },
      type: 'scatter',
      mode,
      name: `${triggerTypeDisplay} (${horizon}mo)`,
      line: {
        color: getTriggerTypeColor(triggerType),
        width: 3,
        dash: getHorizonLineStyle(horizon)
      },
      marker: {
        size: 10,
        color: getTriggerTypeColor(triggerType),
        line: {
          color: '#fff',
          width: 2
        }
      },
      hovertemplate: '<b>%{fullData.name}</b><br>' +
                     'Target Date: %{x}<br>' +
                     'Probability: %{y:.1%}<br>' +
                     'Confidence: [%{customdata[0]:.1%} - %{customdata[1]:.1%}]<br>' +
                     '<extra></extra>',
      customdata,
      connectgaps: false
    }
    
    traces.push(trace)
  })
  
  return traces
}


/**
 * Prepares historical trigger event markers for Plotly chart rendering
 * Creates marker traces for actual trigger events that occurred in the past
 * 
 * @param triggerEvents - Array of historical trigger event data from API
 * @param selectedTriggerType - Optional filter for specific trigger type ('all' shows all types)
 * @returns Array of Plotly marker trace objects for historical events
 */
export const prepareHistoricalMarkers = (
  triggerEvents: TriggerEvent[],
  selectedTriggerType: string = 'all'
): HistoricalMarker[] => {
  const triggerTypes = ['drought', 'flood', 'crop_failure']
  const markers: HistoricalMarker[] = []
  
  triggerTypes.forEach(triggerType => {
    // Filter events by trigger type and optional filter
    const typeTriggers = triggerEvents.filter(t => 
      t.triggerType === triggerType && 
      (selectedTriggerType === 'all' || t.triggerType === selectedTriggerType)
    )
    
    // Skip if no events for this trigger type
    if (typeTriggers.length === 0) {
      return
    }
    
    const marker: HistoricalMarker = {
      x: typeTriggers.map(t => t.date),
      y: typeTriggers.map(() => 1.0), // Position at 100% level (top of chart)
      type: 'scatter',
      mode: 'markers',
      name: `${triggerType} (actual)`, // Add "(actual)" suffix to distinguish from forecasts
      marker: {
        symbol: 'x', // Use 'x' marker symbol for historical events
        size: 12,
        color: getTriggerTypeColor(triggerType),
        line: {
          color: '#000',
          width: 2
        }
      },
      hovertemplate: '<b>Actual Trigger Event</b><br>' +
                     'Type: %{fullData.name}<br>' +
                     'Date: %{x}<br>' +
                     '<extra></extra>',
      showlegend: true
    }
    
    markers.push(marker)
  })
  
  return markers
}
