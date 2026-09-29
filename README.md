# semojum-braille · 한국어 점역 엔진

## 1. 이 패키지가 무엇을 하나

묵자(한국어 글, 인라인 수식, 표, 시각 자료 설명)를 한국어 점자로 옮기는 파이썬 라이브러리다. 규칙 기반이라 모델·네트워크 없이 돌고, 같은 입력에는 늘 같은 점자를 낸다. 근거 규정은 「한국 점자 규정」(문화체육관광부 2024), 「점자 도서 제작 지침」(국립장애인도서관 2025), 「점자 자료 제작 지침」(국립특수교육원 2025)이다. 결과는 유니코드 점자(U+2800~U+28FF) 문자열이다. 글 한 덩어리만 옮길 수도 있고, 요소 여럿을 32칸 × 26줄 쪽으로 조판할 수도 있다.

```
>>> translate_tagged_text('수학 점수가 3점 올랐다.')
'⠠⠍⠚⠁⠀⠨⠎⠢⠠⠍⠫⠀⠼⠉⠨⠎⠢⠀⠥⠂⠐⠣⠌⠊⠲'
```

점자를 글자로 되돌리는 역점역은 짝 패키지 `semojum-braille-back` 이다.

| 절 | 내용 |
|---|---|
| 2 | 설치 |
| 3 | 빠른 시작 |
| 4 | API 레퍼런스(공개 함수 전부) |
| 5 | 입출력 형식: 태그 문법, 점자 표기, 데이터 타입 |
| 6 | 설정(환경 변수) |
| 7 | 모듈 구성(엔진을 고칠 사람용) |
| 8 | 파이썬이 아닌 곳에서 쓰기(사이드카) |
| 9 | 규정 근거 |
| 10 | 한계와 주의 |

이 문서의 예는 모두 실제로 돌린 입출력이다(파이썬 3.10, 엔진 0.1.1). 3.12·3.13 은 시험 전수와 코퍼스 출력이 3.10 과 같다는 것을 따로 확인했다(2절).

---

## 2. 설치

저장소를 받아 그 안에서 설치한다.

```
pip install .              # 쓰기만 할 때
pip install -e .[test]     # 엔진을 고치고 시험까지 돌릴 때
pytest                     # 857 통과 · 3 xfail (2026-09-29)
```

| 항목 | 내용 |
|---|---|
| 파이썬 | 3.10 이상(`requires-python >=3.10`). 3.10 · 3.12 · 3.13 에서 시험 전수와 출력이 같다. 3.11 · 3.14 는 돌려 보지 않았다 |
| 의존 | `braillify==2.0.1`(Rust 확장, 한글 점역) · `pydantic>=2.9,<3`(데이터 타입) |
| 크기 | 설치 약 23MB(리눅스). 이 패키지 자체는 0.76MB, 나머지는 두 의존이다 |
| 데이터 파일 | `symbol_table.json`(특수 기호표) · `regulations.json`(규정 조항 239개). 패키지 안에 함께 실린다 |

`braillify` 는 패키지 메타데이터의 라이선스 칸이 비어 있다. 배포하기 전에 확인한다.

---

## 3. 빠른 시작

```python
from semojum_braille.translator import translate_tagged_text

print(translate_tagged_text("대한민국의 모든 국민은 법 앞에 평등하다."))
```

```
⠊⠗⠚⠒⠑⠟⠈⠍⠁⠺⠀⠑⠥⠊⠵⠀⠈⠍⠁⠑⠟⠵⠀⠘⠎⠃⠀⠣⠲⠝⠀⠙⠻⠊⠪⠶⠚⠊⠲
```

다음으로 볼 곳:
- 줄을 32칸에서 바꿀 자리까지 받으려면 `translate_body`(4.1).
- 제목·본문 요소를 쪽으로 조판하려면 `TextBraille` 로 옮긴 뒤 `LayoutBraille().render`(4.5, 4.7).
- 수식 LaTeX 하나를 옮기려면 `convert_latex`(4.2).
- C#·자바스크립트 같은 다른 언어에서 부르려면 8절.

---

## 4. API 레퍼런스

공개 함수는 이 절에 적은 것이 전부다. 밑줄(`_`)로 시작하는 이름과 7절의 "계약 아님" 칸에 적은 이름은 판이 오르면 바뀔 수 있으니 기대지 않는다.

아래 예는 이 준비 코드를 한 번 돌린 뒤의 입출력이다.

```python
import os, uuid
from types import SimpleNamespace
from semojum_braille import eng_braille, inline_math, symbol_rules
from semojum_braille.kor_math_rules import convert_latex
from semojum_braille.translator import (translate_tagged_text, translate_body, translate_with_breaks,
                                        translate_visual, translate_plain, sanitize_for_braille)
from semojum_braille.schemas import LLMOutput, Draft
from semojum_braille.text_braille import TextBraille, content_rules
from semojum_braille.formula_braille import FormulaBraille
from semojum_braille.table_braille import TableBraille, build_table_tags, parse_table_tags, print_layout
from semojum_braille.visual_braille import VisualBraille, DiagramBraille
from semojum_braille.layout_braille import LayoutBraille, flatten_elements, render_page_text, wordwrap_by_word
from semojum_braille.regulations import make_rule, make_rule_at, rule_meta, section_text, all_rule_ids
```

모든 함수는 **예외를 드물게 던진다.** 옮길 수 없는 글자는 예외 대신 빠지고(10절), 요소 점역 클래스는 한 요소가 실패해도 그 요소만 자리표시로 바꾸고 나머지를 옮긴다. 인자 타입이 틀리면(문자열 자리에 `None` 등) 파이썬 기본 예외가 난다.

### 4.1 글 점역 · `semojum_braille.translator`

#### `translate_tagged_text(text, *, force_roman=False, qnum_period=True) -> str`

묵자 한 덩어리를 점자 문자열 하나로 옮긴다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `text` | `str` | 없음 | 묵자. 줄바꿈 `\n` 은 그대로 점자 줄바꿈이 된다. 인라인 태그(5.1)를 받는다 | 늘 |
| `force_roman` | `bool` | `False` | 한글이 하나도 없는 조각에도 로마자표 `⠴` 를 붙인다 | 머리말·꼬리말처럼 로마자만 있는 줄을 한국어 점자 책 안에 따로 적을 때. 본문에서는 끈다. 한글과 섞인 로마자에는 어차피 붙는다 |
| `qnum_period` | `bool` | `True` | 줄머리 문항 번호(`1 `) 뒤에 마침표 `⠲` 를 넣는 관행을 쓴다 | 시각 자료 설명처럼 줄머리 숫자가 문항 번호가 아닐 때 끈다 |

- **반환**: 점자 문자열. 논리 줄은 `\n` 으로 잇는다. 32칸으로 접지 않는다. 빈 입력은 `""`.
- **예외**: `text` 가 문자열이 아니면 `TypeError`.
- **보는 곳**: 한글 점자 제1장·제2장(자모·약자, `braillify` 가 한다) · 제29항(로마자표) · 제40항(수표) · 제49항(문장 부호) · 수학 점자 제11항(수식 앞뒤 두 칸).

```
>>> translate_tagged_text('수학 점수가 3점 올랐다.')
'⠠⠍⠚⠁⠀⠨⠎⠢⠠⠍⠫⠀⠼⠉⠨⠎⠢⠀⠥⠂⠐⠣⠌⠊⠲'
>>> translate_tagged_text('방정식 <!수식>x+1=3<!/수식>의 해')
'⠘⠶⠨⠻⠠⠕⠁⠀⠀⠭⠢⠼⠁⠒⠒⠼⠉⠀⠀⠺⠀⠚⠗'
>>> translate_tagged_text('DNA')
'⠠⠠⠙⠝⠁'
>>> translate_tagged_text('DNA', force_roman=True)
'⠴⠠⠠⠙⠝⠁'
>>> translate_tagged_text('1 다음 중 옳은 것은?')
'⠼⠁⠲⠀⠊⠣⠪⠢⠀⠨⠍⠶⠀⠥⠂⠴⠵⠀⠸⠎⠵⠦'
>>> translate_tagged_text('1 다음 중 옳은 것은?', qnum_period=False)
'⠼⠁⠀⠊⠣⠪⠢⠀⠨⠍⠶⠀⠥⠂⠴⠵⠀⠸⠎⠵⠦'
>>> translate_tagged_text('첫째 줄\n둘째 줄')
'⠰⠎⠄⠠⠨⠗⠀⠨⠯\n⠊⠯⠠⠨⠗⠀⠨⠯'
```

둘째 예의 수식 앞뒤 `⠀⠀` 는 수학 점자 제11항("수식과 수학적 표기는 앞뒤를 두 칸씩 띄어 쓴다")을 따른 것이다.

#### `translate_body(text) -> tuple[list[str], list[list[int]]]`

본문 요소 하나를 논리 줄별 점자와 줄별 줄바꿈 자리로 옮긴다. 본문·제목·목록·캡션을 옮길 때의 정본 입구다. `translate_with_breaks(text)` 를 기본 인자로 부른 것과 같다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `text` | `str` | 없음 | 요소 하나의 묵자. 줄바꿈은 `\n` | 늘 |

- **반환**: `(lines, breaks)`.
  - `lines: list[str]` 는 논리 줄마다 점자 한 줄이다. 32칸으로 접지 않았다.
  - `breaks: list[list[int]]` 는 `lines` 와 같은 길이다. `breaks[i]` 는 i번째 줄에서 줄을 바꿔도 되는 자리의 목록이다. 값 `b` 는 "`lines[i][b]` 앞에서 끊어도 된다" 는 뜻이고, 음절 경계와 빈칸 자리가 들어 있다. 오름차순이다.
- **예외**: `text` 가 문자열이 아니면 `TypeError`.
- **보는 곳**: 「점자 도서 제작 지침」 1장 2절 1(줄바꿈), 「점자 자료 제작 지침」 2.1.1(2)(한글은 음절 단위로 줄을 바꾼다).

```
>>> translate_body('DNA 지문은 1985년에 처음 쓰였다.')
(['⠴⠠⠠⠙⠝⠁⠲⠀⠨⠕⠑⠛⠵⠀⠼⠁⠊⠓⠑⠀⠉⠡⠝⠀⠰⠎⠪⠢⠀⠠⠠⠪⠱⠌⠊⠲'], [[7, 10, 12, 13, 14, 19, 22, 23, 24, 26, 28, 29, 32, 34]])
>>> translate_body('첫째 줄\n둘째 줄')
(['⠰⠎⠄⠠⠨⠗⠀⠨⠯', '⠊⠯⠠⠨⠗⠀⠨⠯'], [[3, 6, 7], [2, 5, 6]])
```

32칸으로 접을 때는 32칸 안에서 가장 먼 자리에서 끊는다. 접는 함수는 8.5 에 있다.

#### `translate_with_breaks(text, *, force_roman=False, qnum_period=True) -> tuple[list[str], list[list[int]]]`

`translate_body` · `translate_visual` · `translate_plain` 이 모두 부르는 속 함수다. 인자는 `translate_tagged_text` 와 같고, 반환은 `translate_body` 와 같다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `text` | `str` | 없음 | 묵자 | 늘 |
| `force_roman` | `bool` | `False` | 4.1 `translate_tagged_text` 와 같다 | 같다 |
| `qnum_period` | `bool` | `True` | 같다 | 같다 |

