# 점역 레퍼런스 · `semojum_braille.encoder`

`semojum_braille.encoder` 의 공개 함수, 입출력 형식, 설정, 모듈 구성.

| 절 | 내용 |
|---|---|
| 1 | API 레퍼런스(공개 함수 전부) |
| 2 | 입출력 형식: 태그 문법, 점자 표기, 데이터 타입 |
| 3 | 설정(환경 변수) |
| 4 | 모듈 구성(엔진을 고칠 사람용) |
| 5 | 한계와 주의 |

## 1. API 레퍼런스

공개 함수는 이 절에 적은 것이 전부다. 밑줄(`_`)로 시작하는 이름과 4절의 "계약 아님" 칸에 적은 이름은 판이 오르면 바뀔 수 있으니 기대지 않는다.

아래 예는 이 준비 코드를 먼저 돌린 것이다.

```python
import os, uuid
from types import SimpleNamespace
from semojum_braille.encoder import eng_braille, inline_math, symbol_rules
from semojum_braille.encoder.kor_math_rules import convert_latex
from semojum_braille.encoder.translator import (translate_tagged_text, translate_body, translate_with_breaks,
                                        translate_visual, translate_plain, sanitize_for_braille)
from semojum_braille.schemas import LLMOutput, Draft
from semojum_braille.encoder.text_braille import TextBraille, content_rules
from semojum_braille.encoder.formula_braille import FormulaBraille
from semojum_braille.encoder.table_braille import TableBraille, build_table_tags, parse_table_tags, print_layout
from semojum_braille.encoder.visual_braille import VisualBraille, DiagramBraille
from semojum_braille.encoder.layout_braille import LayoutBraille, flatten_elements, render_page_text, wordwrap_by_word
from semojum_braille.encoder.regulations import make_rule, make_rule_at, rule_meta, section_text, all_rule_ids
```

모든 함수는 **예외를 드물게 던진다.** 옮길 수 없는 글자는 예외 대신 빠지고(5절), 요소 점역 클래스는 한 요소가 실패해도 그 요소만 자리표시로 바꾸고 나머지를 옮긴다. 인자 타입이 틀리면(문자열 자리에 `None` 등) 파이썬 기본 예외가 난다.

### 1.1 글 점역 · `semojum_braille.encoder.translator`

#### `translate_tagged_text(text, *, force_roman=False, qnum_period=True) -> str`

묵자 한 덩어리를 점자 문자열 하나로 옮긴다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `text` | `str` | 없음 | 묵자. 줄바꿈 `\n` 은 그대로 점자 줄바꿈이 된다. 인라인 태그(2.1)를 받는다 | 늘 |
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

32칸으로 접을 때는 32칸 안에서 가장 먼 자리에서 끊는다. 접는 함수는 docs/sidecar.md 의 32칸 접기에 있다.

#### `translate_with_breaks(text, *, force_roman=False, qnum_period=True) -> tuple[list[str], list[list[int]]]`

`translate_body` · `translate_visual` · `translate_plain` 이 모두 부르는 속 함수다. 인자는 `translate_tagged_text` 와 같고, 반환은 `translate_body` 와 같다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `text` | `str` | 없음 | 묵자 | 늘 |
| `force_roman` | `bool` | `False` | 1.1 `translate_tagged_text` 와 같다 | 같다 |
| `qnum_period` | `bool` | `True` | 같다 | 같다 |

- **언제 쓰나**: 위 세 입구가 맞지 않아 인자를 직접 정해야 할 때만 쓴다.
- **예외**: `text` 가 문자열이 아니면 `TypeError`.

