# AUTORESEARCH_BLUEPRINT

**Status**: Proposal
**Purpose**: Blueprint for adding an agent-driven experiment loop to HewaSense without sacrificing GOTCHA discipline, reproducibility, or scientific validity.

---

## 1. Goal

Adopt the useful part of the `autoresearch` pattern:
- constrained search surface
- fixed evaluation harness
- autonomous iteration
- keep-or-revert decision loop

Do **not** adopt the hype version:
- not "autonomous scientist"
- not freeform self-editing across the whole repo
- not one-run improvements treated as truth

The HewaSense version should behave like a controlled experiment runner for narrow model, feature, or calibration changes.

---

## 2. Design Principles

1. **Constrain the search surface**
Only one file or one structured config should be editable per experiment family.

2. **Keep evaluation fixed**
The agent should not edit the benchmark harness, validation split, or scoring logic in the same loop that proposes model changes.

3. **Record every run**
Git history alone is not an experiment database.

4. **Promote cautiously**
A single better metric is a candidate, not a final truth.

5. **Respect GOTCHA**
Goals define the workflow, tools execute deterministically, memory records durable lessons, and docs stay synchronized with accepted changes only.

---

## 3. Recommended Folder Structure

```text
phase2/
  autoresearch/
    README.md
    program.md
    search_space.yaml
    registry/
      experiments.jsonl
      promoted_runs.jsonl
    prompts/
      proposer.md
      reviewer.md
    reports/
      latest_summary.md
    runners/
      run_experiment.py
      score_experiment.py
      promote_candidate.py
  goals/
    autoresearch_loop.md
  tools/
    autoresearch/
      run_experiment.py
      summarize_registry.py
      compare_candidates.py
```

Suggested role of each piece:
- `program.md`: operating instructions for the agent
- `search_space.yaml`: allowed knobs and bounds
- `registry/experiments.jsonl`: append-only run ledger
- `runners/run_experiment.py`: one deterministic entrypoint for a trial
- `runners/score_experiment.py`: fixed scoring logic
- `goals/autoresearch_loop.md`: GOTCHA workflow for the loop

---

## 4. Minimal Search Surface

For HewaSense, do not start with architecture search. Start with a narrow, high-signal search surface such as:
- trigger threshold calibration parameters
- feature inclusion or exclusion flags from an allowed list
- post-processing probability calibration parameters
- retraining config values like regularization, learning rate, or lookback length

Avoid first-generation autoresearch over:
- multiple directories
- database schema changes
- API contracts
- frontend behavior
- deployment logic

The first version should be able to say:
"change one bounded model config, run one fixed evaluation, log the result."

---

## 5. `program.md` Template

```md
# Program

You are operating inside a controlled HewaSense autoresearch loop.

Your job is to improve the target metric within the allowed search surface.

Rules:
1. Edit only the files explicitly listed in `search_space.yaml`.
2. Do not modify evaluation code, data splits, docs, or deployment files.
3. Run experiments only through `python autoresearch/runners/run_experiment.py`.
4. Record every run in the registry, whether it improves or fails.
5. If a run crashes, inspect the traceback and classify the failure.
6. If a run improves the screening metric, mark it as a candidate only.
7. Do not declare any result promoted until it passes the promotion gate.

Promotion gate:
- repeat run across N seeds
- evaluate on holdout slice(s)
- compare against current baseline
- require minimum effect size threshold

If the result fails the promotion gate, keep the finding in the registry but do not advance the baseline.
```

This preserves the useful Karpathy-style loop while adding scientific and operational guardrails.

---

## 6. Experiment Registry Schema

Use append-only JSONL, SQLite, or both. JSONL is the fastest first version.

Recommended record shape:

```json
{
  "experiment_id": "exp_2026_04_09_001",
  "timestamp_utc": "2026-04-09T10:00:00Z",
  "branch": "phase2/feature-expansion",
  "commit_before": "abc1234",
  "commit_after": "def5678",
  "search_family": "probability_calibration",
  "edited_files": ["configs/calibration/search_candidate.yaml"],
  "proposal_summary": "Raised drought calibration slope by 0.05",
  "run_type": "screen",
  "dataset_version": "shadow_run_eval_v1",
  "seed": 42,
  "machine": "local-4090",
  "runtime_seconds": 214,
  "status": "completed",
  "metric_primary": {
    "name": "brier_score",
    "value": 0.1821,
    "direction": "lower_is_better"
  },
  "metrics_secondary": {
    "auc": 0.74,
    "calibration_error": 0.03
  },
  "baseline_primary": 0.1854,
  "delta_primary": -0.0033,
  "candidate": true,
  "promoted": false,
  "notes": "Passes screen; requires multi-seed promotion"
}
```

