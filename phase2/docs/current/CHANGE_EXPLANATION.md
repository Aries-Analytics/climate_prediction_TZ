
You asked: **"What are you changing in the forecast code?"**

### 1. The Fix (Not a Change in Logic)
I removed one line of code: `fetchLocationRisk()`.
*   **Why?** This function **did not exist** in the file. It was a leftover artifact (a "ghost function") causing the build to fail.
*   **Did it break anything?** No. The location risk logic is actually handled by a `useMemo` block (lines 86-103) which calculates risk directly from the `forecasts` data.
*   **Result:** The code does exactly what it did before, but now it successfully compiles without crashing.

### 2. Documentation on Building Containers
To find instructions on building containers (Docker), you should check the project root or the `docs/` folder.

If you don't have a specific `CONTRIBUTING.md` or `DEPLOYMENT.md`, I can create one for you. Typically, for a full-stack Python/React app, it looks like this:

**Backend:**
```bash
cd backend
docker build -t tanzania-climate-backend .
```

**Frontend:**
```bash
cd frontend
docker build -t tanzania-climate-frontend .
```

I'll check your current docs to point you to the right file.