```
>>> translate_with_breaks('DNA 검사')
(['⠴⠠⠠⠙⠝⠁⠲⠀⠈⠎⠢⠇'], [[7, 11]])
>>> translate_with_breaks('1 세포 분열', qnum_period=False)
(['⠼⠁⠀⠠⠝⠙⠥⠀⠘⠛⠳'], [[2, 3, 5, 7]])
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
(['⠼⠁⠀⠠⠝⠙⠥⠀⠘⠛⠳⠀⠈⠧⠨⠻'], [[2, 3, 5, 7, 11]])
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

### 1.2 수식

#### `convert_latex(latex) -> str` · `semojum_braille.encoder.kor_math_rules`

LaTeX 수식 하나를 수학 점자로 옮긴다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `latex` | `str` | 없음 | LaTeX 수식. `$` 없이 넣는다 | 수식만 따로 옮길 때. 글 속 수식은 `<!수식>` 태그로 감싸 1.1 함수에 넣으면 이 함수를 거친다 |

- **반환**: 점자 문자열.
- **예외**: `latex` 가 `None` 이면 `AttributeError`. 괄호가 덜 닫힌 식도 예외 없이 옮기지만 결과가 온전하지 않다(`\frac{1}{` → `⠌⠼⠁`).
- **보는 곳**: 수학 점자 제1장~제9장. 어느 구조에 어느 조항을 다는지는 docs/regulations.md.

```
>>> convert_latex('\\frac{1}{2}')
'⠼⠃⠌⠼⠁'
>>> convert_latex('x^2+2x+1=0')
'⠭⠘⠼⠃⠢⠼⠃⠭⠢⠼⠁⠒⠒⠼⠚'
>>> convert_latex('\\sqrt{2}')
'⠜⠼⠃'
```

분수는 분모를 먼저 적는다(`⠼⠃⠌⠼⠁` 은 2분의 1).

#### `wrap(text) -> str` · `semojum_braille.encoder.inline_math`

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

#### `normalize(span) -> str` · `semojum_braille.encoder.inline_math`

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

### 1.3 영어 · `semojum_braille.encoder.eng_braille`

국어 문장 속 영어 구간을 영어 점자 약자(Grade 2)로 옮긴다. 로마자표·종료표는 붙이지 않는다(그건 1.1 함수가 붙인다).

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

### 1.4 특수 기호 · `semojum_braille.encoder.symbol_rules`

#### `substitute_symbols(text) -> str`

기호표(`symbol_table.json`)로 특수 기호를 점자로 바로 바꾼다. 다른 글자는 그대로 둔다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `text` | `str` | 없음 | 글 | 기호 하나가 어떤 점형이 되는지 볼 때. 글 전체는 1.1 함수가 이 표를 써서 옮긴다 |

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

### 1.5 요소 점역 클래스

문서를 요소(본문 한 문단, 수식 하나, 표 하나, 그림 하나) 단위로 옮기는 클래스다. 모두 같은 꼴이다.

```python
Klass().translate(optimized: list[LLMOutput]) -> list[BrailleOutput]
```

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `optimized` | `list[LLMOutput]` | 없음 | 요소 입력 목록. `LLMOutput` 필드는 2.3 | 요소마다 규정 근거(`rule_trail`)와 줄바꿈 자리를 함께 받고 싶을 때, 또 1.7 조판에 넣을 때 |

- **반환**: 입력과 같은 차례, 같은 길이의 `BrailleOutput` 목록(2.3).
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

**보는 곳**: 「점자 도서 제작 지침」 1장 2절 5(글상자) · 6(점역자 주), 3장 1절(표), 한글 점자 제56항(드러냄표) · 제73항(빈칸). 조항은 요소의 `rule_trail` 에 담긴다(docs/regulations.md).

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

들여쓰기(`line_indents`)는 여기서 줄에 붙이지 않고 1.7 조판이 붙인다.

#### `content_rules(source, lines) -> list[RuleApplication]` · `semojum_braille.encoder.text_braille`

요소 내용에 붙일 포괄 규정 근거를 낸다. **지금은 늘 빈 목록을 돌려준다.** 수표·문장 부호처럼 고를 여지가 없는 근거는 달지 않기로 해서 비웠고, 표 내용 근거가 생기면 이 자리에 붙인다.

| 인자 | 타입 | 기본값 | 뜻 | 언제 쓰나 |
|---|---|---|---|---|
| `source` | `str` | 없음 | 묵자 | 지금은 부를 까닭이 없다 |
| `lines` | `list[str]` | 없음 | 점자 줄 | 같다 |

```
>>> content_rules('가', ['⠫'])
[]
```

### 1.6 표 도우미 · `semojum_braille.encoder.table_braille`

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

### 1.7 조판 · `semojum_braille.encoder.layout_braille`

1.5 클래스가 낸 `BrailleOutput` 목록을 쪽(32칸 × 26줄)으로 조판한다. 제목 단계별 들여쓰기·가운데 정렬, 문단 들여쓰기, 제목 앞뒤 빈 줄, 쪽 번호 줄을 넣는다.

**`layout_result` 인자**(아래 함수들이 같이 받는다): `elements` 속성을 가진 아무 객체면 된다. 엔진은 요소마다 `element_id` · `type` · `reading_order` · `heading_level` 넷만 읽는다. `type` 은 `text` · `title` · `list_item` · `caption` 등, `heading_level` 은 0(본문) 또는 1~4(제목 단계)다. 넘기지 않아도 예외는 안 나지만 요소 종류와 제목 단계를 모른 채 본문으로 조판한다.

⚠ **`render` · `layout` · `render_page_text` 는 넘긴 `BrailleOutput` 을 제자리에서 고친다**(조판한 줄을 `braille_lines` 에 되써 넣는다). 같은 객체를 두 번 넣으면 들여쓰기가 두 번 걸린다. 다시 조판하려면 1.5 클래스로 새로 만든다. `flatten_elements` 는 고치지 않는다.

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
| `braille_outputs` | `list[BrailleOutput]` | 없음 | 1.5 의 출력 | 늘 |
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
| `braille_outputs` | `list[BrailleOutput]` | 없음 | 1.5 의 출력. 제자리에서 고쳐진다 | 늘 |
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

어절 단위 줄바꿈 스위치(`BRAILLE_WORDWRAP=word`, 3절)가 켜졌는지 돌려준다. 부를 때마다 환경 변수를 읽는다.

```
>>> wordwrap_by_word()
False
>>> os.environ["BRAILLE_WORDWRAP"] = "word"; wordwrap_by_word()
True
>>> del os.environ["BRAILLE_WORDWRAP"]
```

### 1.8 규정 근거 · `semojum_braille.encoder.regulations`

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


## 2. 입출력 형식

### 2.1 입력 태그 문법

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
| `표` · `행` · `칸` | 쌍·홑 | 표 구조. **`TableBraille` 에만 넣는다**(1.6) | 글 점역 함수에 넣으면 태그가 빠지고 칸 글자가 붙어 버린다 | 도서 지침 3장 1절 |

글상자:

```
>>> translate_tagged_text('<!상자>생각해 보기<!/상자>\n본문\n<!상자끝><!/상자끝>')
'⠿⠛⠛⠛⠛⠀⠠⠗⠶⠫⠁⠚⠗⠀⠘⠥⠈⠕⠀⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠿\n⠘⠷⠑⠛\n⠿⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠶⠿'
```

- **모르는 태그**는 태그만 지우고 안의 글은 옮긴다(`<!모름>사과<!/모름>` → `⠇⠈⠧`). 표준오류에 경고가 찍힐 수 있다.
- `⟦…⟧` 꼴 토막(24자 이하)은 형식 표시로 보고 지운다(`⟦글자⟧ 사과` → `⠀⠇⠈⠧`). 언어 모델이 만든 글에 섞여 드는 표시를 걸러 내려는 것이다.
- 태그 이름은 `tag_names.py` 에만 정의되어 있다. 옛 긴 이름(`점역자주` 등)은 받지 않는다.

### 2.2 점자 표기

- 점자는 유니코드 점자 블록(U+2800~U+28FF) 글자다. 점자 빈칸은 `⠀`(U+2800)이다. 보통 공백(U+0020)과 다르다. 영어 함수(1.3)와 기호 함수(1.4)는 점자가 아닌 글자를 건드리지 않으므로 빈칸이 공백으로 남는다.
- 줄은 `\n` 으로 잇는다. 글 점역 함수(1.1)는 32칸으로 접지 않는다. 32칸 × 26줄 쪽은 조판(1.7)이 만든다.
- ASCII 점자(BRF)는 쓰지 않는다. `layout` 이 쓰는 `.brf` 파일도 유니코드 점자다. ASCII 점자로 내보내려면 바깥에서 바꾼다.
- 파일은 모두 UTF-8 로 읽고 쓴다.

### 2.3 데이터 타입 · `semojum_braille.schemas`

pydantic 모델이다. 모두 키워드 인자로 만든다.

**`LLMOutput`** · 요소 하나의 입력. 이름은 이 엔진이 언어 모델 뒤 단계에서 쓰이던 데서 왔다. 모델 없이 직접 만들어 넣어도 된다.

| 필드 | 타입 | 기본값 | 뜻 |
|---|---|---|---|
| `element_id` | `UUID` | 필수 | 요소 id. 출력과 짝짓는 열쇠 |
| `corrected_text` | `str` | 필수 | 옮길 묵자(본문 글, LaTeX, 표 글, 시각 자료 설명) |
| `routing_tier` | `str` | 필수 | 처리 경로 이름. 엔진은 읽지 않으므로 아무 값(예 `"ZERO"`)이나 넣는다 |
| `render_mode` | `str` | `"text_only"` | 표 조판 안 등(1.5) |
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
| `break_points` | `list[list[int]]` | 줄별 줄바꿈 자리(1.1 `translate_body` 의 `breaks` 와 같은 뜻) |
| `rule_trail` | `list[RuleApplication]` | 규정 근거 |
| `box_borders` | `list[BoxBorder]` | 글상자 테두리 |
| `drafts` · `selected_idx` | `list[Draft]` · `int` | 표·시각 자료의 초안과 고른 번호 |
| `line_indents` | `list[int] \| None` | 줄별 앞 빈칸 수 |
| `corrected_text` | `str` | 입력 묵자(비어 있을 수 있다) |

**`RuleApplication`** · 근거 하나. 점역사 화면에서 "왜 이렇게 옮겼나" 로 보인다.

| 필드 | 타입 | 뜻 |
|---|---|---|
| `rule_id` | `str` | 조항 번호(1.8) |
| `source` · `section` · `rule_name` · `contents` | `str` | 규정 이름, 절 위계, 조항 이름, 조항 본문 |
| `line_no` · `col_start` · `col_end` | `int` | 요소 안 좌표. `line_no=-1` 은 요소 전체 |
| `tag` · `priority` | `str` | 표시 꼬리표, 무게 |

**`Draft`** · 초안 하나: `option: int` · `text: str`(묵자) · `render_mode: str = "narrative"` · `label: str` · `type_label: str` · `braille_lines` · `break_points` · `rule_trail`.

**`BoxBorder`** · 글상자 테두리: `kind: str` · `level: int = 1` · `title: str = ""`.

---


## 3. 설정 (환경 변수)

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
$ python -c "from semojum_braille.encoder.kor_math_rules import convert_latex as c; print(c('(1) x+1=2'), c(r'\sin 2x'))"
⠤⠼⠁⠤⠀⠭⠢⠼⠁⠒⠒⠼⠃ ⠖⠎⠼⠃⠭
$ BRAILLE_STYLE=regulation python -c "from semojum_braille.encoder.kor_math_rules import convert_latex as c; print(c('(1) x+1=2'), c(r'\sin 2x'))"
⠦⠼⠁⠴⠭⠢⠼⠁⠒⠒⠼⠃ ⠖⠎⠷⠼⠃⠭⠾
```

역점역 스위치는 [decoder.md](decoder.md) 에 있다.

---


## 4. 모듈 구성 (엔진을 고칠 사람용)

모듈은 모두 `semojum_braille/encoder/` 아래에 있다. `schemas` 와 `sidecar` 만 `semojum_braille/` 바로 아래에 있다.

| 모듈 | 하는 일 | 공개(1절) | 계약 아님(엔진 안에서만 쓴다) |
|---|---|---|---|
| `__init__` | 자주 쓰는 입구 일곱(1.1 여섯과 `convert_latex`)을 내보낸다. `from semojum_braille.encoder import translate_tagged_text` | 같다 | |
| `translator` | 글 점역 코어. 한글은 `braillify`, 영어·숫자·기호·인라인 수식은 이 모듈이 맡고 줄바꿈 자리를 계산한다 | 1.1 여섯 | `substitute_tags` · `normalize_print_draft` · `strip_leader_dots` · `merge_hidden_runs` · `dropped_pua` · `isolate_border_tags` · `box_borders_from_source` · `border_marker_spans` · `blank_marker_spans` · `tn_marker_spans` · `emphasis_marker_spans` · `source_has_tn` |
| `kor_math_rules` | LaTeX → 수학 점자. 순서가 곧 의미인 단계 파이프라인이다(단계표는 `convert_latex` 독스트링) | `convert_latex` | `digits_to_braille` · `latex_rule_ids` · `unicode_scripts_to_latex` · `caps_phrase_run` · `caps_phrase_cells` · `register_text_hook` · `w2c_register_plain_hook` |
| `inline_math` | 글 속 평문 수식 찾기 | `wrap` · `normalize` | |
| `eng_braille` | 영어 Grade 2 | `translate` · `translate_word` · `iter_words` | |
| `symbol_rules` | 특수 기호표와 판단이 갈리는 기호 | `substitute_symbols` · `symbol_rule_spans` | `preprocess` · `postprocess` |
| `number_sign` | `⠼` 가 수표인지 영어 약자인지 가른다(제40항) | | `number_sign_indices` · `contraction_lookalikes` · `has_number_sign` |
| `text_braille` · `formula_braille` · `table_braille` · `visual_braille` | 요소 점역 클래스 | 1.5 · 1.6 | `table_braille.parse_print_frames` · `record_rows_enabled` |
| `layout_braille` | 조판과 통 문자열 | 1.7 | `format_underline_blank` · `format_citation` · `format_paragraph_start` · `format_bullet_item` · `format_page_change_line` · `format_box_top` · `format_box_bottom` · `format_overflow_page_number` |
| `regulations` | 규정 조항표 | 1.8 | |
| `semojum_braille.schemas` | 데이터 타입(역점역과 함께 쓴다) | 2.3 | |
| `semojum_braille.sidecar` | 표준입출력 사이드카 | [sidecar.md](sidecar.md) | |
| `nested_block` | 시각 자료 안의 시각 자료를 글상자로 묶는다 | | `box_narrative` · `append_nested` |
| `isolation` | 요소별 격리 점역(한 요소 실패를 자리표시로) | | `safe_translate` · `dedupe_trail` |
| `tag_names` | 인라인 태그 이름 정본(2.1) | | `tn` · `box` · `indent_tag` · `split_indent` · `apply_indent_tags` · `strip_indent_tags` · `normalize_tn_spans` · `tn_spans_ok` |
| `tn_notices` | 점역자 주 문구 정본 | | `table_split` · `indent_hierarchy` · `omitted` · `reading_order` · `layout_scan` · `scene` |
| `gates` | 걸러 낸 자리를 쪽마다 센다 | | `gate_reset` · `gate_hit` · `gate_counts` · `gate_flags` · `strip_format_tokens` 등. `guard_on`(`LLM_TEXT_GUARD`)은 이 패키지 안에서는 부르는 곳이 없다 |
| `constants` | 조판 상수(`COLS = 32` · `ROWS = 26`) | | |

- 규정과 도서 관행이 갈리는 자리는 코드 주석에 판단 근거를 적어 두었다. 고칠 때는 `braille-source` 의 규정 원문과 대조한다.
- 점역 모듈은 `Semojum/AI` 저장소의 `app/ai/braille/` 에서 `tools/sync_from_ai.py` 로 옮겨 온다. 고칠 때는 그 저장소에서 고치고 다시 동기화한다([CONTRIBUTING.md](../CONTRIBUTING.md)).

---


## 5. 한계와 주의

**못 하는 것**
- 그림을 보고 설명을 짓지 않는다. 시각 자료는 설명 **글**을 받아 옮길 뿐이다. 글자 인식(OCR)도 하지 않는다.
- 악보(음악 점자)는 옮기지 않는다.
- 기호표에 없는 기호는 **경고 없이 빠진다**(`가▶나` → `⠫⠉`). 옮기기 전에 `symbol_table.json` 에 있는지 확인한다.
- 글 점역 함수(1.1)는 32칸으로 접지 않는다. 접힌 쪽이 필요하면 조판(1.7)을 쓰거나 docs/sidecar.md 의 접기 함수를 쓴다.
- 역점역은 [decoder.md](decoder.md).

**쓸 때 주의**
- 조판 함수(`render` · `layout` · `render_page_text`)는 넘긴 `BrailleOutput` 을 제자리에서 고친다. 같은 객체를 두 번 넣지 않는다(1.7).
- `layout` 은 지금 작업 폴더 아래 `storage/jobs/…` 에 파일을 쓴다(1.7).
- `<!표>` 태그는 `TableBraille` 에만 넣는다. 글 점역 함수에 넣으면 칸 글자가 붙어 버린다(2.1).
- "임포트" 스위치는 프로세스를 띄울 때 준다(3절).
- 역점역(`decoder`)은 점역 모듈의 비공개 이름을 쓴다. 두 모듈은 늘 같은 동기화 커밋에서 함께 옮긴다. 소스를 복사해 넣는다면 `semojum_braille/` 폴더를 통째로 넣는다.

**시험하지 않은 것**
- 스레드 안전. 코드에서 본 공유 상태는 이렇다. 걸러 낸 자리 계수기(`gates`)는 `ContextVar` 라 스레드·작업마다 따로 센다. 캐시 둘(`functools.lru_cache`)은 CPython 에서 스레드 안전하다.
- Windows(설치 크기, 사이드카 속도), 파이썬 3.11 · 3.14.
- BMP 밖 글자가 섞인 입력의 오프셋([sidecar.md](sidecar.md) 의 문자와 인코딩).

**알려진 결함** (2026-09-29, AI 8dc7e7b 기준으로 다시 확인)
- 원문이 낱말 가운데에서 줄을 바꾸고 앞 줄이 32칸 가까이 찼으면, `flatten_elements` 가 두 줄을 이으며 낱말 가운데에 빈칸을 넣는다. 교재 원문 `…초점을 맞춘 개념으\n로, 소리, 음성…` 이 `개념으 로,`(`⠈⠗⠉⠱⠢⠪⠀⠐⠥⠐`)가 된다. 사이드카의 `cells` 도 같다.
