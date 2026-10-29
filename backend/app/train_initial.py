from backend.app.database import SessionLocal
from backend.app.ml.models import ModelTrainingService
from backend.app.ml.prioritization import RetentionPrioritizationEngine
from backend.app.insights import BusinessInsightEngine


def train_initial_model():
    db = SessionLocal()
    try:
        print("Training initial RandomForest model with time-aware splitting...")
        service = ModelTrainingService(db)
        train_res = service.train_and_evaluate(model_type="RandomForest")
        print("Model trained successfully!")
        print(f"Version Tag: {train_res.get('version_tag')}")
        print(f"ROC-AUC: {train_res['metrics'].get('roc_auc')}")
        print(f"PR-AUC: {train_res['metrics'].get('pr_auc')}")
        print(f"Recall: {train_res['metrics'].get('recall')}")
        print(f"Precision: {train_res['metrics'].get('precision')}")
        print(f"Selected Threshold: {train_res.get('selected_threshold')}")

        print("\nGenerating batch customer risk predictions and retention priorities...")
        p_engine = RetentionPrioritizationEngine(db)
        priorities = p_engine.generate_predictions_and_priorities(limit=10)
        print(f"Total customers scored: {priorities.get('total_customers_scored')}")
        print(f"High risk accounts: {priorities.get('high_risk_count')}")

        print("\nComputing deterministic business insights...")
        ins_engine = BusinessInsightEngine(db)
        insights = ins_engine.generate_all_insights()
        print(f"Generated {len(insights)} verified business insights.")
        for ins in insights:
            print(f"- [{ins['severity'].upper()}] {ins['title']}")

        return train_res
    finally:
        db.close()


if __name__ == "__main__":
    train_initial_model()
