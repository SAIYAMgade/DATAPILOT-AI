import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.analytics.metrics import BusinessMetricsEngine
from backend.app.analytics.segmentation import CustomerSegmentationEngine
from backend.app.analytics.cohorts import CohortRetentionEngine
from backend.app.analytics.statistics import StatisticalAnalysisEngine
from backend.app.ml.prioritization import RetentionPrioritizationEngine
from backend.app.insights import BusinessInsightEngine


class ControlledAnalyticsAssistant:
    """Safe, provider-agnostic analytics assistant routing user queries to verified backend calculations."""

    def __init__(self, db: Session):
        self.db = db
        self.metrics_engine = BusinessMetricsEngine(db)
        self.segmentation_engine = CustomerSegmentationEngine(db)
        self.cohort_engine = CohortRetentionEngine(db)
        self.stats_engine = StatisticalAnalysisEngine(db)
        self.prioritization_engine = RetentionPrioritizationEngine(db)
        self.insight_engine = BusinessInsightEngine(db)

    def query(self, question: str) -> Dict[str, Any]:
        """Resolves intent, calls verified analytical engine, and formats factual response."""
        q = question.lower().strip()

        # Route 1: Revenue or executive KPI question
        if any(w in q for w in ["revenue", "sales", "aov", "average order", "kpi", "growth"]):
            summary = self.metrics_engine.get_executive_summary()
            m = summary["metrics"]
            p = summary["period"]
            ans = (
                f"For the 90-day period ({p['start_date']} to {p['end_date']}), total net revenue is "
                f"${m['total_revenue']:,.2f} with an Average Order Value (AOV) of ${m['average_order_value']:,.2f} "
                f"across {m['total_orders']:,} orders. "
                f"Compared to the preceding period ({p['comparison_start']} to {p['comparison_end']}), "
                f"revenue changed by {m['revenue_growth_pct']:+.2f}%."
            )
            return {
                "question": question,
                "intent": "revenue_summary",
                "answer": ans,
                "data": summary,
                "limitations": "Calculations exclude refunded and cancelled orders."
            }

        # Route 2: Churn or Risk Prioritization question
        if any(w in q for w in ["churn", "risk", "at-risk", "prioritize", "retention", "leave"]):
            priorities = self.prioritization_engine.generate_predictions_and_priorities(limit=5)
            if "error" in priorities:
                return {
                    "question": question,
                    "intent": "churn_risk",
                    "answer": f"Unable to assess risk: {priorities['error']}",
                    "data": priorities,
                    "limitations": "Requires a trained machine learning model version."
                }
            top_custs = priorities.get("prioritized_customers", [])
            top_names = ", ".join([f"{c['name']} (Risk: {c['risk_score']:.0%}, Priority: {c['priority_score']})" for c in top_custs[:3]])
            ans = (
                f"The active ML model identified {priorities.get('high_risk_count', 0)} high-risk accounts out of "
                f"{priorities.get('total_customers_scored', 0)} scored. "
                f"Top accounts prioritized for immediate retention outreach: {top_names}."
            )
            return {
                "question": question,
                "intent": "retention_prioritization",
                "answer": ans,
                "data": priorities,
                "limitations": "Probabilities represent statistical risk of 0 transactions over 60 days, not causal destiny."
            }

        # Route 3: Customer Segment question
        if any(w in q for w in ["segment", "rfm", "vip", "frequent", "customer group"]):
            rfm = self.segmentation_engine.compute_rfm_segments()
            summaries = rfm.get("summary", [])
            summary_str = "; ".join([f"{s['segment']}: {s['customer_count']} accounts (${s['total_revenue']:,.0f})" for s in summaries])
            ans = (
                f"Customer accounts are segmented using deterministic RFM rules. Segment breakdown: {summary_str}."
            )
            return {
                "question": question,
                "intent": "customer_segmentation",
                "answer": ans,
                "data": rfm,
                "limitations": "RFM categories reflect past 90-day transaction recency, frequency, and spend."
            }

        # Route 4: Cohort Retention question
        if any(w in q for w in ["cohort", "retention rate", "month 1", "lifecycle"]):
            cohorts = self.cohort_engine.compute_cohort_matrix()
            c_summaries = cohorts.get("cohort_summary", [])
            recent = c_summaries[-1] if c_summaries else {}
            ans = (
                f"Cohort analysis tracks {len(c_summaries)} monthly acquisition cohorts. "
                f"The latest analyzed cohort ({recent.get('cohort', 'N/A')}) started with {recent.get('initial_size', 0)} accounts "
                f"and has generated ${recent.get('total_revenue', 0):,.2f} total revenue to date."
            )
            return {
                "question": question,
                "intent": "cohort_retention",
                "answer": ans,
                "data": cohorts,
                "limitations": "Only completed qualifying orders count toward monthly retention."
            }

        # Route 5: Statistical significance or hypothesis question
        if any(w in q for w in ["stat", "hypothesis", "significant", "p-value", "difference", "test"]):
            st = self.stats_engine.test_segment_transaction_values(group_col="acquisition_channel")
            ans = st.get("interpretation", "Statistical test completed.")
            return {
                "question": question,
                "intent": "statistical_test",
                "answer": ans,
                "data": st,
                "limitations": "Observational transaction data; tests correlation and distribution shift, not causality."
            }

        # Route 6: Fallback for ambiguous or unsupported queries
        return {
            "question": question,
            "intent": "ambiguous",
            "answer": (
                "I can answer verified analytical questions about: (1) Total revenue & growth trends, "
                "(2) Customer churn risk & prioritization, (3) RFM customer segments, "
                "(4) Monthly cohort retention matrices, or (5) Statistical hypothesis testing across channels."
            ),
            "data": None,
            "limitations": "To ensure auditability, questions outside approved analytical endpoints cannot be answered."
        }
