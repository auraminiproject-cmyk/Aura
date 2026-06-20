from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.api.core.security import get_current_user_id

router = APIRouter()


class AsyncBodyJob(BaseModel):
    front_image_base64: str
    side_image_base64: str | None = None


@router.post("/body-reconstruct")
async def enqueue_body_reconstruct(body: AsyncBodyJob, _user_id: str = Depends(get_current_user_id)):
    try:
        from services.api.tasks.celery_app import reconstruct_body_task

        task = reconstruct_body_task.delay(body.front_image_base64, body.side_image_base64)
        return {"task_id": task.id, "status": "queued"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Celery unavailable: {exc}") from exc


@router.get("/{task_id}")
async def get_task_status(task_id: str, _user_id: str = Depends(get_current_user_id)):
    try:
        from services.api.tasks.celery_app import celery_app

        result = celery_app.AsyncResult(task_id)
        return {"task_id": task_id, "state": result.state, "result": result.result if result.ready() else None}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
