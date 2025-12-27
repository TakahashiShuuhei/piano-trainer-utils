#!/usr/bin/env python3
"""
MusicXML to JSON Converter for Piano Practice App

MusicXMLファイルをPiano Practice App用のJSON形式に変換します。
"""

import argparse
import json
import sys
from pathlib import Path
from music21 import converter, tempo


def musicxml_to_json(musicxml_path):
    """
    MusicXMLファイルをJSON形式に変換する

    Args:
        musicxml_path: MusicXMLファイルのパス

    Returns:
        dict: JSON仕様に従った辞書
    """
    # MusicXMLファイルを読み込む
    score = converter.parse(musicxml_path)

    # メタデータを取得
    title = "Untitled"
    if score.metadata and score.metadata.title:
        title = score.metadata.title

    # テンポ（BPM）を取得
    bpm = 120  # デフォルト値
    tempo_marks = score.flatten().getElementsByClass(tempo.MetronomeMark)
    if tempo_marks:
        bpm = int(tempo_marks[0].number)

    # パート別に音符を抽出
    notes_data = []

    # パートが複数ある場合はパート番号から手を判定
    parts = score.parts
    num_parts = len(parts)

    for part_idx, part in enumerate(parts):
        # パート番号から手を判定
        # Part 0 = 右手（高音部）, Part 1 = 左手（低音部）
        hand = "right" if part_idx == 0 else "left"

        for element in part.flatten().notes:
            if element.isNote:  # 単音の場合
                note_dict = {
                    "pitch": element.pitch.midi,  # MIDIノート番号（0-127）
                    "timing": {
                        "beat": float(element.offset),  # 四分音符単位の開始位置
                        "duration": float(element.duration.quarterLength)  # 四分音符単位の長さ
                    }
                }

                # velocityがあれば追加（デフォルトは80なので、異なる場合のみ追加）
                if hasattr(element, 'volume') and element.volume.velocity is not None:
                    velocity = int(element.volume.velocity)
                    if velocity != 80:
                        note_dict["velocity"] = velocity

                # handを追加（デフォルトは"right"なので、"left"の場合のみ追加）
                if hand == "left":
                    note_dict["hand"] = hand

                notes_data.append(note_dict)

            elif element.isChord:  # 和音の場合は各音符を展開
                for pitch in element.pitches:
                    note_dict = {
                        "pitch": pitch.midi,
                        "timing": {
                            "beat": float(element.offset),
                            "duration": float(element.duration.quarterLength)
                        }
                    }

                    # 和音の場合もvelocityを確認
                    if hasattr(element, 'volume') and element.volume.velocity is not None:
                        velocity = int(element.volume.velocity)
                        if velocity != 80:
                            note_dict["velocity"] = velocity

                    # handを追加（デフォルトは"right"なので、"left"の場合のみ追加）
                    if hand == "left":
                        note_dict["hand"] = hand

                    notes_data.append(note_dict)

    # beatでソート（念のため）
    notes_data.sort(key=lambda x: x["timing"]["beat"])

    # JSON形式で出力
    result = {
        "title": title,
        "bpm": bpm,
        "notes": notes_data
    }

    return result


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='MusicXMLファイルをPiano Practice App用のJSON形式に変換します。',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s input.musicxml -o output.json
  %(prog)s song.xml
        """
    )

    parser.add_argument(
        'input',
        type=str,
        help='入力MusicXMLファイルのパス'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='出力JSONファイルのパス（省略時は標準出力）'
    )

    args = parser.parse_args()

    # 入力ファイルの存在確認
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"エラー: ファイルが見つかりません: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        # 変換実行
        result = musicxml_to_json(str(input_path))

        # 出力
        json_str = json.dumps(result, indent=2, ensure_ascii=False)

        if args.output:
            # ファイルに出力
            output_path = Path(args.output)
            output_path.write_text(json_str, encoding='utf-8')
            print(f"変換完了: {args.output}")
        else:
            # 標準出力
            print(json_str)

    except Exception as e:
        print(f"エラー: 変換中に問題が発生しました: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
