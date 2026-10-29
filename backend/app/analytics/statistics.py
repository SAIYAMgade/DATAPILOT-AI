from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from sqlalchemy import text
from sqlalchemy.orm import Session


class StatisticalAnalysisEngine:
    """Rigorous statistical testing engine for business analytics hypotheses using SciPy & Statsmodels."""

    def __init__(self, db: Session):
        self.db = db

    def test_segment_transaction_values(
        self,
        group_col: str = "acquisition_channel"
    ) -> Dict[str, Any]:
        """Compares transaction values between groups using Kruskal-Wallis / Mann-Whitney."""
        sql = text(f"""
            SELECT
                c.{group_col} AS group_name,
                t.amount
            FROM transactions t
            JOIN customers c ON t.customer_id = c.id
            WHERE t.status = 'completed' AND t.is_refund = false
        """)
        rows = self.db.execute(sql).mappings().all()
        if not rows:
            return {"error": "Insufficient transaction records for statistical testing."}

        df = pd.DataFrame(rows)
        groups = df.groupby("group_name")["amount"].apply(list).to_dict()
        group_names = list(groups.keys())

        if len(group_names) < 2:
            return {"error": "At least two distinct groups are required for comparison."}

        # Check sample sizes and summaries
        group_summaries = {}
        valid_groups = []
        for g_name, vals in groups.items():
            arr = np.array(vals)
            group_summaries[g_name] = {
                "sample_size": len(arr),
                "mean": round(float(np.mean(arr)), 2),
                "median": round(float(np.median(arr)), 2),
                "std": round(float(np.std(arr, ddof=1)), 2) if len(arr) > 1 else 0.0,
                "iqr": round(float(stats.iqr(arr)), 2)
            }
            if len(arr) >= 2:
                valid_groups.append(arr)

        if len(valid_groups) < 2:
            return {
                "error": "Insufficient sample size for comparison (at least 2 groups must have >= 2 observations).",
                "group_summaries": group_summaries
            }

        # Select test: Kruskal-Wallis for non-parametric multi-group comparison
        stat, p_val = stats.kruskal(*valid_groups)

        # Effect size: Epsilon-squared = (H - k + 1) / (n - k)
        total_n = sum(len(g) for g in valid_groups)
        k = len(valid_groups)
        eps_sq = (stat - k + 1) / (total_n - k) if total_n > k else 0.0
        eps_sq = max(0.0, min(1.0, eps_sq))

        is_sig = bool(p_val < 0.05)
        interpretation = (
            f"The difference in transaction values across {group_col} groups is statistically significant "
            f"(H={round(float(stat), 2)}, p={p_val:.4e}, ε²={round(float(eps_sq), 3)})."
            if is_sig else
            f"No statistically significant difference in transaction values was detected across {group_col} groups "
            f"(H={round(float(stat), 2)}, p={round(float(p_val), 4)})."
        )

        return {
            "business_question": f"Do customer transaction amounts differ significantly across {group_col}?",
            "null_hypothesis": f"Transaction value distributions are identical across all {group_col} groups.",
            "alternative_hypothesis": f"At least one {group_col} group has a different transaction value distribution.",
            "test_applied": "Kruskal-Wallis H-test (non-parametric ANOVA)",
            "sample_sizes": {g: len(v) for g, v in groups.items()},
            "group_summaries": group_summaries,
            "test_statistic": round(float(stat), 4),
            "p_value": float(p_val),
            "effect_size": {
                "metric": "epsilon_squared",
                "value": round(float(eps_sq), 4),
                "magnitude": "small" if eps_sq < 0.06 else ("medium" if eps_sq < 0.14 else "large")
            },
            "statistically_significant": is_sig,
            "interpretation": interpretation,
            "assumptions_and_limitations": [
                "Assumes independent transaction observations.",
                "Non-parametric test chosen due to right-skewed revenue amounts.",
                "Statistical difference does not imply commercial impact or causality."
            ]
        }

    def test_channel_retention_association(self) -> Dict[str, Any]:
        """Chi-square test of independence between Acquisition Channel and Customer Retention."""
        cutoff_dt = datetime.utcnow() - timedelta(days=60)
        sql = text("""
            WITH last_tx AS (
                SELECT customer_id, MAX(timestamp) AS last_dt
                FROM transactions
                WHERE status = 'completed' AND is_refund = false
                GROUP BY customer_id
            )
            SELECT
                c.acquisition_channel,
                CASE
                    WHEN l.last_dt >= :cutoff_dt THEN 'Retained'
                    ELSE 'Inactive'
                END AS retention_status
            FROM customers c
            LEFT JOIN last_tx l ON c.id = l.customer_id
        """)
        rows = self.db.execute(sql, {"cutoff_dt": cutoff_dt}).mappings().all()
        if not rows:
            return {"error": "Insufficient customer data."}

        df = pd.DataFrame(rows)
        contingency = pd.crosstab(df["acquisition_channel"], df["retention_status"])

        chi2_stat, p_val, dof, expected = stats.chi2_contingency(contingency)

        # Cramer's V effect size
        n = contingency.values.sum()
        min_dim = min(contingency.shape) - 1
        cramers_v = np.sqrt(chi2_stat / (n * min_dim)) if min_dim > 0 and n > 0 else 0.0

        is_sig = bool(p_val < 0.05)
        contingency_dict = contingency.to_dict(orient="index")

        return {
            "business_question": "Is customer 60-day retention associated with the customer acquisition channel?",
            "null_hypothesis": "Customer retention status is independent of acquisition channel.",
            "alternative_hypothesis": "Customer retention status depends on acquisition channel.",
            "test_applied": "Pearson's Chi-Square Test of Independence (χ²)",
            "contingency_table": contingency_dict,
            "degrees_of_freedom": int(dof),
            "test_statistic": round(float(chi2_stat), 4),
            "p_value": float(p_val),
            "effect_size": {
                "metric": "cramers_v",
                "value": round(float(cramers_v), 4),
                "magnitude": "negligible" if cramers_v < 0.1 else ("moderate" if cramers_v < 0.3 else "strong")
            },
            "statistically_significant": is_sig,
            "interpretation": (
                f"Retention rates differ significantly by channel (χ²={round(float(chi2_stat), 2)}, p={p_val:.4f}, V={round(float(cramers_v), 3)})."
                if is_sig else
                f"No statistically significant relationship was found between acquisition channel and retention (p={round(float(p_val), 4)})."
            ),
            "assumptions_and_limitations": [
                "Expected cell counts should generally be >= 5.",
                "Observational data; does not prove channels cause higher retention.",
                "Customer self-selection bias may confound acquisition channels."
            ]
        }

    def compute_metric_confidence_intervals(
        self,
        confidence: float = 0.95
    ) -> Dict[str, Any]:
        """Calculates 95% Confidence Intervals for Average Order Value and Active Rate."""
        sql = text("""
            SELECT amount
            FROM transactions
            WHERE status = 'completed' AND is_refund = false
        """)
        amounts = [float(r[0]) for r in self.db.execute(sql).all()]
        if not amounts:
            return {"error": "No transaction records found."}

        n = len(amounts)
        mean_val = float(np.mean(amounts))
        std_val = float(np.std(amounts, ddof=1))
        se = std_val / np.sqrt(n)

        # Student's t confidence interval
        ci_lower, ci_upper = stats.t.interval(confidence, df=n - 1, loc=mean_val, scale=se)

        # Retention rate Wilson interval
        sql_cust = text("""
            SELECT
                COUNT(id) AS total_custs,
                COUNT(CASE WHEN is_active = true THEN 1 END) AS active_custs
            FROM customers
        """)
        crow = self.db.execute(sql_cust).mappings().first()
        tot_c = crow["total_custs"] or 1
        act_c = crow["active_custs"] or 0
        p_hat = act_c / tot_c

        # Wilson score interval for proportion
        z = stats.norm.ppf((1 + confidence) / 2)
        denom = 1 + (z ** 2) / tot_c
        center = (p_hat + (z ** 2) / (2 * tot_c)) / denom
        delta = (z * np.sqrt((p_hat * (1 - p_hat) + (z ** 2) / (4 * tot_c)) / tot_c)) / denom
        prop_ci_lower = max(0.0, center - delta)
        prop_ci_upper = min(1.0, center + delta)

        return {
            "confidence_level": confidence,
            "average_order_value": {
                "mean": round(mean_val, 2),
                "standard_error": round(se, 3),
                "sample_size": n,
                "ci_lower": round(float(ci_lower), 2),
                "ci_upper": round(float(ci_upper), 2),
                "margin_of_error": round(float(ci_upper - mean_val), 2),
                "method": "Student's t-distribution"
            },
            "active_customer_rate": {
                "proportion": round(p_hat, 4),
                "active_count": act_c,
                "total_count": tot_c,
                "ci_lower": round(float(prop_ci_lower), 4),
                "ci_upper": round(float(prop_ci_upper), 4),
                "method": "Wilson score interval for binomial proportion"
            }
        }

    def test_monthly_revenue_trend(self) -> Dict[str, Any]:
        """OLS regression trend test for monthly revenue using Statsmodels."""
        sql = text("""
            SELECT
                DATE_TRUNC('month', timestamp) AS month_dt,
                SUM(CASE WHEN is_refund = false AND status = 'completed' THEN amount ELSE 0 END) AS revenue
            FROM transactions
            GROUP BY 1
            ORDER BY 1 ASC
        """)
        rows = self.db.execute(sql).mappings().all()
        if len(rows) < 4:
            return {"error": "Need at least 4 monthly periods for trend regression."}

        df = pd.DataFrame(rows)
        df["month_idx"] = np.arange(len(df))
        df["revenue"] = df["revenue"].astype(float)

        X = sm.add_constant(df["month_idx"])
        y = df["revenue"]

        model = sm.OLS(y, X).fit()

        slope = float(model.params["month_idx"])
        p_val = float(model.pvalues["month_idx"])
        r_sq = float(model.rsquared)
        ci = model.conf_int().loc["month_idx"]

        is_sig = bool(p_val < 0.05)
        return {
            "business_question": "Is there a statistically significant upward or downward trend in monthly revenue?",
            "null_hypothesis": "The monthly revenue trend slope is zero (no trend).",
            "alternative_hypothesis": "The monthly revenue trend slope is non-zero.",
            "test_applied": "Ordinary Least Squares (OLS) Linear Trend Model",
            "number_of_periods": len(df),
            "monthly_slope_estimate": round(slope, 2),
            "slope_95_ci": [round(float(ci[0]), 2), round(float(ci[1]), 2)],
            "r_squared": round(r_sq, 4),
            "t_statistic": round(float(model.tvalues["month_idx"]), 4),
            "p_value": float(p_val),
            "statistically_significant": is_sig,
            "interpretation": (
                f"Revenue exhibits a statistically significant {'upward' if slope > 0 else 'downward'} trend of "
                f"${abs(round(slope, 2)):,.2f} per month (p={round(p_val, 4)}, R²={round(r_sq, 3)})."
                if is_sig else
                f"No statistically significant linear trend in monthly revenue was observed (p={round(p_val, 4)})."
            ),
            "assumptions_and_limitations": [
                "Assumes linear relationship and uncorrelated residuals.",
                "Short time horizons are vulnerable to seasonal fluctuations."
            ]
        }
