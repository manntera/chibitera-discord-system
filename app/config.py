import os

from dotenv import load_dotenv

env = "dev"


if env == "dev":
    load_dotenv()


TOKEN: str | None = os.environ.get("TOKEN")