Minimum required fields:
- experiment id
- timestamp
- code version
- edited files
- search family
- seed
- machine
- runtime
- metric(s)
- status
- promotion decision

---

## 7. Execution Workflow

### Stage A: Screening

Purpose:
- cheap, fast filtering of obviously bad ideas

Characteristics:
- 1 seed
- reduced eval budget
- fixed screening slice
- no promotion yet

### Stage B: Candidate Validation

Purpose:
- confirm screening gains are real

Characteristics:
- repeated seeds
- same code path
- broader validation set
- variance measurement

### Stage C: Promotion Gate

Purpose:
- decide whether the baseline should move

Requirements:
- pass predefined effect-size threshold
- pass holdout evaluation
- no regressions on critical secondary metrics
- full experiment record written

### Stage D: Human Review

Even with automation, final promotion in HewaSense should remain human-reviewed for:
- insurance logic changes
- threshold changes
- model behavior changes affecting external claims

---

## 8. Metrics Strategy

Do not optimize one metric blindly.

For HewaSense, candidate metrics should be grouped:

Primary:
- Brier Score
- calibration error
- held-out loss

Secondary:
- precision/recall for trigger events
- false negative rate on known disaster cases
- basis-risk proxy agreement

Safety metrics:
- no off-season trigger leakage
- no advisory-tier contamination of payout calculations
- no contract/schema regression

Any candidate that improves the primary metric while breaking a safety metric must be auto-rejected.

---

## 9. Recommended Deterministic Tools

The agent should call tools like these, not run ad hoc shell logic for core evaluation:

- `run_experiment.py`
  - loads baseline + candidate config
  - executes training/eval
  - writes structured result

- `score_experiment.py`
  - computes fixed metrics only
  - no proposal logic

- `compare_candidates.py`
  - compares candidate vs current baseline
  - outputs pass/fail promotion recommendation

- `summarize_registry.py`
  - produces trend summaries for humans

These should all be listed in `tools/manifest.md` once implemented.

---

## 10. GOTCHA Integration

Recommended repo integration:

- New goal:
  - `goals/autoresearch_loop.md`
  - describes objective, allowed inputs, tools, outputs, and promotion criteria

- New memory policy:
  - only accepted durable lessons go into `memory/MEMORY.md`
  - raw experiment churn stays in registry/reports

- New doc rule:
  - do **not** trigger Law #8 doc sweeps for screening runs
  - trigger doc updates only when a candidate is accepted into the baseline or changes externally reported behavior

This avoids drowning the documentation layer in temporary experiment noise.

---

## 11. What Not To Do

Do not:
- let the agent edit the whole repo
- let the agent change eval harness and candidate simultaneously
- trust one-run wins
- use branch history as the experiment ledger
- optimize on a single static slice forever
- auto-promote anything that changes insurance or payout behavior without explicit human review

---

## 12. Recommended First Version For HewaSense

Start small:

1. Add `autoresearch/search_space.yaml` for one narrow family:
   - probability calibration parameters

2. Add one deterministic runner:
   - `autoresearch/runners/run_experiment.py`

3. Add one registry:
   - `autoresearch/registry/experiments.jsonl`

4. Add one goal:
   - `goals/autoresearch_loop.md`

5. Require manual promotion after:
   - 3-seed repeat
   - holdout check
   - safety metric check

This is enough to capture the useful autoresearch pattern without destabilizing the platform.

---

## 13. Promotion Criteria Example

Example policy:

- Screen pass:
  - primary metric improves by at least 0.5%

- Candidate pass:
  - average improvement remains positive across 3 seeds
  - no safety metric regression

- Promotion pass:
  - holdout metric still improves
  - no known-disaster recall degradation
- human reviewer signs off

---

## 14. Implementation Roadmap

