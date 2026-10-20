"""사이드카 프로토콜(README 8절)이 README 에 적은 대로 도는지 본다."""
import json
import os
import re
import select
import subprocess
import sys
from pathlib import Path

import pytest

from semojum_braille import __version__, assist, sidecar
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


PING = {"ok": True, "version": __version__, "protocol": sidecar.PROTOCOL}


def test_handle_answers_ping_and_reports_unknown_op():
    assert sidecar.handle({"op": "ping"}) == PING
    with pytest.raises(sidecar.SidecarError) as e:
        sidecar.handle({"op": "fold"})
    assert e.value.code == "BAD_FIELD"


def test_build_brf_gives_field_form_file():
    """V4 엔진 가이드 build_brf — job.sources[].blocks[].braille."""
    job = {"sources": [{"orig_page": 7, "blocks": [{"order": 0, "braille": "⠁⠃"}]}]}
    brf = sidecar.handle({"op": "build_brf", "job": job})["brf"]
    assert brf.count("\r\n") == brf.count("\n") == 26 and brf.endswith("\x0c")
    assert sidecar.handle({"op": "build_brf", "job": job})["replaced"] == {}
    bad = sidecar.handle({"op": "build_brf", "job": {"sources": [{"orig_page": 1, "blocks": [{"order": 0, "braille": "⠁\u2009⠃"}]}]}})
    assert bad["replaced"] == {"U+2009": 1} and bad["brf"].startswith("a b\r\n")
    lines = brf.split("\r\n")
    assert lines[0] == "ab"
    assert lines[25].startswith("#g") and lines[25].endswith("#a")   # 페이지행: 원본 쪽 7 · 점자 면 1


def test_stdio_keeps_id_and_survives_bad_line():
    p = subprocess.run([sys.executable, "-m", "semojum_braille.sidecar"],
                       input='{"id": 7, "op": "ping"}\nnot json\n{"id": 8, "op": "ping"}\n',
                       capture_output=True, text=True, timeout=120)
    a, b, c = (json.loads(x) for x in p.stdout.splitlines())
    assert a == {**PING, "id": 7}
    assert b["id"] is None and "error" in b and b["code"] == "BAD_JSON"      # V4 가이드 오류 표
    assert c == {**PING, "id": 8}


def test_read_brf_gives_unicode_pages():
    brf = sidecar.handle({"op": "build_brf", "job": {"sources": [{"orig_page": 1, "blocks": [{"braille": "⠈⠍⠁"}]}]}})["brf"]
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
        if not {"korean_grade", "english_grade"} & q.keys():
            assert sidecar.handle({**q, "korean_grade": 2, "english_grade": 2})["cells"] == a["cells"]


def test_한글_정자는_약자를_쓰지_않는다():
    """#34. 「한국 점자 규정」(재추출): 제13항 573행 '가' 약자 $(585행, ⠫). 정자는 제1항 133행 첫소리 ㄱ @(148행, ⠈)
    + 제6항 364행 ㅏ <(375행, ⠣)."""
    assert _cells("가") == "⠫"
    assert _cells("가", korean_grade=1) == "⠈⠣"
    assert _cells("가", korean_grade=2) == _cells("가", korean_grade=0) == "⠫"      # 0 은 안 보냄 = 2(V4 가이드)
    assert _cells("가") == "⠫"                       # 켠 값이 다음 호출로 새지 않는다


def test_영어_1급은_약자_없이_적고_로마자표를_생략하지_않는다():
    """#34. 「한국 점자 규정」(재추출) 제28항 1329행 t(1429행, ⠞) · h(1369행, ⠓) · e(1354행, ⠑), 제29항 1496~1497행
    로마자표 0(⠴) · 종료표 4(⠲). 문단 전체가 로마자면 표를 생략할 수 있으나(제29항 [다만] 1507행) 1급(초급자 자료)은
    생략하지 않는다(「점자 도서 제작 지침」 제2장 제4절 1.1)(1), 재추출 1494~1499행)."""
    assert _cells("the", english_grade=1) == "⠴⠞⠓⠑⠲"
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


