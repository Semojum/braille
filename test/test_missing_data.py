"""역맵 json 이 없을 때 **조용히 넘어가지 않는지** 확인한다.

왜 이 시험이 있나 (2026-09-29)
  역맵이 빠지면 AI 원본은 **빈 맵으로 돌아** 한글이 조용히 안 풀렸다. 서버에서는 파일이 늘
  있어 드러나지 않았지만, 앱에 넣으면 패키징이 어긋나도 역점역이 그냥 돌고 **결과만 조용히
  틀린다.** 그래서 예외로 바꿨다.
  ⚠ 그 수정을 두 번 틀렸다. 처음엔 `if path.exists():` **안에** raise 를 넣어 파일이 없을 때
  바깥 `return {}` 로 갔고, 그다음엔 `try:` 안에 넣어 `except Exception` 이 삼켰다.
  **파일이 있을 때만 확인하면 둘 다 못 잡는다.** 그래서 없는 경로로 직접 돌린다.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from semojum_braille.decoder import back


def test_음절_역맵이_없으면_예외(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(back, "_MAP_PATH", tmp_path / "없는파일.json")
    with pytest.raises(OSError):
        back._load_syllable_rev()


def test_특수_역맵이_없으면_예외(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # `_load_special_rev` 는 모듈 `__file__` 옆에서 찾는다. 빈 폴더로 돌린다.
    monkeypatch.setattr(back, "__file__", str(tmp_path / "back.py"))
    with pytest.raises(OSError):
        back._load_special_rev()


def test_있을_때는_읽힌다() -> None:
    """반대쪽도 본다 — 예외로 바꾸면서 정상 경로를 깨지 않았는지."""
    assert len(back._load_syllable_rev()) > 10_000
    assert len(back._load_special_rev()) > 30
