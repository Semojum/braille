"""AI 저장소(`Semojum/AI`)의 점역 엔진을 이 레포로 다시 옮긴다.

    python tools/sync_from_ai.py <AI 저장소 경로>

옮기는 것
- `app/ai/braille/*.py`·`*.json` → `semojum_braille/`
- `app/ai/gates.py` → `semojum_braille/gates.py` (translator 가 G3 `strip_format_tokens` 를 부른다)
- `app/schemas/content.py` 중 엔진이 쓰는 다섯 타입 → `semojum_braille/schemas.py`
- `tools/tests_from_ai.txt` 에 적힌 시험 → `test/` (같은 자리), `app/utils/braille_ascii.py` → `test/support/`

코드는 **임포트 경로만** 바꾼다. 동작은 AI 저장소와 같다.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "semojum_braille"

# 긴 것부터. 코드·문자열(patch 경로)·주석을 가리지 않고 바꾼다.
REWRITES = [
    (re.compile(r"\bfrom app\.ai import gates\b"), "from semojum_braille import gates"),
    (re.compile(r"\bapp\.ai\.gates\b"), "semojum_braille.gates"),
    (re.compile(r"\bapp\.ai\.braille\b"), "semojum_braille"),
    (re.compile(r"\bapp\.schemas\.content\b"), "semojum_braille.schemas"),
]
TEST_REWRITES = REWRITES + [
    (re.compile(r"\bapp\.utils\.braille_ascii\b"), "braille_ascii"),
    # 소스 트리를 경로로 읽는 시험(기호표 직접 대조 · make_rule 문자열 훑기).
    (re.compile(r'"app/ai/braille/'), '"semojum_braille/'),
    (re.compile(r'/ "app" / "ai"'), '/ "semojum_braille"'),
]
# 엔진 안에 남아도 되는 `app.` 참조: 타입 검사 전용 임포트(런타임 0).
ALLOWED_APP_REFS = {"from app.schemas.layout import LayoutResult"}

SCHEMA_TYPES = ("RuleApplication", "Draft", "LLMOutput", "BoxBorder", "BrailleOutput")
HELPERS = ["test/braille_style_equiv.py"]


def rewrite(text: str, rules) -> str:
    for pat, new in rules:
        text = pat.sub(new, text)
    return text


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
    doc = ('"""점역 엔진 데이터 모델 — AI 서버 `app/schemas/content.py` 에서 엔진이 쓰는 다섯 타입만 옮겼다."""\n')
    return doc + head + "".join(keep).rstrip() + "\n"


def sync_package(ai: Path) -> None:
    src = ai / "app" / "ai" / "braille"
    for f in PKG.glob("*"):
        if f.is_file():
            f.unlink()
    for f in sorted(src.iterdir()):
        if f.suffix in (".py", ".json"):
            text = f.read_text(encoding="utf-8")
            (PKG / f.name).write_text(rewrite(text, REWRITES) if f.suffix == ".py" else text, encoding="utf-8")
    gates = (ai / "app" / "ai" / "gates.py").read_text(encoding="utf-8")
    gates = gates.replace("from app.utils.logger import get_logger\n", "import logging\n")
    gates = gates.replace("logger = get_logger(__name__)", "logger = logging.getLogger(__name__)")
    (PKG / "gates.py").write_text(rewrite(gates, REWRITES), encoding="utf-8")
    content = (ai / "app" / "schemas" / "content.py").read_text(encoding="utf-8")
    (PKG / "schemas.py").write_text(build_schemas(content), encoding="utf-8")
    bad = {f.name: leftover_app_imports(f.read_text(encoding="utf-8")) for f in PKG.glob("*.py")}
    bad = {k: v for k, v in bad.items() if v}
    assert not bad, f"남은 app 임포트: {bad}"


def sync_tests(ai: Path) -> None:
    listed = [l.strip() for l in (ROOT / "tools" / "tests_from_ai.txt").read_text(encoding="utf-8").splitlines()
              if l.strip() and not l.startswith("#")]
    dst_root = ROOT / "test"
    assert all(rel.startswith("test/unit_test/") for rel in listed), "옮기는 시험은 test/unit_test/ 아래만"
    for p in (dst_root / "unit_test").rglob("test_*.py"):   # 이 레포 고유 시험(test/test_*.py)은 둔다
        p.unlink()
    for rel in listed:
        text = (ai / rel).read_text(encoding="utf-8")
        out = dst_root / Path(rel).relative_to("test")
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


if __name__ == "__main__":
    ai = Path(sys.argv[1]).resolve()
    sync_package(ai)
    sync_tests(ai)
    print("ok", ai)