def test_옵션은_정해진_꼴만_받는다():
    """문자열 "1" · "true" 를 조용히 켜거나 끄면 정자 · 약자가 바뀐 채로 나간다. `BAD_FIELD` 로 돌려준다(V4 가이드 오류 표)."""
    p = subprocess.run([sys.executable, "-m", "semojum_braille.sidecar"],
                       input='{"id": 1, "op": "translate", "text": "\\uac00", "korean_grade": 1}\n'
                             '{"id": 2, "op": "translate", "text": "\\uac00", "korean_grade": "1"}\n'
                             '{"id": 3, "op": "translate", "text": "\\uac00", "english_grade": null}\n'
                             '{"id": 4, "op": "translate", "text": "\\uac00", "split_choices": "true"}\n',
                       capture_output=True, text=True, timeout=120)
    a, b, c, d = (json.loads(x) for x in p.stdout.splitlines())
    assert a["cells"].lstrip("⠀") == "⠈⠣" and a["id"] == 1
    assert "korean_grade" in b["error"] and b["code"] == "BAD_FIELD" and b["id"] == 2
    assert c["cells"].lstrip("⠀") == "⠫"
    assert d["code"] == "BAD_FIELD" and d["id"] == 4


def test_옛_급수_이름은_조용히_무시하지_않고_돌려준다():
    """#72. 앱이 보내던 `korean_grade1` · `english_grade1`(bool)은 엔진이 안 읽어 오류 없이 무시됐다(정자를 골라도 약자)."""
    for old in ("korean_grade1", "english_grade1"):
        r = sidecar._answer(json.dumps({"id": 7, "op": "translate", "text": "가", old: True}).encode())
        assert r["code"] == "BAD_FIELD" and old in r["error"] and r["id"] == 7
    assert sidecar.handle({"op": "translate", "text": "가", "korean_grade": 1})["cells"].lstrip("⠀") == "⠈⠣"


def test_정자로_점역하고_역점역_등급까지_한_바퀴_돈다():
    """#36 · AI#1276. 정자 점자를 2급 역맵으로 읽으면 왕복이 깨져 정자 문서의 등급이 거의 다 low 가 됐다.
    옵션이 translate 에만 가고 decode · grade 에 안 가면 앱에서 같은 일이 난다. 문장은 「한국 점자 규정」 제18항 예(909행)."""
    src = "비가 왔다. 그래서 소풍 계획은 취소되었다."
    p = subprocess.run([sys.executable, "-m", "semojum_braille.sidecar"],
                       input=json.dumps({"id": 1, "op": "translate", "text": src, "korean_grade": 1}) + "\n",
                       capture_output=True, text=True, timeout=120)
    cells = json.loads(p.stdout)["cells"]
    assert "⠁⠎" not in cells                                      # 약어 '그래서'(901행)를 안 썼다
    reqs = [{"id": 2, "op": "decode", "braille": cells, "korean_grade": 1},
            {"id": 3, "op": "grade", "braille": cells, "source": src, "korean_grade": 1},
            {"id": 4, "op": "grade", "braille": cells, "source": src}]       # 옵션 없이: 2급으로 읽는다
    p = subprocess.run([sys.executable, "-m", "semojum_braille.sidecar"],
                       input="".join(json.dumps(r) + "\n" for r in reqs), capture_output=True, text=True, timeout=120)
    dec, g1, g2 = (json.loads(x) for x in p.stdout.splitlines())
    assert dec["text"].strip() == src
    assert g1["grade"] == "high" and g1["round_trip"] == 1.0
    assert g2["round_trip"] < 1.0                                  # 옵션이 안 가면 사슬이 끊긴다


def test_decode_grade_는_옵션이_없으면_그대로다():
    src = "대한민국의 모든 국민은 법 앞에 평등하다."
    from semojum_braille.encoder.translator import translate_tagged_text
    br = translate_tagged_text(src)
    assert sidecar.handle({"op": "decode", "braille": br}) == sidecar.handle({"op": "decode", "braille": br, "korean_grade": 2})
    assert sidecar.handle({"op": "grade", "braille": br, "source": src}) == {"grade": "high", "round_trip": 1.0}


