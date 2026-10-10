"""사이드카 프로토콜(README 8절)이 README 에 적은 대로 도는지 본다."""
import json
import re
import subprocess
import sys
from pathlib import Path

from semojum_braille import sidecar
from semojum_braille.encoder.layout_braille import _flat_breaks


def test_translate_gives_unfolded_cells_and_sorted_breaks():
    r = sidecar.translate("대한민국의 모든 국민은 법 앞에 평등하며, 누구든지 성별이나 종교 때문에 차별받지 아니한다.")
    assert r["cells"].startswith("⠀⠀") and "\n" not in r["cells"]        # 문단 들여쓰기, 32칸으로 안 접음
    assert r["breaks"] == sorted(r["breaks"])
    assert all(0 < b < len(r["cells"]) for b in r["breaks"])


def test_끊을_자리는_들임과_실제_구분자_길이로_센다():
    """#30. 기대값은 AI `test_flat_breaks_1240.py` 와 같은 손셈이다(사이드카가 이 함수를 그대로 쓴다)."""
    assert _flat_breaks(["⠁⠀⠃", "⠉⠀⠙"], [2, 0], [[], []], 0, ["⠀"]) == (3, 5, 7)
    # 앞 줄이 ⠀ 로 끝나면 구분자가 빈 문자열이다. 뒤 줄 자리가 한 칸 밀리면 안 된다(종전 사이드카는 6).
    assert _flat_breaks(["⠁⠀⠃⠀", "⠉⠀⠙"], [0, 0], [[], []], 0, [""]) == (1, 3, 5)
    assert _flat_breaks(["⠀⠀⠁⠀⠃"], [0], [[1, 3]], 2) == (5,)


def test_빈_구분자_뒤에도_끊을_자리가_음절_경계에_있다(monkeypatch):
    """#30. 원문 줄 끝 빈칸으로 구분자가 빈 문자열이 되는 자리(꽉 찬 줄 잇기를 켰을 때). 종전에는 뒤 줄 자리가
    한 칸씩 밀려 '부'(⠘|⠍) · '상'(⠇|⠶) 을 갈랐다. 뒤 줄을 따로 점역한 자리와 같아야 한다."""
    monkeypatch.setenv("RESPONSE_FOLD_JOIN", "1")
    second = "보부상의 활동이 활발해졌다."
    r = sidecar.translate("조선 후기에는 상품 화폐 경제가 발달하면서 장시가 크게 늘어났다 \n" + second)
    alone = sidecar.translate(second)                       # 문단 들여쓰기 2칸
    k = r["cells"].index(alone["cells"][2:])
    assert [b - k for b in r["breaks"] if b > k] == [b - 2 for b in alone["breaks"] if b > 2]


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


def test_grade_follows_server_rules():
    from semojum_braille.encoder.translator import translate_tagged_text
    src = "대한민국의 모든 국민은 법 앞에 평등하다."
    br = translate_tagged_text(src)
    assert sidecar.handle({"op": "grade", "braille": br, "source": src}) == {"grade": "high", "round_trip": 1.0}
    # 표 · 수식 · 영문은 왕복 일치도와 상관없이 low(실측 정확도가 가장 낮은 갈래)
    for etype, text in (("table", src), ("formula", "x+1=3"), ("text", "The quick brown fox")):
        assert sidecar.handle({"op": "grade", "braille": translate_tagged_text(text),
                               "source": text, "type": etype})["grade"] == "low"
    # 원문과 다르게 되돌아오면 low
    assert sidecar.handle({"op": "grade", "braille": translate_tagged_text("대한민국의 모든 국민은"),
                           "source": "대한민국의 모든 국민이 아니다"})["grade"] == "low"


