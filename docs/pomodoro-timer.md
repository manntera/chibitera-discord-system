# JSON構成

## actorlist.json
```json
{
    "actor_info": [
        {"name": "actorA"},
        {"name": "acotorB"}
    ]
}
```
## actor.json
```json
{
    "actor_name": "manntera",
    "profile": "自己紹介",
    "leave": "またね！",
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
        {
            "category": "006",
            "id_list": [
                "006"
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
006…2人目以降入室ボイス
```

# Profileについて

- アクターの紹介文章
  - discordで使えるマークダウンは使用可能
  - 見出し・箇条書き・リンク

# Leaveについて

- メンバーが退出した時にテキストチャンネルに送信する文章
  - discordで使えるマークダウンは使用可能
  - 見出し・箇条書き・リンク


# 内部仕様

## bucket
- フォルダー
  - アクター名
  - actorlist.jsonのnameに記入した名前で作成

## 時間確認
- 再生完了後、現在時刻を保存

- 10秒毎に現在時刻が次のボイスを再生する時間(以上)か確認

```python

from datetime import datetime, timedelta

# 再生完了
latest_time = datetime.now()

# 休憩時間 -> 5分
# 休憩終了予告ボイス -> 休憩終了3分前に再生
# 休憩終了ボイス -> 休憩終了時間に再生

# 以下10秒ごとに確認

# 休憩終了予告ボイスを再生する時間か確認
if latest_time + timedelta(minutes=2) >= datetime.now():
    # 再生
    # latest_timeは更新しない

# 休憩終了ボイスを再生する時間か確認
if latest_time + timedelta(minutes=5) >= datetime.now():
    # 再生
    latest_time = datetime.now()
```