- **언제 쓰나**: 위 세 입구가 맞지 않아 인자를 직접 정해야 할 때만 쓴다.
- **예외**: `text` 가 문자열이 아니면 `TypeError`.

```
>>> translate_with_breaks('DNA 검사')
(['⠴⠠⠠⠙⠝⠁⠲⠀⠈⠎⠢⠇'], [[7, 11]])
>>> translate_with_breaks('1 세포 분열', qnum_period=False)
(['⠼⠁⠀⠠⠝⠙⠥⠀⠘⠛⠳'], [[2, 3, 7]])
```

첫째 예에서 11 은 `검|사` 의 음절 경계다. 한글이 섞인 줄이라 `force_roman` 없이도 로마자표 `⠴` 와 종료표 `⠲` 가 붙었다.

#### `translate_visual(text) -> tuple[list[str], list[list[int]]]`

그림·그래프·도표 같은 시각 자료의 **설명 글** 하나를 옮긴다. `translate_body` 와 다른 점은 문항 번호 마침표 관행을 끈다(`qnum_period=False`)는 것 하나다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `text` | `str` | 없음 | 시각 자료 설명·전사 한 덩어리 | 설명 글의 줄머리 숫자가 문항 번호가 아닐 때 |

- **반환·예외**: `translate_body` 와 같다.

```
>>> translate_visual('1 세포 분열 과정')
(['⠼⠁⠀⠠⠝⠙⠥⠀⠘⠛⠳⠀⠈⠧⠨⠻'], [[2, 3, 7, 11]])
>>> translate_body('1 세포 분열 과정')
(['⠼⠁⠲⠀⠠⠝⠙⠥⠀⠘⠛⠳⠀⠈⠧⠨⠻'], [[3, 4, 6, 8, 9, 11, 12, 13, 15]])
```

#### `translate_plain(text) -> str`

짧은 글을 점자 문자열 하나로 옮긴다. `translate_with_breaks(text, force_roman=True)` 의 줄을 `\n` 으로 이은 것이다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `text` | `str` | 없음 | 짧은 묵자. 여러 줄이면 줄을 지킨다 | 머리말·꼬리말·쪽 제목처럼 본문과 따로 적는 짧은 줄 |

- **반환**: 점자 문자열. 빈 입력이나 빈칸뿐인 입력은 `""`.
- **예외**: `text` 가 문자열이 아니면 `TypeError`.
- **보는 곳**: 「점자 도서 제작 지침」 [예 1-8]. 그 예의 페이지행에 적힌 `머리말`(`⠑⠎⠐⠕⠑⠂`)과 아래 첫째 예가 같다.

```
>>> translate_plain('머리말')
'⠑⠎⠐⠕⠑⠂'
>>> translate_plain('Part 2')
'⠴⠠⠐⠏⠀⠼⠃'
>>> translate_plain('   ')
''
```

#### `sanitize_for_braille(text) -> str`

점자로 옮길 수 없는 글자를 걷어 내거나 받아들이는 꼴로 바꾼다. 점역 함수가 안에서 이미 부르므로, 점역 전에 입력을 미리 살펴볼 때만 따로 부른다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `text` | `str` | 없음 | 묵자 | PDF 에서 뽑은 글처럼 글꼴 전용 영역(PUA) 글자·전각 부호·점 이음선이 섞인 입력을 미리 볼 때 |

- **하는 일**: 제어 문자와 옮길 수 없는 글꼴 전용 글자(U+E000~U+F8FF 가운데 `braillify` 가 모르는 것)를 빈칸으로 바꾼다. 전각 문장 부호를 반각으로 바꾼다. 점 이음선(`······`)을 빈칸으로 바꾸되 규정 줄임표는 둔다.
- **반환**: 바꾼 문자열.

```
>>> sanitize_for_braille('（가）')
'(가)'
>>> sanitize_for_braille('제1장 ······ 12')
'제1장   12'
>>> sanitize_for_braille('x')
' x'
```

### 4.2 수식

#### `convert_latex(latex) -> str` · `semojum_braille.kor_math_rules`

LaTeX 수식 하나를 수학 점자로 옮긴다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `latex` | `str` | 없음 | LaTeX 수식. `$` 없이 넣는다 | 수식만 따로 옮길 때. 글 속 수식은 `<!수식>` 태그로 감싸 4.1 함수에 넣으면 이 함수를 거친다 |

- **반환**: 점자 문자열.
- **예외**: `latex` 가 `None` 이면 `AttributeError`. 괄호가 덜 닫힌 식도 예외 없이 옮기지만 결과가 온전하지 않다(`\frac{1}{` → `⠌⠼⠁`).
- **보는 곳**: 수학 점자 제1장~제9장. 어느 구조에 어느 조항을 다는지는 9절.

```
>>> convert_latex('\\frac{1}{2}')
'⠼⠃⠌⠼⠁'
>>> convert_latex('x^2+2x+1=0')
'⠭⠘⠼⠃⠢⠼⠃⠭⠢⠼⠁⠒⠒⠼⠚'
>>> convert_latex('\\sqrt{2}')
'⠜⠼⠃'
```

분수는 분모를 먼저 적는다(`⠼⠃⠌⠼⠁` 은 2분의 1).

#### `wrap(text) -> str` · `semojum_braille.inline_math`

구분자 없이 글에 섞인 평문 수식(`x+1=3` 등)을 찾아 `<!수식>…<!/수식>` 로 감싼다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `text` | `str` | 없음 | 본문 | 수식에 태그가 안 붙은 글을 옮기기 전. 이미 태그가 붙은 구간은 그대로 둔다 |

- **반환**: 태그를 넣은 문자열.

```
>>> inline_math.wrap('x+1=3일 때 x의 값을 구하시오.')
'<!수식>x+1=3<!/수식>일 때 x의 값을 구하시오.'
>>> inline_math.wrap('<!수식>x+1=3<!/수식>일 때')
'<!수식>x+1=3<!/수식>일 때'
```

첫째 예에서 두 번째 `x` 는 감싸지 않았다. 이 예처럼 글자 하나만 홀로 선 것은 수식으로 보지 않는다.

#### `normalize(span) -> str` · `semojum_braille.inline_math`

평문 수식 표기를 `convert_latex` 가 아는 LaTeX 로 맞춘다. 함수 이름은 명령으로(`cos` → `\cos`), 유니코드 위·아래 첨자는 `^{}`·`_{}` 로 바꾼다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `span` | `str` | 없음 | 평문 수식 한 토막 | `convert_latex` 에 넣기 전 평문 표기를 정리할 때 |

```
>>> inline_math.normalize('cos x')
'\\cos x'
>>> inline_math.normalize('x²+y²')
'x^{2}+y^{2}'
```

### 4.3 영어 · `semojum_braille.eng_braille`

국어 문장 속 영어 구간을 영어 점자 약자(Grade 2)로 옮긴다. 로마자표·종료표는 붙이지 않는다(그건 4.1 함수가 붙인다).

#### `translate(text, ebae=False) -> str`

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `text` | `str` | 없음 | 영어 구간. 낱말 밖 글자(빈칸·문장 부호)는 그대로 둔다 | 영어 구간만 따로 옮길 때 |
| `ebae` | `bool` | `False` | 옛 영어 점자(EBAE)의 낱말 끝 약자를 쓴다 | 옛 영어 점자로 만든 책을 되짚어 견줄 때만. 새로 옮길 때는 끈다(통일영어점자가 기본) |

- **반환**: 점자 문자열. 빈칸은 공백(` `)으로 남는다.
- **예외**: `text` 가 문자열이 아니면 `TypeError`.
- **보는 곳**: 한글 점자 제4장(로마자와 그리스 문자, 제28항~제39항), 「통일영어점자 규정」.

```
>>> eng_braille.translate('The children are playing.')
'⠠⠮ ⠡⠝ ⠜⠑ ⠏⠇⠁⠽⠬.'
>>> eng_braille.translate('nation')
'⠝⠁⠰⠝'
>>> eng_braille.translate('nation', ebae=True)
'⠝⠠⠝'
```

같은 입력을 되풀이해 부르므로 결과를 캐시한다(`functools.lru_cache`, 4,096개).

#### `translate_word(word, ebae=False) -> str`

영어 낱말 하나를 옮긴다. 전부 대문자인 낱말(약어·단위)은 약자를 쓰지 않고 글자 그대로 적으며 대문자 단어표 `⠠⠠` 를 앞세운다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `word` | `str` | 없음 | 낱말 하나 | 낱말 단위로 옮길 때 |
| `ebae` | `bool` | `False` | `translate` 와 같다 | 같다 |

```
>>> eng_braille.translate_word('children')
'⠡⠝'
>>> eng_braille.translate_word('ATP')
'⠠⠠⠁⠞⠏'
```

#### `iter_words(text) -> Iterator[str]`

`translate` 가 약자를 적용하는 단위 그대로 영어 낱말을 뽑는다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `text` | `str` | 없음 | 글 | 영어 약자가 어느 낱말에 걸리는지 셀 때 |

```
>>> list(eng_braille.iter_words("I can't go, OK?"))
['I', "can't", 'go', 'OK']
```

### 4.4 특수 기호 · `semojum_braille.symbol_rules`

#### `substitute_symbols(text) -> str`

기호표(`symbol_table.json`)로 특수 기호를 점자로 바로 바꾼다. 다른 글자는 그대로 둔다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `text` | `str` | 없음 | 글 | 기호 하나가 어떤 점형이 되는지 볼 때. 글 전체는 4.1 함수가 이 표를 써서 옮긴다 |

```
>>> symbol_rules.substitute_symbols('→')
'⠒⠕'
>>> symbol_rules.substitute_symbols('※ 참고')
'⠐⠔ 참고'
```

#### `symbol_rule_spans(source_text, braille) -> list[tuple[int, int, str]]`

규정과 관행이 갈려 점역사가 판단할 기호가 점자 어디에 나왔는지 찾는다. 원문에 실제로 있는 기호만 본다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `source_text` | `str` | 없음 | 점역 전 묵자 | 검토 화면에서 "이 기호는 확인이 필요하다" 를 표시할 때 |
| `braille` | `str` | 없음 | 그 묵자를 옮긴 점자 | 같다 |

- **반환**: `(시작, 끝, 조항 번호)` 목록. 좌표는 `braille` 안의 문자 오프셋이다. 판단이 갈리지 않는 기호(괄호·쌍점 등)는 넣지 않는다.

```
>>> symbol_rules.symbol_rule_spans('물의 온도는 30°C이다.', '⠑⠯⠺⠀⠷⠊⠥⠉⠵⠀⠼⠉⠚⠴⠙⠴⠠⠉⠲⠕⠊⠲')
[(13, 15, 'MCST-한글-6.14.69')]
>>> symbol_rules.symbol_rule_spans('각 α의 크기', '⠫⠁⠀⠨⠁⠺⠀⠋⠪⠈⠕')
[(3, 5, 'MCST-한글-4.10.30')]
```

### 4.5 요소 점역 클래스

문서를 요소(본문 한 문단, 수식 하나, 표 하나, 그림 하나) 단위로 옮기는 클래스다. 모두 같은 꼴이다.

```python
Klass().translate(optimized: list[LLMOutput]) -> list[BrailleOutput]
```

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `optimized` | `list[LLMOutput]` | 없음 | 요소 입력 목록. `LLMOutput` 필드는 5.3 | 요소마다 규정 근거(`rule_trail`)와 줄바꿈 자리를 함께 받고 싶을 때, 또 4.7 조판에 넣을 때 |

