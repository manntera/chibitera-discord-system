import os

from dotenv import load_dotenv

load_dotenv()


TOKEN: str | None = os.environ.get("TOKEN")
