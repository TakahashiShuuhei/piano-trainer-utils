# 開発環境セットアップ

このドキュメントはClaude Code用の開発環境セットアップ手順です。

## 前提条件

- Python 3.x がインストールされていること
- Git がインストールされていること

## セットアップ手順

### 1. 仮想環境の作成

```bash
cd /home/shuhei/dev/piano-trainer-utils
python -m venv env
```

### 2. 仮想環境のアクティベート

```bash
source env/bin/activate
# または
./env/bin/activate
```

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

## 依存パッケージ

- `music21>=9.1.0`: MusicXML処理用
- `pygame>=2.5.0`: conv.py で使用（音楽処理）
- `pyyaml>=6.0`: YAML設定ファイル解析用

## スクリプトの実行

すべてのスクリプトは仮想環境がアクティブな状態で実行してください。

### MusicXML → JSON変換

```bash
python scripts/conv.py input.mxl -o output.json
```

### JSON編集

```bash
python scripts/edit_json.py input.json -o output.json --measures 1 4
```

### デプロイ（セクション生成＆GitHub プッシュ）

```bash
python scripts/deploy.py songs/song-name/song.yaml
```

## ディレクトリ構成

```
piano-trainer-utils/
├── env/                 # 仮想環境（gitignore対象）
├── scripts/
│   ├── conv.py         # MusicXML → JSON変換
│   ├── edit_json.py    # JSON編集
│   └── deploy.py       # デプロイスクリプト（開発中）
├── songs/
│   └── <song-name>/
│       ├── song.yaml
│       ├── source/
│       │   └── full.json
│       └── generated/  # deploy.py が自動生成
├── requirements.txt
├── .gitignore
├── SPEC.md             # 機能仕様
└── CLAUDE.md           # このファイル
```

## 開発時の注意事項

- 必ず仮想環境をアクティベートしてから作業すること
- `scripts/` 内のスクリプトは `/home/shuhei/dev/msc/scripts/` から移行したもの
- `deploy.py` は新規開発中のスクリプト
- 各曲は専用のGitブランチで管理される（例: `take-five`, `someday-my-prince-will-come`）