def test_수식_쪽_문맥을_받으면_평문_속_좌표를_수식_괄호로_적는다():
    """#38. AI 서버는 수식 쪽(쪽 PDF 한컴 수식 글꼴 비율)에서 평문 속 `(1, 0)` 을 수식으로 적는다. 앱이 그 쪽 글을 다시
    점역할 때 같은 꼴이 나와야 한다. 「한국 점자 규정」(재추출) 수학 제6항 3089~3091행 소괄호 `8`·`0`(⠦ · ⠴),
    한글 점자 문장 부호 표 2156~2157행 소괄호 `8'`·`,0`(⠦⠄ · ⠠⠴)."""
    text = "그래프는 점 (1, 0)을 지나고"
    plain = sidecar.translate(text)["cells"]
    math = sidecar.translate(text, math_page=True)["cells"]
    assert "⠦⠄⠼⠁⠐⠀⠼⠚⠠⠴" in plain                               # 한글 소괄호
    assert "⠦⠼⠁⠐⠀⠼⠚⠴" in math and "⠦⠄" not in math            # 수식 소괄호
    assert sidecar.translate(text)["cells"] == plain                 # 켠 값이 새지 않는다
    assert sidecar.handle({"op": "translate", "text": text, "math_page": True})["cells"] == math


def test_표준입력은_줄마다_UTF8_로_풀고_못_푸는_줄만_오류로_답한다():
    """#44. 종전에는 표준입력을 플랫폼 인코딩으로 풀다 못 푸는 바이트에서 프로세스가 죽었다. 한국어 Windows 의
    표준입력 인코딩(cp949)을 `PYTHONIOENCODING` 으로 흉내 내고 실제 프로세스에 바이트를 보낸다.
    '가' = ⠫ 은 「한국 점자 규정」(재추출) 제13항 573행 약자(585행)."""
    lines = [b"\xef\xbb\xbf" + b'{"id": 1, "op": "ping"}',                        # BOM 으로 시작하는 첫 줄(C# Encoding.UTF8)
             '{"id": 2, "op": "translate", "text": "가"}'.encode("utf-8"),           # 이스케이프 안 한 UTF-8 한글
             '{"id": 3, "op": "translate", "text": "가"}'.encode("cp949"),           # UTF-8 이 아닌 줄: 오류, id 는 돌려준다
             b"\xff",                                                              # 깨진 바이트: 오류, id 는 모른다
             b"   ",                                                               # 빈 줄: 응답 없음
             b'{"id": 6, "op": "ping"}']
    p = subprocess.run([sys.executable, "-m", "semojum_braille.sidecar"], input=b"\r\n".join(lines) + b"\r\n",
                       capture_output=True, timeout=120, env={**os.environ, "PYTHONIOENCODING": "cp949"})
    assert p.returncode == 0, p.stderr.decode("utf-8", "replace")
    r1, r2, r3, r4, r6 = (json.loads(x) for x in p.stdout.splitlines())
    assert r1 == {**PING, "id": 1}
    assert r2["cells"].lstrip("⠀") == "⠫" and r2["id"] == 2
    assert r3["error"].startswith("UnicodeDecodeError") and r3["id"] == 3 and "cells" not in r3
    assert r4["error"].startswith("UnicodeDecodeError") and r4["id"] is None
    assert r6 == {**PING, "id": 6}


