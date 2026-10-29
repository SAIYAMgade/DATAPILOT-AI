from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session


class CustomerSegmentationEngine:
    """Interpretable, rule-based RFM customer segmentation engine."""

    DEFAULT_THRESHOLDS = {
        "recency_active_days": 45,
        "recency_at_risk_days": 90,
        "frequency_high": 6,
        "monetary_high_quantile": 0.75,
        "new_customer_window_days": 60,
    }

    def __init__(self, db: Session):
        self.db = db

    def compute_rfm_segments(
        self,
        as_of_date: Optional[datetime] = None,
        custom_thresholds: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Calculates customer RFM values and segments them using deterministic business rules."""
        if not as_of_date:
            max_tx = self.db.execute(text("SELECT MAX(timestamp) FROM transactions")).scalar()
            ref_date = max_tx if max_tx else datetime.utcnow()
        else:
            ref_date = as_of_date
        t = {**self.DEFAULT_THRESHOLDS, **(custom_thresholds or {})}

        # Query RFM metrics per customer via SQL
        sql = text("""
            WITH customer_tx AS (
                SELECT
                    c.id AS customer_id,
                    c.customer_ref,
                    c.name,
                    c.signup_date,
                    c.acquisition_channel,
                    c.region,
                    COUNT(t.id) AS total_orders,
                    COALESCE(SUM(CASE WHEN t.is_refund = false AND t.status = 'completed' THEN t.amount ELSE 0 END), 0) AS total_revenue,
                    COALESCE(AVG(CASE WHEN t.is_refund = false AND t.status = 'completed' THEN t.amount END), 0) AS aov,
                    MAX(t.timestamp) AS last_order_date,
                    MIN(t.timestamp) AS first_order_date
                FROM customers c
                LEFT JOIN transactions t ON c.id = t.customer_id
                GROUP BY c.id, c.customer_ref, c.name, c.signup_date, c.acquisition_channel, c.region
            )
            SELECT
                customer_id,
                customer_ref,
                name,
                signup_date,
                acquisition_channel,
                region,
                total_orders,
                total_revenue,
                aov,
                last_order_date,
                first_order_date
            FROM customer_tx
        """)

        rows = self.db.execute(sql).mappings().all()
        if not rows:
            return {"segments": {}, "customers": [], "thresholds": t}

        # Calculate monetary cutoff dynamically or use threshold
        revenues = [float(r["total_revenue"]) for r in rows if r["total_revenue"] > 0]
        vip_rev_cutoff = float(sorted(revenues)[int(len(revenues) * t["monetary_high_quantile"])]) if revenues else 2000.0

        categorized = []
        segment_counts: Dict[str, Dict[str, Any]] = {
            "High-Value Active": {"count": 0, "revenue": 0.0, "avg_orders": 0.0},
            "Frequent Loyal": {"count": 0, "revenue": 0.0, "avg_orders": 0.0},
            "New Customer": {"count": 0, "revenue": 0.0, "avg_orders": 0.0},
            "Declining / At-Risk": {"count": 0, "revenue": 0.0, "avg_orders": 0.0},
            "Inactive / Churned": {"count": 0, "revenue": 0.0, "avg_orders": 0.0},
            "Occasional Buyer": {"count": 0, "revenue": 0.0, "avg_orders": 0.0},
        }

        for r in rows:
            tot_orders = int(r["total_orders"])
            tot_rev = float(r["total_revenue"])
            last_date = r["last_order_date"]
            signup_date = r["signup_date"]

            if last_date:
                recency_days = (ref_date - last_date).days
            else:
                recency_days = (ref_date - signup_date).days

            # Rule derivation
            if tot_orders == 0 or recency_days > t["recency_at_risk_days"]:
                seg = "Inactive / Churned"
            elif (ref_date - signup_date).days <= t["new_customer_window_days"] and tot_orders <= 2:
                seg = "New Customer"
            elif recency_days <= t["recency_active_days"] and tot_rev >= vip_rev_cutoff:
                seg = "High-Value Active"
            elif recency_days <= t["recency_active_days"] and tot_orders >= t["frequency_high"]:
                seg = "Frequent Loyal"
            elif t["recency_active_days"] < recency_days <= t["recency_at_risk_days"] and (tot_orders >= 3 or tot_rev >= 1000.0):
                seg = "Declining / At-Risk"
            else:
                seg = "Occasional Buyer"

            segment_counts[seg]["count"] += 1
            segment_counts[seg]["revenue"] += tot_rev
            segment_counts[seg]["avg_orders"] += tot_orders

            categorized.append({
                "customer_id": r["customer_id"],
                "customer_ref": r["customer_ref"],
                "name": r["name"],
                "segment": seg,
                "recency_days": max(0, recency_days),
                "frequency": tot_orders,
                "monetary_value": round(tot_rev, 2),
                "aov": round(float(r["aov"]), 2),
                "acquisition_channel": r["acquisition_channel"],
                "region": r["region"],
                "last_order_date": last_date.strftime("%Y-%m-%d") if last_date else None
            })

        # Calculate averages for segment overview
        summary = []
        for s_name, data in segment_counts.items():
            cnt = data["count"]
            summary.append({
                "segment": s_name,
                "customer_count": cnt,
                "total_revenue": round(data["revenue"], 2),
                "avg_revenue_per_customer": round(data["revenue"] / cnt, 2) if cnt > 0 else 0.0,
                "avg_orders_per_customer": round(data["avg_orders"] / cnt, 1) if cnt > 0 else 0.0,
            })

        return {
            "summary": summary,
            "thresholds": {**t, "vip_revenue_cutoff": round(vip_rev_cutoff, 2)},
            "sample_customers": categorized[:100],
            "total_evaluated": len(categorized)
        }
