"""T4-3 #6 — rule_trail 레지스트리 무결성.

환각 0 아키텍처 강제: 코드가 emit하는 모든 rule_id는 regulations.json(226키)에
존재해야 한다. 가짜·댕글링 rule_id = 0. make_rule()이 유일한 emit 경로이므로
(1) 소스의 make_rule("...") 리터럴 전수가 레지스트리 부분집합인지 정적 검사,
(2) 결정적 braille 변환 경로가 실제 emit하는 id가 레지스트리 부분집합인지 동적 검사.
"""

from __future__ import annotations

import json
import pathlib
import re
from uuid import uuid4

import pytest

from semojum_braille.encoder.visual_braille import CartoonBraille, ChartGraphBraille
from semojum_braille.encoder.formula_braille import FormulaBraille
from semojum_braille.encoder.visual_braille import ImageBraille
from semojum_braille.encoder.regulations import all_rule_ids, make_rule, make_rule_at, rule_meta
from semojum_braille.encoder.table_braille import TableBraille
from semojum_braille.encoder.text_braille import TextBraille
from semojum_braille.schemas import Draft, LLMOutput

_APP_AI = pathlib.Path(__file__).resolve().parents[3] / "semojum_braille" / "encoder"
_MAKE_RULE_RE = re.compile(r"""make_rule\(\s*['"]([^'"]+)['"]""")


def _scan_make_rule_ids() -> set[str]:
    ids: set[str] = set()
    for py in _APP_AI.rglob("*.py"):
        for m in _MAKE_RULE_RE.finditer(py.read_text(encoding="utf-8")):
            ids.add(m.group(1))
    return ids


def _collect_trail_ids(outputs) -> set[str]:
    ids: set[str] = set()
    for o in outputs:
        ids.update(r.rule_id for r in o.rule_trail)
        for d in o.drafts:
            ids.update(r.rule_id for r in d.rule_trail)
    return ids


def _llm(text: str, *, drafts=None, render_mode="text_only") -> LLMOutput:
    return LLMOutput(
        element_id=uuid4(),
        corrected_text=text,
        render_mode=render_mode,
        routing_tier="ZERO",
        drafts=drafts or [],
    )


class TestRuleRegistry:

    def test_registry_size(self):
        # MCST+NLD 226 + 자료지침(NISE) 13 (Step17에서 §6.6.3~6.6.8 여섯 조항 추가 —
        # 도표 8종이 저마다 제 조항을 근거로 달 수 있게. 원문은 braille-source/text/ 발췌)
        # 검색 전용 101(supported=false)은 rule_trail 조회 집합에 안 든다 — TestSearchOnly.
        assert len(all_rule_ids()) == 303          # 239 + ICEB 64(#1547)

    def test_make_rule_literals_subset_of_registry(self):
        scanned = _scan_make_rule_ids()
        assert scanned, "make_rule 리터럴을 하나도 찾지 못함 (스캔 경로 오류 의심)"
        dangling = scanned - all_rule_ids()
        assert not dangling, f"regulations.json에 없는 rule_id emit: {sorted(dangling)}"

    def test_make_rule_rejects_dangling(self):
        with pytest.raises(KeyError):
            make_rule("MCST-한글-9.9.9")

    def test_braille_modules_emit_registered_ids(self):
        vis_drafts = [
            Draft(option=1, text="[점역사주] 그림. 설명", render_mode="narrative", label="원본"),
            Draft(option=2, text="[점역사주] 그림. 요약", render_mode="narrative", label="요약"),
        ]
        emitted: set[str] = set()
        emitted |= _collect_trail_ids(TextBraille().translate([_llm("가나다라")]))
        emitted |= _collect_trail_ids(
            FormulaBraille().translate([_llm("x^2", render_mode="formula_block")])
        )
        emitted |= _collect_trail_ids(
            TableBraille().translate([_llm("머리1 | 머리2\n값1 | 값2", render_mode="table_grid")])
        )
        emitted |= _collect_trail_ids(ImageBraille().translate([_llm("", drafts=vis_drafts)]))
        emitted |= _collect_trail_ids(CartoonBraille().translate([_llm("", drafts=vis_drafts)]))
        emitted |= _collect_trail_ids(ChartGraphBraille().translate([_llm("", drafts=vis_drafts)]))

        assert emitted, "emit된 rule_id가 없음"
        dangling = emitted - all_rule_ids()
        assert not dangling, f"점역 모듈이 미등록 rule_id emit: {sorted(dangling)}"


_REGS = json.loads((_APP_AI / "regulations.json").read_text(encoding="utf-8"))["rules"]
_SEARCH_ONLY = sorted(k for k, v in _REGS.items() if v.get("supported", True) is False)


class TestSearchOnly:
    """R-94: 음악 · 국제음성기호는 점역하지 않고 검색만 되게 넣었다(supported=false).

    점역 경로에서 이 id 로 rule_trail 을 다는 일이 없어야 한다 — 조회가 없는 id 와 같게 굴어야 한다.
    """

    def test_검색_전용은_101개(self):
        assert len(_SEARCH_ONLY) == 101
        assert len(_REGS) == 303 + 101

    @pytest.mark.parametrize("rid", _SEARCH_ONLY)
    def test_조회에_안_걸린다(self, rid):
        assert rid not in all_rule_ids()
        assert rule_meta(rid) is None
        with pytest.raises(KeyError, match="검색 전용"):
            make_rule(rid)

    def test_make_rule_at_도_막힌다(self):
        with pytest.raises(KeyError):
            make_rule_at(_SEARCH_ONLY[0], ["⠁⠃"], 0, 1)

    def test_검색에_쓸_필드는_다_있다(self):
        for rid in _SEARCH_ONLY:
            v = _REGS[rid]
            assert v["source"] and v["publisher"] and v["version"] and v["rule_name"] and v["contents"], rid
            assert v["section"], rid
