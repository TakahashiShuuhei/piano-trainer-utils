#!/usr/bin/env python3
"""
楽曲データデプロイツール

YAMLで定義されたセクション設定から楽曲JSONファイルを生成し、
GitHubにデプロイする。
"""

import os
import sys
import yaml
import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# 定数
GITHUB_REPO = "TakahashiShuuhei/piano-trainer-utils"
PRACTICE_APP_URL = "https://takahashishuuhei.github.io/apps/piano-practice/"
EDIT_JSON_SCRIPT = "scripts/edit_json.py"


class DeployError(Exception):
    """デプロイエラー"""
    pass


def load_yaml(yaml_path: str) -> Dict:
    """YAMLファイルを読み込む"""
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise DeployError(f"YAMLファイルが見つかりません: {yaml_path}")
    except yaml.YAMLError as e:
        raise DeployError(f"YAMLパースエラー: {e}")


def validate_config(config: Dict) -> None:
    """設定ファイルをバリデーション"""
    # 必須フィールドチェック
    required_fields = ['title', 'bpm', 'branch', 'source', 'sections']
    for field in required_fields:
        if field not in config:
            raise DeployError(f"必須フィールド '{field}' がありません")

    # sections配列チェック
    if not isinstance(config['sections'], list):
        raise DeployError("'sections' は配列である必要があります")

    if len(config['sections']) == 0:
        raise DeployError("'sections' が空です")

    # 各セクションのバリデーション
    def validate_section(section: Dict, path: str = "") -> None:
        # name必須
        if 'name' not in section:
            raise DeployError(f"セクション{path}に 'name' がありません")

        section_name = section['name']
        current_path = f"{path}/{section_name}" if path else section_name

        # measures と beats の排他チェック
        has_measures = 'measures' in section
        has_beats = 'beats' in section

        if has_measures and has_beats:
            raise DeployError(f"セクション '{current_path}': 'measures' と 'beats' は同時に指定できません")

        if not has_measures and not has_beats:
            raise DeployError(f"セクション '{current_path}': 'measures' または 'beats' のいずれかが必要です")

        # measures の範囲チェック
        if has_measures:
            measures = section['measures']
            if not isinstance(measures, list) or len(measures) != 2:
                raise DeployError(f"セクション '{current_path}': 'measures' は [開始, 終了] の形式が必要です")
            if measures[0] > measures[1]:
                raise DeployError(f"セクション '{current_path}': 'measures' が逆順です: {measures}")

        # beats の範囲チェック
        if has_beats:
            beats = section['beats']
            if not isinstance(beats, list) or len(beats) != 2:
                raise DeployError(f"セクション '{current_path}': 'beats' は [開始, 終了] の形式が必要です")
            if beats[0] > beats[1]:
                raise DeployError(f"セクション '{current_path}': 'beats' が逆順です: {beats}")

        # 再帰的にサブセクションをバリデーション
        if 'sections' in section:
            if not isinstance(section['sections'], list):
                raise DeployError(f"セクション '{current_path}': 'sections' は配列である必要があります")
            for subsection in section['sections']:
                validate_section(subsection, current_path)

    for section in config['sections']:
        validate_section(section)


