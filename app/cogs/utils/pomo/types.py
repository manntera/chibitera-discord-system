from typing import TypedDict

from pydantic import BaseModel

__all__ = ("TActors", "TActor", "_TActor_Voices", "NowVoiceInfo")


class _TActorList(TypedDict):
    name: str


class TActors(TypedDict):
    actor_info: list[_TActorList]


class _TActor_Voices(TypedDict):
    category: str
    id_list: list[str]


class TActor(TypedDict):
    actor_name: str
    profile: str
    leave: str
    voice_list: list[_TActor_Voices]


class NowVoiceInfo(BaseModel):
    index: int
    category_id: str
    voice_id: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"index": 0, "category_id": "001", "voice_id": "001"},
                {"index": 1, "category_id": "002", "voice_id": "002"},
                {"index": 2, "category_id": "003", "voice_id": "003"},
                {"index": 3, "category_id": "004", "voice_id": "004"},
                {"index": 4, "category_id": "005", "voice_id": "006"},
            ]
        }
    }
