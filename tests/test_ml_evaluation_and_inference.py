import numpy as np
import pytest
from backend.app.ml.evaluation import ModelEvaluator


def test_model_evaluator_metrics():
    # Synthetic ground truth & probabilities
    y_true = np.array([1, 1, 0, 0, 1, 0, 1, 0])
    y_prob = np.array([0.9, 0.8, 0.2, 0.1, 0.4, 0.3, 0.85, 0.15])

    metrics = ModelEvaluator.evaluate_predictions(y_true, y_prob, threshold=0.5)

    assert "roc_auc" in metrics
    assert "pr_auc" in metrics
    assert "confusion_matrix" in metrics
    assert metrics["roc_auc"] > 0.8
    assert metrics["precision"] > 0.0
    assert metrics["recall"] > 0.0
    assert metrics["confusion_matrix"]["true_positives"] >= 3


def test_threshold_sweep():
    y_true = np.array([1, 1, 0, 0, 1, 0])
    y_prob = np.array([0.9, 0.7, 0.3, 0.2, 0.6, 0.1])

    sweep = ModelEvaluator.threshold_sweep(y_true, y_prob, steps=5)
    assert len(sweep) == 5
    for item in sweep:
        assert 0.0 <= item["threshold"] <= 1.0
        assert 0.0 <= item["precision"] <= 1.0
        assert 0.0 <= item["recall"] <= 1.0
