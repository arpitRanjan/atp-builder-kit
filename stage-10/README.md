# Stage 10: did it pay off?

## Decision readout

- **What I measured.** 20 traced requests (`tracing_summary.json`): p50 latency 644 ms, p95 971 ms, time to
  first token p50 194 ms, $0.000574 per request and $0.000604 per successful task (19 of 20 succeeded).
  The `model_call` span drives all of the spend (`span_costs.csv`). One cost lever, a cascade on one shared
  history, on the same 10 turn workload (`cost_lever.csv`): $0.002617 vs $0.005751 for the strong model on
  every turn (54 percent less), but quality fell from 9/9 to 6/9.
- **The threshold I set before the analysis** (`ab_threshold.json`, saved before the data was read):
  SHIP only if the lower end of the 95 percent interval is above 0 and the lift is at least 1 point;
  if the segment mix differs, use the segment adjusted lift and find out why before acting.
- **The decision.** The rule says SHIP on the adjusted lift of +2.4 points (95 percent interval +0.2 to +4.6,
  n = 2,000 per arm) (`ab_readout.md`). But the mix-shift check fired (the pooled lift was -4.0 points), so I am
  holding the ship until the assignment is checked. I am also not shipping the cascade: it saves money but
  fails 3 of 9 quality checks.
- **Next step.** Find out why the platform mix differs between the arms (assignment or logging), then re-run
  the readout on a clean split.

Metric tree: `metric-tree.md`. Code changed outside `stage-10/`: none; the spans come from `kit/tracing.py`
around `app/app.py`'s answer function.
