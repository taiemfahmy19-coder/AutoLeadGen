"""AutoLeadGen V3 — Repository Abstraction Layer (SQLite & PostgreSQL/PostGIS Ready)."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class AbstractLeadRepository(ABC):
    """
    Backend-agnostic repository contract.
    Allows transparent migration from SQLite to PostgreSQL + PostGIS
    without modifying service, pipeline, FastAPI, or UI layers.
    """

    @abstractmethod
    def insert_lead(self, business_name: str, phone: str, **kwargs) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_lead_by_id(self, lead_id: int) -> Any:
        raise NotImplementedError

    @abstractmethod
    def get_all_leads(self) -> List[Any]:
        raise NotImplementedError

    @abstractmethod
    def get_leads_paginated(
        self,
        page: int = 1,
        page_size: int = 50,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        raise NotImplementedError

    @abstractmethod
    def get_leads_in_bbox(
        self,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float,
        limit: int = 5000,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def update_lead_fields(self, lead_id: int, **fields) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_lead(self, lead_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        raise NotImplementedError
