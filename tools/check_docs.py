"""README 와 docs/*.md 의 `>>>` 예를 문서에서 꺼내 실제로 돌리고, 적힌 출력과 견준다.

    python tools/check_docs.py            # 틀린 예가 있으면 0 이 아닌 값으로 끝난다
    python tools/check_docs.py docs/encoder.md   # 파일을 골라서

문서마다 ```python 블록 가운데 준비 코드(임포트·함수·변수 정의)를 먼저 돌린다. 역점역 예는
kiwipiepy(`[kiwi]`)를 깐 환경 기준이다. 없으면 kiwi 에 기대는 예가 달리 나온다(docs/decoder.md).
"""
from __future__ import annotations

import doctest
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
SETUP = re.compile(r"^(import |from |def |[A-Za-z_]\w* = )", re.M)


def check(path: Path) -> doctest.TestResults:
    text = path.read_text(encoding="utf-8")
    globs: dict = {}
    for block in re.findall(r"```python\n(.*?)```", text, re.S):
        if SETUP.search(block) and "print(" not in block and "def fold" not in block:
            exec(block, globs)
    body = re.sub(r"(?m)^```.*$", "", text)       # 코드 울타리 줄이 기대 출력에 섞이지 않게
    test = doctest.DocTestParser().get_doctest(body, globs, path.name, str(path), 0)
    runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS)
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:     # 파일을 쓰는 예(layout)가 저장소를 더럽히지 않게
        os.chdir(tmp)
        try:
            runner.run(test)
        finally:
            os.chdir(cwd)
    return runner.summarize(verbose=False)


if __name__ == "__main__":
    failed = 0
    for f in [Path(a).resolve() for a in sys.argv[1:]] or FILES:
        r = check(f)
        print(f"{f.relative_to(ROOT)}: 예 {r.attempted}개, 틀림 {r.failed}개")
        failed += r.failed
    sys.exit(1 if failed else 0)
