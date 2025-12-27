# 楽曲データ管理仕様

## 概要

MusicXMLから生成した楽曲JSON（full.json）を設定ファイル（YAML）で宣言的に分割し、練習用JSONファイルとREADME.mdを自動生成する。

## リポジトリ構成

```
piano-trainer-utils/
├── scripts/
│   ├── conv.py              # MusicXML → JSON変換（既存）
│   ├── edit_json.py         # JSON編集（既存）
│   └── deploy.py            # 新規: 設定ファイルから自動分割＆配置
└── songs/
    └── <song-name>/         # 各曲は専用ブランチで管理
        ├── song.yaml        # 設定ファイル
        ├── source/
        │   ├── song.mxl     # 元のMusicXMLファイル
        │   └── full.json    # 全体のJSON
        └── generated/       # deploy.py実行時に毎回クリア＆再生成
            ├── README.md
            ├── intro.json
            ├── verse-a.json
            └── ...
```

**ブランチ戦略**:
- 各曲は専用のブランチで管理（例: `take-five`, `someday-my-prince-will-come`）
- YAMLの`branch`フィールドで指定
- `main`ブランチからの分岐

## 設定ファイル形式（song.yaml）

```yaml
title: "曲名"
bpm: 120
branch: "take-five"
source: "source/full.json"
beats: 4  # オプション: 1小節の拍数

sections:
  - name: "intro"
    measures: [1, 4]

  - name: "bridge"
    beats: [48.0, 64.0]

  - name: "solo"
    measures: [10, 20]
    sections:
      - name: "first-half"
        measures: [10, 15]
        sections:
          - name: "intro"
            measures: [10, 12]
          - name: "main"
            measures: [13, 15]

      - name: "second-half"
        measures: [16, 20]
```

### 必須フィールド

- `title`: 曲名（文字列）
- `bpm`: テンポ（数値）
- `branch`: デプロイ先のブランチ名（文字列）
- `source`: 元のJSONファイルへの相対パス（文字列）
- `sections`: セクション定義の配列

### オプションフィールド

- `beats`: 1小節の拍数（数値）。指定された場合のみ`edit_json.py`に`--beats`オプションとして渡される

### セクション定義

各セクションは以下のフィールドを持つ：

- `name`: セクション名（文字列、必須）
- `measures`: 小節範囲 `[開始, 終了]`（`beats`と排他）
- `beats`: beat範囲 `[開始, 終了]`（`measures`と排他）
- `sections`: 子セクションの配列（オプション、再帰的に定義可能）

### バリデーションルール

1. `measures` と `beats` が両方指定されている → **エラー**
2. `measures` と `beats` がどちらも指定されていない → **エラー**
3. `measures` が `[end, start]` のように逆順 → **エラー**
4. `beats` が `[end, start]` のように逆順 → **エラー**

## 生成されるファイル

### JSONファイル名の規則

すべての生成ファイルは`generated/`ディレクトリに配置される。
ネストされたセクションはハイフン（`-`）で連結：

- `generated/intro.json`
- `generated/solo.json`
- `generated/solo-first-half.json`
- `generated/solo-first-half-intro.json`
- `generated/solo-first-half-main.json`
- `generated/solo-second-half.json`

### README.md の形式

```markdown
# 曲名

- **BPM**: 120
- **Source**: [full.json](source/full.json)

## Sections

* **intro** (measures 1-4) - [Practice](https://takahashishuuhei.github.io/apps/piano-practice/?song=https://raw.githubusercontent.com/TakahashiShuuhei/piano-trainer-utils/take-five/songs/take-five/generated/intro.json)
* **bridge** (beats 48.0-64.0) - [Practice](https://takahashishuuhei.github.io/apps/piano-practice/?song=https://raw.githubusercontent.com/TakahashiShuuhei/piano-trainer-utils/take-five/songs/take-five/generated/bridge.json)
* **solo** (measures 10-20) - [Practice](https://takahashishuuhei.github.io/apps/piano-practice/?song=https://raw.githubusercontent.com/TakahashiShuuhei/piano-trainer-utils/take-five/songs/take-five/generated/solo.json)
  * **first-half** (measures 10-15) - [Practice](https://takahashishuuhei.github.io/apps/piano-practice/?song=https://raw.githubusercontent.com/TakahashiShuuhei/piano-trainer-utils/take-five/songs/take-five/generated/solo-first-half.json)
    * **intro** (measures 10-12) - [Practice](https://takahashishuuhei.github.io/apps/piano-practice/?song=https://raw.githubusercontent.com/TakahashiShuuhei/piano-trainer-utils/take-five/songs/take-five/generated/solo-first-half-intro.json)
    * **main** (measures 13-15) - [Practice](https://takahashishuuhei.github.io/apps/piano-practice/?song=https://raw.githubusercontent.com/TakahashiShuuhei/piano-trainer-utils/take-five/songs/take-five/generated/solo-first-half-main.json)
  * **second-half** (measures 16-20) - [Practice](https://takahashishuuhei.github.io/apps/piano-practice/?song=https://raw.githubusercontent.com/TakahashiShuuhei/piano-trainer-utils/take-five/songs/take-five/generated/solo-second-half.json)
```

