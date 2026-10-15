# Survivable Wireless Backhaul Network Optimization

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)  ![MILP](https://img.shields.io/badge/optimization-MILP-green)

A **research-oriented Python implementation** inspired by Raayatpanah *et al.* (2023), *Design of survivable wireless backhaul networks with reliability considerations*.

**What it does:** minimize provisioned microwave-link cost while meeting traffic demand, probabilistic reliability, route diversification, and single-relay failure survivability requirements.

> **Reproducibility statement:** This is a small-instance educational implementation of the paper's deterministic-equivalent MILP (Eq. 5), **not** an implementation of the accelerated Benders algorithm, not a full replication of published experiments, and not radio-hardware validation. All demo data and link probabilities are synthetic.

## Core concepts

- Wireless backhaul links use discrete bandwidth and spectral-efficiency options.
- Capacity (Mbit/s) = bandwidth (MHz) × spectral efficiency (bit/s/Hz).
- Link radio configurations have assumed probabilities of meeting their nominal designed capacity.
- Under the **independent fading** assumption, the joint chance constraint becomes `sum(log(rho) * y) >= log(1 - epsilon)`.
- `sigma` limits intact-scenario traffic on each link and on intermediate-node outgoing arcs, promoting node-disjoint flows.
- `alpha` determines the fraction of each surviving demand that must remain routable after any modeled relay failure.
- Individual source/destination failures terminate the associated demands, following the paper's scenario convention.

## Quick start

```bash
python -m venv .venv
# Linux / macOS:
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
python -m pytest -q
python -m backhaul.demo --output outputs
```

`outputs/result.json` contains the selected microwave links, scenario-specific multicommodity flows, total cost, joint reliability, and solver gap. `outputs/network.png` visualizes installed link capacities (Mbit/s).

Try alternative resilience levels:

```bash
python -m backhaul.demo --sigma 0.75 --alpha 0.5 --epsilon 0.05
python -m backhaul.demo --sigma 0.5 --alpha 1.0 --epsilon 0.01
```

## Optimization model

### Decisions

- `y[e,p,q] ∈ {0,1}`: choose at most one radio option on each directed arc.
- `x[h,k,e] >= 0`: demand-`k` flow on arc `e` under failure scenario `h`.

### Objective

Minimize `sum_e,p,q cost[e,p] * y[e,p,q]`.

### Constraints

1. Flow conservation for each surviving demand in every scenario.
2. At most one bandwidth/radio configuration per arc.
3. Allocated capacity bounds aggregate routed flow in every scenario.
4. Diversification limits for the no-failure scenario.
5. Independent-link joint reliability bound.

The model is solved with `scipy.optimize.milp` (HiGHS). The scenario flows are **recourse solutions**: routes may change when a node fails. Costs exclude rerouting overhead and radio implementation expenses.

## Repository layout

```text
src/backhaul/model.py      Optimization model and solver
src/backhaul/demo.py       Synthetic test topology and plot
examples/                  Example definitions and commands
tests/                     Automated optimization tests
docs/                      Mathematical explanation and research roadmap
.github/workflows/tests.yml  GitHub Actions CI
```

## Scientific limitations

- Assumes independent per-link radio fading probabilities supplied externally. Correlated weather or shared-site failures are not modeled.
- Uses a *joint* constraint over selected links (as in Eq. 5f); it is not a Monte Carlo estimate of annual availability.
- Tests only small synthetic graphs and single relay failures. Does not claim to replicate SNDlib results or computational benchmarks.
- Uses fractional multicommodity flows; packet-level behaviors, routing convergence, spectrum interference, propagation, and channel simulation are out of scope.
- In particular, the probability assigned to a chosen spectral-efficiency threshold is an input assumption, not an empirically calibrated radio probability.
- A result is described as optimal only when the MILP solver reports an optimal termination.

## Research development roadmap

1. Implement a classic Benders feasibility-cut decomposition and cross-check solutions against the monolithic MILP.
2. Add valid cutset inequalities, improved initialization and deep-cut separation, as described in the paper.
3. Import original SNDlib topologies and reproduce benchmark settings using transparently documented radio distributions and solver settings.
4. Compare diversification-only, reservation-only, and hybrid strategies for multiple epsilon values.
5. Extend toward correlated fading, multiple simultaneous failures, risk measures, and learning-based failure probability estimation.
6. Publish controlled benchmarks (instance size, runtime, objective, optimality gap, seed and hardware).

## Citation

Raayatpanah, M. A., Beheshtkhah, M. K., Eshghi, F., Kelarestaghi, M., & Nepomuceno, N. (2023). *Design of survivable wireless backhaul networks with reliability considerations*. Computers & Operations Research, 151, 106120. https://doi.org/10.1016/j.cor.2022.106120

This project is an independent educational reimplementation, not an official repository of the authors.

## License

MIT for this repository's original code. The referenced research article remains under its publisher's copyright; it is not bundled in this repository.