### Phase 1: Minimal Viable Loop

Goal:
- prove the repo can run a constrained autonomous experiment loop safely

Deliverables:
- `autoresearch/search_space.yaml`
- `autoresearch/program.md`
- `autoresearch/registry/experiments.jsonl`
- `autoresearch/runners/run_experiment.py`
- `goals/autoresearch_loop.md`

Acceptance criteria:
- one bounded config family can be modified
- one deterministic runner executes the trial
- every run appends a structured registry record
- failed runs are recorded, not silently lost
- no docs outside the experiment area are changed by screening runs

### Phase 2: Validation and Promotion Gates

Goal:
- separate cheap screening from trustworthy promotion

Deliverables:
- `autoresearch/runners/compare_candidates.py`
- multi-seed validation mode
- holdout evaluation mode
- candidate vs baseline comparison report

Acceptance criteria:
- screening and promotion runs are explicitly different run types
- promotion requires repeated-seed evidence
- safety metric failures auto-block promotion
- accepted candidates are distinguishable from screened candidates in the registry

### Phase 3: HewaSense Safety Integration

Goal:
- ensure autoresearch cannot silently break insurance behavior

Deliverables:
- safety checks for off-season logic
- safety checks for advisory-tier exclusion
- safety checks for payout contract invariants
- reviewer checklist for insurance-affecting changes

Acceptance criteria:
- any candidate affecting trigger or payout behavior is auto-flagged for human review
- contract regressions fail before promotion
- promotion output includes both performance and safety summaries

### Phase 4: Operator Usability

Goal:
- make the system understandable and maintainable by humans

Deliverables:
- `autoresearch/reports/latest_summary.md`
- registry summarizer
- top-candidate leaderboard
- failure taxonomy summary

Acceptance criteria:
- a human can answer "what was tried, what worked, and what was promoted?" without reading git history
- repeated failure modes are visible across runs
- baseline changes are traceable to a promotion record

---

## 15. Task Breakdown

Recommended first implementation slices:

1. Add `autoresearch/search_space.yaml`
   - one family only
   - bounded numeric ranges
   - explicit editable files list

2. Add `autoresearch/program.md`
   - include hard constraints
   - include keep/reject rules
   - include promotion gate language

3. Build `run_experiment.py`
   - load baseline config
   - apply candidate override
   - run fixed evaluation
   - emit structured JSON result

4. Add registry writer
   - append-only JSONL
   - no overwrites
   - write failures as failures

5. Add `compare_candidates.py`
   - baseline vs candidate summary
   - pass/fail decision with reasons

6. Add `goals/autoresearch_loop.md`
   - connect the loop to GOTCHA
   - define inputs, outputs, and review gates

7. Add operator docs
   - how to run the loop
   - how to inspect results
   - what requires manual approval

---

## 16. Suggested Ownership Boundaries

To reduce confusion, separate responsibilities like this:

- Agent:
  - propose bounded candidate changes
  - execute deterministic runner
  - summarize results

- Tools:
  - run experiment
  - score experiment
  - compare candidate to baseline
  - append registry records

- Human reviewer:
  - approve promotions that affect insurance semantics
  - approve search-space expansions
  - approve externally consequential baseline moves

This keeps the agent out of the role of final scientific authority.

---

## 17. Open Questions Before Implementation

These should be answered before building Phase 1:

1. What is the first search family?
   - calibration
   - feature toggles
   - training hyperparameters

2. What is the primary metric for that family?
   - Brier Score
   - calibration error
   - held-out loss

3. What safety checks are mandatory in every run?
   - off-season exclusion
   - advisory-tier exclusion
   - payout-threshold integrity

4. What is the first promotion standard?
   - effect size threshold
   - number of seeds
   - holdout requirement

5. What should remain permanently out of scope for autoresearch?
   - payout logic
   - API contracts
   - deployment configuration

---

## 18. Final Position

The right HewaSense adaptation is not "build an autonomous scientist."

It is:
- a constrained experiment loop
- with deterministic runners
- a real experiment registry
- promotion gates
- human review at the boundary where model behavior affects insurance decisions

That would preserve the strongest part of the `autoresearch` idea while keeping the system compatible with GOTCHA, auditability, and scientific caution.
