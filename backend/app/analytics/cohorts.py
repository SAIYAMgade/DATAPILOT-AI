from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session


class CohortRetentionEngine:
    """Calculates customer cohort retention matrices and revenue tracking across monthly cohorts."""

    def __init__(self, db: Session):
        self.db = db

    def compute_cohort_matrix(self) -> Dict[str, Any]:
        """Calculates cohort retention matrix with month-indexing and revenue metrics."""
        # Query first transaction date and all subsequent transactions per customer
        sql = text("""
            WITH first_tx AS (
                SELECT
                    customer_id,
                    MIN(timestamp) AS cohort_first_date
                FROM transactions
                WHERE status = 'completed' AND is_refund = false
                GROUP BY customer_id
            ),
            customer_activity AS (
                SELECT
                    t.customer_id,
                    f.cohort_first_date,
                    t.timestamp AS tx_date,
                    t.amount
                FROM transactions t
                JOIN first_tx f ON t.customer_id = f.customer_id
                WHERE t.status = 'completed' AND t.is_refund = false
            )
            SELECT
                customer_id,
                cohort_first_date,
                tx_date,
                amount
            FROM customer_activity
        """)

        rows = self.db.execute(sql).mappings().all()
        if not rows:
            return {
                "cohort_matrix": [],
                "cohort_revenue_matrix": [],
                "periods": [],
                "cohort_summary": []
            }

        df = pd.DataFrame(rows)
        df["cohort_first_date"] = pd.to_datetime(df["cohort_first_date"])
        df["tx_date"] = pd.to_datetime(df["tx_date"])

        # Cohort Month: YYYY-MM
        df["cohort_month"] = df["cohort_first_date"].dt.to_period("M")
        df["tx_month"] = df["tx_date"].dt.to_period("M")

        # Period Index: integer number of months elapsed
        df["period_index"] = (
            (df["tx_month"].dt.year - df["cohort_month"].dt.year) * 12 +
            (df["tx_month"].dt.month - df["cohort_month"].dt.month)
        )

        # Unique active customers per (cohort_month, period_index)
        cohort_group = df.groupby(["cohort_month", "period_index"])
        cohort_counts = cohort_group["customer_id"].nunique().unstack()
        cohort_rev = cohort_group["amount"].sum().unstack()

        # Cohort size = count at period_index 0
        cohort_sizes = cohort_counts[0]
        retention_matrix = cohort_counts.divide(cohort_sizes, axis=0) * 100.0

        max_period = int(df["period_index"].max())
        period_headers = [f"M+{i}" for i in range(max_period + 1)]

        latest_available_month = df["tx_month"].max()

        matrix_rows = []
        rev_matrix_rows = []
        cohort_summary = []

        for cohort_period in sorted(cohort_counts.index):
            c_str = str(cohort_period)
            c_size = int(cohort_sizes.loc[cohort_period])

            # Detect maximum possible period index for this cohort to prevent false 0% on future months
            months_since_cohort = (latest_available_month.year - cohort_period.year) * 12 + (latest_available_month.month - cohort_period.month)

            ret_dict = {"cohort": c_str, "size": c_size}
            rev_dict = {"cohort": c_str, "size": c_size}

            for p in range(max_period + 1):
                col_name = f"M+{p}"
                if p <= months_since_cohort:
                    ret_val = retention_matrix.loc[cohort_period].get(p)
                    rev_val = cohort_rev.loc[cohort_period].get(p)
                    ret_dict[col_name] = round(float(ret_val), 1) if pd.notna(ret_val) else 0.0
                    rev_dict[col_name] = round(float(rev_val), 2) if pd.notna(rev_val) else 0.0
                else:
                    ret_dict[col_name] = None
                    rev_dict[col_name] = None

            matrix_rows.append(ret_dict)
            rev_matrix_rows.append(rev_dict)

            # Cumulative revenue and m1 retention for summary
            total_cohort_rev = float(cohort_rev.loc[cohort_period].sum())
            m1_ret = float(retention_matrix.loc[cohort_period].get(1, 0.0)) if months_since_cohort >= 1 and pd.notna(retention_matrix.loc[cohort_period].get(1)) else None

            cohort_summary.append({
                "cohort": c_str,
                "initial_size": c_size,
                "total_revenue": round(total_cohort_rev, 2),
                "revenue_per_customer": round(total_cohort_rev / c_size, 2) if c_size > 0 else 0.0,
                "month_1_retention_pct": round(m1_ret, 1) if m1_ret is not None else None,
                "months_observed": months_since_cohort + 1
            })

        return {
            "retention_matrix": matrix_rows,
            "revenue_matrix": rev_matrix_rows,
            "period_columns": period_headers,
            "cohort_summary": cohort_summary,
            "definition": "Retention is defined as having at least one completed qualifying transaction in the given monthly observation window."
        }
