# Learning Benders feasibility cuts step by step

## 1. Planning decisions and recourse decisions

Planning variables `y[e,j]` are binary, while `x[h,k,e]` are nonnegative flows for demand `k` on arc `e` in scenario `h`. When a node fails, all its incident arcs are removed and the same installed capacity must support a new routing pattern. The design objective minimizes the sum of bandwidth configuration costs.

## 2. Master

The master only retains `y` with the at-most-one-option-per-arc constraint, the independent-link reliability inequality and all accumulated Benders cuts. Before a cut is added, the master can propose an impossibly cheap solution with no working path.

## 3. Feasibility oracle

At proposed `yhat`, solve an LP whose variables are flows `x>=0` plus equality-restoration slacks (`s_plus,s_minus`) and inequality-restoration slacks (`r>=0`). The model is always feasible because violations can be paid for. Objective: minimize the sum of violations. The optimal objective `theta(yhat)` is zero if and only if the original scenario flow equations and inequalities are feasible.

In matrix notation with capacity effects stored as `B y`, the oracle solves:

```
min     sum(s_plus) + sum(s_minus) + sum(r)
s.t.    Aeq*x + s_plus - s_minus = beq
         Aub*x - r <= d + B*yhat
         x,s_plus,s_minus,r >= 0
```

## 4. Dual-based feasibility cut

By LP duality, the optimal oracle value is a convex, piecewise-linear function of the capacity right-hand sides. If `m` denotes the optimal inequality marginals returned by HiGHS, let `g = m @ B`.

Then for any alternative master decision `y`:

```
theta(y) >= theta(yhat) + g @ (y-yhat)
```

A fully feasible design satisfies `theta(y)=0`, hence must satisfy

```
g @ y <= g @ yhat - theta(yhat).
```

This necessary inequality is the new Benders cut. If `theta(yhat)>0`, this cut excludes the current design because it would violate the inequality by `theta(yhat)`.

This is a pedagogical feasibility-cut formulation, not the paper's extreme-ray implementation from Eqs. (7)-(8).

## 5. Termination

If the oracle violation is within tolerance and the master MILP solver certifies optimality, the current design is feasible and globally optimal for the mathematical model. Otherwise, keep cutting until a solution is found or the iteration limit is reached.

## 6. What to measure in research

Record number of nodes, arcs, demands, failure scenarios, radio options, master solve times, oracle times, Benders iterations, total wall time, objective, reliability probability, and optimum/MIP gap. Repeat on consistent hardware and controlled solver versions.
