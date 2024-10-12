# models.py

from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Presence:
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    start_msg_sent: bool = False
    end_msg_sent: bool = False

@dataclass
class PresencesPerUser:
    recipient_id: str  # Telefonnummer oder Gruppen-ID
    recipient_type: str  # "individual" oder "group"
    presence: Presence = field(default_factory=Presence)
