/**
 * Property-based tests for forecast chart utilities
 * Feature: forecast-probability-visualization
 */

import { describe, it, expect } from 'vitest'
import * as fc from 'fast-check'
import { prepareForecastTraces, prepareHistoricalMarkers } from './forecastChartUtils'

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

// Arbitraries for generating test data
const triggerTypeArb = fc.constantFrom('drought', 'flood', 'crop_failure')
const horizonArb = fc.constantFrom(3, 4, 5, 6)
const probabilityArb = fc.float({ min: 0, max: 1 })
const dateArb = fc.date({ min: new Date('2020-01-01'), max: new Date('2030-12-31') })

const forecastArb = fc.record({
  id: fc.integer({ min: 1, max: 10000 }),
  forecastDate: dateArb.map(d => d.toISOString().split('T')[0]),
  targetDate: dateArb.map(d => d.toISOString().split('T')[0]),
  horizonMonths: horizonArb,
  triggerType: triggerTypeArb,
  probability: probabilityArb,
  confidenceLower: probabilityArb,
  confidenceUpper: probabilityArb,
  modelVersion: fc.constantFrom('v1.0', 'v1.1', 'v2.0'),
  createdAt: dateArb.map(d => d.toISOString())
})

const triggerEventArb = fc.record({
  id: fc.integer({ min: 1, max: 10000 }),
  date: dateArb.map(d => d.toISOString().split('T')[0]),
  triggerType: triggerTypeArb,
  confidence: fc.float({ min: 0, max: 1 }),
  severity: fc.float({ min: 0, max: 1 })
})

describe('prepareForecastTraces - Property Tests', () => {
  /**
   * Property 3: Horizon differentiation through line styles
   * Feature: forecast-probability-visualization, Property 3: Horizon differentiation through line styles
   * Validates: Requirements 1.4
   * 
   * For any trigger type with multiple forecast horizons, each horizon's trace 
   * should have a unique line dash style (solid, dash, dot, or dashdot)
   */
  it('should assign unique line styles to different horizons for the same trigger type', () => {
    fc.assert(
      fc.property(
        triggerTypeArb,
        fc.array(dateArb, { minLength: 1, maxLength: 10 }),
        probabilityArb,
        (triggerType, dates, baseProbability) => {
          // Create forecasts for all 4 horizons with the same trigger type
          const forecasts: Forecast[] = [3, 4, 5, 6].flatMap(horizon =>
            dates.map((date, idx) => ({
              id: horizon * 1000 + idx,
              forecastDate: new Date().toISOString().split('T')[0],
              targetDate: date.toISOString().split('T')[0],
              horizonMonths: horizon,
              triggerType,
              probability: Math.min(1, Math.max(0, baseProbability + (idx * 0.01))),
              confidenceLower: Math.max(0, baseProbability - 0.1),
              confidenceUpper: Math.min(1, baseProbability + 0.1),
              modelVersion: 'v1.0',
              createdAt: new Date().toISOString()
            }))
          )

          const traces = prepareForecastTraces(forecasts)
          
          // Filter traces for this trigger type
          const triggerTraces = traces.filter(t => t.name.includes(triggerType))
          
          // Should have 4 traces (one per horizon)
          expect(triggerTraces.length).toBe(4)
          
          // Extract line styles
          const lineStyles = triggerTraces.map(t => t.line.dash)
          
          // All line styles should be unique
          const uniqueStyles = new Set(lineStyles)
          expect(uniqueStyles.size).toBe(4)
          
          // Verify specific horizon-to-style mappings
          const horizon3Trace = triggerTraces.find(t => t.name.includes('(3mo)'))
          const horizon4Trace = triggerTraces.find(t => t.name.includes('(4mo)'))
          const horizon5Trace = triggerTraces.find(t => t.name.includes('(5mo)'))
          const horizon6Trace = triggerTraces.find(t => t.name.includes('(6mo)'))
          
          expect(horizon3Trace?.line.dash).toBe('solid')
          expect(horizon4Trace?.line.dash).toBe('dash')
          expect(horizon5Trace?.line.dash).toBe('dot')
          expect(horizon6Trace?.line.dash).toBe('dashdot')
        }
      ),
      { numRuns: 100 }
    )
  })

  /**
   * Property 7: Empty series exclusion
   * Feature: forecast-probability-visualization, Property 7: Empty series exclusion
   * Validates: Requirements 3.2
   * 
   * For any combination of trigger type and horizon with zero data points, 
   * no trace should be created in the chart data array
   */
  it('should exclude series with no data points from traces', () => {
    fc.assert(
      fc.property(
        fc.array(forecastArb, { minLength: 0, maxLength: 50 }),
        (forecasts) => {
          const traces = prepareForecastTraces(forecasts)
          
          // Every trace should have at least one data point
          traces.forEach(trace => {
            expect(trace.x.length).toBeGreaterThan(0)
            expect(trace.y.length).toBeGreaterThan(0)
          })
          
          // Count unique series in input
          const inputSeries = new Set(
            forecasts.map(f => `${f.triggerType}_${f.horizonMonths}`)
          )
          
          // Count traces in output
          const outputSeries = new Set(
            traces.map(t => {
              const match = t.name.match(/(\w+) \((\d+)mo\)/)
              return match ? `${match[1]}_${match[2]}` : ''
            })
          )
          
          // Output should not have more series than input
          expect(outputSeries.size).toBeLessThanOrEqual(inputSeries.size)
        }
      ),
      { numRuns: 100 }
    )
  })
})


