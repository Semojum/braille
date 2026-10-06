"""사이드카 프로토콜(README 8절)이 README 에 적은 대로 도는지 본다."""
import json
import subprocess
import sys

from semojum_braille import sidecar


def test_translate_gives_unfolded_cells_and_sorted_breaks():
    r = sidecar.translate("대한민국의 모든 국민은 법 앞에 평등하며, 누구든지 성별이나 종교 때문에 차별받지 아니한다.")
    assert r["cells"].startswith("⠀⠀") and "\n" not in r["cells"]        # 문단 들여쓰기, 32칸으로 안 접음
    assert r["breaks"] == sorted(r["breaks"])
    assert all(0 < b < len(r["cells"]) for b in r["breaks"])


def test_title_level2_starts_at_seventh_cell():
    r = sidecar.translate("1 국어의 탐구와 활용", "title", 2)
    assert r["cells"].startswith("⠀" * 6) and r["cells"][6] != "⠀"


def test_handle_answers_ping_and_reports_unknown_op():
    assert sidecar.handle({"op": "ping"}) == {"ok": True}
    assert "error" in sidecar.handle({"op": "fold"})


def test_brf_gives_field_form_file():
    job = {"pages": [{"orig_page_no": 7, "elements": [{"text": "⠁⠃"}]}]}
    brf = sidecar.handle({"op": "brf", "job": job})["brf"]
    assert brf.count("\r\n") == brf.count("\n") == 26 and brf.endswith("\x0c")
    lines = brf.split("\r\n")
    assert lines[0] == "ab"
    assert lines[25].startswith("#g") and lines[25].endswith("#a")   # 페이지행: 원본 쪽 7 · 점자 면 1


def test_stdio_keeps_id_and_survives_bad_line():
    p = subprocess.run([sys.executable, "-m", "semojum_braille.sidecar"],
                       input='{"id": 7, "op": "ping"}\nnot json\n{"id": 8, "op": "ping"}\n',
                       capture_output=True, text=True, timeout=120)
    a, b, c = (json.loads(x) for x in p.stdout.splitlines())
    assert a == {"ok": True, "id": 7}
    assert b["id"] is None and "error" in b
    assert c == {"ok": True, "id": 8}


def test_read_brf_gives_unicode_pages():
    brf = sidecar.handle({"op": "brf", "job": {"pages": [{"orig_page_no": 1, "elements": [{"text": "⠈⠍⠁"}]}]}})["brf"]
    pages = sidecar.handle({"op": "read_brf", "brf": brf})["pages"]
    assert any("⠈⠍⠁" in line for line in pages[0])
