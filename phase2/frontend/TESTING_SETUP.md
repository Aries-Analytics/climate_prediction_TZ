# Testing Setup Instructions

## Installation

To run the property-based tests for the forecast chart utilities, you need to install the testing dependencies:

```bash
cd frontend
npm install
```

This will install:
- `vitest` - Fast unit test framework
- `@vitest/ui` - UI for running tests
- `@testing-library/react` - React testing utilities
- `@testing-library/jest-dom` - DOM matchers
- `jsdom` - DOM implementation for Node
- `fast-check` - Property-based testing library
- `@vitest/coverage-v8` - Code coverage

## Running Tests

### Run all tests
```bash
npm test
```

### Run tests once (CI mode)
```bash
npm run test:run
```

### Run tests with UI
```bash
npm run test:ui
```

### Run tests with coverage
```bash
npm run test:coverage
```

## Test Files

- `src/utils/forecastChartUtils.ts` - Utility functions for chart data transformation
- `src/utils/forecastChartUtils.test.ts` - Property-based and unit tests

## Property Tests

The test suite includes property-based tests that run 100 iterations each with randomly generated data:

1. **Property 1**: Multi-point series render as lines (Requirements 1.1)
2. **Property 2**: Single-point series render as markers only (Requirements 1.2)
3. **Property 11**: Array length consistency (Requirements 5.2)

Additional property tests verify:
- Trace data validation
- Invalid forecast filtering
- Data grouping preservation

## Test Coverage

Run `npm run test:coverage` to generate a coverage report in the `coverage/` directory.
