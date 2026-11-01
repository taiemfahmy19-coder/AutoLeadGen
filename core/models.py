"""AutoLeadGen v2 - Core Domain Models and Dataclasses."""
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
from datetime import datetime
from config.constants import (
    STATUS_NEW,
    WA_STATUS_UNKNOWN,
    PHONE_UNKNOWN,
)


@dataclass
class Lead:
    id: Optional[int] = None
    business_name: str = ""
    phone: str = ""
    address: str = ""
    website: str = ""
    industry: str = ""
    city: str = ""
    source: str = "search"
    score: int = 0
    status: str = STATUS_NEW
    language: str = "Arabic"
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    whatsapp_status: str = WA_STATUS_UNKNOWN
    phone_validity: str = PHONE_UNKNOWN

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row) -> "Lead":
        if not row:
            return cls()
        # Schema tuple mapping:
        # 0: id, 1: business_name, 2: phone, 3: address, 4: website, 5: industry,
        # 6: city, 7: source, 8: score, 9: status, 10: language, 11: created_at, 12: updated_at,
        # 13: whatsapp_status, 14: phone_validity
        return cls(
            id=row[0] if len(row) > 0 else None,
            business_name=row[1] if len(row) > 1 and row[1] else "",
            phone=row[2] if len(row) > 2 and row[2] else "",
            address=row[3] if len(row) > 3 and row[3] else "",
            website=row[4] if len(row) > 4 and row[4] else "",
            industry=row[5] if len(row) > 5 and row[5] else "",
            city=row[6] if len(row) > 6 and row[6] else "",
            source=row[7] if len(row) > 7 and row[7] else "search",
            score=row[8] if len(row) > 8 and row[8] is not None else 0,
            status=row[9] if len(row) > 9 and row[9] else STATUS_NEW,
            language=row[10] if len(row) > 10 and row[10] else "Arabic",
            created_at=row[11] if len(row) > 11 and row[11] else "",
            updated_at=row[12] if len(row) > 12 and row[12] else "",
            whatsapp_status=row[13] if len(row) > 13 and row[13] else WA_STATUS_UNKNOWN,
            phone_validity=row[14] if len(row) > 14 and row[14] else PHONE_UNKNOWN,
        )


@dataclass
class Interaction:
    id: Optional[int] = None
    lead_id: Optional[int] = None
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    channel: str = "WhatsApp"
    message: str = ""
    status: str = "MANUALLY_MARKED"
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LeadScoreBreakdown:
    phone_valid: int = 0
    mobile_carrier: int = 0
    whatsapp_verified: int = 0
    business_name: int = 0
    address: int = 0
    industry_clarity: int = 0
    source_quality: int = 0
    total: int = 0

    def to_dict(self) -> Dict[str, int]:
        return asdict(self)