- **반환**: 입력과 같은 차례, 같은 길이의 `BrailleOutput` 목록(5.3).
- **예외**: 한 요소가 실패하면 그 요소의 `braille_lines` 가 `[처리 불가: …]` 자리표시가 되고 나머지 요소는 계속 옮긴다. 이때 표준오류에 경고가 한 줄 찍힌다. `LLMOutput` 을 만들 때 필수 필드가 빠지면 pydantic `ValidationError` 가 난다.

| 클래스 | 모듈 | 읽는 `LLMOutput` 필드 | 하는 일 |
|---|---|---|---|
| `TextBraille` | `text_braille` | `corrected_text` | 본문·제목·목록·캡션. 점역자 주·글상자·빈칸·드러냄표 자리를 근거로 남긴다 |
| `FormulaBraille` | `formula_braille` | `corrected_text`(LaTeX) | 수식 요소. 분수·근호·첨자 같은 구조를 근거로 남긴다 |
| `TableBraille` | `table_braille` | `corrected_text`(행은 줄, 칸은 `\|`, 또는 `<!표>` 태그) · `render_mode` · `tn_text` · `nested_text` | 표. 조판 다섯 안을 모두 만들어 `drafts` 에 담고 `render_mode` 에 맞는 안을 고른다 |
| `VisualBraille` · `ImageBraille` · `ChartGraphBraille` | `visual_braille` | `corrected_text` 또는 `drafts` · `selected_idx` · `line_indents` | 그림·그래프 설명. 초안이 여럿이면 초안마다 옮긴다 |
| `DiagramBraille` | `visual_braille` | 같다 | 개념도·흐름도. 줄별 들여쓰기(`line_indents`)를 가진 골격 하나를 낸다 |
| `CartoonBraille` | `visual_braille` | 같다 | 만화. 장면·대사 들여쓰기 골격(`line_indents`)을 따른다 |

`TableBraille` 의 조판 안: `unfold`(풀어쓰기, 기본) · `table_grid`(테두리+구분선) · `transposed`(행과 열 바꿈) · `linear`(테두리만) · `numbered`(번호 체계). `render_mode` 가 이 가운데 없으면 `unfold` 를 고른다. `|` 도 `<!표>` 태그도 없는 글은 표가 아니라고 보고, `tn_text`(없으면 글 자체)를 글로 옮긴 한 안만 낸다.

**보는 곳**: 「점자 도서 제작 지침」 1장 2절 5(글상자) · 6(점역자 주), 3장 1절(표), 한글 점자 제56항(드러냄표) · 제73항(빈칸). 조항은 요소의 `rule_trail` 에 담긴다(9절).

예 1, 본문:

```
>>> from semojum_braille.schemas import LLMOutput
>>> bo = TextBraille().translate([LLMOutput(element_id=uuid.UUID(int=1), corrected_text="대한민국의 모든 국민은 법 앞에 평등하다.", routing_tier="ZERO")])[0]
>>> bo.braille_lines
['⠊⠗⠚⠒⠑⠟⠈⠍⠁⠺⠀⠑⠥⠊⠵⠀⠈⠍⠁⠑⠟⠵⠀⠘⠎⠃⠀⠣⠲⠝⠀⠙⠻⠊⠪⠶⠚⠊⠲']
>>> bo.break_points
[[2, 4, 6, 9, 10, 11, 13, 15, 16, 19, 21, 22, 23, 26, 27, 29, 30, 31, 33, 36, 37]]
>>> bo.rule_trail
[]
```

예 2, 점역자 주가 든 본문. 근거가 점자 좌표와 함께 붙는다:

```
>>> bo2 = TextBraille().translate([LLMOutput(element_id=uuid.UUID(int=2), corrected_text="<!주>그림 설명<!/주> 다음 글을 읽고", routing_tier="ZERO")])[0]
>>> bo2.braille_lines
['⠠⠄⠈⠪⠐⠕⠢⠀⠠⠞⠑⠻⠠⠄⠀⠊⠣⠪⠢⠀⠈⠮⠮⠀⠕⠂⠁⠈⠥']
>>> [(r.rule_id, r.rule_name, r.line_no, r.col_start, r.col_end) for r in bo2.rule_trail]
[('NLD-1.2.6', '점역자 주', 0, 0, 2), ('NLD-1.2.6', '점역자 주', 0, 12, 14)]
```

예 3, 수식:

```
>>> fb = FormulaBraille().translate([LLMOutput(element_id=uuid.UUID(int=3), corrected_text="\\frac{a}{b}+\\sqrt{2}", routing_tier="ZERO")])[0]
>>> fb.braille_lines
['⠃⠌⠁⠢⠜⠼⠃']
>>> [r.rule_id for r in fb.rule_trail]
['MCST-수학-1.7', 'MCST-수학-2.22']
>>> fb2 = FormulaBraille().translate([LLMOutput(element_id=uuid.UUID(int=4), corrected_text="x^2-4=0", routing_tier="ZERO")])[0]
>>> fb2.braille_lines
['⠭⠘⠼⠃⠔⠼⠙⠒⠒⠼⠚']
```

예 4, 표. 기본은 풀어쓰기이고 `render_mode` 로 다른 안을 고른다:

```
>>> t = TableBraille().translate([LLMOutput(element_id=uuid.UUID(int=5), corrected_text="이름 | 나이\n철수 | 10\n영희 | 11", routing_tier="ZERO")])[0]
>>> t.selected_idx, [d.render_mode for d in t.drafts]
(0, ['unfold', 'table_grid', 'transposed', 'linear', 'numbered'])
>>> t.braille_lines
['⠀⠀⠕⠐⠪⠢⠀⠀⠉⠣⠕', '⠀⠀⠰⠞⠠⠍⠀⠀⠼⠁⠚', '⠀⠀⠻⠚⠺⠀⠀⠼⠁⠁']
>>> t2 = TableBraille().translate([LLMOutput(element_id=uuid.UUID(int=6), corrected_text="이름 | 나이\n철수 | 10\n영희 | 11", routing_tier="ZERO", render_mode="table_grid")])[0]
>>> t2.selected_idx, t2.braille_lines
(1, ['⠿⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠿', '⠀⠀⠕⠐⠪⠢⠀⠀⠉⠣⠕', '⠐⠐⠐⠐⠐⠐⠐⠐⠐⠐⠐⠐⠐⠐⠐⠐⠐⠐⠐⠐⠐⠐⠐⠐⠐⠐⠐⠐⠐⠐⠐⠐', '⠀⠀⠰⠞⠠⠍⠀⠀⠼⠁⠚', '⠀⠀⠻⠚⠺⠀⠀⠼⠁⠁', '⠿⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠿'])
```

예 5, 시각 자료. 초안 둘 가운데 `selected_idx` 의 것이 `braille_lines` 가 된다:

```
>>> v = VisualBraille().translate([LLMOutput(element_id=uuid.UUID(int=7), corrected_text="", routing_tier="ZERO", drafts=[
...     Draft(option=1, text="세포 분열 그림", label="짧은 제목"),
...     Draft(option=2, text="세포가 둘로 나뉘는 과정을 네 단계로 그렸다.", label="줄글")], selected_idx=1)])[0]
>>> v.selected_idx, v.braille_lines
(1, ['⠠⠝⠙⠥⠫⠀⠊⠯⠐⠥⠀⠉⠉⠍⠗⠉⠵⠀⠈⠧⠨⠻⠮⠀⠉⠝⠀⠊⠒⠈⠌⠐⠥⠀⠈⠪⠐⠱⠌⠊⠲'])
>>> [(d.option, d.label, d.braille_lines) for d in v.drafts]
[(1, '짧은 제목', ['⠠⠝⠙⠥⠀⠘⠛⠳⠀⠈⠪⠐⠕⠢']), (2, '줄글', ['⠠⠝⠙⠥⠫⠀⠊⠯⠐⠥⠀⠉⠉⠍⠗⠉⠵⠀⠈⠧⠨⠻⠮⠀⠉⠝⠀⠊⠒⠈⠌⠐⠥⠀⠈⠪⠐⠱⠌⠊⠲'])]
>>> dg = DiagramBraille().translate([LLMOutput(element_id=uuid.UUID(int=8), corrected_text="생물\n동물\n식물", routing_tier="ZERO", line_indents=[0, 2, 2])])[0]
>>> dg.braille_lines, dg.line_indents
(['⠠⠗⠶⠑⠯', '⠊⠿⠑⠯', '⠠⠕⠁⠑⠯'], [0, 2, 2])
```

들여쓰기(`line_indents`)는 여기서 줄에 붙이지 않고 4.7 조판이 붙인다.

#### `content_rules(source, lines) -> list[RuleApplication]` · `semojum_braille.text_braille`

요소 내용에 붙일 포괄 규정 근거를 낸다. **지금은 늘 빈 목록을 돌려준다.** 수표·문장 부호처럼 고를 여지가 없는 근거는 달지 않기로 해서 비웠고, 표 내용 근거가 생기면 이 자리에 붙인다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `source` | `str` | 없음 | 묵자 | 지금은 부를 까닭이 없다 |
| `lines` | `list[str]` | 없음 | 점자 줄 | 같다 |

```
>>> content_rules('가', ['⠫'])
[]
```

### 4.6 표 도우미 · `semojum_braille.table_braille`

#### `build_table_tags(rows) -> str`

행렬을 `<!표><!행><!칸>` 태그 글로 만든다. `TableBraille` 의 입력으로 쓴다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `rows` | `list[list[str]]` | 없음 | 행마다 칸 목록 | 칸 글에 `\|` 가 들어 있어 `\|` 구분 입력을 못 쓸 때 |

```
>>> build_table_tags([['이름', '나이'], ['철수', '10']])
'<!표>\n<!행><!칸>이름<!칸>나이<!/행>\n<!행><!칸>철수<!칸>10<!/행>\n<!/표>'
```

#### `parse_table_tags(text) -> list[list[str]] | None`

`<!표>` 태그 글을 행렬로 되돌린다. 태그가 없으면 `None`.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `text` | `str` | 없음 | 태그 글 | 태그 글을 고치거나 검사할 때 |

```
>>> parse_table_tags('<!표>\n<!행><!칸>이름<!칸>나이<!/행>\n<!행><!칸>철수<!칸>10<!/행>\n<!/표>')
[['이름', '나이'], ['철수', '10']]
>>> print(parse_table_tags('이름 | 나이'))
None
```

#### `print_layout(corrected_text, mode) -> str`

표 조판 안이 묵자로 어떻게 배치되는지 보여 준다. 점역사가 안을 고를 때 곁에 두는 미리보기다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `corrected_text` | `str` | 없음 | `\|` 구분 표 글 | 표 안을 사람에게 보여 줄 때 |
| `mode` | `str` | 없음 | `unfold` · `table_grid` · `transposed` · `linear` · `numbered` | 같다 |

```
>>> print_layout('이름 | 나이\n철수 | 10', 'linear')
'┌\n이름  나이\n철수  10\n└'
>>> print_layout('이름 | 나이\n철수 | 10', 'transposed')
'[점역자 주] 행과 열을 바꾸어 표기함\n┌\n이름: 철수\n├\n나이: 10\n└'
```

### 4.7 조판 · `semojum_braille.layout_braille`

4.5 클래스가 낸 `BrailleOutput` 목록을 쪽(32칸 × 26줄)으로 조판한다. 제목 단계별 들여쓰기·가운데 정렬, 문단 들여쓰기, 제목 앞뒤 빈 줄, 쪽 번호 줄을 넣는다.

