from typing import Dict, Any, List, Tuple
import numpy as np
from sklearn.metrics import (
    roc_auc_score, average_precision_score, precision_score, recall_score,
    f1_score, confusion_matrix, brier_score_loss
)


class ModelEvaluator:
    """Evaluates churn classification models with comprehensive metric reporting."""

    @staticmethod
    def evaluate_predictions(
        y_true: np.ndarray,
        y_prob: np.ndarray,
        threshold: float = 0.5
    ) -> Dict[str, Any]:
        """Calculates discrimination, calibration, and classification metrics at a given threshold."""
        y_true = np.asarray(y_true)
        y_prob = np.asarray(y_prob)

        # Handle edge cases where only 1 class is present
        unique_classes = np.unique(y_true)
        has_both_classes = len(unique_classes) > 1

        roc_auc = float(roc_auc_score(y_true, y_prob)) if has_both_classes else 0.5
        pr_auc = float(average_precision_score(y_true, y_prob)) if has_both_classes else float(np.mean(y_true))
        brier = float(brier_score_loss(y_true, y_prob))

        y_pred = (y_prob >= threshold).astype(int)

        precision = float(precision_score(y_true, y_pred, zero_division=0))
        recall = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))

        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

        return {
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
            "brier_score": round(brier, 4),
            "threshold": round(threshold, 2),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "confusion_matrix": {
                "true_negatives": tn,
                "false_positives": fp,
                "false_negatives": fn,
                "true_positives": tp,
            },
            "sample_counts": {
                "total": len(y_true),
                "actual_churned": int(np.sum(y_true == 1)),
                "actual_retained": int(np.sum(y_true == 0)),
                "predicted_churned": int(np.sum(y_pred == 1)),
            }
        }

    @staticmethod
    def threshold_sweep(
        y_true: np.ndarray,
        y_prob: np.ndarray,
        steps: int = 19
    ) -> List[Dict[str, Any]]:
        """Sweeps decision thresholds from 0.05 to 0.95 to help analysts evaluate precision/recall trade-offs."""
        thresholds = np.linspace(0.05, 0.95, steps)
        curve = []
        for th in thresholds:
            y_pred = (y_prob >= th).astype(int)
            p = float(precision_score(y_true, y_pred, zero_division=0))
            r = float(recall_score(y_true, y_pred, zero_division=0))
            f = float(f1_score(y_true, y_pred, zero_division=0))
            curve.append({
                "threshold": round(float(th), 2),
                "precision": round(p, 4),
                "recall": round(r, 4),
                "f1": round(f, 4),
            })
        return curve
