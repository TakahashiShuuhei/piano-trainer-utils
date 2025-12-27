#!/usr/bin/env python3
"""
MXLファイルを再生するスクリプト
"""

import sys
import os
import tempfile
import time
import argparse
from pathlib import Path

def install_requirements():
    """必要なパッケージをインストール"""
    import subprocess
    
    packages = ['music21', 'pygame']
    
    for package in packages:
        try:
            __import__(package)
            print(f"✓ {package} is already installed")
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

def play_mxl_file(file_path: str, speed: float = 1.0):
    """MXLファイルを再生

    Args:
        file_path: MXLファイルのパス
        speed: 再生速度の倍率（1.0 = 通常速度、2.0 = 2倍速、0.5 = 0.5倍速）
    """
    try:
        from music21 import converter, midi
        import pygame

        print(f"Loading {file_path}...")

        # MXLファイルを読み込み
        score = converter.parse(file_path)
        print(f"✓ Loaded: {score.metadata.title if score.metadata and score.metadata.title else 'Untitled'}")

        # 速度を変更
        if speed != 1.0:
            print(f"Adjusting speed to {speed}x...")
            score = score.scaleOffsets(1/speed).scaleDurations(1/speed)
            print(f"✓ Speed adjusted to {speed}x")
        
        # 一時MIDIファイルを作成
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as temp_file:
            temp_midi_path = temp_file.name
        
        try:
            # MIDIに変換
            print("Converting to MIDI...")
            midi_file = midi.translate.music21ObjectToMidiFile(score)
            midi_file.open(temp_midi_path, 'wb')
            midi_file.write()
            midi_file.close()
            print("✓ Converted to MIDI")
            
            # pygame初期化
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
            pygame.mixer.init()
            
            # MIDI再生
            print("🎵 Playing... (Press Ctrl+C to stop)")
            pygame.mixer.music.load(temp_midi_path)
            pygame.mixer.music.play()
            
            # 再生中は待機
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            print("✓ Playback finished")
            
        finally:
            # 一時ファイルを削除
            if os.path.exists(temp_midi_path):
                os.unlink(temp_midi_path)
            
    except ImportError as e:
        print(f"Error: Missing required package - {e}")
        print("Please install required packages first:")
        print("pip install music21 pygame")
        return False
    except Exception as e:
        print(f"Error playing file: {e}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description='MXLファイルを再生するスクリプト',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python play_mxl.py 001.mxl              # 通常速度で再生
  python play_mxl.py 001.mxl --speed 1.5  # 1.5倍速で再生
  python play_mxl.py 001.mxl --speed 0.8  # 0.8倍速で再生
        """
    )
    parser.add_argument('file', help='MXLファイルのパス')
    parser.add_argument('--speed', '-s', type=float, default=1.0,
                        help='再生速度の倍率 (デフォルト: 1.0)')

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found")
        sys.exit(1)

    # ファイル拡張子をチェック
    if not args.file.lower().endswith(('.mxl', '.xml', '.musicxml')):
        print("Warning: File doesn't appear to be a MusicXML file")

    # 速度の妥当性チェック
    if args.speed <= 0:
        print("Error: Speed must be greater than 0")
        sys.exit(1)

    if args.speed < 0.1 or args.speed > 10.0:
        print(f"Warning: Speed {args.speed}x is unusual (recommended range: 0.1 - 10.0)")

    try:
        # 必要なパッケージをチェック/インストール
        print("Checking required packages...")
        install_requirements()

        # ファイルを再生
        success = play_mxl_file(args.file, args.speed)

        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Playback stopped by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()