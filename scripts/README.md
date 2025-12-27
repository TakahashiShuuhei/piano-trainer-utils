# Scripts

このディレクトリには、MusicXMLファイルの変換と再生を行うPythonスクリプトが含まれています。

## ファイル一覧

### conv.py
MusicXMLファイルをJSONフォーマットに変換するスクリプト

**機能:**
- music21ライブラリを使用してMusicXMLファイルを解析
- MXL（圧縮MusicXML）ファイルに対応
- タイ、和音、テンポマークを自動処理
- MIDI音高番号への変換
- タイミング情報（拍位置、音長）の計算

**使用方法:**
```bash
python conv.py <input_file> -o <output.json>
python conv.py <input_file>  # 標準出力に表示
```

**例:**
```bash
# MXLファイルを変換（圧縮形式に対応）
python conv.py score.mxl -o output.json

# XMLファイルを変換
python conv.py score.xml -o output.json

# 標準出力に表示
python conv.py score.musicxml
```

**対応フォーマット:**
- .mxl (圧縮MusicXML)
- .xml (MusicXML)
- .musicxml

**出力フォーマット:**
```json
{
  "title": "曲名",
  "bpm": 120,
  "notes": [
    {
      "pitch": 60,
      "timing": {
        "beat": 0.0,
        "duration": 1.0
      },
      "velocity": 80
    }
  ]
}
```

### edit_json.py
JSON楽曲データ編集ユーティリティ

**機能:**
- 指定した小節範囲の抽出（beat位置を自動調整）
- 指定したbeat範囲の直接抽出
- 音高による音符のフィルタリング
- 右手/左手パートの抽出（練習用）
  - **handフィールド優先**: JSONにhandフィールドがあればそれを使用
  - **音高フォールバック**: handフィールドがない場合は音高で判定

**使用方法:**
```bash
python edit_json.py <input.json> -o <output.json> [オプション]
```

**主なオプション:**

*範囲抽出:*
- `--measures START END`: 小節範囲を抽出（1から開始）
- `--beats N`: 1小節の拍数（デフォルト: 4）
- `--beat-range START END`: beat範囲を直接指定して抽出（0から開始、終了位置は含まない）

*音高フィルタリング:*
- `--right-hand`: 右手パート（高音部）のみ抽出（handフィールド優先）
- `--left-hand`: 左手パート（低音部）のみ抽出（handフィールド優先）
- `--threshold N`: 右手/左手の閾値となるMIDI音高（デフォルト: 60 = C4）handフィールドがない場合のフォールバック
- `--use-pitch-threshold`: handフィールドを無視して音高のみで判定
- `--min-pitch N`: 最小MIDI音高
- `--max-pitch N`: 最大MIDI音高

**例:**
```bash
# 3-8小節を抽出
python edit_json.py input.json -o output.json --measures 3 8

# 3-8小節を抽出（1小節=3拍の曲）
python edit_json.py input.json -o output.json --measures 3 8 --beats 3

# beat 8.0から16.0までを抽出
python edit_json.py input.json -o output.json --beat-range 8.0 16.0

# 右手パートのみ抽出（handフィールド優先、なければC4=60以上）
python edit_json.py input.json -o output.json --right-hand

# 左手パートのみ抽出（handフィールド優先、なければC4=60未満）
python edit_json.py input.json -o output.json --left-hand

# カスタム閾値で左手抽出（handフィールド優先、なければA3=57未満）
python edit_json.py input.json -o output.json --left-hand --threshold 57

# handフィールドを無視して音高のみで判定（後方互換性）
python edit_json.py input.json -o output.json --right-hand --use-pitch-threshold

# 音高範囲で抽出（C3=48からC5=72まで）
python edit_json.py input.json -o output.json --min-pitch 48 --max-pitch 72

# 組み合わせ: 3-8小節の右手パートのみ
python edit_json.py input.json -o output.json --measures 3 8 --right-hand

# 組み合わせ: beat 8.0から16.0までの左手パートのみ
python edit_json.py input.json -o output.json --beat-range 8.0 16.0 --left-hand
```

### play_mxl.py
MusicXML/MXLファイルを再生するスクリプト

**機能:**
- MXL/MusicXMLファイルの読み込みと再生
- 必要なパッケージの自動チェックとインストール
- MIDIへの変換と音声再生

**使用方法:**
```bash
python play_mxl.py <mxl_file>
```

**例:**
```bash
python play_mxl.py 001.mxl
```

**対応フォーマット:**
- .mxl (圧縮MusicXML)
- .xml (MusicXML)
- .musicxml

### requirements.txt
Pythonパッケージの依存関係リスト

**依存パッケージ:**
- `music21>=9.1.0` - MusicXML/MIDI処理
- `pygame>=2.5.0` - オーディオ再生

## セットアップ

必要なパッケージをインストール:
```bash
pip install -r requirements.txt
```

または、`play_mxl.py`が自動的にインストールします。

## 技術詳細

### conv.pyの処理フロー
1. MusicXMLファイルをパース
2. 各パート・小節を順次処理
3. 音符要素から音高（MIDI番号）とタイミング情報を抽出
4. タイ処理: 連続する音符を結合
5. 和音処理: 同じ拍位置の音符をグループ化
6. 複数声部: 声部ごとに独立したタイミングトラック
7. JSONフォーマットに変換して出力

### play_mxl.pyの処理フロー
1. MusicXML/MXLファイルを`music21`で読み込み
2. 一時MIDIファイルに変換
3. `pygame.mixer`で再生
4. 再生完了後、一時ファイルを削除