**`layout_result` 인자**(아래 함수들이 같이 받는다): `elements` 속성을 가진 아무 객체면 된다. 엔진은 요소마다 `element_id` · `type` · `reading_order` · `heading_level` 넷만 읽는다. `type` 은 `text` · `title` · `list_item` · `caption` 등, `heading_level` 은 0(본문) 또는 1~4(제목 단계)다. 넘기지 않아도 예외는 안 나지만 요소 종류와 제목 단계를 모른 채 본문으로 조판한다.

⚠ **`render` · `layout` · `render_page_text` 는 넘긴 `BrailleOutput` 을 제자리에서 고친다**(조판한 줄을 `braille_lines` 에 되써 넣는다). 같은 객체를 두 번 넣으면 들여쓰기가 두 번 걸린다. 다시 조판하려면 4.5 클래스로 새로 만든다. `flatten_elements` 는 고치지 않는다.

아래 예는 제목(2단계) 하나와 본문 하나를 쓴다. `make_bos()` 는 부를 때마다 두 요소를 새로 옮기고, `lr` 은 두 요소의 종류와 제목 단계를 담은 `layout_result` 다.

```python
def make_bos():
    return TextBraille().translate([
        LLMOutput(element_id=uuid.UUID(int=11), corrected_text="1 국어의 탐구와 활용", routing_tier="ZERO"),
        LLMOutput(element_id=uuid.UUID(int=12), routing_tier="ZERO",
                  corrected_text="대한민국의 모든 국민은 법 앞에 평등하며, 누구든지 성별이나 종교 때문에 차별받지 아니한다.")])


lr = SimpleNamespace(elements=[
    SimpleNamespace(element_id=uuid.UUID(int=11), type="title", reading_order=0, heading_level=2),
    SimpleNamespace(element_id=uuid.UUID(int=12), type="text", reading_order=1, heading_level=0)])
```

#### `flatten_elements(braille_outputs, layout_result=None) -> dict[UUID, FlatElement]`

요소마다 **32칸으로 접지 않은** 통 문자열을 만든다. 들여쓰기·가운데 여백·앞뒤 빈 줄까지 넣은 글이다. 화면이 줄을 접는 편집기처럼, 쪽 나눔을 부르는 쪽이 하는 경우에 쓴다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `braille_outputs` | `list[BrailleOutput]` | 없음 | 4.5 의 출력 | 늘 |
| `layout_result` | 위 설명 | `None` | 요소 종류·제목 단계 | 제목·목록이 섞여 있을 때는 꼭 넘긴다 |

- **반환**: 요소 id → `FlatElement`. `FlatElement` 는 `text` · `trail` · `prefix` · `suffix` · `draft_texts` 다섯 필드를 가진 튜플이다. `text` 는 `prefix + 본문 + suffix` 이고, `prefix`·`suffix` 는 앞뒤 빈 줄이다. 요소들의 `text` 를 그냥 이어 붙이면 지침대로 빈 줄이 들어간 문서가 된다. `trail` 은 이 통 문자열 좌표로 옮긴 `rule_trail`, `draft_texts` 는 초안별 통 문자열이다.
- **예외**: 없다. 빈 목록은 `{}`.

```
>>> flat = flatten_elements(make_bos(), lr)
>>> flat[uuid.UUID(int=11)]
FlatElement(text='\n⠀⠀⠀⠀⠀⠀⠼⠁⠲⠀⠈⠍⠁⠎⠺⠀⠓⠢⠈⠍⠧⠀⠚⠧⠂⠬⠶\n\n', trail=[], prefix='\n', suffix='\n\n', draft_texts=())
>>> flat[uuid.UUID(int=12)].text
'⠀⠀⠊⠗⠚⠒⠑⠟⠈⠍⠁⠺⠀⠑⠥⠊⠵⠀⠈⠍⠁⠑⠟⠵⠀⠘⠎⠃⠀⠣⠲⠝⠀⠙⠻⠊⠪⠶⠚⠑⠱⠐⠀⠉⠍⠈⠍⠊⠵⠨⠕⠀⠠⠻⠘⠳⠕⠉⠀⠨⠿⠈⠬⠀⠠⠊⠗⠑⠛⠝⠀⠰⠣⠘⠳⠘⠔⠨⠕⠀⠣⠉⠕⠚⠒⠊⠲\n'
>>> flatten_elements(make_bos())[uuid.UUID(int=11)].text   # layout_result 없이
'⠀⠀⠼⠁⠲⠀⠈⠍⠁⠎⠺⠀⠓⠢⠈⠍⠧⠀⠚⠧⠂⠬⠶\n'
```

2단계 제목은 7칸에서 시작한다(앞 빈칸 6). `layout_result` 없이 부르면 제목을 본문으로 보고 3칸에서 시작한다.

#### `LayoutBraille().render(braille_outputs, page_no, *, layout_result=None) -> tuple[list[list[str]], float]`

요소들을 쪽으로 조판한다. 파일은 쓰지 않는다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `braille_outputs` | `list[BrailleOutput]` | 없음 | 4.5 의 출력. 제자리에서 고쳐진다 | 늘 |
| `page_no` | `int` | 없음 | 쪽 번호 줄에 적을 번호 | 늘 |
| `layout_result` | 위 설명 | `None` | 요소 종류·제목 단계 | 제목·목록이 있을 때 |

- **반환**: `(pages, overflow_rate)`. `pages` 는 쪽마다 26줄 목록이고 마지막 줄이 쪽 번호 줄이다. `overflow_rate` 는 음절·빈칸 자리가 없어 32칸째에서 강제로 자른 줄의 비율(0.0~1.0)이다.

```
>>> pages, rate = LayoutBraille().render(make_bos(), page_no=1, layout_result=lr)
>>> len(pages), rate
(1, 0.0)
>>> pages[0][:6]
['⠀⠀⠀⠀⠀⠀⠼⠁⠲⠀⠈⠍⠁⠎⠺⠀⠓⠢⠈⠍⠧⠀⠚⠧⠂⠬⠶', '', '⠀⠀⠊⠗⠚⠒⠑⠟⠈⠍⠁⠺⠀⠑⠥⠊⠵⠀⠈⠍⠁⠑⠟⠵⠀⠘⠎⠃⠀⠣⠲⠝', '⠙⠻⠊⠪⠶⠚⠑⠱⠐⠀⠉⠍⠈⠍⠊⠵⠨⠕⠀⠠⠻⠘⠳⠕⠉⠀⠨⠿⠈⠬⠀', '⠠⠊⠗⠑⠛⠝⠀⠰⠣⠘⠳⠘⠔⠨⠕⠀⠣⠉⠕⠚⠒⠊⠲', '']
>>> pages[0][-1]
'⠀⠀⠀⠀⠀⠀⠀⠼⠁⠲⠀⠈⠍⠁⠎⠺⠀⠓⠢⠈⠍⠧⠀⠚⠧⠂⠬⠶⠀⠀⠼⠁'
>>> long = TextBraille().translate([LLMOutput(element_id=uuid.UUID(int=13), corrected_text="가나다라마바사아자차카타파하 " * 80, routing_tier="ZERO")])
>>> lp, lrate = LayoutBraille().render(long, page_no=3)
>>> len(lp), [len(p) for p in lp], lrate
(2, [26, 26], 0.0)
```

첫째 예의 마지막 줄은 쪽 번호 줄이다. 이 예에서는 제목 글과 쪽 번호 `⠼⠁` 이 들어 있다. 같은 객체를 한 번 더 조판하면 제목이 한 번 더 들여 써진다(위 ⚠):

```
>>> bos = make_bos()
>>> _ = LayoutBraille().render(bos, page_no=1, layout_result=lr)
>>> again, _ = LayoutBraille().render(bos, page_no=1, layout_result=lr)
>>> again[0][0]
'⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠁⠲⠀⠈⠍⠁⠎⠺⠀⠓⠢⠈'
```

#### `LayoutBraille().layout(braille_outputs, page_no, job_id, *, layout_result=None) -> float`

`render` 와 같이 조판하고 결과를 파일로 쓴다. 반환은 `render` 의 `overflow_rate` 다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `braille_outputs` | `list[BrailleOutput]` | 없음 | `render` 와 같다 | 늘 |
| `page_no` | `int` | 없음 | 쪽 번호. 파일 이름에도 들어간다 | 늘 |
| `job_id` | `str` | 없음 | 작업 이름. 저장 폴더 이름이 된다 | 늘 |
| `layout_result` | 위 설명 | `None` | `render` 와 같다 | 같다 |

- **쓰는 곳**: **지금 작업 폴더 아래** `storage/jobs/{job_id}/temp/page_{page_no:03d}/result/` 에 `{page_no:03d}_result.txt` 와 `{page_no:03d}_result.brf` 를 쓴다. 두 파일의 내용은 같고 둘 다 UTF-8 유니코드 점자다(ASCII 점자 BRF 가 아니다).
- **예외**: 폴더를 만들거나 쓸 수 없으면 `OSError`.

```
>>> import pathlib, tempfile
>>> os.chdir(tempfile.mkdtemp())
>>> LayoutBraille().layout(make_bos(), page_no=1, job_id='demo', layout_result=lr)
0.0
>>> sorted(str(f) for f in pathlib.Path('storage').rglob('*.*'))
['storage/jobs/demo/temp/page_001/result/001_result.brf', 'storage/jobs/demo/temp/page_001/result/001_result.txt']
>>> pathlib.Path('storage/jobs/demo/temp/page_001/result/001_result.txt').read_text(encoding='utf-8').split('\n') == [ln for p in pages for ln in p]
True
```

#### `LayoutBraille().finalize(blocks, page_no=1) -> list[list[str]]`

이미 32칸 줄로 된 블록(점역사가 고친 결과 등)을 쪽으로 조립한다. 점역은 다시 하지 않는다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `blocks` | `list[dict]` | 없음 | 블록마다 `{"type", "heading_level", "order", "lines"}`. `lines` 는 32칸 이하 점자 줄 목록, `order` 는 차례 | 사람이 고친 점자를 다시 쪽으로 묶을 때 |
| `page_no` | `int` | `1` | 쪽 번호 | 같다 |

- **반환**: 쪽마다 줄 목록. 제목 뒤 빈 줄과 쪽 번호 줄을 넣는다.

```
>>> blocks = [{"type": "title", "heading_level": 2, "order": 0, "lines": ["⠀⠀⠀⠀⠀⠀⠼⠁⠲⠀⠈⠍⠁⠎⠺⠀⠓⠢⠈⠍⠧⠀⠚⠧⠂⠬⠶"]},
...           {"type": "text", "heading_level": 0, "order": 1, "lines": ["⠀⠀⠊⠗⠚⠒⠑⠟⠈⠍⠁⠺⠀⠑⠥⠊⠵⠀⠈⠍⠁⠑⠟⠵⠀⠘⠎⠃⠀⠣⠲⠝", "⠙⠻⠊⠪⠶⠚⠊⠲"]}]
>>> fin = LayoutBraille().finalize(blocks, page_no=1)
>>> len(fin), fin[0][:5]
(1, ['⠀⠀⠀⠀⠀⠀⠼⠁⠲⠀⠈⠍⠁⠎⠺⠀⠓⠢⠈⠍⠧⠀⠚⠧⠂⠬⠶', '', '⠀⠀⠊⠗⠚⠒⠑⠟⠈⠍⠁⠺⠀⠑⠥⠊⠵⠀⠈⠍⠁⠑⠟⠵⠀⠘⠎⠃⠀⠣⠲⠝', '⠙⠻⠊⠪⠶⠚⠊⠲', ''])
>>> fin[0][-1]
'⠀⠀⠀⠀⠀⠀⠀⠼⠁⠲⠀⠈⠍⠁⠎⠺⠀⠓⠢⠈⠍⠧⠀⠚⠧⠂⠬⠶⠀⠀⠼⠁'
```

