# JSON構成

## actorlist.json
```json
{
    "actor_info": [
        {"id": 001},
        {"id": 002}
    ]
}
```
## actor.json
```json
{
    "actor_name": "manntera"
    "profile": "自己紹介",
    "voice_list": [
        {
            "category": "001",
            "id_list": [
                "001"
            ]
        },
        {
            "category": "002",
            "id_list": [
                "002"
            ]
        },
        {
            "category": "003",
            "id_list": [
                "003"
            ]
        },
        {
            "category": "004",
            "id_list": [
                "004"
            ]
        },
        {
            "category": "005",
            "id_list": [
                "005"
            ]
        }
    ]
}
```

## VoiceListについて

```
001…担当挨拶・初回作業開始ボイス
002…作業終了前ボイス
003…作業終了(休憩開始)ボイス
004…休憩終了前ボイス
005…休憩終了(作業開始)ボイス
```

# Profileについて

- アクターの紹介文章
  - discordで使えるマークダウンは使用可能
  - 見出し・箇条書き・リンク