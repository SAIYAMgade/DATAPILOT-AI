from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.models import BusinessInsight
from backend.app.analytics.metrics import BusinessMetricsEngine
from backend.app.analytics.cohorts import CohortRetentionEngine


class BusinessInsightEngine:
    """Generates deterministic, traceable business insights from verified database analytics."""

    def __init__(self, db: Session):
        self.db = db
        self.metrics_engine = BusinessMetricsEngine(db)
        self.cohort_engine = CohortRetentionEngine(db)

    def generate_all_insights(self) -> List[Dict[str, Any]]:
        """Evaluates deterministic business rules against database records and refreshes insight ledger."""
        insights = []

        # 1. Revenue Trajectory Insight (MoM comparison)
        summary = self.metrics_engine.get_executive_summary()
        m = summary["metrics"]
        growth = m["revenue_growth_pct"]
        rev_cur = m["total_revenue"]
        rev_prev = m["previous_revenue"]

        if rev_cur > 0 and rev_prev > 0:
            if growth < -5.0:
                insights.append({
                    "title": "Substantial Period-over-Period Revenue Contraction",
                    "category": "revenue",
                    "metric_name": "total_revenue",
                    "comparison_period": f"{summary['period']['comparison_start']} to {summary['period']['end_date']}",
                    "current_value": rev_cur,
                    "previous_value": rev_prev,
                    "change_pct": growth,
                    "severity": "critical" if growth < -15.0 else "warning",
                    "supporting_evidence": {
                        "current_revenue": rev_cur,
                        "previous_revenue": rev_prev,
                        "growth_pct": growth,
                        "aov": m["average_order_value"],
                        "total_orders": m["total_orders"]
                    },
                    "limitations": "Compares two consecutive 90-day windows without adjusting for seasonal cycle peaks."
                })
            else:
                insights.append({
                    "title": "Positive Revenue Trajectory Observed",
                    "category": "revenue",
                    "metric_name": "total_revenue",
                    "comparison_period": f"{summary['period']['comparison_start']} to {summary['period']['end_date']}",
                    "current_value": rev_cur,
                    "previous_value": rev_prev,
                    "change_pct": growth,
                    "severity": "info",
                    "supporting_evidence": {
                        "current_revenue": rev_cur,
                        "previous_revenue": rev_prev,
                        "growth_pct": growth
                    },
                    "limitations": "Linear trajectory assumes stable macro factors and acquisition rates."
                })

        # 2. Pareto Revenue Concentration Insight
        pareto = self.metrics_engine.get_pareto_concentration()
        top_share = pareto["top_20_pct_generates"]
        if top_share > 60.0:
            insights.append({
                "title": f"High Revenue Concentration: Top 20% Accounts Generate {top_share:.1f}% Revenue",
                "category": "risk",
                "metric_name": "pareto_top_20_share",
                "comparison_period": "All-time cumulative",
                "current_value": top_share,
                "previous_value": None,
                "change_pct": None,
                "severity": "warning" if top_share > 75.0 else "info",
                "supporting_evidence": {
                    "concentration_distribution": pareto["concentration_points"],
                    "top_20_pct_share": top_share
                },
                "limitations": "Pareto distribution is typical in SME B2B, but poses key-account concentration risk."
            })

        # 3. Churn Risk Exposure Insight
        sql_pred = text("""
            SELECT
                COUNT(id) AS total_scored,
                COUNT(CASE WHEN risk_category = 'High' THEN 1 END) AS high_risk,
                COUNT(CASE WHEN risk_category = 'Medium' THEN 1 END) AS med_risk
            FROM customer_risk_predictions
            WHERE model_version_id = (SELECT id FROM model_versions WHERE is_active = true ORDER BY id DESC LIMIT 1)
        """)
        p_row = self.db.execute(sql_pred).mappings().first()
        if p_row and p_row["total_scored"] and p_row["total_scored"] > 0:
            tot = p_row["total_scored"]
            hi = p_row["high_risk"]
            hi_pct = round((hi / tot * 100), 1)
            if hi_pct > 15.0:
                insights.append({
                    "title": f"Elevated Customer Inactivity Risk: {hi} Accounts ({hi_pct}%) in High Risk",
                    "category": "retention",
                    "metric_name": "high_risk_customer_ratio",
                    "comparison_period": "Next 60 days projection",
                    "current_value": hi_pct,
                    "previous_value": None,
                    "change_pct": None,
                    "severity": "critical" if hi_pct > 25.0 else "warning",
                    "supporting_evidence": {
                        "total_scored": tot,
                        "high_risk_count": hi,
                        "medium_risk_count": p_row["med_risk"],
                        "high_risk_pct": hi_pct
                    },
                    "limitations": "ML predictions are statistical probabilities, not guaranteed individual churn events."
                })

        # 4. Product Category Contribution Insight
        breakdowns = self.metrics_engine.get_breakdowns()
        cats = breakdowns["by_category"]
        if cats:
            top_cat = cats[0]
            bottom_cat = cats[-1]
            tot_cat_rev = sum(c["revenue"] for c in cats)
            top_share_cat = round((top_cat["revenue"] / tot_cat_rev * 100), 1) if tot_cat_rev > 0 else 0
            insights.append({
                "title": f"Leading Category '{top_cat['name']}' Powers {top_share_cat}% of Business Revenue",
                "category": "revenue",
                "metric_name": "category_share",
                "comparison_period": "All-time",
                "current_value": top_share_cat,
                "previous_value": None,
                "change_pct": None,
                "severity": "info",
                "supporting_evidence": {
                    "top_category": top_cat,
                    "lowest_category": bottom_cat,
                    "total_category_revenue": tot_cat_rev
                },
                "limitations": "Does not account for product cost of goods sold or individual category profit margins."
            })

        # 5. Cohort Retention Decay Insight
        cohort_res = self.cohort_engine.compute_cohort_matrix()
        summaries = [s for s in cohort_res.get("cohort_summary", []) if s.get("month_1_retention_pct") is not None]
        if len(summaries) >= 2:
            recent_m1 = summaries[-1]["month_1_retention_pct"]
            prior_m1 = summaries[-2]["month_1_retention_pct"]
            m1_diff = round(recent_m1 - prior_m1, 1)

            if m1_diff < -5.0:
                insights.append({
                    "title": f"Recent Cohort Retention Slippage: Month-1 Retention Dropped by {abs(m1_diff)}pp",
                    "category": "retention",
                    "metric_name": "month_1_retention_pct",
                    "comparison_period": f"{summaries[-2]['cohort']} vs {summaries[-1]['cohort']}",
                    "current_value": recent_m1,
                    "previous_value": prior_m1,
                    "change_pct": m1_diff,
                    "severity": "warning",
                    "supporting_evidence": {
                        "prior_cohort": summaries[-2]["cohort"],
                        "prior_m1_retention": prior_m1,
                        "latest_cohort": summaries[-1]["cohort"],
                        "latest_m1_retention": recent_m1
                    },
                    "limitations": "Recent cohorts have shorter seasoning time and may experience catch-up transactions."
                })

        # Save to database
        self.db.query(BusinessInsight).delete()
        for ins in insights:
            record = BusinessInsight(
                title=ins["title"],
                category=ins["category"],
                metric_name=ins["metric_name"],
                comparison_period=ins["comparison_period"],
                current_value=float(ins["current_value"]),
                previous_value=float(ins["previous_value"]) if ins["previous_value"] is not None else None,
                change_pct=float(ins["change_pct"]) if ins["change_pct"] is not None else None,
                supporting_evidence=ins["supporting_evidence"],
                limitations=ins["limitations"],
                severity=ins["severity"]
            )
            self.db.add(record)
        self.db.commit()

        return insights
