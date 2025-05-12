from typing import List
import discord
from storage import MessageStorage


class MessageService:
    def __init__(self, message_storage: MessageStorage, buffer_size: int = 20):
        self._buffer: List[discord.Message] = []
        self._buffer_size = buffer_size

        self._message_storage = message_storage

    async def log_message(self, message: discord.Message):
        self._buffer.append(message)
        if len(self._buffer) >= self._buffer_size:
            await self.flush_buffer()

    async def flush_buffer(self):
        if self._buffer:
            await self._message_storage.bulk_log_message(self._buffer)
            self._buffer.clear()
