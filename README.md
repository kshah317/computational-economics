# Computational Economics

Data-driven analyses in economics and public policy: causal inference, forecasting, and applied data work on economic/policy questions.

**Suggested GitHub topics:** `computational-economics` `policy-analysis` `data-analysis` `econometrics` `python` `r`

## Structure

One subfolder per analysis under `projects/`. If a project grows large or needs its own release cycle, split it into its own top-level repo later — start here and promote only when it earns it.

```
computational-economics/
├── README.md
└── projects/
    ├── example-policy-analysis/   <- rename per project; one README each
    └── growth-convergence/
```

## Projects

| Project | Question | Data source | Key finding |
|---|---|---|---|
| [example-policy-analysis](projects/example-policy-analysis) | *placeholder* | *placeholder* | *placeholder* |
| [growth-convergence](projects/growth-convergence) | Did poorer countries grow faster than rich ones between 1990 and 2023? | World Bank, GDP per capita (PPP) | Yes, on average. The slope is significantly negative (p = 0.0001), though the fit is loose (R² = 0.085) since plenty of countries diverge instead of converging. |

## Conventions

- Each project folder gets its own README with: the question, data source(s) and license, method, and headline result.
- Raw data isn't committed if large or license-restricted — link to source and include a fetch/download script instead.