def run_command(cmd: List[str], error_message: str) -> str:
    """コマンドを実行して結果を返す"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise DeployError(f"{error_message}\n{e.stderr}")


def get_current_branch() -> str:
    """現在のブランチ名を取得"""
    return run_command(
        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
        "現在のブランチ取得に失敗"
    )


def branch_exists(branch_name: str) -> bool:
    """ブランチが存在するかチェック"""
    try:
        subprocess.run(
            ['git', 'rev-parse', '--verify', branch_name],
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def switch_branch(target_branch: str) -> None:
    """ブランチを切り替える"""
    current_branch = get_current_branch()

    if current_branch == target_branch:
        print(f"Already on branch '{target_branch}'")
        return

    print(f"Switching to branch '{target_branch}'...")

    # 未コミット変更をクリア
    run_command(
        ['git', 'reset', '--hard'],
        "git reset --hard に失敗"
    )

    # ブランチの存在チェック
    if branch_exists(target_branch):
        # 既存ブランチにチェックアウト
        run_command(
            ['git', 'checkout', target_branch],
            f"ブランチ '{target_branch}' へのチェックアウトに失敗"
        )
    else:
        # mainから新規ブランチ作成
        # まずmainにチェックアウト
        run_command(
            ['git', 'checkout', 'main'],
            "mainブランチへのチェックアウトに失敗"
        )
        # 新規ブランチ作成
        run_command(
            ['git', 'checkout', '-b', target_branch],
            f"ブランチ '{target_branch}' の作成に失敗"
        )


def clear_generated_dir(song_dir: Path) -> None:
    """generated/ディレクトリをクリアして再作成"""
    generated_dir = song_dir / 'generated'

    if generated_dir.exists():
        print("Clearing generated/ directory...")
        shutil.rmtree(generated_dir)

    generated_dir.mkdir(parents=True, exist_ok=True)


def build_section_path(parent_path: str, section_name: str) -> str:
    """セクションのパスを構築"""
    if parent_path:
        return f"{parent_path}-{section_name}"
    return section_name


def generate_section_json(
    config: Dict,
    section: Dict,
    song_dir: Path,
    parent_path: str = ""
) -> List[Tuple[str, str, str]]:
    """
    セクションのJSONを生成（再帰的）

    Returns:
        List of (section_name, file_path, range_str) tuples
    """
    results = []

    section_name = section['name']
    section_path = build_section_path(parent_path, section_name)

    # 出力ファイルパス
    output_file = song_dir / 'generated' / f"{section_path}.json"

    # edit_json.py のコマンドを構築
    source_file = song_dir / config['source']
    if not source_file.exists():
        raise DeployError(f"ソースファイルが見つかりません: {source_file}")

    cmd = ['python', EDIT_JSON_SCRIPT, str(source_file), '-o', str(output_file)]

    # measures または beats を追加
    if 'measures' in section:
        measures = section['measures']
        cmd.extend(['--measures', str(measures[0]), str(measures[1])])

        # beats-per-measure オプション（YAMLに指定があれば）
        if 'beats' in config:
            cmd.extend(['--beats', str(config['beats'])])

        # pickup-beats オプション（YAMLに指定があれば）
        if 'pickup_beats' in config:
            cmd.extend(['--pickup-beats', str(config['pickup_beats'])])

        range_str = f"measures {measures[0]}-{measures[1]}"
    else:
        beats = section['beats']
        cmd.extend(['--beat-range', str(beats[0]), str(beats[1])])
        range_str = f"beats {beats[0]}-{beats[1]}"

    # edit_json.py を実行
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise DeployError(f"JSONファイル生成に失敗: {section_path}\n{e.stderr}")

    results.append((section_path, str(output_file), range_str))

    # 再帰的にサブセクションを処理
    if 'sections' in section:
        for subsection in section['sections']:
            sub_results = generate_section_json(config, subsection, song_dir, section_path)
            results.extend(sub_results)

    return results


def generate_raw_url(branch: str, song_name: str, file_name: str) -> str:
    """raw.githubusercontent.com のURLを生成"""
    return f"https://raw.githubusercontent.com/{GITHUB_REPO}/{branch}/songs/{song_name}/generated/{file_name}"


def generate_practice_url(raw_url: str) -> str:
    """練習アプリのURLを生成"""
    return f"{PRACTICE_APP_URL}?song={raw_url}"


def generate_readme(
    config: Dict,
    sections_info: List[Tuple[str, str, str]],
    song_name: str,
    output_path: Path
) -> None:
    """README.mdを生成"""
    lines = [
        f"# {config['title']}",
        "",
        f"- **BPM**: {config['bpm']}",
        f"- **Source**: [full.json](../source/full.json)",
        "",
        "## Sections",
        ""
    ]

    def count_depth(section_path: str) -> int:
        """セクションパスから階層の深さを計算"""
        return section_path.count('-')

    for section_path, file_path, range_str in sections_info:
        depth = count_depth(section_path)
        indent = "  " * depth

        # セクション名（パスの最後の部分）
        display_name = section_path.split('-')[-1]

        # ファイル名
        file_name = os.path.basename(file_path)

        # URL生成
        raw_url = generate_raw_url(config['branch'], song_name, file_name)
        practice_url = generate_practice_url(raw_url)

        lines.append(f"{indent}* **{display_name}** ({range_str}) - [Practice]({practice_url})")

    # ファイルに書き込み
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def commit_and_push(branch: str, title: str, song_dir: Path) -> None:
    """生成ファイルをコミット＆プッシュ"""
    print("\nCommitting and pushing...")

    # git add (song_dir全体)
    run_command(
        ['git', 'add', str(song_dir)],
        "git add に失敗"
    )

    # git commit
    commit_message = f"Deploy sections for {title}"
    run_command(
        ['git', 'commit', '-m', commit_message],
        "git commit に失敗"
    )

    # git push
    run_command(
        ['git', 'push', 'origin', branch],
        f"git push origin {branch} に失敗"
    )


def main():
    if len(sys.argv) != 2:
        print("使い方: python scripts/deploy.py songs/song-name/song.yaml")
        sys.exit(1)

    yaml_path = sys.argv[1]

    try:
        # YAMLファイル読み込み
        config = load_yaml(yaml_path)

        # バリデーション
        validate_config(config)

        # 曲のディレクトリを取得
        yaml_file = Path(yaml_path)
        song_dir = yaml_file.parent
        song_name = song_dir.name

        # ブランチ切り替え
        switch_branch(config['branch'])

        # generated/ ディレクトリをクリア
        clear_generated_dir(song_dir)

        # 各セクションのJSON生成
        print()
        sections_info = []
        for section in config['sections']:
            results = generate_section_json(config, section, song_dir)
            sections_info.extend(results)

        # 生成結果を表示
        for section_path, file_path, range_str in sections_info:
            file_name = os.path.basename(file_path)
            raw_url = generate_raw_url(config['branch'], song_name, file_name)
            practice_url = generate_practice_url(raw_url)
            print(f"✓ generated/{file_name}")
            print(f"  → {practice_url}")
            print()

        # README.md生成
        readme_path = song_dir / 'generated' / 'README.md'
        generate_readme(config, sections_info, song_name, readme_path)
        print("✓ generated/README.md 生成完了")

        # コミット＆プッシュ
        commit_and_push(config['branch'], config['title'], song_dir)

        print(f"✓ Deployed to branch '{config['branch']}'")

    except DeployError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n中断されました")
        sys.exit(1)


if __name__ == "__main__":
    main()
