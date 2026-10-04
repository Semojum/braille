"""braille-assist `vectors.json`(0.3.0)을 옮겨 온 조판 함수에 그대로 맞춘다.

벡터는 옮기기 전 동작의 명세다. 이 시험이 깨지면 옮기면서 동작이 바뀐 것이다.
벡터 파일은 braille-assist develop 2c41d8d 의 것을 바이트 그대로 둔다(`test/data/assist_vectors.json`).
"""
import json
from pathlib import Path

import pytest

from semojum_braille import assist
from semojum_braille.brf import serialize_brf

_DATA = json.loads((Path(__file__).parent / "data" / "assist_vectors.json").read_text(encoding="utf-8"))
_CASES = [(fn, c) for fn, cases in _DATA["cases"].items() for c in cases]


@pytest.mark.parametrize("fn, case", _CASES, ids=[f"{fn}:{c['name']}" for fn, c in _CASES])
def test_벡터(fn, case):
    args = dict(case["args"])
    if "opts" in args:
        args["opts"] = assist.Options(**args["opts"])
    assert getattr(assist, fn)(**args) == case["expect"]


def test_벡터가_다섯_함수를_다_덮는다():
    assert set(_DATA["cases"]) == {"page_row", "page_change_line", "to_brf_ascii", "build_pages", "build_brf"}
    assert len(_CASES) == sum(len(v) for v in _DATA["cases"].values()) > 50


@pytest.mark.parametrize("fn, case", [(f, c) for f, c in _CASES if f == "build_brf"],
                         ids=[c["name"] for f, c in _CASES if f == "build_brf"])
def test_파일_꼴은_면_나누기가_같고_바이트만_현장_꼴(fn, case):
    job = case["args"]["job"]
    pages = assist.build_pages_from_job(job)
    o = assist.options_from_job(job)
    got = assist.build_brf_file(job)
    assert got == serialize_brf(pages, rows=o.rows, cols=o.cols)
    assert got.count(b"\x0c") == len(pages) and got.count(b"\r\n") == got.count(b"\n") == o.rows * len(pages)
