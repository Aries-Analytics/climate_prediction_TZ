# /e2e — Run HewaSense Playwright E2E Tests

Run the full Playwright E2E test suite against the HewaSense frontend.

## Prerequisites check (do these steps in order)

1. **Credentials** — Check if `TEST_USER` and `TEST_PASSWORD` are available. If not set, ask the user for them before running anything.

2. **Backend** — Remind the user that the backend must be running (either via `docker compose` locally or the production server must be reachable at `localhost:8000` via the proxy). If unsure, ask.

## Execution

3. `cd` into `phase2/frontend`

4. Run the tests:
   ```
   TEST_USER=<user> TEST_PASSWORD=<pass> npm run test:e2e
   ```
   The `playwright.config.ts` will auto-start the Vite dev server if not already running (`reuseExistingServer: true`).

## Results interpretation

5. Parse the output and report a clean summary:
   - Total tests run / passed / failed / skipped
   - Which projects passed (setup, chromium)
   - Duration

6. **If all pass:** report success. Offer to open the HTML report (`npm run test:e2e:report`) for details.

7. **If any fail:**
   - List each failing test with its file, test name, and error message
   - Diagnose the likely cause:
     - `auth.setup.ts` failure → credentials wrong or backend not reachable
     - Navigation/URL failures → route changed or auth redirect broken
     - Selector failures → component structure changed (re-read the relevant TSX file before guessing)
     - Timeout failures → slow backend response or lazy-load issue
   - Offer to re-run with `--headed` for visual debugging: `TEST_USER=<user> TEST_PASSWORD=<pass> npm run test:e2e:headed`

## Notes
- Tests run sequentially (`workers: 1`) — this is intentional; do not add `--workers` flags
- Auth state is saved to `e2e/.auth/user.json` after the setup step and reused by all other tests
- `e2e/.auth/` is gitignored — it will be regenerated on each fresh run
