"""AutoLeadGen V3 — Background Task Queue & Scheduler Manager."""
import json
import uuid
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, Any, Optional, List

from apscheduler.schedulers.background import BackgroundScheduler
from database.repository import LeadRepository
from utils.logger import info, error


class TaskCancelled(Exception):
    """Raised inside a background worker when cancel_requested is set."""


class TaskManager:
    def __init__(self, max_workers: int = 4):
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="alg_worker")
        self._scheduler = BackgroundScheduler(daemon=True)
        self._lock = threading.Lock()
        self._futures = {}
        self._ws_broadcaster: Optional[Callable[[str, Dict[str, Any]], None]] = None
        if not self._scheduler.running:
            self._scheduler.start()

    def set_broadcaster(self, fn: Callable[[str, Dict[str, Any]], None]):
        self._ws_broadcaster = fn

    def _emit(self, event_type: str, payload: Dict[str, Any]):
        if self._ws_broadcaster:
            try:
                self._ws_broadcaster(event_type, payload)
            except Exception:
                pass

    def submit_task(
        self,
        func: Callable[..., Any],
        params: Optional[Dict[str, Any]] = None,
        task_type: str = "generic",
    ) -> str:
        task_id = str(uuid.uuid4())[:12]
        params = params or {}
        repo = LeadRepository()
        try:
            repo.create_task(task_id=task_id, task_type=task_type, params_json=json.dumps(params, ensure_ascii=False))
        finally:
            repo.close()

        future = self._executor.submit(self._run_wrapped, task_id, task_type, func, params)
        with self._lock:
            self._futures[task_id] = future
        self._emit("task_started", {"task_id": task_id, "task_type": task_type, "status": "running", "progress": 0.0})
        return task_id

    def _run_wrapped(self, task_id: str, task_type: str, func: Callable, params: Dict[str, Any]):
        repo = LeadRepository()

        def report_progress(pct: float, msg: str = ""):
            if repo.is_task_cancelled(task_id):
                raise TaskCancelled(f"Task {task_id} cancelled by user.")
            pct = max(0.0, min(1.0, float(pct)))
            repo.update_task_progress(task_id, progress=pct, status="running", error_log=msg)
            self._emit("task_progress", {"task_id": task_id, "task_type": task_type, "progress": pct, "message": msg})

        def is_cancelled() -> bool:
            return repo.is_task_cancelled(task_id)

        try:
            result = func(
                **params,
                task_id=task_id,
                progress_cb=report_progress,
                cancel_check=is_cancelled,
            )
            res_json = json.dumps(result if result is not None else {}, default=str, ensure_ascii=False)
            repo.update_task_progress(task_id, progress=1.0, status="completed", result_json=res_json)
            self._emit("task_completed", {"task_id": task_id, "task_type": task_type, "progress": 1.0, "result": result})
            info(f"Task {task_id} ({task_type}) completed.")
        except TaskCancelled as ce:
            repo.update_task_progress(task_id, progress=0.0, status="cancelled", error_log=str(ce))
            self._emit("task_cancelled", {"task_id": task_id, "task_type": task_type})
            info(f"Task {task_id} cancelled.")
        except Exception as exc:
            tb = traceback.format_exc()
            error(f"Task {task_id} failed: {exc}\n{tb}")
            repo.update_task_progress(task_id, progress=0.0, status="failed", error_log=str(exc))
            self._emit("task_failed", {"task_id": task_id, "task_type": task_type, "error": str(exc)})
        finally:
            repo.close()

    def cancel_task(self, task_id: str) -> bool:
        repo = LeadRepository()
        try:
            task = repo.get_task_by_id(task_id)
            if not task:
                return False
            repo.cancel_task(task_id)
            return True
        finally:
            repo.close()

    def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        repo = LeadRepository()
        try:
            return repo.get_task_by_id(task_id)
        finally:
            repo.close()

    def list_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        repo = LeadRepository()
        try:
            return repo.list_tasks(limit=limit)
        finally:
            repo.close()

    def add_interval_job(self, job_id: str, func: Callable, minutes: int = 5):
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)
        self._scheduler.add_job(func, "interval", minutes=minutes, id=job_id, replace_existing=True)


task_manager = TaskManager()
