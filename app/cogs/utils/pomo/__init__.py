from config import BUCKET_NAME
from google.cloud import storage

from .download import *
from .error import *
from .play import Play
from .timekepper import Timekeeper
from .types import *

__all__ = ("PomodoroTimer", "Play")


class PomodoroTimer:
    def __init__(self, bot):
        self.storage_client = storage.Client()
        self.bucket: storage.Bucket = self.storage_client.bucket(BUCKET_NAME)
        self.bot = bot
        self.download = Download(bot, self.bucket)
        self.timekeeper = Timekeeper(bot, self.bucket)

    def clear(self):
        self.timekeeper.clear()
        self.download.clear()
