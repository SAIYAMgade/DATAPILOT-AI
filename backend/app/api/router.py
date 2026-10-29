from fastapi import APIRouter

from backend.app.api.routes_metrics import router as metrics_router
from backend.app.api.routes_customers import router as customers_router
from backend.app.api.routes_segmentation import router as segmentation_router
from backend.app.api.routes_cohorts import router as cohorts_router
from backend.app.api.routes_stats import router as stats_router
from backend.app.api.routes_ml import router as ml_router
from backend.app.api.routes_insights import router as insights_router
from backend.app.api.routes_ingestion import router as ingestion_router
from backend.app.api.routes_assistant import router as assistant_router

api_router = APIRouter(prefix="/api")

api_router.include_router(metrics_router)
api_router.include_router(customers_router)
api_router.include_router(segmentation_router)
api_router.include_router(cohorts_router)
api_router.include_router(stats_router)
api_router.include_router(ml_router)
api_router.include_router(insights_router)
api_router.include_router(ingestion_router)
api_router.include_router(assistant_router)
