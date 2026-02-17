# Identification Strategy — Feb 17, 2026

Status: **Active decision** — to be implemented next

## Background

The original Cholesky ordering (util → liq → vol) imposes that a volatility shock has no
contemporaneous effect on liquidation. At daily frequency in DeFi, this is indefensible:
Perez et al. (2021) show 70%+ of liquidations fire within the same block (~12 sec) as the
triggering price move. The thesis's own H1 rejection (utilization doesn't predict liquidation)
confirms that liquidations are event-driven by price shocks, not by utilization buildup —
which directly contradicts the restriction that price/volatility can't affect liquidation same-day.

Prompted by peer feedback at Feb 2026 presentation. Full analysis in
`identification brainstorm feb17.pdf` (project root).

## Primary Specification: Option A — Reversed Cholesky

**Ordering: vol → liq → util**

```
         µ_vol   µ_liq   µ_util
u_vol  [   *       0       0    ]
u_liq  [   *       *       0    ]
u_util [   *       *       *    ]
```

### The three zero restrictions

| # | Restriction | Economic claim | Strength |
|---|---|---|---|
| 1 | Liq shock → no same-day effect on vol | Liquidation price impact is second-order vs. market-wide price shock at daily aggregation | **Moderate** — weakest of the three |
| 2 | Util shock → no same-day effect on vol | Protocol-level borrowing doesn't move ETH price | **Very strong** |
| 3 | Util shock → no same-day effect on liq | Borrowing changes don't trigger liquidations | **Very strong** — matches H1 rejection, Heimbach & Huang (2024) |

### Defense of Zero #1 (the weak link)

**Quantitative argument**: Daily liquidation volume across all DeFi protocols is typically
<0.1% of collateral asset daily trading volume. Even applying Lehar & Parlour's (2022)
38.7% permanent price impact coefficient at the transaction level, the implied daily price
change from liquidations is ~1-5 bps against typical ETH daily moves of 200-500 bps.

**Precedent**: This follows the "small open economy" defense standard in international
macro SVARs (Cushman & Zha 1997, Kim & Roubini 2000) — Canada's domestic demand
shocks don't contemporaneously affect world oil prices because Canada is ~2% of world
GDP. Same logic: Aave liquidations are to ETH price what Canadian demand is to world
oil prices.

Also parallels Kilian (2009) oil market SVAR, where speculative demand shocks are
restricted from affecting physical oil production within the month, defended by computing
the ratio of speculative flows to physical supply.

**Empirical validation (TODO)**: Compute the ratio of daily liquidation USD volume to
daily trading volume of the collateral assets across our sample. Present as a table/figure
in the thesis to empirically ground this restriction.

### Economic narrative

Exogenous market volatility (price shocks) is the primitive driver → triggers liquidation
cascades in protocols where positions breach health factors → utilization adjusts last as
surviving borrowers respond (deleverage or get liquidated) and new borrowers enter.

This aligns with the thesis's own empirical findings and the DeFi literature.

## Complementary Specification: Option B1 — Blanchard-Quah with Log Price Level

**Replace realized volatility with log collateral basket price level.**

| Variable | Integration | Entry |
|---|---|---|
| log_basket_price | I(1) | Differenced (= basket return) |
| liquidation | I(0) | Levels |
| utilization | I(0) | Levels |

### Long-run restrictions

- "Liquidation shocks have no permanent effect on the basket price level" — **very strong**.
  Cascading liquidations cause temporary price dislocations, but the long-run price of
  ETH is determined by fundamentals, not by Aave liquidations.
- "Utilization shocks have no permanent effect on the basket price level" — **very strong**.
  Borrowing demand on a lending protocol doesn't alter fundamental asset value.

### Why this works

With one I(1) variable (log price), the long-run impact matrix has one non-trivial row.
The two zero restrictions on that row (liq and util shocks don't permanently shift price)
fully identify the system. This is the standard Blanchard-Quah (1989) setup generalized
to three variables.

### What it tells you

| | Option A | Option B1 |
|---|---|---|
| **Variable** | Realized volatility (I(0)) | Log basket price level (I(1)) |
| **ID scheme** | Short-run Cholesky | Long-run Blanchard-Quah |
| **Question** | Does liq amplify *risk* (second moment)? | Does liq amplify *price declines* (first moment)? |
| **Ordering** | vol → liq → util | price → liq → util |

If both tell the same qualitative story — that liquidation cascades propagate meaningfully
through the system — that is convergent validity from two independent identification
strategies on two different economic objects.

### Trade-off

B1 shifts the research question from volatility amplification to price amplification. This is
closely related but not identical. Volatility is about uncertainty/risk; price level is about
directional impact. Both are relevant to the thesis question about feedback loops.

## Robustness Checks

### All 6 orderings (Option D)

Run Cholesky with all 6 permutations. Report pairwise IRF correlations across orderings
in a table. If qualitatively stable, this shows results aren't driven by ordering assumptions.

### Hourly frequency (if feasible)

Re-estimate with hourly data. At hourly frequency, the contemporaneous timing argument
for vol → liq → util becomes much stronger (price move in hour 1 → liquidations in hour 2
→ utilization adjusts in hour 3). If same patterns hold, this validates the daily specification.

## Why NOT the other options

| Option | Why not (for now) |
|---|---|
| **B (BQ on current variables)** | All three variables are I(0). Long-run impact matrix is trivially zero — restrictions have no bite. |
| **C (Sign restrictions)** | Set identification yields wide bounds, potentially uninformative. Not natively supported in Pedroni framework. |
| **E (External instrument)** | Strongest ID but most implementation work. BTC returns as instrument for vol shock is viable. Flagged as future work. |
| **F (Hybrid SR+LR)** | Requires I(1) variable for the LR restriction. Same stationarity problem as B. |

## Implementation Plan

1. **Option A**: Change `variable_order` and `lr_constraint`/`lr_sign` in notebook to
   `['volatility', 'liquidation', 'utilization']`. Re-run.
2. **Quantitative defense**: Compute liquidation-to-trading-volume ratio from existing data.
3. **All 6 orderings**: Loop over permutations, store IRFs, compute correlation matrix.
4. **Option B1**: Construct log basket price variable from existing composition + price data.
   Estimate separate BQ-identified SVAR.

## Key References

- **Pedroni (2013)** — Core framework. Supports both SR and LR identification.
- **Blanchard & Quah (1989)** — Long-run restrictions. Requires I(1) variables.
- **Cushman & Zha (1997), Kim & Roubini (2000)** — Precedent for "small entity" quantitative defense of zero restrictions.
- **Kilian (2009)** — Oil SVAR; quantitative defense of ordering restrictions via volume ratios.
- **Lehar & Parlour (2022)** — 38.7% permanent liquidation price impact at transaction level.
- **Heimbach & Huang (2024)** — Leverage increases vulnerability but doesn't predict liquidation.
- **Perez et al. (2021)** — 70%+ of liquidations within same block.
