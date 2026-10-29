import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models import Customer, ModelVersion, CustomerRiskPrediction
from backend.app.ml.features import FeatureEngineeringService
from backend.app.ml.evaluation import ModelEvaluator


NUMERIC_COLS = [
    "recency_days", "frequency_obs", "monetary_obs", "avg_tx_amount",
    "std_tx_amount", "activity_count", "velocity_ratio", "active_weeks", "days_tenure"
]
CATEGORICAL_COLS = ["acquisition_channel", "region"]


class ModelTrainingService:
    """Manages machine learning model training, evaluation, threshold tuning, and artifact persistence."""

    def __init__(self, db: Session):
        self.db = db
        self.feature_service = FeatureEngineeringService(db)

    def train_and_evaluate(
        self,
        model_type: str = "RandomForest",
        train_cutoff: Optional[datetime] = None,
        test_cutoff: Optional[datetime] = None,
        observation_days: int = 90,
        prediction_days: int = 60,
        target_recall: float = 0.75
    ) -> Dict[str, Any]:
        """Trains model with time-aware splitting, evaluates discrimination, and persists artifacts."""
        # Temporal cutoffs
        t_test = test_cutoff or datetime(2026, 1, 15)
        t_train = train_cutoff or (t_test - timedelta(days=60))

        # 1. Extract Training Set strictly as of t_train
        X_train_df, y_train = self.feature_service.extract_features_and_target(
            cutoff_date=t_train,
            observation_days=observation_days,
            prediction_days=prediction_days
        )

        # 2. Extract Test Set strictly as of t_test
        X_test_df, y_test = self.feature_service.extract_features_and_target(
            cutoff_date=t_test,
            observation_days=observation_days,
            prediction_days=prediction_days
        )

        if X_train_df.empty or X_test_df.empty or len(y_train.unique()) < 2:
            return {"error": "Insufficient customer data or variation across temporal cutoff dates."}

        feature_cols = NUMERIC_COLS + CATEGORICAL_COLS
        X_train = X_train_df[feature_cols]
        X_test = X_test_df[feature_cols]

        # 3. Build Preprocessing & Estimator Pipeline
        preprocessor = ColumnTransformer(
            transformers=[
                ("num", Pipeline([
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler())
                ]), NUMERIC_COLS),
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_COLS)
            ]
        )

        seed = settings.RANDOM_SEED
        if model_type == "Baseline":
            classifier = DummyClassifier(strategy="prior")
        elif model_type == "LogisticRegression":
            classifier = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=seed)
        else:
            model_type = "RandomForest"
            classifier = RandomForestClassifier(
                n_estimators=100,
                max_depth=6,
                class_weight="balanced",
                random_state=seed
            )

        pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("classifier", classifier)
        ])

        # 4. Fit ONLY on training data
        pipeline.fit(X_train, y_train)

        # 5. Predict probabilities
        if hasattr(pipeline, "predict_proba"):
            train_probs = pipeline.predict_proba(X_train)[:, 1]
            test_probs = pipeline.predict_proba(X_test)[:, 1]
        else:
            train_probs = np.full(len(X_train), 0.5)
            test_probs = np.full(len(X_test), 0.5)

        # 6. Threshold Selection: Pick threshold balancing precision and recall on training/validation
        sweep = ModelEvaluator.threshold_sweep(y_train.values, train_probs)
        # Select threshold maximizing F1 or closest to target recall
        selected_th = 0.5
        best_f1 = -1.0
        for entry in sweep:
            if entry["f1"] > best_f1 and entry["recall"] >= 0.5:
                best_f1 = entry["f1"]
                selected_th = entry["threshold"]

        # 7. Evaluate Final Test Set at selected threshold
        eval_metrics = ModelEvaluator.evaluate_predictions(y_test.values, test_probs, threshold=selected_th)
        eval_metrics["threshold_tradeoff_curve"] = sweep

        # 8. Extract Feature Importance
        feature_importance_list = self._extract_feature_importances(pipeline, NUMERIC_COLS, CATEGORICAL_COLS)

        # 9. Persist Artifacts and Record Model Version in DB
        version_tag = f"CHURN-{model_type.upper()}-{uuid.uuid4().hex[:6].upper()}"
        artifacts_dir = os.path.join(os.getcwd(), settings.ARTIFACTS_DIR, "models")
        os.makedirs(artifacts_dir, exist_ok=True)
        artifact_path = os.path.join(artifacts_dir, f"{version_tag}.joblib")
        joblib.dump(pipeline, artifact_path)

        # Deactivate older models
        self.db.query(ModelVersion).update({ModelVersion.is_active: False})

        model_version = ModelVersion(
            version_tag=version_tag,
            model_type=model_type,
            observation_days=observation_days,
            prediction_days=prediction_days,
            feature_names=feature_cols,
            threshold=selected_th,
            metrics=eval_metrics,
            feature_importance=feature_importance_list,
            artifact_path=artifact_path,
            is_active=True
        )
        self.db.add(model_version)
        self.db.commit()

        return {
            "version_tag": version_tag,
            "model_type": model_type,
            "selected_threshold": selected_th,
            "metrics": eval_metrics,
            "feature_importance": feature_importance_list,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "train_cutoff": t_train.strftime("%Y-%m-%d"),
            "test_cutoff": t_test.strftime("%Y-%m-%d")
        }

    def _extract_feature_importances(
        self,
        pipeline: Pipeline,
        num_cols: List[str],
        cat_cols: List[str]
    ) -> List[Dict[str, Any]]:
        preprocessor = pipeline.named_steps["preprocessor"]
        classifier = pipeline.named_steps["classifier"]

        # Get one-hot encoded column names
        try:
            ohe = preprocessor.named_transformers_["cat"]
            cat_feature_names = list(ohe.get_feature_names_out(cat_cols))
        except Exception:
            cat_feature_names = cat_cols

        all_names = num_cols + cat_feature_names

        importances = []
        if hasattr(classifier, "feature_importances_"):
            raw_imp = classifier.feature_importances_
            for name, val in zip(all_names, raw_imp):
                importances.append({"feature": name, "importance": round(float(val), 4)})
        elif hasattr(classifier, "coef_"):
            raw_imp = np.abs(classifier.coef_[0])
            for name, val in zip(all_names, raw_imp):
                importances.append({"feature": name, "importance": round(float(val), 4)})

        importances.sort(key=lambda x: x["importance"], reverse=True)
        return importances[:12]
