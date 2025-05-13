from dataclasses import dataclass
from datetime import datetime


@dataclass
class Tournament:
    tournament_id: int
    tournament_name: str
    signups_close_date: datetime
    tournament_start_date: datetime
    team_count: int
    team_size: int