#### `render_page_text(braille_outputs, page_no, *, layout_result=None) -> list[list[str]]`

`LayoutBraille().render(...)[0]` 와 같다. 쪽 줄만 필요할 때 쓴다. 제자리에서 고치는 것도 같다.

```
>>> render_page_text(make_bos(), 1, layout_result=lr) == pages
True
```

#### `wordwrap_by_word() -> bool`

어절 단위 줄바꿈 스위치(`BRAILLE_WORDWRAP=word`, 6절)가 켜졌는지 돌려준다. 부를 때마다 환경 변수를 읽는다.

```
>>> wordwrap_by_word()
False
>>> os.environ["BRAILLE_WORDWRAP"] = "word"; wordwrap_by_word()
True
>>> del os.environ["BRAILLE_WORDWRAP"]
```

### 4.8 규정 근거 · `semojum_braille.regulations`

규정 조항표(`regulations.json`, 239조항)를 읽어 근거(`RuleApplication`)를 만든다. 184조항이 「한국 점자 규정」, 42조항이 「점자 도서 제작 지침」, 13조항이 「점자 자료 제작 지침」이다.

조항 번호 꼴: `MCST-한글-6.13.49`(한국 점자 규정 한글 편 제6장 제13절 제49항), `MCST-수학-1.7`(수학 편 제1장 제7항), `NLD-1.2.6`(도서 지침 1장 2절 6), `NISE-…`(자료 지침).

#### `make_rule(rule_id, *, line_no=-1, col_start=0, col_end=0, tag="", priority="primary") -> RuleApplication`

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `rule_id` | `str` | 없음 | 조항 번호 | 늘 |
| `line_no` | `int` | `-1` | 근거가 걸린 줄. -1 은 요소 전체 | 특정 줄에만 걸리는 근거일 때 |
| `col_start` · `col_end` | `int` | `0` | 그 줄 안의 칸 범위 | 같다 |
| `tag` | `str` | `""` | 화면 표시용 꼬리표. 비우면 조항의 기본 꼬리표 | 기본 꼬리표와 다르게 보일 때 |
| `priority` | `str` | `"primary"` | 근거의 무게 | 보조 근거로 달 때 |

- **예외**: 없는 조항이면 `KeyError`. 없는 조항을 근거로 다는 일을 막으려는 것이다.

```
>>> make_rule('NLD-1.2.6')
RuleApplication(rule_id='NLD-1.2.6', source='점자 도서 제작 지침', section='제1장. 점역의 일반 사항 · 제2절. 점자 자료의 기본 형식 · 6. 점역자 주', rule_name='점역자 주', contents='독자의 이해를 돕기 위해 추가적인 설명이 필요한 경우에는 점역자 주를 사용한다.', priority='primary', line_no=-1, col_start=0, col_end=0, tag='tn_open')
>>> make_rule('NLD-9.9.9')
Traceback (most recent call last):
  ...
KeyError: "rule_id 'NLD-9.9.9' not in regulations.json (댕글링 rule_id 금지 — regulations.json에 조항을 먼저 추가하라)"
```

#### `make_rule_at(rule_id, lines, start, end, *, tag="", priority="primary") -> RuleApplication`

점자 문자열 오프셋(`start`~`end`)을 요소 좌표(줄·칸)로 바꿔 `make_rule` 을 부른다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `rule_id` | `str` | 없음 | 조항 번호 | 늘 |
| `lines` | `list[str]` | 없음 | 요소의 점자 줄 | 줄을 `\n` 으로 이은 문자열 안의 오프셋을 알 때 |
| `start` · `end` | `int` | 없음 | 그 오프셋 범위 | 같다 |
| `tag` · `priority` | | | `make_rule` 과 같다 | |

```
>>> make_rule_at('NLD-1.2.6', ['⠠⠄⠈⠪⠐⠕⠢⠀⠠⠞⠑⠻⠠⠄'], 0, 2)
RuleApplication(rule_id='NLD-1.2.6', source='점자 도서 제작 지침', section='제1장. 점역의 일반 사항 · 제2절. 점자 자료의 기본 형식 · 6. 점역자 주', rule_name='점역자 주', contents='독자의 이해를 돕기 위해 추가적인 설명이 필요한 경우에는 점역자 주를 사용한다.', priority='primary', line_no=0, col_start=0, col_end=2, tag='tn_open')
```

#### `rule_meta(rule_id) -> dict | None` · `section_text(section) -> str` · `all_rule_ids() -> frozenset[str]`

| 함수 | 인자 | 반환 | 언제 쓰나 |
|---|---|---|---|
| `rule_meta` | `rule_id: str` | 조항 원본 메타(발행처·판·절 위계·본문). 없으면 `None` | 조항의 출처를 화면에 자세히 보일 때 |
| `section_text` | `section: dict[str, str]` | 절 위계를 ` · ` 로 이은 한 줄 | 위계를 한 줄로 보일 때 |
| `all_rule_ids` | 없음 | 등록된 조항 번호 전부 | 조항 번호가 유효한지 미리 볼 때 |

```
>>> rule_meta('NLD-1.2.6')
{'source': '점자 도서 제작 지침', 'publisher': '국립장애인도서관', 'version': 2025, 'section': {'Chapter': '제1장. 점역의 일반 사항', 'Section': '제2절. 점자 자료의 기본 형식', 'Paragraph': '6. 점역자 주'}, 'rule_name': '점역자 주', 'contents': '독자의 이해를 돕기 위해 추가적인 설명이 필요한 경우에는 점역자 주를 사용한다.', 'default_tag': 'tn_open'}
>>> section_text(rule_meta('NLD-1.2.6')['section'])
'제1장. 점역의 일반 사항 · 제2절. 점자 자료의 기본 형식 · 6. 점역자 주'
>>> len(all_rule_ids()), sorted(all_rule_ids())[:3]
(239, ['MCST-과학-1', 'MCST-과학-10', 'MCST-과학-11'])
```

---

## 5. 입출력 형식

### 5.1 입력 태그 문법

묵자만으로는 알 수 없는 것(점역자 주, 글상자, 빈칸 모양 등)을 인라인 태그로 알려 준다. 꼴은 `<!이름>…<!/이름>` 쌍이거나 `<!이름>` 홑이다. 태그는 점자 기호로 바뀌고 사라진다. 아래 출력은 모두 `translate_tagged_text` 의 실물이다.

| 태그 | 꼴 | 뜻 | 입력 → 출력 | 근거 |
|---|---|---|---|---|
| `주` | 쌍 | 점역자 주 | `<!주>그림 생략<!/주>` → `⠠⠄⠈⠪⠐⠕⠢⠀⠠⠗⠶⠐⠜⠁⠠⠄` | 도서 지침 1장 2절 6 |
| `강조` | 쌍 | 드러냄표·밑줄 강조 | `이것은 <!강조>매우<!/강조> 중요하다.` → `⠕⠸⠎⠵⠀⠠⠤⠑⠗⠍⠤⠄⠀⠨⠍⠶⠬⠚⠊⠲` | 제56항 |
| `굵은` | 쌍 | 굵은 글자 강조 | `<!굵은>주의<!/굵은> 사항` → `⠰⠤⠨⠍⠺⠤⠆⠀⠇⠚⠶` | 제56항 |
| `상자` · `상자끝` | 쌍 | 글상자 위 테두리(안에 제목) · 아래 테두리. 각각 제 줄에 둔다 | 아래 예 | 도서 지침 1장 2절 5 |
| `빈칸` | 홑 | 표 기입칸 | `빈칸: <!빈칸>` → `⠘⠟⠋⠒⠐⠂⠀⠿⠿` | 제73항 |
| `밑줄` | 홑 | 밑줄 빈칸 | `빈칸: <!밑줄>` → `⠘⠟⠋⠒⠐⠂⠀⠸⠤` | 제73항 |
| `네모` | 홑 | 네모 빈칸 | `빈칸: <!네모>` → `⠘⠟⠋⠒⠐⠂⠀⠸⠦⠀⠴⠇` | 제73항 |
| `네모글` | 쌍 | 네모 안에 든 글자 | `<!네모글>가<!/네모글> 항목` → `⠸⠦⠫⠴⠇⠀⠚⠶⠑⠭` | 제64항 |
| `수식` | 쌍 | LaTeX 수식 | `<!수식>x^2<!/수식>의 값` → `⠭⠘⠼⠃⠀⠀⠺⠀⠫⠃⠄` | 수학 점자 |
| `N칸` | 줄머리 홑 | 그 줄의 앞 빈칸 수(들여쓰기). 조판이 쓰고 점역 결과에는 안 남는다 | `<!2칸>둘째 단계` → `⠊⠯⠠⠨⠗⠀⠊⠒⠈⠌` | 도서 지침 2장 |
| `표` · `행` · `칸` | 쌍·홑 | 표 구조. **`TableBraille` 에만 넣는다**(4.6) | 글 점역 함수에 넣으면 태그가 빠지고 칸 글자가 붙어 버린다 | 도서 지침 3장 1절 |

글상자:

```
>>> translate_tagged_text('<!상자>생각해 보기<!/상자>\n본문\n<!상자끝><!/상자끝>')
'⠿⠛⠛⠛⠛⠀⠠⠗⠶⠫⠁⠚⠗⠀⠘⠥⠈⠕⠀⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠿\n⠘⠷⠑⠛\n⠿⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠿'
```

- **모르는 태그**는 태그만 지우고 안의 글은 옮긴다(`<!모름>사과<!/모름>` → `⠇⠈⠧`). 표준오류에 경고가 찍힐 수 있다.
- `⟦…⟧` 꼴 토막(24자 이하)은 형식 표시로 보고 지운다(`⟦글자⟧ 사과` → `⠀⠇⠈⠧`). 언어 모델이 만든 글에 섞여 드는 표시를 걸러 내려는 것이다.
- 태그 이름은 `tag_names.py` 에만 정의되어 있다. 옛 긴 이름(`점역자주` 등)은 받지 않는다.

### 5.2 점자 표기

- 점자는 유니코드 점자 블록(U+2800~U+28FF) 글자다. 점자 빈칸은 `⠀`(U+2800)이다. 보통 공백(U+0020)과 다르다. 영어 함수(4.3)와 기호 함수(4.4)는 점자가 아닌 글자를 건드리지 않으므로 빈칸이 공백으로 남는다.
- 줄은 `\n` 으로 잇는다. 글 점역 함수(4.1)는 32칸으로 접지 않는다. 32칸 × 26줄 쪽은 조판(4.7)이 만든다.
- ASCII 점자(BRF)는 쓰지 않는다. `layout` 이 쓰는 `.brf` 파일도 유니코드 점자다. ASCII 점자로 내보내려면 바깥에서 바꾼다.
- 파일은 모두 UTF-8 로 읽고 쓴다.

### 5.3 데이터 타입 · `semojum_braille.schemas`

pydantic 모델이다. 모두 키워드 인자로 만든다.

