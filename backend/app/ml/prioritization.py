from datetime import datetime
from typing import Dict, Any, List, Optional
import os
import joblib
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.models import Customer, ModelVersion, CustomerRiskPrediction
from backend.app.ml.features import FeatureEngineeringService
from backend.app.ml.models import NUMERIC_COLS, CATEGORICAL_COLS


class RetentionPrioritizationEngine:
    """Ranks at-risk customers by combining predicted churn risk with customer business value."""

    SEGMENT_MULTIPLIERS = {
        "High-Value VIP": 1.4,
        "VIP": 1.4,
        "Frequent Loyal": 1.2,
        "Frequent": 1.2,
        "New Customer": 1.1,
        "New": 1.1,
        "Occasional Buyer": 0.9,
        "Irregular": 0.9,
        "Declining": 1.0,
        "Inactive": 0.8
    }

    def __init__(self, db: Session):
        self.db = db
        self.feature_service = FeatureEngineeringService(db)

    def generate_predictions_and_priorities(
        self,
        as_of_date: Optional[datetime] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Runs batch inference using active model and computes transparent business priority scores."""
        if not as_of_date:
            max_tx = self.db.execute(text("SELECT MAX(timestamp) FROM transactions")).scalar()
            ref_date = max_tx if max_tx else datetime.utcnow()
        else:
            ref_date = as_of_date

        # 1. Fetch active model
        active_model = self.db.query(ModelVersion).filter_by(is_active=True).first()
        if not active_model or not os.path.exists(active_model.artifact_path):
            return {"error": "No trained active model artifact found. Train a model in the laboratory first."}

        pipeline = joblib.load(active_model.artifact_path)
        threshold = active_model.threshold

        # 2. Extract features as of ref_date
        features_df, _ = self.feature_service.extract_features_and_target(
            cutoff_date=ref_date,
            observation_days=active_model.observation_days,
            prediction_days=active_model.prediction_days
        )

        if features_df.empty:
            return {"error": "No customer records available for inference."}

        X = features_df[NUMERIC_COLS + CATEGORICAL_COLS]
        probs = pipeline.predict_proba(X)[:, 1] if hasattr(pipeline, "predict_proba") else np.full(len(X), 0.5)

        # Clear prior predictions for this model version to keep table fresh
        self.db.query(CustomerRiskPrediction).filter_by(model_version_id=active_model.id).delete()

        # Calculate max monetary for scaling
        max_monetary = max(1.0, float(features_df["monetary_obs"].max()))

        # Query customer names and segments
        sql_cust = text("SELECT id, customer_ref, name, segment, email FROM customers")
        cust_info = {r["id"]: r for r in self.db.execute(sql_cust).mappings().all()}

        prioritized = []
        for i, row in features_df.iterrows():
            cid = int(row["customer_id"])
            c_meta = cust_info.get(cid, {})
            risk_score = float(probs[i])
            monetary = float(row["monetary_obs"])
            recency = int(row["recency_days"])
            segment = c_meta.get("segment", "Standard")

            # Risk Category based on model threshold
            if risk_score >= threshold:
                risk_cat = "High"
            elif risk_score >= threshold * 0.6:
                risk_cat = "Medium"
            else:
                risk_cat = "Low"

            # Composite Priority Formula:
            # Priority = Risk_Score * (0.4 + 0.6 * (Monetary / Max_Monetary)) * Multiplier
            seg_mult = self.SEGMENT_MULTIPLIERS.get(segment, 1.0)
            val_factor = 0.4 + 0.6 * (monetary / max_monetary)
            priority_score = round(risk_score * val_factor * seg_mult * 100.0, 1)

            # Traceable recommended action
            if risk_cat == "High" and monetary > 2000:
                rec_action = "Urgent: Assign Executive Account Manager for VIP retention outreach."
            elif risk_cat == "High":
                rec_action = "Send personalized re-engagement discount or tailored product renewal."
            elif risk_cat == "Medium":
                rec_action = "Nurture with product check-in email and feature highlights."
            else:
                rec_action = "Monitor; normal customer lifecycle cadence."

            pred_record = CustomerRiskPrediction(
                customer_id=cid,
                model_version_id=active_model.id,
                risk_score=round(risk_score, 4),
                risk_category=risk_cat,
                observation_end_date=ref_date,
                prediction_horizon_days=active_model.prediction_days,
                priority_score=priority_score,
                contributing_features={
                    "recency_days": recency,
                    "monetary_obs": monetary,
                    "frequency_obs": int(row["frequency_obs"]),
                    "velocity_ratio": float(row["velocity_ratio"]),
                    "segment": segment,
                    "recommended_action": rec_action
                }
            )
            self.db.add(pred_record)

            prioritized.append({
                "customer_id": cid,
                "customer_ref": c_meta.get("customer_ref", f"CUST-{cid}"),
                "name": c_meta.get("name", "Account"),
                "email": c_meta.get("email"),
                "segment": segment,
                "risk_score": round(risk_score, 4),
                "risk_category": risk_cat,
                "priority_score": priority_score,
                "historical_value": round(monetary, 2),
                "recency_days": recency,
                "frequency": int(row["frequency_obs"]),
                "recommended_action": rec_action
            })

        self.db.commit()

        # Sort by priority score descending
        prioritized.sort(key=lambda x: x["priority_score"], reverse=True)

        return {
            "model_version": active_model.version_tag,
            "decision_threshold": threshold,
            "total_customers_scored": len(prioritized),
            "high_risk_count": len([p for p in prioritized if p["risk_category"] == "High"]),
            "prioritized_customers": prioritized[:limit],
            "formula_documentation": (
                "Priority Score = Risk_Score * (0.4 + 0.6 * (Monetary_Spend / Max_Spend)) * Segment_Multiplier * 100. "
                "Transparently balances churn probability with business account value."
            )
        }
