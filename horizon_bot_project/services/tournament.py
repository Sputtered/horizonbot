from datetime import datetime
from hbp_types.tournament import Tournament
from storage import TournamentStorage


class TournamentService:
    def __init__(self, storage: TournamentStorage):
        self._storage = storage

    async def get_current_tournament(self) -> Tournament | None:
        return await self._storage.get_current_tournament()

    async def is_signups_open(self) -> bool:
        return await self._storage.is_signups_open()

    async def create_tournament(self, tournament: Tournament) -> bool:
        if (
            tournament.signups_close_date < datetime.now()
            or tournament.tournament_start_date < datetime.now()
        ):
            raise ValueError("Signups and close date must be in the future")

        if tournament.signups_close_date >= tournament.tournament_start_date:
            raise ValueError("Signups must close before the tournament starts")

        existing = await self.get_current_tournament()
        if existing:
            raise RuntimeError("There is already an ongoing tournament")

        await self._storage.insert_tournament(tournament)
        return True
