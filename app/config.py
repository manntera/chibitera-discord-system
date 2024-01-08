import os

from pydantic import BaseModel, Field

# 環境変数

TOKEN: str | None = os.environ.get("DISCORD_TOKEN_SECRET")
SAGYOU_CHANNEL_ID: int = int(os.environ.get("SAGYOU_CHANNEL_ID") or 0)
NOTICE_CHANNEL_ID: int = int(os.environ.get("NOTICE_CHANNEL_ID") or 0)

POMO_DEBUG_CHANNEL_ID: int = int(os.environ.get("POMO_DEBUG_CHANNEL_ID") or 0)
LEAVE_CHANNEL_ID: int = int(os.environ.get("LEAVE_CHANNEL_ID") or 0)

SENTRY_SDK: str = os.environ.get("SENTRY_SDK") or ""
DEBUG_MODE: bool = bool(os.environ.get("DEBUG_MODE", 0))

# ファイルパス関連

BUCKET_NAME = "pomodorotimer"
PATH_ACTORLIST_JSON = "actors/actorlist.json"
PATH_ACTOR_JSON = "actors/{timekeeper_name}/actor.json"
PATH_ACTOR_VOICE_FILE_NAME = (
    "actors/{timekeeper_name}/{voice_id}.wav"  # actor.jsonのid_listから取得したボイスIDのファイルを取得
)


# 各ボイスIndex

GREETING_INDEX = 0
BEFORE_COMPLETE_OF_WORK_INDEX = 1
COMPLETE_OF_WORK_INDEX = 2
BEFORE_COMPLETE_OF_BREAK_INDEX = 3
COMPLETE_OF_BREAK_INDEX = 4
JOIN_MEMBER_INDEX = 5


class VoiceInfo(BaseModel):
    desc: str = Field(description="このモードの説明")
    timedelta: dict = Field(description="再生する時間のdict")
    next_mode: str = Field(description="次のモード")
    debug_message: str = Field("デバッグ時のメッセージ")
    is_update_latest_time: bool = Field(description="最後に再生した時間を更新するかしないか")


BEFORE_WORK_INFO = VoiceInfo(
    desc="作業終了前",
    timedelta={"minutes": 2},  # 42
    next_mode="work_time",
    debug_message="作業終了予告ボイス再生完了",
    is_update_latest_time=False,
)

WORK_INFO = VoiceInfo(
    desc="作業終了",
    timedelta={"minutes": 2},  # 45
    next_mode="break_time",  # before_break_time
    debug_message="作業終了ボイス再生完了",
    is_update_latest_time=True,
)

BEFORE_BREAK_INFO = VoiceInfo(
    desc="作業終了前",
    timedelta={"minutes": 2},  # 12
    next_mode="break_time",
    debug_message="休憩終了予告ボイス再生完了",
    is_update_latest_time=False,
)

BREAK_INFO = VoiceInfo(
    desc="作業終了",
    timedelta={"minutes": 2},  # 15
    next_mode="work_time",  # before_work_time
    debug_message="休憩終了ボイス再生完了",
    is_update_latest_time=True,
)


class VoiceInfos(BaseModel):
    before_break_time: VoiceInfo = BEFORE_BREAK_INFO
    break_time: VoiceInfo = BREAK_INFO
    before_work_time: VoiceInfo = BEFORE_WORK_INFO
    work_time: VoiceInfo = WORK_INFO
