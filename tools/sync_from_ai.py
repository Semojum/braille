"""AI 저장소(`Semojum/AI`)의 점역·역점역 엔진을 이 레포로 다시 옮긴다.

    python tools/sync_from_ai.py <AI 저장소 경로>

옮기는 것
- `app/ai/braille/*.py`·`*.json` → `semojum_braille/encoder/`
- `app/ai/gates.py` → `semojum_braille/encoder/gates.py` (translator 가 G3 `strip_format_tokens` 를 부른다)
- `app/schemas/content.py` 중 엔진이 쓰는 다섯 타입 → `semojum_braille/schemas.py`
- `app/utils/braille_back.py` → `semojum_braille/decoder/back.py`
- 같은 폴더의 역맵 json 셋 → `semojum_braille/decoder/`
- `tools/tests_from_ai.txt` 에 적힌 시험 → `test/` (같은 자리), `app/utils/braille_ascii.py` → `test/support/`

코드는 **임포트 경로만** 바꾼다. 예외는 아래 두 패치 목록뿐이고, 둘 다 자리를 못 찾으면 멈춘다.
- `SILENT_FIXES`: 역맵 json 이 없을 때 빈 맵으로 조용히 넘어가던 것을 예외로 바꾼다.
- `KIWI_OPTIONAL`: kiwipiepy 가 없으면 낱말 목록(`decoder/kor_words.json`)으로 한국어 낱말을 가른다.
  kiwipiepy 가 깔려 있으면 AI 원본과 똑같이 돈다.

이 레포에만 있는 파일(`OWN`)은 덮어쓰지도 지우지도 않는다.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "semojum_braille"
ENC = PKG / "encoder"
DEC = PKG / "decoder"

# 이 레포에만 있는 파일. AI 원본에 없고, 동기화가 건드리지 않는다.
OWN = {
    PKG / "__init__.py",
    PKG / "sidecar.py",
    PKG / "brf.py",               # .brf 파일 꼴(현장 유통본 바이트). AI 에 없다
    ENC / "__init__.py",          # AI 쪽 `app/ai/braille/__init__.py` 는 빈 파일이다. 공개 이름을 여기서 내보낸다
    DEC / "__init__.py",
    DEC / "wordlist.py",          # kiwi 없이 쓰는 낱말 판정
    DEC / "kor_words.json",       # 그 낱말 목록(tools/build_word_list.py 로 만든다)
}

# 긴 것부터. 코드·문자열(patch 경로)·주석을 가리지 않고 바꾼다.
REWRITES = [
    (re.compile(r"\bfrom app\.ai import gates\b"), "from semojum_braille.encoder import gates"),
    (re.compile(r"\bapp\.ai\.gates\b"), "semojum_braille.encoder.gates"),
    (re.compile(r"\bapp\.ai\.braille\b"), "semojum_braille.encoder"),
    (re.compile(r"\bapp\.schemas\.content\b"), "semojum_braille.schemas"),
    (re.compile(r"\bapp\.utils\.braille_back\b"), "semojum_braille.decoder.back"),
    # `from app.utils import braille_back as B` 꼴. 점으로 이어진 경로만 바꾸면 이게 남는다.
    # ⚠ `as B` 가 뒤따르므로 별칭을 여기서 붙이면 `as X as B` 가 되어 문법이 깨진다.
    #   별칭이 있는 꼴을 먼저 잡고, 없는 꼴을 그다음에 잡는다.
    (re.compile(r"\bfrom app\.utils import braille_back as (\w+)"), r"from semojum_braille.decoder import back as \1"),
    (re.compile(r"\bfrom app\.utils import braille_back\b"), "from semojum_braille.decoder import back as braille_back"),
]
TEST_REWRITES = REWRITES + [
    (re.compile(r"\bapp\.utils\.braille_ascii\b"), "braille_ascii"),
    # 소스 트리를 경로로 읽는 시험(기호표 직접 대조 · make_rule 문자열 훑기 · 역맵 파일).
    (re.compile(r'"app/ai/braille/'), '"semojum_braille/encoder/'),
    (re.compile(r'/ "app" / "ai"'), '/ "semojum_braille" / "encoder"'),
    (re.compile(r'"app/utils/'), '"semojum_braille/decoder/'),
]
# 엔진 안에 남아도 되는 `app.` 참조: 타입 검사 전용 임포트(런타임 0).
ALLOWED_APP_REFS = {"from app.schemas.layout import LayoutResult"}

SCHEMA_TYPES = ("RuleApplication", "Draft", "LLMOutput", "BoxBorder", "BrailleOutput")
DECODER_JSONS = ("braille_syllable_map.json", "braille_special_rev.json", "kor_syllable_freq.json")
HELPERS = ["test/braille_style_equiv.py"]

# ★ 무음 실패를 예외로 바꾼다 (2026-09-29).
#   역맵 json 이 없으면 AI 원본은 **빈 맵으로 조용히 넘어간다.** 서버에서는 파일이 늘 있어
#   드러나지 않았지만, 앱에 넣으면 패키징이 어긋나도 역점역이 그냥 돌고 **결과만 조용히 틀린다.**
#   없는데 도는 것은 기능이 아니다. 여기서만 고친다(점역 결과를 안 바꾼다).
SILENT_FIXES = [
    # ① 음절 역맵 — 가드 `if _MAP_PATH.exists():` 와 바깥 `return {}` 를 통째로 걷어낸다.
    #   ⚠ 가드 안에 raise 를 넣어도 **파일이 없으면 가드가 거짓이라 바깥 return 으로 간다.**
    #     2026-09-29 에 그렇게 고쳐서 안 먹었다(code 가 빈 폴더로 재현해 잡았다).
    (
        '    if _MAP_PATH.exists():\n'
        '        return json.loads(_MAP_PATH.read_text(encoding="utf-8"))\n'
        '    return {}\n',
        '    # 없거나 깨지면 예외. 빈 맵으로 돌면 한글이 조용히 안 풀린다.\n'
        '    return json.loads(_MAP_PATH.read_text(encoding="utf-8"))\n',
    ),
    # ② 특수 역맵 — `try/except Exception: return {}` 를 통째로 걷어낸다.
    #   ⚠ try 안에 raise 를 넣으면 그 except 가 삼킨다. 같은 날 같은 실수를 했다.
    (
        '    try:\n'
        '        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}\n'
        '    except Exception:\n'
        '        return {}\n',
        '    # 없거나 깨지면 예외(위와 같은 이유).\n'
        '    return json.loads(p.read_text(encoding="utf-8"))\n',
    ),
    # 도크스트링도 고친다. "없으면 빈 맵" 은 이제 거짓이다.
    (
        '    """점자셀→한글음절 역맵(JSON 캐시). 없으면 빈 맵(경고)."""',
        '    """점자셀→한글음절 역맵(JSON 캐시). 없거나 깨지면 예외."""',
    ),
]

# ★ kiwipiepy 를 선택 의존(`pip install semojum-braille[kiwi]`)으로 돌린다 (2026-09-29, 대표 지시).
#   AI 원본은 kiwi 가 없으면 낱말 판정이 처음 불릴 때 ImportError 로 `decode` 전체가 멈춘다.
#   kiwi 가 없을 때만 낱말 목록으로 가른다. 판정 규칙은 T18 에서 잰 "낱말 목록" 판 그대로다
#   (라틴이 끼면 아니다 · 한글 덩어리가 모두 두 음절 이상이고 목록에 있으면 낱말). 앞의 두 줄
#   검사는 원본 함수에 이미 있다. kiwi 가 있으면 한 글자도 안 바뀐다.
KIWI_OPTIONAL = [
    (
        '    """읽힌 한글이 **실재하는 한국어 낱말**인가(kiwi 형태소 분석)."""',
        '    """읽힌 한글이 **실재하는 한국어 낱말**인가(kiwi 형태소 분석. kiwi 가 없으면 낱말 목록)."""',
    ),
    (
        '    if _KIWI is None:\n'
        '        from kiwipiepy import Kiwi\n'
        '        _KIWI = Kiwi()\n',
        '    if _KIWI is None:\n'
        '        try:\n'
        '            from kiwipiepy import Kiwi\n'
        '        except ImportError:          # [kiwi] 선택 의존을 안 깔았다 → 낱말 목록(이 레포 전용 패치)\n'
        '            _KIWI = False\n'
        '        else:\n'
        '            _KIWI = Kiwi()\n'
        '    if _KIWI is False:\n'
        '        from semojum_braille.decoder.wordlist import known\n'
        '        return known(runs)\n',
    ),
]


def rewrite(text: str, rules) -> str:
    for pat, new in rules:
        text = pat.sub(new, text)
    return text


def apply_patches(body: str, patches, name: str) -> str:
    for before, after in patches:
        if before not in body:
            # ★ 경고만 찍고 넘어가면 원본이 바뀐 날 패치가 조용히 빠진다. 멈춘다.
            raise SystemExit(
                f"{name} 패치 자리를 못 찾았다. AI 원본이 바뀌었다.\n"
                f"  찾던 것: {before.strip()[:70]}\n"
                f"  tools/sync_from_ai.py 의 {name} 를 원본에 맞게 고쳐라."
            )
        body = body.replace(before, after, 1)
    return body


def leftover_app_imports(text: str) -> list[str]:
    bad = []
    for line in text.splitlines():
        s = line.strip()
        if re.match(r"(from|import)\s+app\.", s) and s not in ALLOWED_APP_REFS:
            bad.append(s)
    return bad


def build_schemas(src: str) -> str:
    """content.py 에서 다섯 타입만 남긴다(`ExtractedContent` 는 엔진이 안 쓴다)."""
    head, *blocks = re.split(r"(?m)^(?=class )", src)
    keep = [b for b in blocks if re.match(r"class (\w+)", b).group(1) in SCHEMA_TYPES]
    names = [re.match(r"class (\w+)", b).group(1) for b in keep]
    assert sorted(names) == sorted(SCHEMA_TYPES), names
    doc = '"""점역·역점역 데이터 모델 — AI 서버 `app/schemas/content.py` 에서 엔진이 쓰는 다섯 타입만 옮겼다."""\n'
    return doc + head + "".join(keep).rstrip() + "\n"


def sync_encoder(ai: Path) -> None:
    src = ai / "app" / "ai" / "braille"
    ENC.mkdir(parents=True, exist_ok=True)
    for f in ENC.glob("*"):
        if f.is_file() and f not in OWN:
            f.unlink()
    for f in sorted(src.iterdir()):
        dst = ENC / f.name
        if f.suffix not in (".py", ".json") or dst in OWN:
            continue
        text = f.read_text(encoding="utf-8")
        dst.write_text(rewrite(text, REWRITES) if f.suffix == ".py" else text, encoding="utf-8")
    gates = (ai / "app" / "ai" / "gates.py").read_text(encoding="utf-8")
    gates = gates.replace("from app.utils.logger import get_logger\n", "import logging\n")
    gates = gates.replace("logger = get_logger(__name__)", "logger = logging.getLogger(__name__)")
    (ENC / "gates.py").write_text(rewrite(gates, REWRITES), encoding="utf-8")
    content = (ai / "app" / "schemas" / "content.py").read_text(encoding="utf-8")
    (PKG / "schemas.py").write_text(build_schemas(content), encoding="utf-8")


def sync_decoder(ai: Path) -> None:
    src = ai / "app" / "utils" / "braille_back.py"
    body = rewrite(src.read_text(encoding="utf-8"), REWRITES)
    body = apply_patches(body, SILENT_FIXES, "SILENT_FIXES")
    body = apply_patches(body, KIWI_OPTIONAL, "KIWI_OPTIONAL")
    DEC.mkdir(parents=True, exist_ok=True)
    (DEC / "back.py").write_text(body, encoding="utf-8")
    for name in DECODER_JSONS:
        p = ai / "app" / "utils" / name
        if not p.is_file():
            # 역맵이 빠진 패키지는 조용히 틀린 글을 낸다. 만들지 않는다.
            raise SystemExit(f"AI 원본에 역맵이 없다: {p}")
        shutil.copy2(p, DEC / name)


def sync_tests(ai: Path) -> int:
    listed = [l.strip() for l in (ROOT / "tools" / "tests_from_ai.txt").read_text(encoding="utf-8").splitlines()
              if l.strip() and not l.startswith("#")]
    assert all(rel.startswith("test/unit_test/") for rel in listed), "옮기는 시험은 test/unit_test/ 아래만"
    assert len(listed) == len(set(listed)), "tests_from_ai.txt 에 같은 줄이 둘 있다"
    dst_root = ROOT / "test"
    for p in (dst_root / "unit_test").rglob("test_*.py"):   # 이 레포 고유 시험(test/test_*.py)은 둔다
        p.unlink()
    for rel in listed:
        text = (ai / rel).read_text(encoding="utf-8")
        out = ROOT / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rewrite(text, TEST_REWRITES), encoding="utf-8")
        # AI 쪽 패키지 꼴(__init__.py 유무)을 그대로 따른다 — 같은 이름 시험 파일 충돌 방지.
        d = Path(rel).parent
        while d != Path("."):
            if (ai / d / "__init__.py").exists():
                (ROOT / d / "__init__.py").touch()
            d = d.parent
    for rel in HELPERS:   # 시험이 `from test.<모듈> import` 로 부르는 보조
        (ROOT / rel).write_text(rewrite((ai / rel).read_text(encoding="utf-8"), TEST_REWRITES), encoding="utf-8")
    support = dst_root / "support"
    support.mkdir(exist_ok=True)
    shutil.copy(ai / "app" / "utils" / "braille_ascii.py", support / "braille_ascii.py")
    return len(listed)


def check_package() -> None:
    bad = {str(f.relative_to(ROOT)): leftover_app_imports(f.read_text(encoding="utf-8")) for f in PKG.rglob("*.py")}
    bad = {k: v for k, v in bad.items() if v}
    assert not bad, f"남은 app 임포트: {bad}"
    missing = [str(f.relative_to(ROOT)) for f in OWN if not f.exists()]
    assert not missing, f"이 레포 고유 파일이 없다: {missing}"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)
    ai = Path(sys.argv[1]).resolve()
    sync_encoder(ai)
    sync_decoder(ai)
    n = sync_tests(ai)
    check_package()
    print(f"끝: {ai} · 시험 {n}개")
