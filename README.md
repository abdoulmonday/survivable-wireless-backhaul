# Survivable Wireless Backhaul — MILP and Classical Benders (v0.2)

A research-oriented Python implementation of reliability-aware, survivable wireless backhaul capacity planning, **inspired by** Raayatpanah et al. (2023).

> **Scope:** This is an independent educational reconstruction for small synthetic networks. It implements the deterministic-equivalent monolithic MILP and **classical Benders feasibility-cut decomposition with an elastic LP oracle**. It does **not** reproduce the accelerated Benders method of the paper, its SNDlib experiments, or measured radio-channel probabilities.

## Quick start

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
python -m pytest -q
python -m backhaul.demo
```

The comparison results are saved in `outputs/comparison.json`.

## Method

Each directed edge is configured with at most one radio option with a bandwidth, spectral efficiency, cumulative reliability probability, and cost. Each communication demand is routed as a divisible commodity, potentially with different flows in every node-failure scenario. The MILP minimizes cost and enforces:

1. Flow balance for intact network and each protected relay failure.
2. Limits on each flow and each intermediate node's total outgoing flow in the no-failure scenario (`sigma`).
3. Aggregate installed link capacity constraints for each scenario.
4. `sum(log(rho) * y) >= log(1-epsilon)`, under independent link fading.
5. At most one radio configuration per directed edge.

**Master:** integer radio selections `y`, plus reliability and feasibility cuts.

**Feasibility oracle:** solve the LP `min sum(abs(flow-balance residuals)) + sum(capacity/diversification violations)` for fixed `y` using nonnegative artificial variables. Its optimal value `theta(y)` is zero iff the flow problem is feasible. Dual marginals give a globally valid affine under-estimator `theta(y) >= theta(yhat)+g·(y-yhat)`; therefore, all feasible designs satisfy `g·y <= g·yhat-theta(yhat)`. This is the cut added to the master.

The *exact mathematical cut* depends on the LP relaxation used, and this implementation differs from the explicit extreme-ray Benders subproblem presented as Eq. (7) and (8) in the article. Both are valid feasibility-cut mechanisms.

## Repository

```text
src/backhaul/model.py        Problem data, baseline monolithic MILP, master model
src/backhaul/benders.py      Elastic feasibility LP and Benders cuts
src/backhaul/demo.py         Comparison script for a 4-node synthetic network
tests/test_benders.py        Benders/MILP agreement + feasibility tests
docs/benders_walkthrough.md  Equations and a step-by-step algorithm
.github/workflows/tests.yml Test workflow
```

## Demonstration (synthetic data)

For the four-node toy network with a single demand A→D (30 Mbit/s), protection against relay B and relay C failures, `sigma=0.5`, `alpha=1.0`, and `epsilon=0.05`, both approaches found a cost of 56 arbitrary units. Classical Benders converged in 63 master iterations with the included options and constraints. Results may vary with versions or numerical tolerances.

These figures are not results from the article. `rho` values are illustrative inputs, not measured network availability.

## Research roadmap

- [x] Formulate monolithic deterministic-equivalent MILP.
- [x] Implement classical feasibility-cut Benders decomposition.
- [x] Cross-check objective with monolithic MILP on synthetic cases.
- [ ] Profile MILP vs Benders over multiple graph sizes and demands.
- [ ] Reproduce the paper's extreme-ray dual cuts, cutset inequalities, warm starts, and upper-bound heuristic.
- [ ] Import benchmark SNDlib graphs; document link-specific options and probability distributions.
- [ ] Study correlated fading and larger simultaneous failures.

## Limitations

Assumes independent fading between selected links, fractional multicommodity flows, static demand rates, one failed relay at a time, no detailed spectrum-interference model, and user-supplied link reliability probabilities. A joint reliability probability is not an empirical uptime estimate. For larger instances the educational Benders implementation may perform worse than direct MILP; no speed-up is claimed.

## Citation

Raayatpanah, M. A., Beheshtkhah, M. K., Eshghi, F., Kelarestaghi, M., & Nepomuceno, N. (2023). *Design of survivable wireless backhaul networks with reliability considerations*. Computers & Operations Research, 151, 106120. https://doi.org/10.1016/j.cor.2022.106120