**フォーマット規則**:
- ネストされたセクションは2スペースのインデント
- リンク形式: `[Practice](https://takahashishuuhei.github.io/apps/piano-practice/?song=<JSONのrawURL>)`
- 範囲表示: `measures X-Y` または `beats X-Y`

## deploy.py の仕様

### 使い方

```bash
python scripts/deploy.py songs/song-name/song.yaml
```

### 処理フロー

1. YAMLファイルを読み込み
2. バリデーション実行
3. Git操作:
   - 現在のブランチを確認
   - YAMLの`branch`と異なる場合、未コミットの変更を`git reset --hard`でクリア
   - ブランチが存在しない場合、`main`から新規作成
   - 対象ブランチにチェックアウト
4. `generated/`ディレクトリをクリア（存在する場合は削除して再作成）
5. 各セクション（再帰的に）について：
   - `edit_json.py` を呼び出してJSONを`generated/`に生成
   - ファイル名とURLを計算
6. README.mdを`generated/`に生成
7. Git操作:
   - `git add generated/` で生成ファイルをステージング
   - `git commit -m "Deploy sections for <title>"`
   - `git push origin <branch>`
8. 結果をコンソールに出力

### 出力例

```
Switching to branch 'take-five'...
Clearing generated/ directory...

✓ generated/intro.json
  → https://takahashishuuhei.github.io/apps/piano-practice/?song=https://raw.githubusercontent.com/TakahashiShuuhei/piano-trainer-utils/take-five/songs/take-five/generated/intro.json

✓ generated/solo.json
  → https://takahashishuuhei.github.io/apps/piano-practice/?song=https://raw.githubusercontent.com/TakahashiShuuhei/piano-trainer-utils/take-five/songs/take-five/generated/solo.json

✓ generated/solo-first-half.json
  → https://takahashishuuhei.github.io/apps/piano-practice/?song=https://raw.githubusercontent.com/TakahashiShuuhei/piano-trainer-utils/take-five/songs/take-five/generated/solo-first-half.json

✓ generated/README.md 生成完了

Committing and pushing...
✓ Deployed to branch 'take-five'
```

### エラーハンドリング

- `edit_json.py` の実行が失敗した場合 → 即座に停止してエラーメッセージを表示
- `source` で指定されたファイルが存在しない → エラー
- YAMLのバリデーションエラー → エラー内容を表示して停止

### Git操作の詳細

1. **ブランチの切り替え**:
   - 現在のブランチがYAMLの`branch`と異なる場合、未コミットの変更を`git reset --hard`でクリア
   - ブランチが存在しない場合、`git checkout -b <branch> origin/main`で`main`から新規作成
   - ブランチが存在する場合、`git checkout <branch>`で切り替え

2. **generated/ディレクトリのクリア**:
   - `generated/`ディレクトリが存在する場合は削除
   - 新規に`generated/`ディレクトリを作成
   - これにより、削除されたセクションのファイルも自動的にクリーンアップされる

3. **コミット＆プッシュ**:
   - 生成されたファイルを`git add generated/`でステージング
   - `git commit -m "Deploy sections for <title>"`でコミット
   - `git push origin <branch>`でリモートにプッシュ

## 定数

- **GitHubリポジトリ**: `TakahashiShuuhei/piano-trainer-utils`
- **ブランチ**: `main`
- **練習アプリURL**: `https://takahashishuuhei.github.io/apps/piano-practice/`

## 依存関係

- Python 3.x
- `pyyaml` パッケージ
- 既存の `edit_json.py` スクリプト

## edit_json.py の呼び出し仕様

### measures指定の場合

```bash
python scripts/edit_json.py <source-json> \
  --measures <start> <end> \
  --beats <beats-per-measure> \
  --output <output-json>
```

- `--beats` はYAMLの`beats`フィールドから取得（デフォルト: 4）
- 例: `python scripts/edit_json.py source/full.json --measures 1 4 --beats 4 --output intro.json`

### beats指定の場合

```bash
python scripts/edit_json.py <source-json> \
  --beat-range <start> <end> \
  --output <output-json>
```

- `--beats` オプションは不要
- 例: `python scripts/edit_json.py source/full.json --beat-range 48.0 64.0 --output bridge.json`