describe('prepareForecastTraces - Filter Consistency', () => {
  /**
   * Property 9: Filter consistency
   * Feature: forecast-probability-visualization, Property 9: Filter consistency
   * Validates: Requirements 3.5
   * 
   * For any filter combination (trigger type and/or horizon), all traces in the 
   * resulting chart data should match the filter criteria
   */
  it('should only include traces matching the filter criteria', () => {
    fc.assert(
      fc.property(
        fc.array(forecastArb, { minLength: 10, maxLength: 50 }),
        fc.option(triggerTypeArb, { nil: undefined }),
        fc.option(horizonArb, { nil: undefined }),
        (forecasts, filterType, filterHorizon) => {
          // Apply filters to forecasts
          const filtered = forecasts.filter(f => {
            const typeMatch = !filterType || f.triggerType === filterType
            const horizonMatch = !filterHorizon || f.horizonMonths === filterHorizon
            return typeMatch && horizonMatch
          })
          
          const traces = prepareForecastTraces(filtered)
          
          // Every trace should match the filter criteria
          traces.forEach(trace => {
            if (filterType) {
              expect(trace.name).toContain(filterType)
            }
            if (filterHorizon) {
              expect(trace.name).toContain(`(${filterHorizon}mo)`)
            }
          })
          
          // Verify no traces exist for filtered-out combinations
          if (filterType && filterHorizon) {
            // Should have at most 1 trace (the specific combination)
            expect(traces.length).toBeLessThanOrEqual(1)
          }
        }
      ),
      { numRuns: 100 }
    )
  })
})

describe('Data Validation and Error Handling Tests', () => {
  /**
   * Unit tests for error handling
   * Validates: Requirements 5.4, 5.5
   */
  it('should filter out forecasts with invalid probability values', () => {
    const forecasts: Forecast[] = [
      {
        id: 1,
        forecastDate: '2024-01-01',
        targetDate: '2024-04-01',
        horizonMonths: 3,
        triggerType: 'drought',
        probability: 1.5, // Invalid: > 1
        confidenceLower: 0.4,
        confidenceUpper: 0.6,
        modelVersion: 'v1.0',
        createdAt: '2024-01-01T00:00:00Z'
      },
      {
        id: 2,
        forecastDate: '2024-01-01',
        targetDate: '2024-04-01',
        horizonMonths: 3,
        triggerType: 'flood',
        probability: 0.5, // Valid
        confidenceLower: 0.4,
        confidenceUpper: 0.6,
        modelVersion: 'v1.0',
        createdAt: '2024-01-01T00:00:00Z'
      },
      {
        id: 3,
        forecastDate: '2024-01-01',
        targetDate: '2024-04-01',
        horizonMonths: 3,
        triggerType: 'crop_failure',
        probability: -0.1, // Invalid: < 0
        confidenceLower: 0.4,
        confidenceUpper: 0.6,
        modelVersion: 'v1.0',
        createdAt: '2024-01-01T00:00:00Z'
      }
    ]
    
    const traces = prepareForecastTraces(forecasts)
    
    // Should only have 1 trace (for the valid forecast)
    expect(traces.length).toBe(1)
    expect(traces[0].name).toContain('flood')
  })
  
  it('should handle empty forecast arrays gracefully', () => {
    const forecasts: Forecast[] = []
    
    const traces = prepareForecastTraces(forecasts)
    
    // Should return empty array without errors
    expect(traces).toEqual([])
  })
  
  it('should validate array length consistency', () => {
    const forecasts: Forecast[] = [
      {
        id: 1,
        forecastDate: '2024-01-01',
        targetDate: '2024-04-01',
        horizonMonths: 3,
        triggerType: 'drought',
        probability: 0.5,
        confidenceLower: 0.4,
        confidenceUpper: 0.6,
        modelVersion: 'v1.0',
        createdAt: '2024-01-01T00:00:00Z'
      },
      {
        id: 2,
        forecastDate: '2024-01-01',
        targetDate: '2024-05-01',
        horizonMonths: 3,
        triggerType: 'drought',
        probability: 0.6,
        confidenceLower: 0.5,
        confidenceUpper: 0.7,
        modelVersion: 'v1.0',
        createdAt: '2024-01-01T00:00:00Z'
      }
    ]
    
    const traces = prepareForecastTraces(forecasts)
    
    // Verify array lengths match
    traces.forEach(trace => {
      expect(trace.x.length).toBe(trace.y.length)
      expect(trace.x.length).toBe(trace.customdata.length)
      expect(trace.error_y.array.length).toBe(trace.x.length)
      expect(trace.error_y.arrayminus.length).toBe(trace.x.length)
    })
  })
})

