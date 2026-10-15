# Survivable Wireless Backhaul Network Optimization (v0.3)

**Research-oriented Python project:** mixed-integer programming, classical Benders feasibility cuts, and capacity cutset-inequality acceleration for resilient wireless backhaul planning.

> **Scientific scope:** independent educational reimplementation inspired by the cited paper, on **synthetic small networks**. This is **not** an official implementation of the authors' accelerated Benders algorithm or a replication of the SNDlib benchmarks. Our cutset separation exhaustively enumerates subsets on small networks; it is not suitable for large networks.

## Scientific paper / Article de référence

**Raayatpanah, M. A., Beheshtkhah, M. K., Eshghi, F., Kelarestaghi, M., & Nepomuceno, N. (2023).** *Design of survivable wireless backhaul networks with reliability considerations*. **Computers & Operations Research**, **151**, article **106120**.

- DOI: **[10.1016/j.cor.2022.106120](https://doi.org/10.1016/j.cor.2022.106120)**
- Journal: *Computers & Operations Research* (Elsevier)
- Relevant material: Section 4 (mathematical formulation, especially Eq. 5); Section 5 (Benders and valid inequalities); Section 6 (computational experiments).

**What this project reproduces conceptually:** a deterministic-equivalent survivable wireless-backhaul capacity-design MILP, node-failure flow recourse, log-linear independent-link reliability, and feasibility-cut decomposition.

**What is our own educational extension:** enumerated necessary directed cutset capacity inequalities for speeding up feasibility-cut Benders on small networks. **What is not reproduced:** the complete accelerated algorithm in the paper, its separation ILP, initialization heuristic, extreme-ray implementation, radio probability estimation and published benchmarks. Cite the paper for the scientific formulation, *not* for performance figures obtained in this repository.

### BibTeX

```bibtex
@article{raayatpanah2023survivable,
  title={Design of survivable wireless backhaul networks with reliability considerations},
  author={Raayatpanah, Mohammad Ali and Beheshtkhah, Mahdi Kabiri and Eshghi, Farshad and Kelarestaghi, Manoochehr and Nepomuceno, Napole\~ao},
  journal={Computers \& Operations Research},
  volume={151},
  pages={106120},
  year={2023},
  doi={10.1016/j.cor.2022.106120}
}
```

## Setup (Windows PowerShell)

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest -v
python -m backhaul.demo
python -m backhaul.benchmark
```

On Linux/macOS use `python3 -m venv .venv; source .venv/bin/activate` and the same remaining commands. The optional benchmark outputs `outputs/benchmark.json`, a **single-run demonstration, not a rigorous speed-up study**.

## Three versions / Trois étapes

| Version | Main implementation | Purpose |
|---|---|---|
| 0.1 | Direct MILP | Baseline flow-routing and radio-design optimization |
| 0.2 | Classical Benders | Separate binary design (master) and continuous flow-feasibility (LP oracle) |
| 0.3 | Cutset-enhanced Benders | Add necessary capacity cuts before expensive flow checks |

## Mathematics (simplified)

For each directed arc `(u,v)` and radio choice `j`, the binary variable `y[e,j]` selects capacity `B[e,j]` at cost `c[e,j]`. Flows `x[h,k,e] >= 0` route a demand `k` under failure scenario `h`.

Minimize `sum c[e,j] y[e,j]` under flow balance, per-scenario capacity, diversity limits, radio-choice constraints, and independent-fading chance constraint `sum log(rho[e,j]) y[e,j] >= log(1-epsilon)`.

For each scenario `h` and nonempty strict set of surviving nodes `S`, the necessary directed cutset condition is:

`sum_{e=(u,v): u in S, v outside S} sum_j B[e,j] y[e,j] >= sum_{k: source in S, target outside S} alpha[h,k] d[k]`.

It is **necessary but not sufficient** for multicommodity flow feasibility. This is why the LP oracle is still required even after all cutset checks pass.

## Files

```text
src/backhaul/model.py       Data classes, Instance, master, monolithic MILP
src/backhaul/benders.py     Elastic flow LP, dual feasibility cuts
src/backhaul/cutsets.py     Directed cutset enumeration and separation
src/backhaul/accelerated.py Cutset-enhanced Benders implementation
src/backhaul/demo.py        4-node synthetic baseline and solver comparison
src/backhaul/benchmark.py   Small illustrative timing comparison
tests/test_benders.py       Baseline solver agreement and validity tests
tests/test_cutsets.py       Cutset and accelerated solver tests
docs/benders_walkthrough.md Mathematical introduction
docs/defense_guide.md        Detailed v0.1–v0.3 learning and jury Q&A
.github/workflows/tests.yml Automated testing
```

## Results and limitations

On the synthetic 4-node demo, direct MILP, classical Benders, and cutset-enhanced Benders should find the same optimal provisioning cost, subject to solver termination. `solve_accelerated` reports cutset cuts, Benders cuts, iterations, and oracle calls. No universal speed advantage is claimed: small-instance runtime is noisy, and exhaustive subset enumeration scales exponentially with node count.

Assumptions include independent fading; fractional multicommodity flows; deterministic demand; independently reassigned routing in failure scenarios; one relay failure at a time; assumed (not measured) link reliability; no spectrum/interference or propagation simulation.

## Research roadmap

- [x] Monolithic MILP, classical Benders, and small-instance cutset-enhanced Benders
- [x] Automated tests and transparent scientific attribution
- [ ] Multiseed, multisize benchmarking with machine/solver/version metadata
- [ ] Polynomial-time special-case separation and the paper's separation MILP / stronger inequalities
- [ ] Improved Benders initial solution, heuristic bounds, and extreme-ray cuts
- [ ] Import SNDlib topologies and reproduce comparable experimental settings
- [ ] Investigate correlated weather fades, multiple failures and uncertainty calibration

## License

MIT for independently authored code; the referenced article is not redistributed by this repository.