def test_braillify_고지는_묶은_판의_것이다():
    """#32 · Semojum/AI#1255. 앱이 사이드카를 실어 내면 braillify 휠도 같이 나가는데 휠에 고지 파일이 없다.
    판을 올리면 그 판의 LICENSE(2.2.0 부터는 NOTICE 도)를 `third_party/braillify-<판>/` 에 새로 받아 둔다."""
    pin = re.search(r'"braillify==([^"]+)"', (Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8"))
    d = Path(sidecar.__file__).with_name("third_party")
    assert [p.name for p in d.iterdir()] == [f"braillify-{pin.group(1)}"]
    assert (d / f"braillify-{pin.group(1)}" / "LICENSE").read_text(encoding="utf-8").lstrip().startswith("Apache License")


def _cells(text, **opts):
    return sidecar.translate(text, **opts)["cells"].lstrip("⠀")      # 문단 들여쓰기는 빼고 본다


def test_문서에_적은_translate_줄이_지금도_그대로_오간다():
    """#34. 옵션 인자를 보태도 옵션 없는 기존 호출의 응답은 같아야 한다. 기대값은 docs/sidecar.md 3절의 실제로 오간 줄이다."""
    doc = (Path(__file__).parents[1] / "docs" / "sidecar.md").read_text(encoding="utf-8")
    pairs = [(json.loads(q), json.loads(a)) for q, a in re.findall(r"^→ (\{.*\})\n← (\{.*\})$", doc, re.M)]
    pairs = [(q, a) for q, a in pairs if q["op"] == "translate"]
    assert len(pairs) >= 3
    for q, a in pairs:
        assert {**sidecar.handle(q), "id": q["id"]} == a
        if not {"korean_grade1", "english_grade1"} & q.keys():
            assert sidecar.handle({**q, "korean_grade1": False, "english_grade1": False})["cells"] == a["cells"]


def test_한글_정자는_약자를_쓰지_않는다():
    """#34. 「한국 점자 규정」(재추출): 제13항 573행 '가' 약자 $(585행, ⠫). 정자는 제1항 133행 첫소리 ㄱ @(148행, ⠈)
    + 제6항 364행 ㅏ <(375행, ⠣)."""
    assert _cells("가") == "⠫"
    assert _cells("가", korean_grade1=True) == "⠈⠣"
    assert _cells("가") == "⠫"                       # 켠 값이 다음 호출로 새지 않는다


def test_영어_1급은_약자_없이_적고_로마자표를_생략하지_않는다():
    """#34. 「한국 점자 규정」(재추출) 제28항 1329행 t(1429행, ⠞) · h(1369행, ⠓) · e(1354행, ⠑), 제29항 1496~1497행
    로마자표 0(⠴) · 종료표 4(⠲). 문단 전체가 로마자면 표를 생략할 수 있으나(제29항 [다만] 1507행) 1급(초급자 자료)은
    생략하지 않는다(「점자 도서 제작 지침」 제2장 제4절 1.1)(1), 재추출 1494~1499행)."""
    assert _cells("the", english_grade1=True) == "⠴⠞⠓⠑⠲"
    assert "⠞⠓⠑" not in _cells("the")               # 기본(2급)은 약자로 적는다


def test_빠진_글자를_AI_쪽_플래그와_같은_갈래로_알린다():
    """#34. 점자 기호가 없어 조용히 빠진 글자. 기호가 생기면 이 시험의 글자를 다른 것으로 바꾼다."""
    r = sidecar.translate("가▶나")
    assert r["cells"].lstrip("⠀") == "⠫⠉"
    assert r["dropped"] == [{"text": "▶", "count": 1, "flag": "R17"}]
    assert sidecar.translate("★★★★☆")["dropped"] == [{"text": "★", "count": 4, "flag": "R17"}]
    assert sidecar.translate("")["dropped"] == [{"text": "", "count": 1, "flag": "R15"}]
    assert sidecar.translate("하ᄀᆞᄋᆉ다")["dropped"] == [{"text": "ᄋᆉ", "count": 1, "flag": "R18"}]
    assert sidecar.translate("가나")["dropped"] == []


def test_옵션은_참거짓만_받는다():
    """문자열 "true" 를 조용히 켜거나 끄면 정자 · 약자가 바뀐 채로 나간다. 오류로 돌려준다."""
    p = subprocess.run([sys.executable, "-m", "semojum_braille.sidecar"],
                       input='{"id": 1, "op": "translate", "text": "\\uac00", "korean_grade1": true}\n'
                             '{"id": 2, "op": "translate", "text": "\\uac00", "korean_grade1": "true"}\n'
                             '{"id": 3, "op": "translate", "text": "\\uac00", "english_grade1": null}\n',
                       capture_output=True, text=True, timeout=120)
    a, b, c = (json.loads(x) for x in p.stdout.splitlines())
    assert a["cells"].lstrip("⠀") == "⠈⠣" and a["id"] == 1
    assert "korean_grade1" in b["error"] and b["id"] == 2
    assert c["cells"].lstrip("⠀") == "⠫"
