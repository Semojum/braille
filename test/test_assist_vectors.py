"""조판 함수(`semojum_braille.assist`)를 저장소 루트 `vectors.json` 에 맞춘다.

`vectors.json` 은 파이썬 · ts(`ts/`) · java(`java/`) 세 구현이 같은 출력을 내는지 보는 하나뿐인 정답 파일이다.
ts · java 는 `.github/workflows/assist.yml` 이 같은 파일로 돌린다. 케이스 정의의 정본은 `tools/gen_vectors.py` 다.
(braille-assist develop 38e21e2 에서 옮겨 왔다. 그 전에는 `test/data/assist_vectors.json` 에 같은 바이트의 사본을 두었다.)
"""
import json
from pathlib import Path

import pytest

from semojum_braille import assist
from semojum_braille.brf import serialize_brf

_DATA = json.loads((Path(__file__).parents[1] / "vectors.json").read_text(encoding="utf-8"))
_CASES = [(fn, c) for fn, cases in _DATA["cases"].items() for c in cases]


@pytest.mark.parametrize("fn, case", _CASES, ids=[f"{fn}:{c['name']}" for fn, c in _CASES])
def test_벡터(fn, case):
    args = dict(case["args"])
    if "opts" in args:
        args["opts"] = assist.Options(**args["opts"])
    assert getattr(assist, fn)(**args) == case["expect"]


def test_벡터가_여섯_함수를_다_덮는다():
    assert set(_DATA["cases"]) == {"page_row", "page_change_line", "to_brf_ascii", "build_pages", "build_brf", "wrap"}
    assert len(_CASES) == sum(len(v) for v in _DATA["cases"].values()) > 50


def test_줄바꿈은_두_갈래다():
    """2026-10-10 대표 확정. 10-09 에 넣은 점자 칸(`cell`) 갈래는 뺐다. 넘기면 조용히 바꾸지 않고 멈춘다."""
    assert assist.WRAP_MODES == ("syllable", "word")
    with pytest.raises(ValueError):
        assist.wrap("⠁" * 40, 32, "cell")
    with pytest.raises(ValueError):
        assist.Options(wrap="cell")


@pytest.mark.parametrize("fn, case", [(f, c) for f, c in _CASES if f == "build_brf"],
                         ids=[c["name"] for f, c in _CASES if f == "build_brf"])
def test_파일_꼴은_면_나누기가_같고_바이트만_현장_꼴(fn, case):
    job = case["args"]["job"]
    pages = assist.build_pages_from_job(job)
    o = assist.options_from_job(job)
    got = assist.build_brf_file(job)
    assert got == serialize_brf(pages, rows=o.rows, cols=o.cols)
    assert got.count(b"\x0c") == len(pages) and got.count(b"\r\n") == got.count(b"\n") == o.rows * len(pages)