describe('Plotly Configuration Tests', () => {
  /**
   * Unit tests for Plotly layout configuration
   * Validates: Requirements 1.3, 5.1, 5.3
   */
  it('should configure traces with connectgaps false for sparse data handling', () => {
    const forecasts: Forecast[] = [
      {
        id: 1,
        forecastDate: '2024-01-01',
        targetDate: '2024-04-01',
        horizonMonths: 3,
        triggerType: 'drought',
        probability: 0.5,
        confidenceLower: 0.4,
        confidenceUpper: 0.6,
        modelVersion: 'v1.0',
        createdAt: '2024-01-01T00:00:00Z'
      },
      {
        id: 2,
        forecastDate: '2024-01-01',
        targetDate: '2024-06-01', // Gap in dates
        horizonMonths: 3,
        triggerType: 'drought',
        probability: 0.6,
        confidenceLower: 0.5,
        confidenceUpper: 0.7,
        modelVersion: 'v1.0',
        createdAt: '2024-01-01T00:00:00Z'
      }
    ]
    
    const traces = prepareForecastTraces(forecasts)
    
    // All traces should have connectgaps set to false
    traces.forEach(trace => {
      expect(trace.connectgaps).toBe(false)
    })
  })
  
  it('should configure probability values in 0-1 range', () => {
    const forecasts: Forecast[] = [
      {
        id: 1,
        forecastDate: '2024-01-01',
        targetDate: '2024-04-01',
        horizonMonths: 3,
        triggerType: 'drought',
        probability: 0.75,
        confidenceLower: 0.65,
        confidenceUpper: 0.85,
        modelVersion: 'v1.0',
        createdAt: '2024-01-01T00:00:00Z'
      }
    ]
    
    const traces = prepareForecastTraces(forecasts)
    
    // All y values should be in [0, 1] range
    traces.forEach(trace => {
      trace.y.forEach(yValue => {
        expect(yValue).toBeGreaterThanOrEqual(0)
        expect(yValue).toBeLessThanOrEqual(1)
      })
    })
  })
})

