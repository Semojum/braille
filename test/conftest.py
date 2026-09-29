"""pytest 전역 설정.

- 시험 보조(`support/braille_ascii.py`)를 임포트 경로에 올린다.
- kiwipiepy(선택 의존 `[kiwi]`)가 없는 환경에서는, kiwi 가 아는 낱말을 전제로 한 AI 쪽 시험을 건너뛴다.
  kiwi 가 없으면 역점역이 낱말 목록으로 가르는데, 목록은 이 낱말들을 모른다(docs/decoder.md).
- AI 저장소에서 이미 깨져 있는 시험은 xfail(strict)로 둔다. AI 가 고쳐 다시 동기화하면 XPASS 가
  실패로 드러나니 그때 목록에서 뺀다.
옮겨 온 시험 파일은 동기화 때 덮어쓰므로 표시는 여기서 한다.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent / "support"))

_NEEDS_KIWI = {
    # `손녀` 는 목록에 없다(영어 교재에만 나오는 생활 낱말).
    "test/unit_test/braille/test_english_paragraph_context.py::test_실재하는_한국어_낱말은_안_바꾼다",
}


# AI 저장소 develop 에서도 같은 자리가 깨진다(원인과 확인한 커밋).
_BROKEN_IN_AI = {
    "test/unit_test/braille/test_subscript_paren_t26.py::test_첨자_괄호는_소괄호":
        "AI 8dc7e7b 에서도 깨진다. #975 시험의 CO₂ 기대값(⠠⠉⠕)이 #977 대문자표 수정(⠠⠉⠠⠕) 전 꼴이다",
}


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    no_kiwi = importlib.util.find_spec("kiwipiepy") is None
    skip = pytest.mark.skip(reason="kiwipiepy 없음: 역점역이 낱말 목록으로 가르고, 목록은 이 시험의 낱말을 모른다")
    for item in items:
        if no_kiwi and item.nodeid in _NEEDS_KIWI:
            item.add_marker(skip)
        if item.nodeid in _BROKEN_IN_AI:
            item.add_marker(pytest.mark.xfail(reason=_BROKEN_IN_AI[item.nodeid], strict=True))
