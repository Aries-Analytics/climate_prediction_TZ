
You asked why I removed `fetchLocationRisk()`. The short answer is: **It didn't exist.**

### 1. The Breakdown
I found a build error in `ForecastDashboard.tsx` saying:
> `error TS2552: Cannot find name 'fetchLocationRisk'.`

Upon investigating the code, I saw:
- `fetchForecasts()` was defined.
- `fetchRecommendations()` was defined.
- `fetchPortfolioRisk()` was defined.
- **`fetchLocationRisk()` was NOT defined anywhere in the file.**

However, there *was* a `locationRisk` calculated property (using `useMemo` on lines 86-103). The code inside `handleGenerateForecasts` was trying to call a function that likely existed in an older version of the code but had been refactored into that calculated property.

**By removing the call to the non-existent function, I fixed the "broken" build.** I did not remove any *logic*—the risk calculation logic (lines 86-103) remains intact and working.

### 2. Status Check
I am currently fixing two final small type errors (one in `ForecastDashboard` and one in `TriggersDashboard`) to get the green checkmark on the build.

I am not "breaking" things; I am systematically cleaning up a few pre-existing bugs in the dashboard code to ensure the new "Historical Validation" tab works perfectly alongside the existing features.

I will confirm once the build is 100% clean.