@pytest.mark.skipif(sys.platform == "win32", reason="select 가 파이프를 못 기다린다")
def test_표준입력을_닫지_않아도_한_줄씩_답한다():
    """#44. 바이트로 읽어도 줄이 오는 대로 답해야 한다. 표준입력이 닫힐 때까지 모아 두면 앱이 첫 응답을 못 받는다."""
    p = subprocess.Popen([sys.executable, "-m", "semojum_braille.sidecar"],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        for i in (1, 2):
            p.stdin.write(json.dumps({"id": i, "op": "ping"}).encode("ascii") + b"\n")
            p.stdin.flush()
            assert select.select([p.stdout], [], [], 60)[0], "응답이 안 온다"
            assert json.loads(p.stdout.readline()) == {**PING, "id": i}
    finally:
        p.stdin.close()
        p.wait(timeout=60)
    assert p.returncode == 0


def test_판_번호는_한_곳에서_읽는다():
    """#44. pyproject 는 판을 따로 적지 않고 `semojum_braille.__version__` 을 읽는다. ping 이 내는 값이 그 값이다."""
    toml = (Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    assert re.search(r'^dynamic = \["version"\]', toml, re.M) and not re.search(r'^version = "', toml, re.M)
    assert 'version = {attr = "semojum_braille.__version__"}' in toml
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__)


@pytest.mark.parametrize("text", ["😀", "١٢٣", "ང"])
def test_점자로_옮길_글자가_없는_요소는_점역_못_함으로_온다(text):
    """#52. 종전 사이드카는 `_translate_one` 을 바로 불러 이런 요소가 빈 cells 로 조용히 사라졌다(dropped 도 비었다).
    AI 서버 체인(`safe_translate`)처럼 점역자 주 '점역 못 함'으로 바꾸고 blocked 를 참으로 낸다."""
    from semojum_braille.encoder.isolation import blocked_braille
    r = sidecar.translate(text)
    assert r["blocked"] is True
    assert r["cells"].lstrip("⠀") == blocked_braille()


def test_한자만_있는_요소와_보통_글은_blocked_가_아니다():
    """한자만 있는 요소는 빈 출력이 정답이다(도서 관행, isolation._CJK_RE). 보통 글은 종전과 같은 점자다."""
    han = sidecar.translate("大韓民國")
    assert han["blocked"] is False and han["cells"] == ""
    ok = sidecar.translate("대한민국")
    assert ok["blocked"] is False and ok["cells"] == "⠀⠀⠊⠗⠚⠒⠑⠟⠈⠍⠁"


def test_엔진_예외도_그_요소만_점역_못_함으로_온다(monkeypatch):
    """종전에는 엔진 예외가 요청째 error 였다. AI 서버처럼 그 요소만 '점역 못 함'으로 바꾼다."""
    def boom(opt):
        raise RuntimeError("시험용 예외")
    monkeypatch.setattr(sidecar._TB, "_translate_one", boom)
    r = sidecar.handle({"op": "translate", "text": "가"})
    assert "error" not in r and r["blocked"] is True


def test_force_roman_은_꼬리말처럼_로마자표를_붙인다():
    """#54. 「한국 점자 규정」 제29항(규정 1496행): 국어 문장 안의 로마자 앞에 로마자표 ⠴. [다만] 문단 전체가 로마자면
    생략할 수 있어 본문 길은 `Ⅳ` 하나짜리 요소에 ⠴ 를 안 붙인다. 꼬리말은 한국어 책의 한 조각이라 붙인다
    (translator.translate_plain 주석: gold 페이지행 4,776 : 542). BE 가 꼬리말에 쓰는 translate_plain 과 같아야
    앱이 사이드카로 갈아타도 꼬리말이 안 바뀐다."""
    from semojum_braille.encoder.translator import translate_plain
    for t in ("Ⅳ", "Ⅱ. 물질대사", "Ⅳ 생명의 연속성", "머리말", "01 지수와 로그"):
        r = sidecar.translate(t, "header_footer", force_roman=True)
        assert r["cells"] == translate_plain(t) and r["blocked"] is False, t
    assert sidecar.translate("Ⅳ", "header_footer", force_roman=True)["cells"].startswith("⠴")
    assert not sidecar.translate("Ⅳ", "text")["cells"].startswith("⠴")      # 본문 길은 종전 그대로
    r = sidecar.handle({"op": "translate", "text": "Ⅳ", "type": "header_footer", "force_roman": True})
    assert r["cells"] == translate_plain("Ⅳ")


def test_꼬리말은_로마자_강제가_저절로_켜진다():
    """#60. 쓰는 자리가 꼬리말뿐이라 `type="header_footer"` 면 따로 안 켜도 켜진다. 2027 dev · val header_footer
    1,124개 중 이걸로 바뀌는 것은 34개이고, 전부 한글 없는 영어 꼬리말에 ⠴ 가 붙는 것이다('Level' · 'Mini Test')."""
    from semojum_braille.encoder.translator import translate_plain
    for t in ("Ⅳ", "Level", "Mini Test", "Ⅱ. 물질대사"):
        assert sidecar.translate(t, "header_footer")["cells"] == translate_plain(t), t
        assert sidecar.handle({"op": "translate", "text": t, "type": "header_footer"})["cells"] == translate_plain(t), t
    assert sidecar.translate("Level", "header_footer")["cells"].startswith("⠴")
    assert not sidecar.translate("Level", "text")["cells"].startswith("⠴")


def test_force_roman_도_점역_못_한_요소는_드러낸다():
    """force_roman 길도 safe_translate 를 지난다(#52 와 같은 판정)."""
    r = sidecar.translate("😀", "header_footer", force_roman=True)
    assert r["blocked"] is True


def _표(*rows):
    from semojum_braille.encoder.tag_names import build_table_tags
    return build_table_tags([list(r) for r in rows])


@pytest.mark.parametrize("mode", ["unfold", "table_grid", "transposed", "linear", "numbered"])
def test_table_은_고른_안과_다섯_안을_같이_낸다(mode):
    """#56. AI 서버 표 체인(`TableBraille` → `flatten_elements`)과 같은 길이다. 서버 응답과의 바이트 대조(표 900개)는 PR 본문."""
    r = sidecar.table(_표(["구분", "가", "나"], ["값", "1", "2"]), mode)
    assert r["render_mode"] == mode and not r["blocked"] and r["dropped"] == []       # 태그는 빠진 글자로 안 센다
    assert [d["render_mode"] for d in r["drafts"]] == ["unfold", "table_grid", "transposed", "linear", "numbered"]
    chosen = next(d for d in r["drafts"] if d["render_mode"] == mode)
    assert (r["cells"], r["breaks"]) == (chosen["cells"], chosen["breaks"]) and "⠼⠁" in r["cells"]
    assert sidecar.handle({"op": "table", "table_source": _표(["구분", "가"], ["값", "1"]),
                           "render_mode": mode})["render_mode"] == mode


def test_table_상자_안_표는_테두리만_바뀐다():
    src = _표(["구분", "가", "나"], ["값", "1", "2"])
    a = sidecar.table(src, "table_grid")["cells"].split("\n")
    b = sidecar.table(src, "table_grid", box_level=1)["cells"].split("\n")
    assert a[0] != b[0] and a[-1] != b[-1]          # 위아래 테두리
    assert a[1:-1] == b[1:-1]                        # 칸 줄은 그대로


def test_table_에_태그가_없으면_점역자_주_한_안이다():
    r = sidecar.table("칸이 없는 글", tn_text="<!주>표. 칸 없음<!/주>")
    assert r["drafts"] == [] and r["render_mode"] == "" and r["cells"].lstrip("⠀").startswith("⠠⠄")


@pytest.mark.parametrize("mode", ["unfold", "table_grid", "numbered"])
def test_translate_에_표를_넣으면_table_과_같다(mode):
    """#60. 앱은 창구 하나(`translate`)로 표도 점역한다. `type="table"` 이거나 글이 표 태그면 `table` op 와 같은 길이다.
    ★ type 을 `text` 로 넘긴 표도 같아야 한다. 갈림이 엔진만 표로 바꾸고 `flatten_elements` 의 요소 type 을 `text` 로
    두면 표 줄마다 문단 들여쓰기 2칸이 더 붙는다(2027 dev · val 표 900개가 900/900 다름)."""
    src = _표(["구분", "가", "나"], ["값", "1", "2"])
    want = sidecar.table(src, mode, box_level=1)
    assert sidecar.translate(src, "table", render_mode=mode, box_level=1) == want
    assert sidecar.translate(src, "text", render_mode=mode, box_level=1) == want
    assert sidecar.handle({"op": "translate", "text": src, "type": "table", "render_mode": mode, "box_level": 1}) == want


def test_표가_아니면_translate_응답에_표_칸이_없다():
    r = sidecar.translate("가나다")
    assert set(r) == {"cells", "breaks", "dropped", "blocked", "unknown_tags"}


def test_묵자_1000자를_넘으면_TOO_LONG_이고_태그는_세지_않는다():
    """V4 가이드 translate `text` · 오류 표. 태그째 세면 2027 dev · val 표 2개가 걸리는데 표는 문장으로 못 쪼갠다."""
    with pytest.raises(sidecar.SidecarError) as e:
        sidecar.translate("가" * 1001)
    assert e.value.code == "TOO_LONG"
    sidecar._check("가" * 1000)                                 # 상한 판정만(1,000자 점역은 수 초 걸린다)
    sidecar._check("<!강조>가<!/강조>" * 500)                  # 묵자 500자 · 태그째 7,000자
    r = sidecar._answer(json.dumps({"id": 9, "op": "translate", "text": "가" * 1001}).encode())
    assert r["code"] == "TOO_LONG" and r["id"] == 9 and "cells" not in r


def test_수식이_10중첩_또는_1000자를_넘으면_BAD_LATEX():
    deep = "<!수식>" + "{" * 11 + "x" + "}" * 11 + "<!/수식>"
    with pytest.raises(sidecar.SidecarError) as e:
        sidecar.translate(deep)
    assert e.value.code == "BAD_LATEX"
    with pytest.raises(sidecar.SidecarError) as e:
        sidecar.translate("<!수식>" + "x+" * 501 + "<!/수식>")
    assert e.value.code == "BAD_LATEX"
    assert sidecar.translate("<!수식>" + "{" * 10 + "x" + "}" * 10 + "<!/수식>")["cells"]
    assert sidecar.translate("<!수식>\\{ x \\}" + "<!/수식>")["cells"]   # 글자로 쓴 중괄호는 세지 않는다


def test_모르는_태그는_unknown_tags_로_알린다():
    """엔진은 모르는 태그를 지우고 점역한다. 앱이 알 수 있게 이름을 낸다(V4 가이드 translate 응답)."""
    r = sidecar.translate("가<!없는태그>나<!/없는태그><!강조>다<!/강조><!주>라<!/주><!2칸>마<!없는태그>바<!/없는태그>")
    assert r["unknown_tags"] == ["없는태그"]
    # 목록표 글자 태그 넷은 아는 태그다(AI #1382). 빈칸 둘은 번역기 입구에서 엔진 이름으로 풀리는 별칭이다.
    r = sidecar.translate("<!색강조>가<!/색강조> <!취소선>나<!/취소선> <!밑줄빈칸> <!네모빈칸>")
    assert r["unknown_tags"] == [] and "⠸⠤" in r["cells"] and "⠸⠦⠀⠴⠇" in r["cells"]
    assert sidecar.translate(_표(["가", "나"]))["unknown_tags"] == []
    assert sidecar.translate("<!상자>제목<!/상자>\n가\n<!상자끝><!/상자끝>")["unknown_tags"] == []


def test_split_choices_는_선택지를_한_줄에_하나씩_적는다():
    """proto 정본 `split_choices = 12`(안 보내면 짧은 선택지를 합친다 = 종전 동작). 엔진 문맥 `CHOICES_ONE_PER_LINE`."""
    src = "① 가\n② 나\n③ 다\n④ 라\n⑤ 마"
    merged, split = sidecar.translate(src)["cells"], sidecar.translate(src, split_choices=True)["cells"]
    assert merged.count("\n") < 4 and split.count("\n") == 4
    assert sidecar.translate(src)["cells"] == merged                 # 켠 값이 다음 호출로 새지 않는다
    assert sidecar.handle({"op": "translate", "text": src, "split_choices": True})["cells"] == split


def test_read_brf_는_BRF_가_아니면_BAD_BRF():
    with pytest.raises(sidecar.SidecarError) as e:
        sidecar.handle({"op": "read_brf", "brf": "가나다"})
    assert e.value.code == "BAD_BRF"


def test_table_도_엔진_예외는_그_표만_점역_못_함으로_온다(monkeypatch):
    from semojum_braille.encoder.table_braille import TableBraille

    def boom(self, opt):
        raise RuntimeError("엔진 예외")
    monkeypatch.setattr(TableBraille, "_translate_one", boom)
    r = sidecar.table(_표(["가", "나"]), "table_grid")
    assert r["blocked"] and r["drafts"] == []


def test_symbols_는_기호표_묶음과_점형을_낸다():
    """V4 가이드 `symbols`. `cells` 는 문맥 없는 기호표 값이다. 참고표 ※ 는 「한국 점자 규정」 제60항(재추출 2533행)
    `"9` = ⠐⠔(앞뒤 한 칸은 넣은 뒤 translate 가 문맥으로 정한다)."""
    allsym = sidecar.handle({"op": "symbols"})["symbols"]
    assert {"char": "※", "cells": "⠐⠔", "group": "기타부호"} in allsym
    assert all(set(x) == {"char", "cells", "group"} and x["cells"] for x in allsym)
    arrows = sidecar.handle({"op": "symbols", "group": "화살표"})["symbols"]
    assert arrows and {x["group"] for x in arrows} == {"화살표"} and len(arrows) < len(allsym)
    assert sidecar.handle({"op": "symbols", "group": "없는 묶음"})["symbols"] == []


def test_build_brf_옛_op_와_잘못된_옵션은_BAD_FIELD():
    with pytest.raises(sidecar.SidecarError) as e:
        sidecar.handle({"op": "brf", "job": {}})
    assert e.value.code == "BAD_FIELD"
    r = sidecar._answer(json.dumps({"id": 1, "op": "build_brf", "job": {"sources": [], "opts": {"page_row_pages": "홀수"}}}).encode())
    assert r["code"] == "BAD_FIELD" and "page_row_pages" in r["error"]


def test_build_brf_는_page_row_pages_네_값을_받는다():
    """FE 백엔드 수정 목록 2026-10-20 B-06. BE 업로드 옵션 `pageNumberLine` 은 odd|every|none 셋이고
    앱은 짝수 면을 `none` 으로 바꿔 보내고 있었다. `Options.page_row_on` 은 처음부터 네 값을 받는데
    조판 job 입구(`_PAGE_ROW_PAGES`)만 둘로 좁혀 `none`·`even` 이 `BAD_FIELD` 였다."""
    def page_rows(on):
        """면마다 페이지행이 있는지. 페이지행은 면의 마지막 줄이고 32칸을 채워 번호로 시작한다."""
        src = [{"orig_page": i + 1, "blocks": [{"order": 0, "braille": "⠁"}]} for i in range(6)]
        pages = assist.build_pages_from_job({"sources": src, "opts": {"rows": 3, "page_row_pages": on}})
        return [bool(p and len(p[-1]) == 32 and p[-1].startswith("⠼")) for p in pages]

    assert all(page_rows("every"))
    assert not any(page_rows("none"))
    assert page_rows("odd")[:4] == [True, False, True, False]
    assert page_rows("even")[:4] == [False, True, False, True]


def test_참거짓_옵션_셋에_문자열을_주면_켜지지_않고_BAD_FIELD():
    """#73. `bool("false")` 가 참이라 끄려고 보낸 문자열이 켰다(show_orig_page · show_braille_page · pad_to_even).
    가이드 오류표(268행) "필드 타입이나 값 범위가 맞지 않음 → BAD_FIELD"."""
    src = [{"orig_page": 3, "blocks": [{"order": 0, "braille": "⠀⠀⠁⠃⠉"}]}]
    for key in ("show_orig_page", "show_braille_page", "pad_to_even"):
        r = sidecar._answer(json.dumps({"id": 5, "op": "build_brf", "job": {"sources": src, "opts": {key: "false"}}}).encode())
        assert r["code"] == "BAD_FIELD" and key in r["error"] and r["id"] == 5, key
        assert "brf" in sidecar.handle({"op": "build_brf", "job": {"sources": src, "opts": {key: False}}})
    off = sidecar.handle({"op": "build_brf", "job": {"sources": src, "opts": {"rows": 4, "pad_to_even": False}}})["brf"]
    on = sidecar.handle({"op": "build_brf", "job": {"sources": src, "opts": {"rows": 4, "pad_to_even": True}}})["brf"]
    assert on.count("\f") == off.count("\f") + 1        # 참거짓 값은 종전대로 듣는다


def test_정수_옵션은_타입과_범위를_본다():
    """#73. `heading_level: "1"` · `cols: "32"` 를 조용히 받고 `rows: 0` 을 조용히 26줄로 했다."""
    src = [{"orig_page": 1, "blocks": [{"order": 0, "braille": "⠀⠀⠁⠃⠉"}]}]
    r = sidecar._answer(json.dumps({"id": 2, "op": "translate", "text": "가", "heading_level": "1"}).encode())
    assert r["code"] == "BAD_FIELD" and "heading_level" in r["error"]
    assert sidecar.handle({"op": "translate", "text": "가", "heading_level": 1})["cells"]
    for opts in ({"cols": "32"}, {"rows": 0}, {"rows": True}):
        r = sidecar._answer(json.dumps({"id": 3, "op": "build_brf", "job": {"sources": src, "opts": opts}}).encode())
        assert r["code"] == "BAD_FIELD" and next(iter(opts)) in r["error"], opts
    assert sidecar.handle({"op": "build_brf", "job": {"sources": src, "opts": {"cols": 32, "rows": 26}}})["brf"]


def test_조판_태그는_아는_태그이고_translate_가_맡을_몫만_한다():
    """#66 — 조판 태그(목록표). 줄 태그만 든 요소는 32칸 미리보기, 면 넘김 표식은 빈 점자(종전엔 '점역 못 함' 주가
    나갔다), 정렬 · 머리말은 글에서 뺀다(앱이 블록 align · job.header(s) 로 옮긴다)."""
    r = sidecar.translate("<!표시작>")
    assert r["cells"] == "⠖" + "⠒" * 30 + "⠲" and r["unknown_tags"] == [] and not r["blocked"]
    for t in ("<!쪽바꿈>", "<!장바꿈>", "<!머리말>제1장<!/머리말>"):
        r = sidecar.translate(t)
        assert (r["cells"], r["blocked"], r["unknown_tags"]) == ("", False, []), t
    assert sidecar.translate("<!가운데정렬>제목") == sidecar.translate("제목")
    assert sidecar.translate("<!머리말>제1장<!/머리말>본문")["cells"] == sidecar.translate("본문")["cells"]


def test_쪽_번호_자리표시는_점역을_그대로_지나가고_그_안에서는_안_끊는다():
    """#66 — build_brf 가 그 면의 번호로 채운다. 태그 앞뒤 자리는 끊을 수 있고, 태그 안쪽은 안 된다."""
    r = sidecar.translate("제<!점자면번호>쪽, 원본 <!묵자쪽번호>쪽")
    cells = r["cells"]
    assert "<!점자면번호>" in cells and "<!묵자쪽번호>" in cells and r["unknown_tags"] == []
    for tag in ("<!점자면번호>", "<!묵자쪽번호>"):
        a = cells.index(tag)
        assert not [b for b in r["breaks"] if a < b < a + len(tag)]
    assert cells.replace("<!점자면번호>", "").replace("<!묵자쪽번호>", "") == sidecar.translate("제쪽, 원본 쪽")["cells"]


def test_원본_쪽_꼬리말은_footer_mode_두_값만_받고_없으면_종전과_같다():
    """#78(대표 결정 2026-10-19 ②). 원본 쪽 열쇠 `footers_by_orig_page` · 범위 `opts.footer_mode`(carry · page).
    새 입력을 안 쓰면 출력이 바이트로 같고, 모르는 범위 값은 `BAD_FIELD` 다."""
    src = [{"orig_page": n, "blocks": [{"order": 0, "braille": "\n".join("⠁⠃" for _ in range(7))}]} for n in (1, 2, 3)]
    base = {"sources": src, "footer": "⠋", "opts": {"rows": 6, "page_row_pages": "every"}}
    old = sidecar.handle({"op": "build_brf", "job": base})["brf"]
    assert sidecar.handle({"op": "build_brf", "job": {**base, "footers_by_orig_page": {}}})["brf"] == old
    carry = sidecar.handle({"op": "build_brf", "job": {**base, "footers_by_orig_page": {"2": "⠛"}}})["brf"]
    page = sidecar.handle({"op": "build_brf", "job": {**base, "footers_by_orig_page": {"2": "⠛"},
                                                       "opts": {**base["opts"], "footer_mode": "page"}}})["brf"]
    rows = lambda brf: [p.splitlines()[-1] for p in brf.split("\f") if p.strip()]   # 면마다 마지막 줄(페이지행)
    assert "g" in rows(carry)[-1] and "g" not in rows(page)[-1]       # 3쪽만 실린 마지막 면: 이어가기만 2쪽 꼬리말(⠛ = g)
    r = sidecar._answer(json.dumps({"id": 4, "op": "build_brf",
                                    "job": {**base, "opts": {"footer_mode": "through"}}}).encode())
    assert r["code"] == "BAD_FIELD" and "footer_mode" in r["error"]
