"""역점역의 kiwi 없는 낱말 판정이 쓰는 목록(`semojum_braille/decoder/kor_words.json`)을 만든다.

    python tools/build_word_list.py <묵자 json 폴더>

폴더의 `*.json` 은 MinerU 추출 결과(요소 목록 `elements[].content`)다. 이름에 "영어" 가 든 파일은
뺀다(역점역 판정이 주로 불리는 영어 교재를 목록이 미리 보지 않게). 인라인 태그(`<!…>`)는 걷고,
한글 덩어리 가운데 두 번 이상 나오고 두 음절 이상인 것만 남긴다. 문턱이나 조정값은 없다.
지금 목록은 2027 수능특강 비영어 12권 1,355쪽에서 만들었다(27,790개).
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "semojum_braille" / "decoder" / "kor_words.json"
HANGUL_RUN = re.compile(r"[가-힣]+")
TAG = re.compile(r"<!/?[^>]*>")


def build(folder: Path) -> dict:
    cnt, pages = Counter(), 0
    for f in sorted(folder.glob("*.json")):
        if "영어" in f.name:
            continue
        pages += 1
        for e in json.loads(f.read_text(encoding="utf-8")).get("elements", []):
            if isinstance(e.get("content"), str):
                cnt.update(HANGUL_RUN.findall(TAG.sub("", e["content"])))
    words = sorted(w for w, c in cnt.items() if c >= 2 and len(w) >= 2)
    meta = {"source": f"한국어 교재 묵자 {pages:,}쪽. 영어 교재 쪽은 넣지 않았다",
            "rule": "한글 덩어리([가-힣]+) 가운데 두 번 이상 나오고 두 음절 이상인 것",
            "count": len(words), "gold_braille_used": False, "built_by": "tools/build_word_list.py"}
    return {"meta": meta, "words": words}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)
    data = build(Path(sys.argv[1]))
    OUT.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(data["meta"])
