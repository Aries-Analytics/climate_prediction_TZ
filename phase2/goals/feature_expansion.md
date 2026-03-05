# Feature Expansion — ATLAS Workflow

## Goal

Build new features on the verified stabilization foundation. Every new feature follows the ATLAS cycle with Auditor gate before merge.

---

## App Brief (A — Architect)

Before starting any feature:

```markdown
## Feature Brief
- **Problem:** [What gap does this feature fill?]
- **User:** [Who benefits — farmers, insurers, admins?]
- **Success:** [What measurable outcome proves it works?]
- **Constraints:** [API costs, data availability, timeline]
```

The Orchestrator creates this brief and saves it as `goals/feature_[name].md`.

---

## Design Phase (T — Trace)

1. **Data Schema** — What new tables/columns? What migrations needed?
2. **API Contracts** — New endpoints? Update `state.json → shared_contract`
3. **Integration Map** — External services? New API keys needed?
4. **Edge Cases** — What could break? Rate limits? Missing data scenarios?

---

## Validation Phase (L — Link)

Before writing implementation code:

```
[ ] Feature branch created from phase2/feature-expansion
[ ] Database schema changes designed (not yet applied)
[ ] All API dependencies verified accessible
[ ] No conflicts with existing contracts in state.json
[ ] Relevant context files updated if new domain knowledge needed
```

---

## Build Phase (A — Assemble)

**Persona: Backend Architect or Frontend Engineer**

Build order:
1. Database schema / migrations first
2. Backend API routes second
3. Frontend UI last

Rules:
- Check `tools/manifest.md` before writing new scripts
- Add any new tool scripts to the manifest
- Follow all laws in `.agent/rules/SKILL.md`
- Update `context/` files if adding new domain concepts

---

## Verification Phase (S — Stress-test)

**Persona: Auditor**

```
[ ] Feature solves the stated problem from the brief
[ ] audit.py exits code 0
[ ] All existing tests still pass
[ ] New tests written for new functionality
[ ] No synthetic fallbacks introduced
[ ] Contracts in state.json updated if applicable
[ ] Documentation updated
```

**On pass:** Merge feature branch → `phase2/feature-expansion`, delete feature branch.
**On fail:** Rejection report per `hardprompts/rejection_report.md`, back to Architect mode.

---

## Related Files

- **Args:** `args/persona_config.yaml`
- **Context:** `context/hewasense_domain.md`
- **Tools:** `tools/manifest.md`
