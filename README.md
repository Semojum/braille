# semojum-braille

세모점 점역 엔진. 묵자(한국어 본문·수식·표·시각 대체텍스트)를 한국어 점자로 옮긴다.

**앱 내장용 패키지다.** 종전에는 AI 서버(`Semojum/AI`)에 두고 앱이 API 로 불렀다. 이제 앱이
이 패키지를 직접 설치해 함수로 부른다. 네트워크 왕복이 없고, LLM 을 부르지 않는다.

## 설치

```bash
pip install semojum-braille          # 배포 뒤
pip install -e .                     # 개발
```

Python 3.10 이상. **시험한 판은 3.10 · 3.12 · 3.13** 이고 셋의 출력이 바이트 단위로 같다.
앱에 넣을 때는 **3.13** 을 쓴다 — 3.12 의 Windows 임베더블은 3.12.10(2025-04)이 마지막이고
그 뒤 보안 수정을 받을 길이 없다. 3.13 은 임베더블 3.13.15(2026-08-05)가 나와 있다.
설치본 파이썬은 2년마다 올려야 한다(PEP 719). 의존은 `braillify` 와 `pydantic` 둘이다.

## 쓰기

```python
from semojum_braille.translator import translate_tagged_text

cells, rules = translate_tagged_text("이차방정식 $x^2+2x+1=0$ 의 해를 구하시오.")
```

## 무엇이 들어 있나

| 모듈 | 무엇 |
|---|---|
| `translator.py` | 정본 진입점. 태그 붙은 묵자를 점자 셀로 |
| `text_braille.py` | 한글 본문·문장 부호 |
| `formula_braille.py` · `inline_math.py` · `kor_math_rules.py` | 수식. 「수학 점자」 규정 |
| `eng_braille.py` | 로마자. 「통일영어점자」 |
| `symbol_rules.py` · `symbol_table.json` | 특수 기호 표 |
| `table_braille.py` | 표 |
| `layout_braille.py` | 줄바꿈·들여쓰기·칸 수 |
| `visual_braille.py` | 시각 자료 대체텍스트 |
| `regulations.py` · `regulations.json` | 규정 조항 표. 적용한 조항을 결과에 남긴다 |
| `schemas.py` | 입출력 타입(pydantic) |

점자는 유니코드 점자 블록(U+2800–U+28FF)으로 낸다. 파일은 항상 UTF-8 이다.

## 규정

「한국 점자 규정」·「수학 점자」·「통일영어점자」를 따른다. 규정에 조항이 없거나 「점자 도서
제작 지침」만 있는 자리에서는 발간된 점자 도서의 관행을 따른다. 어느 쪽을 택했는지는 코드 주석에
원장 항목 번호로 적혀 있다.

## 시험

```bash
pip install -e ".[test]"
pytest test
```

정답 코퍼스(묵자–점자 정렬쌍)를 읽는 시험은 이 레포에 없다. 그 시험은 코퍼스가 있는
`Semojum/AI` 에 남아 있다.

## 어디서 왔나

`Semojum/AI` 의 `app/ai/braille/` 를 옮긴 것이다. 기준 커밋과 재동기화 방법은
`tools/sync_from_ai.py` 에 있다.
