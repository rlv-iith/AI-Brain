# Credit Risk AI — Finshield Hackathon 2025

**Category:** FinTech / Explainable ML  
**Result:** National Finalist  
**Stack:** XGBoost, SHAP, Docker Compose, FastAPI, React

## What it does
End-to-end credit risk decision platform with "glass-box" explainability. Given a loan applicant's data, the model outputs a risk score and a per-feature SHAP explanation that shows exactly why the decision was made — useful for auditors and regulators.

## Key technical decisions
- **XGBoost** chosen over deep models for interpretability and performance on tabular data
- **SHAP** waterfall charts surfaced the top 5 contributing features per prediction
- **Fairness-aware feature pipeline** handled edge cases like career breaks without penalising applicants unfairly
- **Docker Compose** bundled the FastAPI ML backend + React frontend as one deployable unit

## Impact
- National-level finalist out of hundreds of teams
- System could reduce manual credit review time by ~40% based on benchmark tests
