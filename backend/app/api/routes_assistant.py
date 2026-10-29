from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.assistant import ControlledAnalyticsAssistant
from backend.app.schemas import AssistantRequest

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])


@router.post("/query")
def query_assistant(payload: AssistantRequest, db: Session = Depends(get_db)):
    assistant = ControlledAnalyticsAssistant(db)
    return assistant.query(payload.question)
