from dataclasses import dataclass
from typing import List
from datetime import datetime


@dataclass
class Team:
    canonical_name: str
    team_name: str
    members: List[int]
    signup_message_id: int
    denied_by: int | None = None
    approved_at: datetime | None = None
    signup_pending: bool = True