**`LLMOutput`** · 요소 하나의 입력. 이름은 이 엔진이 언어 모델 뒤 단계에서 쓰이던 데서 왔다. 모델 없이 직접 만들어 넣어도 된다.

| 필드 | 타입 | 기본값 | 뜻 |
|---|---|---|---|
| `element_id` | `UUID` | 필수 | 요소 id. 출력과 짝짓는 열쇠 |
| `corrected_text` | `str` | 필수 | 옮길 묵자(본문 글, LaTeX, 표 글, 시각 자료 설명) |
| `routing_tier` | `str` | 필수 | 처리 경로 이름. 엔진은 읽지 않으므로 아무 값(예 `"ZERO"`)이나 넣는다 |
| `render_mode` | `str` | `"text_only"` | 표 조판 안 등(4.5) |
| `tn_text` | `str \| None` | `None` | 표가 아닌 글을 표 자리에 넣을 때 쓸 점역자 주 글 |
| `drafts` | `list[Draft]` | `[]` | 시각 자료 초안들 |
| `selected_idx` | `int` | `0` | 고른 초안 번호 |
| `line_indents` | `list[int] \| None` | `None` | 줄별 앞 빈칸 수 |
| `nested_text` | `str \| None` | `None` | 표·그림 안에 든 그림 설명. 글상자로 덧붙인다 |
| `rule_trail` | `list[RuleApplication]` | `[]` | 앞 단계에서 이미 단 근거. 시각 자료 클래스만 출력 근거 앞에 이어 붙인다 |
| `processing_time_ms` | `int` | `0` | 엔진은 읽지 않는다 |

**`BrailleOutput`** · 요소 하나의 출력.

| 필드 | 타입 | 뜻 |
|---|---|---|
| `element_id` | `UUID` | 입력과 같다 |
| `braille_lines` | `list[str]` | 논리 줄별 점자(조판 뒤에는 조판된 줄) |
| `break_points` | `list[list[int]]` | 줄별 줄바꿈 자리(4.1 `translate_body` 의 `breaks` 와 같은 뜻) |
| `rule_trail` | `list[RuleApplication]` | 규정 근거 |
| `box_borders` | `list[BoxBorder]` | 글상자 테두리 |
| `drafts` · `selected_idx` | `list[Draft]` · `int` | 표·시각 자료의 초안과 고른 번호 |
| `line_indents` | `list[int] \| None` | 줄별 앞 빈칸 수 |
| `corrected_text` | `str` | 입력 묵자(비어 있을 수 있다) |

**`RuleApplication`** · 근거 하나. 점역사 화면에서 "왜 이렇게 옮겼나" 로 보인다.

| 필드 | 타입 | 뜻 |
|---|---|---|
| `rule_id` | `str` | 조항 번호(4.8) |
| `source` · `section` · `rule_name` · `contents` | `str` | 규정 이름, 절 위계, 조항 이름, 조항 본문 |
| `line_no` · `col_start` · `col_end` | `int` | 요소 안 좌표. `line_no=-1` 은 요소 전체 |
| `tag` · `priority` | `str` | 표시 꼬리표, 무게 |

**`Draft`** · 초안 하나: `option: int` · `text: str`(묵자) · `render_mode: str = "narrative"` · `label: str` · `type_label: str` · `braille_lines` · `break_points` · `rule_trail`.

**`BoxBorder`** · 글상자 테두리: `kind: str` · `level: int = 1` · `title: str = ""`.

---

## 6. 설정 (환경 변수)

기본값이 권하는 값이다. 바꾸는 것은 규정형 점자가 필요하거나 결과를 견줄 때다.

⚠ "임포트" 라고 적은 스위치는 **모듈을 처음 임포트할 때 한 번 읽는다.** 그 뒤에 바꾸면 안 먹으므로, 프로세스를 띄울 때 환경 변수로 준다. "부를 때" 스위치는 부를 때마다 읽는다.

| 스위치 | 읽는 때 | 기본값 | 뜻 | 언제 바꾸나 |
|---|---|---|---|---|
| `BRAILLE_STYLE` | 임포트 | `book` | `book` 은 점자 도서 관행, `regulation` 은 규정 원형을 쓴다. 규정과 도서 관행이 갈리는 몇 자리만 달라진다. 수식 줄머리 문항 번호, 삼각함수 인수 묶음, 근호 안 곱, 표 한 행을 한 줄에 적는 폭(40칸/32칸), 표 칸 사이 쌍점, 보기 기호 표기 등이다 | 「한국 점자 규정」 원형대로 내야 할 때 |
| `BRAILLE_WORDWRAP` | 부를 때 | `syllable` | `word` 면 조판이 음절이 아니라 어절 단위로 줄을 바꾼다 | 시험 문제지처럼 어절 단위 줄바꿈이 필요할 때. 줄 끝 여백이 늘어 쪽수가 늘 수 있다 |
| `TABLE_SHORTEN` | 임포트 | `1` | 표가 32칸에 안 들어갈 때 열 너비를 줄인다. 반복 단위를 열 제목으로 올리고, 값 끝 문장 부호·수표·한 종류 기호를 뗀다(「점자 자료 제작 지침」 3.2.2) | 표를 원문 그대로 두고 싶을 때 `0` |
| `TABLE_GRID_SEP` | 부를 때 | 없음 | `colon` 이면 격자 표에서 행 머리 뒤를 늘 쌍점으로 가른다 | 칸을 늘 쌍점으로 가르는 관행을 따를 때 |
| `TABLE_RECORD_ROWS` | 부를 때 | `0` | `1` 이면 칸이 길 때 한 줄에 칸 하나만 적는다 | 긴 칸 둘이 한 줄에 몰리는 표를 풀 때(시험용 스위치) |
| `TABLE_RECORD_MIN_CELL` | 임포트 | `42` | 위 스위치가 켜졌을 때 "긴 칸" 의 칸 수 문턱 | 위 스위치와 함께 |

`BRAILLE_STYLE` 로 달라지는 실물:

```
$ python -c "from semojum_braille.kor_math_rules import convert_latex as c; print(c('(1) x+1=2'), c(r'\sin 2x'))"
⠤⠼⠁⠤⠀⠭⠢⠼⠁⠒⠒⠼⠃ ⠖⠎⠼⠃⠭
$ BRAILLE_STYLE=regulation python -c "from semojum_braille.kor_math_rules import convert_latex as c; print(c('(1) x+1=2'), c(r'\sin 2x'))"
⠦⠼⠁⠴⠭⠢⠼⠁⠒⠒⠼⠃ ⠖⠎⠷⠼⠃⠭⠾
```

역점역 패키지의 스위치는 그 저장소 README 에 있다.

---

## 7. 모듈 구성 (엔진을 고칠 사람용)

| 모듈 | 하는 일 | 공개(4절) | 계약 아님(엔진 안에서만 쓴다) |
|---|---|---|---|
| `translator` | 글 점역 코어. 한글은 `braillify`, 영어·숫자·기호·인라인 수식은 이 모듈이 맡고 줄바꿈 자리를 계산한다 | 4.1 여섯 | `substitute_tags` · `normalize_print_draft` · `strip_leader_dots` · `merge_hidden_runs` · `dropped_pua` · `isolate_border_tags` · `box_borders_from_source` · `border_marker_spans` · `blank_marker_spans` · `tn_marker_spans` · `emphasis_marker_spans` · `source_has_tn` |
| `kor_math_rules` | LaTeX → 수학 점자. 순서가 곧 의미인 단계 파이프라인이다(단계표는 `convert_latex` 독스트링) | `convert_latex` | `digits_to_braille` · `latex_rule_ids` · `unicode_scripts_to_latex` · `caps_phrase_run` · `caps_phrase_cells` · `register_text_hook` · `w2c_register_plain_hook` |
| `inline_math` | 글 속 평문 수식 찾기 | `wrap` · `normalize` | |
| `eng_braille` | 영어 Grade 2 | `translate` · `translate_word` · `iter_words` | |
| `symbol_rules` | 특수 기호표와 판단이 갈리는 기호 | `substitute_symbols` · `symbol_rule_spans` | `preprocess` · `postprocess` |
| `number_sign` | `⠼` 가 수표인지 영어 약자인지 가른다(제40항) | | `number_sign_indices` · `contraction_lookalikes` · `has_number_sign` |
| `text_braille` · `formula_braille` · `table_braille` · `visual_braille` | 요소 점역 클래스 | 4.5 · 4.6 | `table_braille.parse_print_frames` · `record_rows_enabled` |
| `layout_braille` | 조판과 통 문자열 | 4.7 | `format_underline_blank` · `format_citation` · `format_paragraph_start` · `format_bullet_item` · `format_page_change_line` · `format_box_top` · `format_box_bottom` · `format_overflow_page_number` |
| `regulations` | 규정 조항표 | 4.8 | |
| `schemas` | 데이터 타입 | 5.3 | |
| `sidecar` | 표준입출력 사이드카 | 8절 | |
| `nested_block` | 시각 자료 안의 시각 자료를 글상자로 묶는다 | | `box_narrative` · `append_nested` |
| `isolation` | 요소별 격리 점역(한 요소 실패를 자리표시로) | | `safe_translate` · `dedupe_trail` |
| `tag_names` | 인라인 태그 이름 정본(5.1) | | `tn` · `box` · `indent_tag` · `split_indent` · `apply_indent_tags` · `strip_indent_tags` · `normalize_tn_spans` · `tn_spans_ok` |
| `tn_notices` | 점역자 주 문구 정본 | | `table_split` · `indent_hierarchy` · `omitted` · `reading_order` · `layout_scan` · `scene` |
| `gates` | 걸러 낸 자리를 쪽마다 센다 | | `gate_reset` · `gate_hit` · `gate_counts` · `gate_flags` · `strip_format_tokens` 등. `guard_on`(`LLM_TEXT_GUARD`)은 이 패키지 안에서는 부르는 곳이 없다 |
| `constants` | 조판 상수(`COLS = 32` · `ROWS = 26`) | | |

- 규정과 도서 관행이 갈리는 자리는 코드 주석에 판단 근거를 적어 두었다. 고칠 때는 `braille-source` 의 규정 원문과 대조한다.
- 이 저장소는 `Semojum/AI` 저장소의 `app/ai/braille/` 에서 동기화해 만든다. 고칠 때는 그 저장소에서 고치고 다시 동기화한다.

---

## 8. 파이썬이 아닌 곳에서 쓰기 (사이드카)

C#·자바스크립트처럼 파이썬이 아닌 프로그램은 이 엔진을 담은 파이썬 프로세스(**사이드카**)를 띄워 두고 표준입출력으로 말을 건다.

### 8.1 띄우기

```
python -m semojum_braille.sidecar
```

- 부르는 쪽이 이 명령으로 프로세스를 **하나 띄워 두고 계속 쓴다.** 부를 때마다 새로 띄우지 않는다.
- 표준입력으로 요청 JSON 을 **한 줄에 하나** 보낸다. 표준출력으로 응답 JSON 이 **한 줄에 하나** 온다. 받은 순서대로 답한다.
- 표준오류에는 엔진 로그(경고)가 나온다. 응답은 표준출력에만 쓴다.
- 표준입력을 닫으면 사이드카가 끝난다.
- 역점역(`decode`)은 역점역 패키지(`semojum-braille-back`)가 깔려 있을 때만 된다. 없으면 `decode` 요청에 오류 응답이 온다.
- 역점역 패키지가 있으면 기동하자마자 뒤에서 역점역을 한 번 불러 형태소 분석기 kiwi 를 미리 올린다. 영어책 역점역의 첫 호출이 약 2초 멈추는 것을 가리려는 것이다.

