"""엔진 조항표 사본은 「통일영어점자 규정」(ICEB) 조항을 싣지 않는다(#111).

ICEB 조항 글은 CC BY-NC-ND 2.5 AU 라 비영리 조건이 있다. 이 엔진은 상용 앱에 실려 나가므로 동기화 도구가
뺀다(`tools/sync_from_ai.py` `REGULATION_DROP_PREFIXES`). AI 저장소 정본에는 그대로 있다. AI 쪽 조항 수 시험
둘은 `test/conftest.py` `_ENGINE_DROPS_ICEB` 로 건너뛰고, 엔진 쪽 수는 여기서 본다.
"""
import json
from pathlib import Path

from semojum_braille.encoder.regulations import all_rule_ids

_DATA = json.loads((Path(__file__).resolve().parents[1] / "semojum_braille" / "encoder" / "regulations.json")
                   .read_text(encoding="utf-8"))


def test_ICEB_조항과_출처_칸이_없다():
    assert not [k for k in _DATA["rules"] if k.startswith("ICEB-")]
    assert "ICEB" not in _DATA["_meta"]["sources"]
    assert "ICEB-" in _DATA["_meta"]["engine_copy"]


def test_근거_조회_239_검색_전용_101():
    assert len(all_rule_ids()) == 239
    assert sum(1 for v in _DATA["rules"].values() if v.get("supported", True) is False) == 101
