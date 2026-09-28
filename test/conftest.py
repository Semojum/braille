"""pytest 전역 설정. 시험 보조(`support/braille_ascii.py`)를 임포트 경로에 올린다."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "support"))
