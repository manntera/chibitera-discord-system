import os

TOKEN: str | None = os.environ.get("DISCORD_TOKEN_SECRET")
SAGYOU_CHANNEL_ID: int = int(os.environ.get("SAGYOU_CHANNEL_ID") or 0)
NOTICE_CHANNEL_ID: int = int(os.environ.get("NOTICE_CHANNEL_ID") or 0)

POMO_DEBUG_CHANNEL_ID: int = int(os.environ.get("POMO_DEBUG_CHANNEL_ID") or 0)
LEAVE_CHANNEL_ID: int = int(os.environ.get("LEAVE_CHANNEL_ID") or 0)

SENTRY_SDK: str = os.environ.get("SENTRY_SDK") or ""