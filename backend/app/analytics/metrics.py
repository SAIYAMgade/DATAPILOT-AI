from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session


class BusinessMetricsEngine:
    """Computes authoritative business and revenue metrics via robust SQL queries."""

    def __init__(self, db: Session):
        self.db = db

    def get_executive_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Calculates executive KPI card metrics with period-over-period delta comparisons."""
        # Determine current window and previous comparison window
        if not end_date:
            max_tx = self.db.execute(text("SELECT MAX(timestamp) FROM transactions")).scalar()
            now = max_tx if max_tx else datetime.utcnow()
        else:
            now = end_date
        if not start_date:
            start_date = now - timedelta(days=90)
        window_days = (now - start_date).days
        prev_start = start_date - timedelta(days=window_days)
        prev_end = start_date

        sql_cur = text("""
            SELECT
                COUNT(id) AS total_orders,
                COALESCE(SUM(CASE WHEN is_refund = false AND status = 'completed' THEN amount ELSE 0 END), 0) AS total_revenue,
                COALESCE(AVG(CASE WHEN is_refund = false AND status = 'completed' THEN amount END), 0) AS aov,
                COUNT(DISTINCT customer_id) AS transacting_customers
            FROM transactions
            WHERE timestamp >= :start_dt AND timestamp <= :end_dt
        """)

        cur_row = self.db.execute(sql_cur, {"start_dt": start_date, "end_dt": now}).mappings().first()
        prev_row = self.db.execute(sql_cur, {"start_dt": prev_start, "end_dt": prev_end}).mappings().first()

        cur_rev = float(cur_row["total_revenue"] or 0)
        prev_rev = float(prev_row["total_revenue"] or 0)
        rev_change_pct = round(((cur_rev - prev_rev) / prev_rev * 100), 2) if prev_rev > 0 else 0.0

        cur_aov = float(cur_row["aov"] or 0)
        prev_aov = float(prev_row["aov"] or 0)
        aov_change_pct = round(((cur_aov - prev_aov) / prev_aov * 100), 2) if prev_aov > 0 else 0.0

        # Active customers: transacted in last 30 days of window
        sql_active = text("""
            SELECT COUNT(DISTINCT customer_id) AS active_custs
            FROM transactions
            WHERE timestamp >= :active_thresh AND timestamp <= :end_dt
              AND status = 'completed' AND is_refund = false
        """)
        active_thresh = now - timedelta(days=30)
        active_custs = self.db.execute(sql_active, {"active_thresh": active_thresh, "end_dt": now}).scalar() or 0

        # Total registered customers
        sql_total_custs = text("SELECT COUNT(id) FROM customers WHERE signup_date <= :end_dt")
        total_customers = self.db.execute(sql_total_custs, {"end_dt": now}).scalar() or 0

        # New customers signed up during window
        sql_new_custs = text("SELECT COUNT(id) FROM customers WHERE signup_date >= :start_dt AND signup_date <= :end_dt")
        new_customers = self.db.execute(sql_new_custs, {"start_dt": start_date, "end_dt": now}).scalar() or 0

        # Churn risk customers from active predictions if available
        sql_high_risk = text("""
            SELECT COUNT(DISTINCT customer_id)
            FROM customer_risk_predictions
            WHERE risk_category = 'High'
              AND model_version_id = (SELECT id FROM model_versions WHERE is_active = true ORDER BY id DESC LIMIT 1)
        """)
        try:
            high_risk_custs = self.db.execute(sql_high_risk).scalar() or 0
        except Exception:
            high_risk_custs = 0

        return {
            "period": {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": now.strftime("%Y-%m-%d"),
                "comparison_start": prev_start.strftime("%Y-%m-%d"),
                "comparison_end": prev_end.strftime("%Y-%m-%d")
            },
            "metrics": {
                "total_revenue": round(cur_rev, 2),
                "previous_revenue": round(prev_rev, 2),
                "revenue_growth_pct": rev_change_pct,
                "average_order_value": round(cur_aov, 2),
                "aov_growth_pct": aov_change_pct,
                "total_orders": int(cur_row["total_orders"] or 0),
                "transacting_customers": int(cur_row["transacting_customers"] or 0),
                "active_customers_30d": int(active_custs),
                "total_registered_customers": int(total_customers),
                "new_acquired_customers": int(new_customers),
                "high_risk_customers": int(high_risk_custs)
            }
        }

    def get_revenue_time_series(
        self,
        granularity: str = "monthly",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Time-series revenue trends with SQL CTE, Window LAG for period-over-period change."""
        # Detect database dialect for date truncation
        is_postgres = not str(self.db.bind.url).startswith("sqlite")
        date_expr = "DATE_TRUNC('month', timestamp)" if granularity == "monthly" else "DATE_TRUNC('week', timestamp)"
        if not is_postgres:
            date_expr = "strftime('%Y-%m-01', timestamp)" if granularity == "monthly" else "strftime('%Y-%W', timestamp)"

        sql = text(f"""
            WITH periodic_agg AS (
                SELECT
                    {date_expr} AS period_date,
                    COUNT(id) AS transaction_count,
                    COALESCE(SUM(CASE WHEN is_refund = false AND status = 'completed' THEN amount ELSE 0 END), 0) AS revenue,
                    COALESCE(AVG(CASE WHEN is_refund = false AND status = 'completed' THEN amount END), 0) AS avg_amount,
                    COUNT(DISTINCT customer_id) AS active_accounts
                FROM transactions
                WHERE (:start_dt IS NULL OR timestamp >= :start_dt)
                  AND (:end_dt IS NULL OR timestamp <= :end_dt)
                GROUP BY 1
            )
            SELECT
                period_date,
                transaction_count,
                revenue,
                avg_amount,
                active_accounts,
                LAG(revenue, 1) OVER (ORDER BY period_date) AS prev_period_revenue,
                ROUND(
                    CASE
                        WHEN LAG(revenue, 1) OVER (ORDER BY period_date) > 0
                        THEN ((revenue - LAG(revenue, 1) OVER (ORDER BY period_date)) / LAG(revenue, 1) OVER (ORDER BY period_date) * 100)::numeric
                        ELSE 0
                    END, 2
                ) AS mom_growth_pct
            FROM periodic_agg
            ORDER BY period_date ASC
        """)

        params = {"start_dt": start_date, "end_dt": end_date}
        rows = self.db.execute(sql, params).mappings().all()

        results = []
        for r in rows:
            dt_val = r["period_date"]
            if isinstance(dt_val, datetime):
                dt_str = dt_val.strftime("%Y-%m-%d")
            else:
                dt_str = str(dt_val)

            results.append({
                "period": dt_str,
                "revenue": round(float(r["revenue"]), 2),
                "transaction_count": int(r["transaction_count"]),
                "average_amount": round(float(r["avg_amount"]), 2),
                "active_accounts": int(r["active_accounts"]),
                "prev_period_revenue": round(float(r["prev_period_revenue"] or 0), 2),
                "growth_pct": float(r["mom_growth_pct"] or 0.0)
            })

        return results

    def get_breakdowns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Revenue breakdowns by category, acquisition channel, and region."""
        # By Category
        sql_cat = text("""
            SELECT
                COALESCE(c.name, 'Uncategorized') AS category_name,
                COUNT(t.id) AS order_count,
                COALESCE(SUM(CASE WHEN t.is_refund = false AND t.status = 'completed' THEN t.amount ELSE 0 END), 0) AS revenue,
                ROUND(AVG(t.amount)::numeric, 2) AS avg_order_value
            FROM transactions t
            LEFT JOIN product_categories c ON t.category_id = c.id
            GROUP BY c.name
            ORDER BY revenue DESC
        """)
        cats = [
            {
                "name": r["category_name"],
                "orders": int(r["order_count"]),
                "revenue": round(float(r["revenue"]), 2),
                "aov": float(r["avg_order_value"] or 0)
            }
            for r in self.db.execute(sql_cat).mappings().all()
        ]

        # By Channel
        sql_channel = text("""
            SELECT
                cu.acquisition_channel AS channel,
                COUNT(DISTINCT cu.id) AS customer_count,
                COUNT(t.id) AS order_count,
                COALESCE(SUM(CASE WHEN t.is_refund = false AND t.status = 'completed' THEN t.amount ELSE 0 END), 0) AS revenue
            FROM customers cu
            LEFT JOIN transactions t ON cu.id = t.customer_id
            GROUP BY cu.acquisition_channel
            ORDER BY revenue DESC
        """)
        channels = [
            {
                "channel": r["channel"],
                "customers": int(r["customer_count"]),
                "orders": int(r["order_count"]),
                "revenue": round(float(r["revenue"]), 2)
            }
            for r in self.db.execute(sql_channel).mappings().all()
        ]

        # By Region
        sql_region = text("""
            SELECT
                cu.region AS region,
                COUNT(DISTINCT cu.id) AS customer_count,
                COALESCE(SUM(CASE WHEN t.is_refund = false AND t.status = 'completed' THEN t.amount ELSE 0 END), 0) AS revenue
            FROM customers cu
            LEFT JOIN transactions t ON cu.id = t.customer_id
            GROUP BY cu.region
            ORDER BY revenue DESC
        """)
        regions = [
            {
                "region": r["region"],
                "customers": int(r["customer_count"]),
                "revenue": round(float(r["revenue"]), 2)
            }
            for r in self.db.execute(sql_region).mappings().all()
        ]

        return {
            "by_category": cats,
            "by_channel": channels,
            "by_region": regions
        }

    def get_pareto_concentration(self) -> Dict[str, Any]:
        """Calculates revenue concentration / Pareto distribution using SQL Window Functions."""
        sql = text("""
            WITH customer_revenues AS (
                SELECT
                    customer_id,
                    SUM(CASE WHEN is_refund = false AND status = 'completed' THEN amount ELSE 0 END) AS total_spent
                FROM transactions
                GROUP BY customer_id
            ),
            ranked_revenues AS (
                SELECT
                    customer_id,
                    total_spent,
                    ROW_NUMBER() OVER (ORDER BY total_spent DESC) AS rank,
                    COUNT(*) OVER () AS total_custs,
                    SUM(total_spent) OVER () AS total_revenue,
                    SUM(total_spent) OVER (ORDER BY total_spent DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_revenue
                FROM customer_revenues
            )
            SELECT
                rank,
                total_custs,
                total_spent,
                ROUND((rank::numeric / NULLIF(total_custs, 0) * 100)::numeric, 2) AS customer_pct,
                ROUND((running_revenue::numeric / NULLIF(total_revenue, 0)::numeric * 100)::numeric, 2) AS cumulative_revenue_pct
            FROM ranked_revenues
            WHERE rank IN (
                1,
                GREATEST(1, CAST(ROUND((total_custs * 0.05)::numeric) AS INTEGER)),
                GREATEST(1, CAST(ROUND((total_custs * 0.10)::numeric) AS INTEGER)),
                GREATEST(1, CAST(ROUND((total_custs * 0.20)::numeric) AS INTEGER)),
                GREATEST(1, CAST(ROUND((total_custs * 0.50)::numeric) AS INTEGER)),
                total_custs
            )
            ORDER BY rank ASC
        """)
        rows = self.db.execute(sql).mappings().all()
        points = [
            {
                "rank": int(r["rank"]),
                "customer_pct": float(r["customer_pct"]),
                "cumulative_revenue_pct": float(r["cumulative_revenue_pct"])
            }
            for r in rows
        ]

        top_20 = next((p["cumulative_revenue_pct"] for p in points if p["customer_pct"] >= 18 and p["customer_pct"] <= 25), None)
        return {
            "concentration_points": points,
            "top_20_pct_generates": top_20 or (points[-1]["cumulative_revenue_pct"] if points else 0.0),
            "interpretation": "Pareto distribution indicating share of total revenue contributed by top customer deciles."
        }
