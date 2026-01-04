# Implementation Plan

- [x] 1. Create data transformation utilities




  - Create utility functions for transforming forecast API data into properly structured Plotly traces
  - Implement chronological sorting of data points by targetDate
  - Implement logic to determine trace mode ('lines+markers' vs 'markers') based on data point count
  - Implement error bar calculation from confidence intervals
  - _Requirements: 1.1, 1.2, 4.1_

- [x] 1.1 Write property test for multi-point series rendering

  - **Property 1: Multi-point series render as lines**
  - **Validates: Requirements 1.1**

- [x] 1.2 Write property test for single-point series rendering

  - **Property 2: Single-point series render as markers only**
  - **Validates: Requirements 1.2**

- [x] 1.3 Write property test for array length consistency

  - **Property 11: Array length consistency**
  - **Validates: Requirements 5.2**

- [x] 2. Implement forecast trace preparation function




  - Create `prepareForecastTraces()` function that groups forecasts by trigger type and horizon
  - Implement distinct line styles (solid, dash, dot, dashdot) for different horizons
  - Implement color coding by trigger type (drought: orange, flood: blue, crop_failure: red)
  - Add hover template configuration with date, probability, and confidence interval
  - Ensure empty series are filtered out
  - _Requirements: 1.1, 1.4, 3.2, 4.2_

- [x] 2.1 Write property test for horizon line style differentiation

  - **Property 3: Horizon differentiation through line styles**
  - **Validates: Requirements 1.4**


- [x] 2.2 Write property test for empty series exclusion

  - **Property 7: Empty series exclusion**
  - **Validates: Requirements 3.2**


- [x] 3. Implement historical marker preparation function

  - Create `prepareHistoricalMarkers()` function for trigger event data
  - Use 'x' marker symbol for historical events
  - Add "(actual)" suffix to legend labels
  - Position markers at y=1.0 (100% level)
  - Ensure historical markers render after forecast lines (z-ordering)
  - _Requirements: 3.3, 3.4_

- [x] 3.1 Write property test for historical marker differentiation

  - **Property 8: Historical marker differentiation**
  - **Validates: Requirements 3.4**


- [x] 4. Implement data filtering logic

  - Create `filterForecastData()` function that applies trigger type and horizon filters
  - Ensure filtered data maintains proper structure for trace preparation
  - Handle edge cases (no data after filtering)
  - _Requirements: 3.5_

- [x] 4.1 Write property test for filter consistency

  - **Property 9: Filter consistency**
  - **Validates: Requirements 3.5**



- [ ] 5. Add legend state management to ForecastDashboard component
  - Add React state for tracking legend visibility per series
  - Implement legend click handler that updates visibility state
  - Implement "Reset View" button that restores all series to visible
  - Update trace preparation to use visibility state

  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 5.1 Write unit test for legend interaction preservation
  - Test that legend remains in DOM after single-click


  - Test that legend remains in DOM after double-click
  - Test that reset button makes all series visible
  - _Requirements: 2.1, 2.2, 2.4_

- [ ] 6. Update Plotly layout configuration
  - Configure legend with explicit itemclick and itemdoubleclick behavior
  - Set showlegend: true to prevent legend disappearance

  - Configure legend positioning and styling (horizontal, bottom, with border)
  - Ensure y-axis range is [0, 1] with percentage tick format
  - Set connectgaps: false on all traces to handle sparse data

  - _Requirements: 1.3, 2.5, 3.1, 5.3_

- [ ] 6.1 Write unit test for Plotly configuration
  - Test that layout.legend has required properties
  - Test that y-axis has correct range and format
  - _Requirements: 1.3, 5.1, 5.3_

- [x] 7. Add data validation and error handling

  - Implement validation for probability values (0-1 range)
  - Implement validation for array length consistency
  - Add error boundary around Chart component
  - Add console warnings for data inconsistencies
  - Handle API errors gracefully with user-friendly messages
  - _Requirements: 5.2, 5.4, 5.5_

- [x] 7.1 Write unit tests for error handling

  - Test invalid probability filtering
  - Test array length mismatch handling
  - Test error boundary catches Plotly errors
  - _Requirements: 5.4, 5.5_


- [ ] 8. Integrate all changes into ForecastDashboard component
  - Replace existing timeline data preparation with new utility functions
  - Add legend state management hooks
  - Add "Reset View" button to dashboard controls
  - Update Chart component props with new layout configuration
  - Test with real API data

  - _Requirements: All_

- [ ] 9. Checkpoint - Ensure all tests pass

  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Add integration tests for full component
  - Test chart renders with forecast data
  - Test legend interactions work correctly
  - Test filters update chart properly
  - Test historical markers toggle on/off
  - _Requirements: All_

- [ ] 11. Perform manual testing and accessibility review
  - Verify chart displays continuous lines for multi-date series
  - Verify legend interactions work as expected
  - Test keyboard navigation of legend items
  - Verify color contrast meets WCAG standards
  - Test on multiple browsers (Chrome, Firefox, Safari, Edge)
  - _Requirements: All_
