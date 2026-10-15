# Research notes — reading guide

1. **Pages 1–3:** problem framing, backhaul, stochastic radio capacity, diversification and reservation.
2. **Pages 3–5, Eqs. (1)–(5):** original chance-constrained network-flow optimization and log-linear reformulation under independent fading.
3. **Pages 5–7, Eqs. (6)–(21):** Benders master (binary radio choices), feasibility subproblem (continuous multicommodity flow), dual cuts, and accelerations.
4. **Pages 8–10:** SNDlib benchmark instances, radio efficiencies, experiments, and solve-time comparison.

## Terminology

**Reliability:** probability capacity constraints are satisfied under random fading.

**Survivability:** post-failure feasibility for specified fractions of surviving demands.

**Diversification:** limits per-link and intermediate-node flow under no failure.

**Reservation:** additional installed capacity to support rerouting after failure.

## Scope

The source paper develops accelerated Benders decomposition. This v0.1 solves the monolithic deterministic-equivalent MILP for instructional purposes. Algorithm reproduction is a planned second stage, not a completed feature.
