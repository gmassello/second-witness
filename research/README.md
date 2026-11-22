# Research

Evidence behind the figures in `docs/BRIEF.md`. Not part of Second Witness: no requirement, flow or test of the product depends on this directory.

| File | What it does | Command |
|---|---|---|
| `fetch.py` | Downloads one month of GMN data into `raw/` (gitignored): the monthly trajectory summary, the station coordinates and the per-night upload index of every country. Cached per file; 404 days are marked and skipped | `python3 research/fetch.py 202610` |
| `measure.py` | Computes the network figures the BRIEF cites (two-station orbits, islands, cut points, country shares, third-witness uncertainty, closest islands, stations that stopped, running cameras with no partner). Standard library only | `python3 research/measure.py 202610 --prev 202609 --json research/metrics-202610.json` |
| `measure.py --self-check` | Asserts on a small synthetic network | `python3 research/measure.py --self-check` |
| `metrics-202610.json` | Output for October 2026 against September 2026 | — |

Data: Global Meteor Network, CC BY 4.0 — https://globalmeteornetwork.org/data/ (cite Vida et al. 2020, MNRAS 491(2), and Vida et al. 2021, MNRAS 506(4)).
