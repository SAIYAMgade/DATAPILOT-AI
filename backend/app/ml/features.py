from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session


class FeatureEngineeringService:
    """Builds leak-free customer features with strict temporal cutoff boundaries."""

    def __init__(self, db: Session):
        self.db = db

    def extract_features_and_target(
        self,
        cutoff_date: datetime,
        observation_days: int = 90,
        prediction_days: int = 60,
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Extracts temporal features strictly before cutoff_date and target strictly after cutoff_date.
        Target = 1 (Churned: 0 qualifying transactions in [cutoff, cutoff + prediction_days]), 0 (Retained).
        """
        obs_start = cutoff_date - timedelta(days=observation_days)
        pred_end = cutoff_date + timedelta(days=prediction_days)

        # 1. Eligible customers: signed up on or before cutoff_date
        sql_customers = text("""
            SELECT id, customer_ref, acquisition_channel, region, signup_date
            FROM customers
            WHERE signup_date <= :cutoff
        """)
        cust_df = pd.DataFrame(self.db.execute(sql_customers, {"cutoff": cutoff_date}).mappings().all())
        if cust_df.empty:
            return pd.DataFrame(), pd.Series(dtype=int)

        # 2. Historical transactions strictly within observation window [obs_start, cutoff_date]
        sql_tx_obs = text("""
            SELECT customer_id, timestamp, amount
            FROM transactions
            WHERE timestamp >= :obs_start AND timestamp <= :cutoff
              AND status = 'completed' AND is_refund = false
        """)
        tx_obs_df = pd.DataFrame(self.db.execute(sql_tx_obs, {
            "obs_start": obs_start,
            "cutoff": cutoff_date
        }).mappings().all())

        # 3. Future transactions strictly within prediction window (cutoff_date, pred_end]
        sql_tx_pred = text("""
            SELECT DISTINCT customer_id
            FROM transactions
            WHERE timestamp > :cutoff AND timestamp <= :pred_end
              AND status = 'completed' AND is_refund = false
        """)
        future_active_ids = set(
            r[0] for r in self.db.execute(sql_tx_pred, {
                "cutoff": cutoff_date,
                "pred_end": pred_end
            }).all()
        )

        # 4. Activity events in observation window
        sql_act = text("""
            SELECT customer_id, COUNT(id) AS activity_cnt
            FROM customer_activities
            WHERE timestamp >= :obs_start AND timestamp <= :cutoff
            GROUP BY customer_id
        """)
        act_dict = dict(self.db.execute(sql_act, {
            "obs_start": obs_start,
            "cutoff": cutoff_date
        }).all())

        # Halfway point for velocity calculation
        midpoint = cutoff_date - timedelta(days=observation_days // 2)

        feature_records = []
        labels = []

        if not tx_obs_df.empty:
            tx_obs_df["timestamp"] = pd.to_datetime(tx_obs_df["timestamp"])
            tx_by_cust = tx_obs_df.groupby("customer_id")
        else:
            tx_by_cust = {}

        for _, cust in cust_df.iterrows():
            cid = cust["id"]
            c_signup = pd.to_datetime(cust["signup_date"])
            days_tenure = max(1, (cutoff_date - c_signup).days)

            if cid in tx_by_cust.groups if hasattr(tx_by_cust, "groups") else False:
                cust_txs = tx_by_cust.get_group(cid)
                freq = len(cust_txs)
                monetary = float(cust_txs["amount"].sum())
                avg_amt = float(cust_txs["amount"].mean())
                std_amt = float(cust_txs["amount"].std()) if freq > 1 else 0.0

                latest_tx_time = cust_txs["timestamp"].max()
                recency = max(0, (cutoff_date - latest_tx_time).days)

                # Velocity: transactions in second half vs first half
                t_first_half = (cust_txs["timestamp"] < midpoint).sum()
                t_second_half = (cust_txs["timestamp"] >= midpoint).sum()
                velocity = (t_second_half + 1.0) / (t_first_half + 1.0)

                # Active weeks
                active_weeks = cust_txs["timestamp"].dt.isocalendar().week.nunique()
            else:
                freq = 0
                monetary = 0.0
                avg_amt = 0.0
                std_amt = 0.0
                recency = observation_days
                velocity = 1.0
                active_weeks = 0

            activity_cnt = act_dict.get(cid, 0)

            # Target: 1 if NOT in future active IDs (Churned), 0 if active
            is_churned = 0 if cid in future_active_ids else 1

            feature_records.append({
                "customer_id": cid,
                "recency_days": recency,
                "frequency_obs": freq,
                "monetary_obs": round(monetary, 2),
                "avg_tx_amount": round(avg_amt, 2),
                "std_tx_amount": round(std_amt, 2),
                "activity_count": activity_cnt,
                "velocity_ratio": round(velocity, 3),
                "active_weeks": active_weeks,
                "days_tenure": days_tenure,
                "acquisition_channel": cust["acquisition_channel"],
                "region": cust["region"]
            })
            labels.append(is_churned)

        df_features = pd.DataFrame(feature_records)
        series_target = pd.Series(labels, name="target_churn")

        return df_features, series_target