describe('Legend Interaction Tests', () => {
  /**
   * Unit tests for legend interaction preservation
   * Validates: Requirements 2.1, 2.2, 2.4
   * 
   * These tests verify that legend configuration prevents disappearance
   */
  it('should maintain legend visibility with proper configuration', () => {
    // Test that traces are configured to support legend interactions
    const forecasts: Forecast[] = [
      {
        id: 1,
        forecastDate: '2024-01-01',
        targetDate: '2024-04-01',
        horizonMonths: 3,
        triggerType: 'drought',
        probability: 0.5,
        confidenceLower: 0.4,
        confidenceUpper: 0.6,
        modelVersion: 'v1.0',
        createdAt: '2024-01-01T00:00:00Z'
      }
    ]
    
    const traces = prepareForecastTraces(forecasts)
    
    // Traces should be configured for legend interaction
    expect(traces.length).toBeGreaterThan(0)
    traces.forEach(trace => {
      // Trace should have a name for legend
      expect(trace.name).toBeDefined()
      expect(trace.name.length).toBeGreaterThan(0)
      
      // Trace should be visible by default
      expect(trace.mode).toBeDefined()
    })
  })
  
  it('should support toggling individual series', () => {
    // Create multiple series
    const forecasts: Forecast[] = [
      {
        id: 1,
        forecastDate: '2024-01-01',
        targetDate: '2024-04-01',
        horizonMonths: 3,
        triggerType: 'drought',
        probability: 0.5,
        confidenceLower: 0.4,
        confidenceUpper: 0.6,
        modelVersion: 'v1.0',
        createdAt: '2024-01-01T00:00:00Z'
      },
      {
        id: 2,
        forecastDate: '2024-01-01',
        targetDate: '2024-04-01',
        horizonMonths: 3,
        triggerType: 'flood',
        probability: 0.3,
        confidenceLower: 0.2,
        confidenceUpper: 0.4,
        modelVersion: 'v1.0',
        createdAt: '2024-01-01T00:00:00Z'
      }
    ]
    
    const traces = prepareForecastTraces(forecasts)
    
    // Should have multiple traces
    expect(traces.length).toBeGreaterThanOrEqual(2)
    
    // Each trace should have unique name
    const names = traces.map(t => t.name)
    const uniqueNames = new Set(names)
    expect(uniqueNames.size).toBe(traces.length)
  })
})

describe('prepareHistoricalMarkers - Property Tests', () => {
  /**
   * Property 8: Historical marker differentiation
   * Feature: forecast-probability-visualization, Property 8: Historical marker differentiation
   * Validates: Requirements 3.4
   * 
   * For any historical trigger event, the trace should use marker symbol 'x' 
   * and the legend label should include "(actual)" to distinguish from forecasts
   */
  it('should use x marker symbol and (actual) suffix for all historical events', () => {
    fc.assert(
      fc.property(
        fc.array(triggerEventArb, { minLength: 1, maxLength: 50 }),
        fc.constantFrom('all', 'drought', 'flood', 'crop_failure'),
        (triggerEvents, selectedType) => {
          const markers = prepareHistoricalMarkers(triggerEvents, selectedType)
          
          // Every marker should use 'x' symbol
          markers.forEach(marker => {
            expect(marker.marker.symbol).toBe('x')
          })
          
          // Every marker name should include "(actual)"
          markers.forEach(marker => {
            expect(marker.name).toContain('(actual)')
          })
          
          // Markers should be positioned at y=1.0 (100% level)
          markers.forEach(marker => {
            marker.y.forEach(yValue => {
              expect(yValue).toBe(1.0)
            })
          })
          
          // Markers should be in scatter mode with markers only
          markers.forEach(marker => {
            expect(marker.type).toBe('scatter')
            expect(marker.mode).toBe('markers')
          })
        }
      ),
      { numRuns: 100 }
    )
  })

  it('should filter markers by selected trigger type', () => {
    fc.assert(
      fc.property(
        fc.array(triggerEventArb, { minLength: 5, maxLength: 50 }),
        triggerTypeArb,
        (triggerEvents, selectedType) => {
          const markers = prepareHistoricalMarkers(triggerEvents, selectedType)
          
          // All markers should match the selected trigger type
          markers.forEach(marker => {
            expect(marker.name).toContain(selectedType)
          })
          
          // Should have at most 1 marker trace (for the selected type)
          expect(markers.length).toBeLessThanOrEqual(1)
        }
      ),
      { numRuns: 100 }
    )
  })

  it('should exclude trigger types with no events', () => {
    fc.assert(
      fc.property(
        fc.array(triggerEventArb, { minLength: 0, maxLength: 50 }),
        (triggerEvents) => {
          const markers = prepareHistoricalMarkers(triggerEvents, 'all')
          
          // Count unique trigger types in input
          const inputTypes = new Set(triggerEvents.map(e => e.triggerType))
          
          // Count marker traces in output
          expect(markers.length).toBeLessThanOrEqual(inputTypes.size)
          
          // Every marker should have at least one data point
          markers.forEach(marker => {
            expect(marker.x.length).toBeGreaterThan(0)
            expect(marker.y.length).toBeGreaterThan(0)
            expect(marker.x.length).toBe(marker.y.length)
          })
        }
      ),
      { numRuns: 100 }
    )
  })
})