잰 값(리눅스, 2026-09-29): 기동부터 첫 응답까지 약 0.1초, 한 쪽(35요소·1,318자) 점역 약 0.21초, 보통 쪽 역점역 약 0.02초. Windows 에서는 재지 않았다.

### 8.2 문자와 인코딩

- JSON 은 **ASCII 로만** 오간다. 한글과 점자는 `\uXXXX` 로 적는다. 콘솔 코드 페이지와 상관없게 하려는 것이다. .NET `System.Text.Json` 의 기본 직렬화도 같은 꼴을 낸다.
- 점자·빈칸·줄바꿈이 모두 BMP 안이라 **UTF-16 문자열(C# `string`, 자바스크립트 문자열)의 인덱스와 이 문서의 오프셋이 같다.** `breaks` 값을 그대로 인덱스로 쓴다.
  단서 하나: 엔진이 점자로 못 옮긴 글자가 `cells` 에 드물게 남을 수 있다. 그 글자가 BMP 밖(이모지 등)이면 UTF-16 에서는 두 칸으로 세어져 뒤 오프셋이 하나씩 밀린다. 그런 요소는 `breaks` 를 버리고 빈칸 자리로 접는다.

### 8.3 실제로 오간 줄

아래는 사이드카를 띄워 실제로 주고받은 줄이다(엔진 0.1.1). `→` 가 표준입력, `←` 가 표준출력이다.

**전선 위 모습 그대로** (제목 요소 하나):

```
→ {"id": 3, "op": "translate", "text": "1 \uad6d\uc5b4\uc758 \ud0d0\uad6c\uc640 \ud65c\uc6a9", "type": "title", "heading_level": 2}
← {"cells": "\u2800\u2800\u2800\u2800\u2800\u2800\u283c\u2801\u2832\u2800\u2808\u280d\u2801\u280e\u283a\u2800\u2813\u2822\u2808\u280d\u2827\u2800\u281a\u2827\u2802\u282c\u2836", "breaks": [9, 10, 13, 14, 15, 16, 18, 20, 21, 22, 25], "id": 3}
```

풀어 쓰면 `cells` 는 `⠀⠀⠀⠀⠀⠀⠼⠁⠲⠀⠈⠍⠁⠎⠺⠀⠓⠢⠈⠍⠧⠀⠚⠧⠂⠬⠶` 이다(2단계 제목이라 7칸에서 시작). 아래부터는 `\uXXXX` 를 풀어 적는다.

**ping** (기동 확인):

```
→ {"id": 1, "op": "ping"}
← {"ok": true, "id": 1}
```

**translate** (본문 한 요소):

```
→ {"id": 2, "op": "translate", "text": "대한민국의 모든 국민은 법 앞에 평등하며, 누구든지 성별이나 종교 때문에 차별받지 아니한다.", "type": "text", "heading_level": 0}
← {"cells": "⠀⠀⠊⠗⠚⠒⠑⠟⠈⠍⠁⠺⠀⠑⠥⠊⠵⠀⠈⠍⠁⠑⠟⠵⠀⠘⠎⠃⠀⠣⠲⠝⠀⠙⠻⠊⠪⠶⠚⠑⠱⠐⠀⠉⠍⠈⠍⠊⠵⠨⠕⠀⠠⠻⠘⠳⠕⠉⠀⠨⠿⠈⠬⠀⠠⠊⠗⠑⠛⠝⠀⠰⠣⠘⠳⠘⠔⠨⠕⠀⠣⠉⠕⠚⠒⠊⠲", "breaks": [4, 6, 8, 11, 12, 13, 15, 17, 18, 21, 23, 24, 25, 28, 29, 31, 32, 33, 35, 38, 39, 42, 43, 45, 47, 49, 51, 52, 54, 56, 57, 58, 59, 61, 63, 64, 67, 69, 70, 71, 73, 75, 77, 79, 80, 81, 83, 85], "id": 2}
```

`cells` 앞 두 칸(`⠀⠀`)은 문단 들여쓰기다(3칸에서 시작). 85칸짜리 한 줄이고 아직 32칸으로 접지 않았다. 접는 법은 8.5.

**decode** (위 `cells` 를 그대로 되돌린다):

```
→ {"id": 4, "op": "decode", "braille": "⠀⠀⠊⠗⠚⠒⠑⠟⠈⠍⠁⠺⠀⠑⠥⠊⠵⠀⠈⠍⠁⠑⠟⠵⠀⠘⠎⠃⠀⠣⠲⠝⠀⠙⠻⠊⠪⠶⠚⠑⠱⠐⠀⠉⠍⠈⠍⠊⠵⠨⠕⠀⠠⠻⠘⠳⠕⠉⠀⠨⠿⠈⠬⠀⠠⠊⠗⠑⠛⠝⠀⠰⠣⠘⠳⠘⠔⠨⠕⠀⠣⠉⠕⠚⠒⠊⠲"}
← {"text": "  대한민국의 모든 국민은 법 앞에 평등하며, 누구든지 성별이나 종교 때문에 차별받지 아니한다.", "id": 4}
```

**decode**, 영어 교과 책의 한 줄:

```
→ {"id": 5, "op": "decode", "braille": "⠀⠀⠼⠁⠲⠀⠴⠥⠝⠊⠧⠻⠎⠁⠇⠲⠀⠸⠌⠀⠠⠌⠕⠁⠠⠪⠙⠕⠎", "english": true}
← {"text": "  1. universal / 셰익스피어", "id": 5}
```

**오류** (모르는 op, JSON 이 아닌 줄):

```
→ {"id": 6, "op": "fold"}
← {"error": "모르는 op: 'fold'", "id": 6}
→ not json
← {"error": "JSONDecodeError: Expecting value: line 1 column 1 (char 0)", "id": null}
```

### 8.4 필드

**요청**

| op | 필드 | 타입 | 기본값 | 뜻 | 예 |
|---|---|---|---|---|---|
| 모두 | `id` | 아무 JSON 값 | 없음 | 응답에 그대로 돌아온다. 요청과 응답을 짝짓는 데 쓴다 | `2` |
| 모두 | `op` | 문자열 | 없음 | `translate` · `decode` · `ping` | `"translate"` |
| translate | `text` | 문자열 | `""` | 묵자 요소 하나. 줄바꿈은 `\n`. 인라인 태그(5.1)를 그대로 넣는다 | `"대한민국의 모든…"` |
| translate | `type` | 문자열 | `"text"` | 요소 종류. `text` · `title` · `list_item` · `caption` 중 하나. 들여쓰기가 이것에 따라 달라진다 | `"title"` |
| translate | `heading_level` | 정수 | `0` | 0 은 본문. 1~4 는 제목 단계다. 1단계는 가운데 정렬, 2단계는 7칸, 3·4단계는 5칸에서 시작한다 | `2` |
| decode | `braille` | 문자열 | `""` | 점자. 여러 줄이면 `\n` 으로 잇는다 | `"⠊⠗⠚⠒…"` |
| decode | `english` | 참거짓 | `false` | 영어 교과 책이면 `true`. 한글로 잘못 읽힌 영어 토막을 되찾는다. 다른 책에서는 켜지 않는다 | `true` |

**응답**

| op | 필드 | 타입 | 뜻 |
|---|---|---|---|
| 모두 | `id` | 요청과 같음 | 요청의 `id`. JSON 이 아닌 줄을 받으면 `null` |
| translate | `cells` | 문자열 | 점역 결과. `flatten_elements` 가 내는 요소 통 문자열(4.7)에서 앞뒤 빈 줄(`prefix`·`suffix`)을 뺀 본문과 같다. 들여쓰기 칸과 가운데 여백이 들어 있고, 논리 줄은 `\n` 으로 잇는다. **32칸으로 접지 않았다.** 제목·표 둘레의 앞뒤 빈 줄은 이웃 요소에 따라 정해지므로 부르는 쪽의 조판이 넣는다 |
| translate | `breaks` | 정수 배열 | `cells` 안에서 줄을 바꿔도 되는 자리. 값 `b` 는 "`cells[b]` 앞에서 끊어도 된다" 는 뜻이다. 음절 경계와 빈칸 자리가 모두 들어 있다. 오름차순이다 |
| decode | `text` | 문자열 | 역점역한 글. 원문 복원이 아니라 **검수용 근사**다. 줄바꿈은 그대로 둔다 |
| ping | `ok` | 참거짓 | 늘 `true` |
| 실패 | `error` | 문자열 | `"예외이름: 내용"` 또는 설명. 이때 다른 필드는 없다 |

**파이썬에서 같은 일을 하는 함수**: `semojum_braille.sidecar` 의 `translate(text, etype="text", hlevel=0) -> dict`(`{"cells", "breaks"}` 를 낸다) · `handle(req: dict) -> dict`(요청 하나를 처리한다) · `main() -> None`(표준입출력 고리).

### 8.5 32칸 접기 (부르는 쪽이 할 일)

사이드카는 32칸으로 접지 않는다. 부르는 쪽이 아래 함수로 접는다. 파이썬으로 적었지만 **다른 언어로 옮길 몫은 이 함수 하나다.**

```python
W, BLANK = 32, "⠀"


def fold(cells, breaks, center=False, cuts=None):
    """cells(논리 줄을 \\n 으로 이은 통 문자열)를 32칸 줄로 접는다. 부르는 쪽이 할 몫이다.

    breaks 자리(그 셀 앞)에서만 끊고, 32칸 안에 자리가 없을 때만 32칸째에서 강제로 자른다.
    자리 목록이 없는 줄(사람이 점자를 직접 고친 요소 등)은 빈칸 자리에서 끊는다. 이어지는 줄 머리 빈칸은 버린다.
    center: 1단계 제목이면 32칸을 넘어 접힌 줄만 조각마다 가운데로 놓는다(안 접힌 줄은 cells 에 이미 가운데 여백이 있다).
    cuts: 넘기면 끊은 자리마다 '음절'·'빈칸'·'강제'를 적는다(검증용).
    """
    out, base = [], 0
    for line in cells.split("\n"):
        offs = [b - base for b in breaks if base < b < base + len(line)]
        base += len(line) + 1
        if not offs:
            offs = [i for i, c in enumerate(line) if c == BLANK and i and line[i - 1] != BLANK]
        seg, start = [], 0
        while len(line) - start > W:
            ok = [b for b in offs if start < b <= start + W]
            b = max(ok) if ok else start + W
            if not ok and line[b - 1] == "⠠" and line[b] == "⠄":   # 2칸 지시부호(점역자 주)는 안 가른다
                b -= 1
            if cuts is not None:
                cuts.append("강제" if not ok else "빈칸" if line[b] in (" ", BLANK) else "음절")
            seg.append(line[start:b])
            start = b
            while start < len(line) and line[start] in (" ", BLANK):
                start += 1
        if start < len(line) or not seg:
            seg.append(line[start:])
        if center and len(line) > W:
            seg = [BLANK * ((W - len(s)) // 2) + s for s in seg]
        out += seg
    return out
```

8.3 의 translate 응답(85칸)을 이 함수로 접은 실제 결과:

```
⠀⠀⠊⠗⠚⠒⠑⠟⠈⠍⠁⠺⠀⠑⠥⠊⠵⠀⠈⠍⠁⠑⠟⠵⠀⠘⠎⠃⠀⠣⠲⠝| 32칸
⠙⠻⠊⠪⠶⠚⠑⠱⠐⠀⠉⠍⠈⠍⠊⠵⠨⠕⠀⠠⠻⠘⠳⠕⠉⠀⠨⠿⠈⠬⠀ | 31칸
⠠⠊⠗⠑⠛⠝⠀⠰⠣⠘⠳⠘⠔⠨⠕⠀⠣⠉⠕⠚⠒⠊⠲         | 23칸
```

둘째 줄 끝의 `⠀` 는 빈칸 자리에서 끊은 흔적이다. 엔진 조판(4.7)도 똑같이 끊는다.

**다른 언어로 옮길 때 지킬 것**

1. 32칸 안에서 **가장 먼** `breaks` 자리에서 끊는다. 그런 자리가 없을 때만 32칸째에서 강제로 자른다. 강제로 자를 때 점역자 주 표 `⠠⠄`(두 칸)는 가르지 않고 한 칸 앞에서 자른다.
2. 이어지는 줄의 머리에 오는 빈칸(`⠀`, 공백)은 버린다.
3. `breaks` 가 하나도 없는 줄은 빈칸 무리의 첫 자리에서 끊는다. **이때도 줄 머리 들여쓰기는 지킨다.** 줄 맨 앞의 빈칸 무리는 끊는 자리로 치지 않는다.
4. 1단계 제목(`heading_level` 1)은 32칸을 넘어 접힌 줄만 조각마다 가운데로 놓는다. 안 접힌 줄은 `cells` 에 이미 가운데 여백이 있다.
5. `breaks` 값은 `cells` 전체 기준이다. 줄마다 그 줄의 시작 오프셋을 빼서 쓴다.
6. 사람이 어떤 요소의 **점자를 직접 고치면** 그 요소의 `breaks` 는 낡는다. 그 요소는 `breaks` 를 버리고 3번(빈칸 자리)으로 접는다.

**검증**: 2027 수능특강 8권(39,562요소)에서 이 함수로 접은 결과를 엔진 조판과 견줬다. 다른 요소가 0이다.

### 8.6 `breaks` 를 꼭 써야 하는 까닭

한국어 점자는 **한글을 음절 단위로 줄바꿈하는 것이 원칙**이다(「점자 자료 제작 지침」 2.1.1(2), 「점자 도서 제작 지침」 1장 2절 1). 그런데 셀만 봐서는 음절 경계를 알 수 없다. `⠉` 는 `나`(약자)이기도 하고 초성 ㄴ 이기도 하다. `나이`(⠉⠣⠕)에서 ⠉|⠣ 는 음절 안이고 ⠉⠣|⠕ 가 음절 경계다. 묵자를 아는 엔진만 이것을 가른다. 그래서 엔진이 자리를 알려 주고 부르는 쪽은 그 자리에서만 끊는다.

- 2027 수능특강 8권 39,562요소 실측: `breaks` 없이 **빈칸에서만 접으면 66.7% 가 엔진과 다르게 접힌다.** `breaks` 로 접으면 다른 요소가 0이다.
- 지침은 시험 문제지처럼 특별한 경우 **어절 단위** 줄바꿈도 허용한다. 어절 단위로 접으려면 `breaks` 중 빈칸 자리만 쓰면 된다.

### 8.7 오류와 사이드카가 죽었을 때

- 한 요청이 실패하면 `error` 응답이 오고 사이드카는 계속 돈다(8.3 예).
- **표준오류를 반드시 비운다.** 엔진이 경고를 표준오류로 쓴다. 표준오류를 파이프로 받고 읽지 않으면 파이프가 차서 사이드카가 멈춘다. C# 이면 `RedirectStandardError = true` 로 두고 `BeginErrorReadLine` 으로 비동기로 읽어 버리거나, 리디렉트를 끈다.
- 사이드카가 죽으면 표준출력이 닫힌다(C# `ReadLine()` 이 `null`). 부르는 쪽은 다시 띄우고, 답을 못 받은 요청을 다시 보낸다. translate 와 decode 는 같은 입력에 늘 같은 출력을 내므로 다시 보내도 된다. 짧은 사이에 거듭 죽으면(예: 1분에 세 번) 다시 띄우기를 멈추고 사용자에게 알린다.
- 부르는 프로그램이 끝날 때 사이드카도 함께 끝나게 하려면 Windows 에서는 Job Object(`JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`)에 넣는다. 평소에는 표준입력을 닫으면 스스로 끝난다.
- 이 저장소에는 C# 코드가 없다. 위 C# 이름(`Process`·`RedirectStandardError`·`BeginErrorReadLine`)은 .NET 표준 API 이고, 여기서 돌려 본 것은 같은 일을 하는 파이썬 부르는 쪽이다.
- 스레드: 점역은 CPU 계산이라 한 프로세스 안에서 스레드를 늘려도 빨라지지 않는다. 사이드카 하나가 요청을 차례로 처리하게 두고, 동시에 여러 건이 필요하면 사이드카를 여럿 띄운다.

---

## 9. 규정 근거

엔진이 요소의 `rule_trail` 에 다는 조항과, 근거를 따로 달지 않고 지키는 조항이다. 조항 문구는 `braille-source` 의 규정 원문과 맞췄다.

**「한국 점자 규정」 한글 점자**

| 조항 | 내용 | 어디서 |
|---|---|---|
| 제1장 · 제2장 | 자모, 약자와 약어 | `braillify`(translator 가 부른다) |
| 제4장 제28항~제39항 | 로마자와 그리스 문자. 제29항 로마자표 `⠴`, 제30항 그리스 문자 | translator · eng_braille · symbol_rules · kor_math_rules(`MCST-한글-4.10.30`) |
| 제40항 | 숫자는 수표 `⠼` 를 앞세운다 | translator · number_sign |
| 제49항 | 문장 부호 | translator · layout_braille(`MCST-한글-6.13.49`) |
| 제56항 | 드러냄표·밑줄·굵은 글자 강조 | 태그 `강조`·`굵은`(`MCST-한글-6.13.56`) |
| 제57항 | 숨김표가 여럿 붙어 나올 때 | translator |
| 제64항 | 동그라미 문자·네모 문자 | translator · 태그 `네모글` |
| 제69항 | 로마자 단위 기호 | symbol_rules(`MCST-한글-6.14.69`) |
| 제70항 | 화살표 | symbol_rules |
| 제72항 | 글머리 기호 | layout_braille(`MCST-한글-6.14.72`) |
| 제73항 | 채워 넣어야 할 빈칸 | 태그 `빈칸`·`밑줄`·`네모`(`MCST-한글-6.14.73`) |

**「한국 점자 규정」 수학 점자**: 제11항(수식 앞뒤 두 칸)은 translator 가, 나머지는 `kor_math_rules` 가 지킨다. 근거로 다는 조항은 제1장 제2·4·7항, 제2장 제15·18·19·21·22·25항, 제3장 제29·32항, 제4장 제42·43항, 제5장 제46~49항, 제6장 제50·51·54·55·56·59항, 제7장 제60·61항, 제9장 제65항이다(`MCST-수학-장.항`).

**「점자 도서 제작 지침」**

| 조항 | 내용 | 어디서 |
|---|---|---|
| 1장 1절 3 | 쪽은 가로 32칸, 세로 26줄 | constants · layout_braille |
| 1장 2절 1 | 줄바꿈 | translator(줄바꿈 자리) · layout_braille(`NLD-1.2.1`) |
| 1장 2절 5 | 글상자 | 태그 `상자`·`상자끝` · text/table/visual_braille(`NLD-1.2.5`) |
| 1장 2절 6 | 점역자 주 | 태그 `주` · text/table/visual_braille(`NLD-1.2.6`) |
| 2장 2절 1 · 2 | 단계별 제목 표기, 문단 형식 | layout_braille(`NLD-2.2.1`·`NLD-2.2.2`) |
| 2장 3절 5 | 글머리 기호 | layout_braille(`NLD-2.3.5`) |
| 3장 1절 1 · 2 | 표 일반 사항, 유형별 점역 | table_braille(`NLD-3.1.1`·`NLD-3.1.2`) |
| [예 1-8] | 페이지행의 짧은 글 | translate_plain |

**「점자 자료 제작 지침」**: 2.1.1(2) 한글은 음절 단위로 줄을 바꾼다(줄바꿈 자리). 시각 자료 장은 visual_braille 의 초안 형식이 따른다.

`BRAILLE_STYLE=book`(기본)은 규정과 점자 도서 관행이 갈리는 몇 자리에서 도서 관행을 쓴다(6절). 규정 원형이 필요하면 `regulation` 으로 띄운다.

---

## 10. 한계와 주의

**못 하는 것**
- 그림을 보고 설명을 짓지 않는다. 시각 자료는 설명 **글**을 받아 옮길 뿐이다. 글자 인식(OCR)도 하지 않는다.
- 악보(음악 점자)는 옮기지 않는다.
- 기호표에 없는 기호는 **경고 없이 빠진다**(`가▶나` → `⠫⠉`). 옮기기 전에 `symbol_table.json` 에 있는지 확인한다.
- 글 점역 함수(4.1)는 32칸으로 접지 않는다. 접힌 쪽이 필요하면 조판(4.7)을 쓰거나 8.5 의 접기 함수를 쓴다.
- 역점역은 이 패키지에 없다(`semojum-braille-back`).

**쓸 때 주의**
- 조판 함수(`render` · `layout` · `render_page_text`)는 넘긴 `BrailleOutput` 을 제자리에서 고친다. 같은 객체를 두 번 넣지 않는다(4.7).
- `layout` 은 지금 작업 폴더 아래 `storage/jobs/…` 에 파일을 쓴다(4.7).
- `<!표>` 태그는 `TableBraille` 에만 넣는다. 글 점역 함수에 넣으면 칸 글자가 붙어 버린다(5.1).
- "임포트" 스위치는 프로세스를 띄울 때 준다(6절).
- 역점역 패키지는 이 엔진의 내부 표를 쓰므로 판을 `==` 로 묶는다(지금 `==0.1.1`). 소스를 통째로 복사해 넣는다면 두 저장소를 같은 동기화 커밋끼리 넣는다. 어긋나면 임포트 때가 아니라 영어가 섞인 입력이 올 때 `TypeError` 가 난다.

**시험하지 않은 것**
- 스레드 안전. 코드에서 본 공유 상태는 이렇다. 걸러 낸 자리 계수기(`gates`)는 `ContextVar` 라 스레드·작업마다 따로 센다. 캐시 둘(`functools.lru_cache`)은 CPython 에서 스레드 안전하다.
- Windows(설치 크기, 사이드카 속도), 파이썬 3.11 · 3.14.
- BMP 밖 글자가 섞인 입력의 오프셋(8.2).

**알려진 결함** (2026-09-29 기준, 고치는 중)
- 줄을 32칸으로 접을 때 닫는 따옴표나 쉼표가 다음 줄 머리로 넘어가는 경우가 있다. 줄 머리 금지 규칙이 완성형 한글 뒤에서만 걸린다.
- `flatten_elements` 가 32칸 가까이 찬 줄을 이을 때 낱말 가운데에 빈칸이 들어가는 경우가 있다(`개념으 로`).
- 파이썬 3.12 이상에서 `kor_math_rules.py` 를 처음 임포트할 때 `SyntaxWarning: invalid escape sequence '\p'` 가 한 번 찍힌다. 동작에는 영향이 없다.
