from fastapi import APIRouter
from pydantic import BaseModel
from app.events import ai_events

router = APIRouter(prefix="/events", tags=["events"])

class EventPayload(BaseModel):
    data: dict

@router.post("/broadcast")
async def broadcast_event(payload: EventPayload):
    # Receives an event via HTTP and broadcasts it to all connected WebSockets
    await ai_events.notify(payload.data)
    return {"status": "success", "message": "Event relayed to WebSockets"}