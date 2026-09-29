# semojum-braille · 세모점 점역 엔진

묵자(한국어 글·수식·표·시각 자료 설명)를 한국어 점자로 옮긴다. 근거는 「한국 점자 규정」(문화체육관광부 2024), 「점자 도서 제작 지침」(국립장애인도서관 2025), 「점자 자료 제작 지침」(국립특수교육원 2025)이다.

**이 문서를 읽을 사람은 앱(C#) 개발자다.** 앱은 파이썬 함수를 직접 부르지 않는다. 이 엔진을 담은 파이썬 프로세스(**사이드카**)를 띄워 두고 표준입출력으로 말을 건다. 그래서 1·2절이 앱이 쓸 것이고, 파이썬 API 는 3절부터다.

| 절 | 내용 | 누가 읽나 |
|---|---|---|
| 1 | 사이드카 프로토콜 | 앱 개발자 |
| 2 | 32칸 접기(앱이 할 일) | 앱 개발자 |
| 3 | 정본 진입점 셋 | 엔진을 파이썬에서 부를 사람 |
| 4 | 모듈별 설명 | 엔진을 고칠 사람 |
| 5 | 쓰는 쪽이 알아야 할 것 | 모두 |

역점역(점자 → 글자)은 짝 저장소 `semojum-braille-back` 이다. 사이드카는 그 패키지가 함께 깔려 있으면 역점역도 받는다.

---

## 1. 사이드카 프로토콜

### 1.1 띄우기

```
python -m semojum_braille.sidecar
```

- 앱이 이 명령으로 프로세스를 **하나 띄워 두고 계속 쓴다.** 부를 때마다 새로 띄우지 않는다.
- 표준입력으로 요청 JSON 을 **한 줄에 하나** 보낸다. 표준출력으로 응답 JSON 이 **한 줄에 하나** 온다. 받은 순서대로 답한다.
- 표준오류에는 엔진 로그(경고)가 나온다. 응답은 표준출력에만 쓴다.
- 표준입력을 닫으면 사이드카가 끝난다.
- 역점역(`decode`)은 역점역 패키지(`semojum-braille-back`)가 깔려 있을 때만 된다. 없으면 `decode` 요청에 오류 응답이 온다.
- 기동하자마자 뒤에서 역점역을 한 번 불러 kiwi(형태소 분석기)를 미리 올린다. 영어책 역점역의 첫 호출이 약 2초 멈추는 것을 가리려는 것이다.

잰 값(리눅스, 2026-09-29): 기동부터 첫 응답까지 약 0.1초, 한 쪽(35요소·1,318자) 점역 약 0.21초, 보통 쪽 역점역 약 0.02초. Windows 값은 빌드 러너에서 다시 잰다.

### 1.2 문자와 인코딩

- JSON 은 **ASCII 로만** 오간다. 한글과 점자는 `\uXXXX` 로 적는다. 콘솔 코드 페이지와 상관없게 하려는 것이다. .NET `System.Text.Json` 의 기본 직렬화도 같은 꼴을 낸다.
- 점자는 유니코드 점자 블록(U+2800~U+28FF) 글자다. 점자 빈칸은 `⠀`(U+2800)이다.
- 점자·빈칸·줄바꿈이 모두 BMP 안이라 **C# `string` 인덱스와 이 문서의 오프셋이 같다.** `breaks` 값을 그대로 인덱스로 쓴다.
  단서 하나: 엔진이 점자로 못 옮긴 글자가 `cells` 에 드물게 남을 수 있다(엔진이 경고로 센다). 그 글자가 BMP 밖(이모지 등)이면 C# 에서는 두 칸으로 세어져 뒤 오프셋이 하나씩 밀린다. 그런 요소는 `breaks` 를 버리고 빈칸 자리로 접는다.

### 1.3 실제로 오간 줄

아래는 사이드카를 띄워 실제로 주고받은 줄이다(엔진 0.1.1). `→` 가 표준입력, `←` 가 표준출력이다.

**전선 위 모습 그대로** (제목 요소 하나):

```
→ {"id": 3, "op": "translate", "text": "1 국어의 탐구와 활용", "type": "title", "heading_level": 2}
← {"cells": "⠀⠀⠀⠀⠀⠀⠼⠁⠲⠀⠈⠍⠁⠎⠺⠀⠓⠢⠈⠍⠧⠀⠚⠧⠂⠬⠶", "breaks": [9, 10, 13, 14, 15, 16, 18, 20, 21, 22, 25], "id": 3}
```

아래부터는 `\uXXXX` 를 풀어 적는다.

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

`cells` 앞 두 칸(`⠀⠀`)은 문단 들여쓰기다(3칸에서 시작). 85칸짜리 한 줄이고 아직 32칸으로 안 접었다. 접는 법은 2절.

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

### 1.4 필드

**요청**

| op | 필드 | 타입 | 기본값 | 뜻 | 예 |
|---|---|---|---|---|---|
| 모두 | `id` | 아무 JSON 값 | 없음 | 응답에 그대로 돌아온다. 요청과 응답을 짝짓는 데 쓴다 | `2` |
| 모두 | `op` | 문자열 | 없음 | `translate` · `decode` · `ping` | `"translate"` |
| translate | `text` | 문자열 | `""` | 묵자 요소 하나. 줄바꿈은 `\n`. 서버가 준 태그(`<!수식>…<!/수식>` 등)를 그대로 넣는다 | `"대한민국의 모든…"` |
| translate | `type` | 문자열 | `"text"` | 요소 종류. `text` · `title` · `list_item` · `caption` 중 하나. 서버 응답의 요소 종류를 그대로 넘긴다. 들여쓰기가 이것에 따라 달라진다 | `"title"` |
| translate | `heading_level` | 정수 | `0` | 0 은 본문. 1~4 는 제목 단계다. 1단계는 가운데 정렬, 2단계는 7칸, 3·4단계는 5칸에서 시작한다 | `2` |
| decode | `braille` | 문자열 | `""` | 점자. 여러 줄이면 `\n` 으로 잇는다 | `"⠊⠗⠚⠒…"` |
| decode | `english` | 참거짓 | `false` | 영어 교과 책이면 `true`. 한글로 잘못 읽힌 영어 토막을 되찾는다. 다른 책에서는 켜지 않는다 | `true` |

**응답**

| op | 필드 | 타입 | 뜻 |
|---|---|---|---|
| 모두 | `id` | 요청과 같음 | 요청의 `id`. JSON 이 아닌 줄을 받으면 `null` |
| translate | `cells` | 문자열 | 점역 결과. 서버 `TextElement.contents` 의 **본문**과 같다. 들여쓰기 칸과 글머리 정정이 들어 있고, 논리 줄은 `\n` 으로 잇는다. **32칸으로 접지 않았다.** 서버 contents 에 붙는 앞뒤 빈 줄(제목·표 둘레)은 이웃 요소에 따라 정해지므로 여기에는 없다. 그 빈 줄은 앱의 조판이 넣는다 |
| translate | `breaks` | 정수 배열 | `cells` 안에서 줄을 바꿔도 되는 자리. 값 `b` 는 "`cells[b]` 앞에서 끊어도 된다" 는 뜻이다. 음절 경계와 빈칸 자리가 모두 들어 있다. 오름차순이다 |
| decode | `text` | 문자열 | 역점역한 글. 원문 복원이 아니라 **검수용 근사**다. 줄바꿈은 그대로 둔다 |
| ping | `ok` | 참거짓 | 늘 `true` |
| 실패 | `error` | 문자열 | `"예외이름: 내용"` 또는 설명. 이때 다른 필드는 없다 |

### 1.5 `breaks` 를 꼭 써야 하는 까닭

한국어 점자는 **한글을 음절 단위로 줄바꿈하는 것이 원칙**이다(「점자 자료 제작 지침」 2.1.1(2), 「점자 도서 제작 지침」 1장 2절 1). 그런데 셀만 봐서는 음절 경계를 알 수 없다. `⠉` 는 `나`(약자)이기도 하고 초성 ㄴ 이기도 하다. `나이`(⠉⠣⠕)에서 ⠉|⠣ 는 음절 안이고 ⠉⠣|⠕ 가 음절 경계다. 묵자를 아는 엔진만 이것을 가른다. 그래서 엔진이 자리를 알려 주고 앱은 그 자리에서만 끊는다.

- 2027 수능특강 8권 39,562요소 실측: `breaks` 없이 **빈칸에서만 접으면 66.7% 가 엔진과 다르게 접힌다.** `breaks` 로 접으면 엔진 조판과 다른 요소가 0이다.
- 지침은 시험 문제지처럼 특별한 경우 **어절 단위** 줄바꿈도 허용한다. 어절 단위로 접으려면 `breaks` 중 빈칸 자리만 쓰면 된다. 어느 쪽을 기본으로 할지는 점역사 자문 항목이다.

### 1.6 오류와 사이드카가 죽었을 때

- 한 요청이 실패하면 `error` 응답이 오고 사이드카는 계속 돈다(1.3 예).
- **표준오류를 반드시 비운다.** 엔진이 경고를 표준오류로 쓴다. C# 에서 `RedirectStandardError = true` 로 두고 읽지 않으면 파이프가 차서 사이드카가 멈춘다. `BeginErrorReadLine` 으로 비동기로 읽어 버리거나, 리디렉트를 끈다.
- 사이드카가 죽으면 표준출력이 닫힌다(C# `ReadLine()` 이 `null`). 앱은 다시 띄우고, 답을 못 받은 요청을 다시 보낸다. translate 와 decode 는 같은 입력에 늘 같은 출력을 내므로 다시 보내도 된다. 짧은 사이에 거듭 죽으면(예: 1분에 세 번) 다시 띄우기를 멈추고 사용자에게 알린다.
- 앱이 끝날 때 사이드카도 함께 끝나게 하려면 Windows Job Object(`JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`)에 넣는다. 평소에는 표준입력을 닫으면 스스로 끝난다.
- 이 저장소에는 C# 코드가 없다. 위 C# 이름(`Process`·`RedirectStandardError`·`BeginErrorReadLine`)은 .NET 표준 API 이고, 여기서 돌려 본 것은 같은 일을 하는 파이썬 부르는 쪽이다.

---

## 2. 32칸 접기 (앱이 할 일)

사이드카는 32칸으로 접지 않는다. 앱이 아래 함수로 접는다. 파이썬으로 적었지만 **C# 로 옮길 몫은 이 함수 하나다.**

```python
W, BLANK = 32, "⠀"


def fold(cells, breaks, center=False, cuts=None):
    """cells(논리 줄을 \\n 으로 이은 통 문자열)를 32칸 줄로 접는다. **앱(C#)이 할 몫.**

    breaks 자리(그 셀 앞)에서만 끊고, 32칸 안에 자리가 없을 때만 32칸째에서 강제로 자른다.
    자리 목록이 없는 줄(점역사가 점자를 직접 고친 요소 등)은 빈칸 자리에서 끊는다. 이어지는 줄 머리 빈칸은 버린다.
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

1.3 의 translate 응답(85칸)을 이 함수로 접은 실제 결과:

```
⠀⠀⠊⠗⠚⠒⠑⠟⠈⠍⠁⠺⠀⠑⠥⠊⠵⠀⠈⠍⠁⠑⠟⠵⠀⠘⠎⠃⠀⠣⠲⠝| 32칸
⠙⠻⠊⠪⠶⠚⠑⠱⠐⠀⠉⠍⠈⠍⠊⠵⠨⠕⠀⠠⠻⠘⠳⠕⠉⠀⠨⠿⠈⠬⠀ | 31칸
⠠⠊⠗⠑⠛⠝⠀⠰⠣⠘⠳⠘⠔⠨⠕⠀⠣⠉⠕⠚⠒⠊⠲         | 23칸
```

둘째 줄 끝의 `⠀` 는 빈칸 자리에서 끊은 흔적이다. 엔진 조판도 똑같이 끊는다.

**C# 로 옮길 때 지킬 것**

1. 32칸 안에서 **가장 먼** `breaks` 자리에서 끊는다. 그런 자리가 없을 때만 32칸째에서 강제로 자른다. 강제로 자를 때 점역자 주 표 `⠠⠄`(두 칸)는 가르지 않고 한 칸 앞에서 자른다.
2. 이어지는 줄의 머리에 오는 빈칸(`⠀`, 공백)은 버린다.
3. `breaks` 가 하나도 없는 줄은 빈칸 무리의 첫 자리에서 끊는다. **이때도 줄 머리 들여쓰기는 지킨다.** 줄 맨 앞의 빈칸 무리는 끊는 자리로 치지 않는다. 엔진의 대체 경로에 들여쓴 줄을 그대로 넣으면 들여쓰기가 없어지지만, 엔진 조판은 들여쓰기를 접은 뒤에 붙이므로 결과가 이 함수와 같다(8권 실측 3건).
4. 1단계 제목(`heading_level` 1)은 32칸을 넘어 접힌 줄만 조각마다 가운데로 놓는다. 안 접힌 줄은 `cells` 에 이미 가운데 여백이 있다.
5. `breaks` 값은 `cells` 전체 기준이다. 줄마다 그 줄의 시작 오프셋을 빼서 쓴다.
6. 점역사가 앱에서 어떤 요소의 **점자를 직접 고치면** 그 요소의 `breaks` 는 낡는다. 그 요소는 `breaks` 를 버리고 3번(빈칸 자리)으로 접는다.

**검증**: 2027 수능특강 8권(39,562요소)에서 이 함수로 접은 결과를 엔진 조판과 견줬다. 다른 요소가 0이다. `cells` 는 서버 contents 본문과 39,562요소 모두 같다.

---

## 3. 정본 진입점 셋

파이썬에서 부를 때 쓰는 입구다. 아래 출력은 실제로 돌린 결과다.

### 3.1 `translate_tagged_text(text, *, force_roman=False, qnum_period=True) -> str`

`semojum_braille.translator`. 묵자 한 덩어리를 점자 **문자열 하나**로 옮긴다. 줄은 `\n` 으로 이어 나온다.

| 인자 | 타입 | 기본값 | 뜻 |
|---|---|---|---|
| `text` | str | 없음 | 묵자. `<!수식>LaTeX<!/수식>` 같은 인라인 태그를 받는다 |
| `force_roman` | bool | False | 한글이 없는 조각에도 로마자표(⠴)를 붙인다. 꼬리말용이다(「한국 점자 규정」 제29항) |
| `qnum_period` | bool | True | 문항 번호 뒤 마침표 관행을 쓴다(번호 `1 ` 을 `1.` 로 적는다). 시각 자료 설명에서는 끈다 |

```
>>> translate_tagged_text('수학 점수가 3점 올랐다.')
'⠠⠍⠚⠁⠀⠨⠎⠢⠠⠍⠫⠀⠼⠉⠨⠎⠢⠀⠥⠂⠐⠣⠌⠊⠲'
>>> translate_tagged_text('<!수식>\\frac{1}{2}<!/수식>보다 큰 수')
'⠼⠃⠌⠼⠁⠀⠀⠘⠥⠊⠀⠋⠵⠀⠠⠍'
```

### 3.2 `translate_body(text) -> tuple[list[str], list[list[int]]]`

`semojum_braille.translator`. **본문 요소 하나**를 논리 줄별 점자와 줄별 줄바꿈 자리로 옮긴다. 제품과 채점기가 같이 쓰는 입구다. 사이드카의 `translate` 도 이것을 거친다(그 위에 들여쓰기를 붙인다).

| 인자 | 타입 | 뜻 |
|---|---|---|
| `text` | str | 본문 요소 하나의 묵자. 줄바꿈은 `\n` |

| 반환 | 뜻 |
|---|---|
| `list[str]` | 논리 줄마다 점자 한 줄. 32칸으로 안 접었다 |
| `list[list[int]]` | 줄마다 줄을 바꿔도 되는 자리(그 셀 앞). 그 줄 안 오프셋이다 |

```
>>> translate_body('DNA 지문은 1985년에 처음 쓰였다.')
(['⠴⠠⠠⠙⠝⠁⠲⠀⠨⠕⠑⠛⠵⠀⠼⠁⠊⠓⠑⠀⠉⠡⠝⠀⠰⠎⠪⠢⠀⠠⠠⠪⠱⠌⠊⠲'], [[7, 10, 12, 13, 14, 19, 22, 23, 24, 26, 28, 29, 32, 34]])
>>> translate_body('첫째 줄\n둘째 줄')
(['⠰⠎⠄⠠⠨⠗⠀⠨⠯', '⠊⠯⠠⠨⠗⠀⠨⠯'], [[3, 6, 7], [2, 5, 6]])
```

### 3.3 `decode(braille, *, math=False, english=False) -> str`

역점역 패키지 `semojum_braille_back`. 점자를 글자로 되돌린다. 자세한 것은 그 저장소 README.

```
>>> decode('⠴⠠⠠⠙⠝⠁⠲⠀⠨⠕⠑⠛⠵⠀⠼⠁⠊⠓⠑⠀⠉⠡⠝⠀⠰⠎⠪⠢⠀⠠⠠⠪⠱⠌⠊⠲')
'DNA 지문은 1985년에 처음 쓰였다.'
>>> decode('⠀⠀⠰⠠⠺⠒⠀⠠⠓⠪⠄⠎⠀⠭⠀⠛⠕⠬⠂⠀⠠⠇⠊⠁⠍⠦', english=True)
"  W= How's 옥 운이욜 Liam?"
>>> decode('⠀⠀⠰⠠⠺⠒⠀⠠⠓⠪⠄⠎⠀⠭⠀⠛⠕⠬⠂⠀⠠⠇⠊⠁⠍⠦')   # english=False
'  W= 틋어 옥 운이욜 싸닥우?'
```

---

## 4. 모듈별 설명

`semojum_braille` 안의 모듈이다. **여기 적은 이름만 공개 계약이다.** 밑줄(`_`)로 시작하는 이름은 적지 않았고, 판이 오르면 바뀔 수 있다. "엔진 안에서만 쓰는 이름" 칸의 것도 밖에서 기대지 않는다.

요소를 옮기는 클래스(`TextBraille` 등)는 모두 같은 꼴이다. `translate(optimized: list[LLMOutput]) -> list[BrailleOutput]` 이고, 한 요소가 실패하면 그 요소만 자리표시로 바뀌고 나머지는 계속 옮긴다.

### translator · 점역 코어
한글·영어·숫자·문장 부호·인라인 수식을 한 줄 점자로 옮긴다. 줄바꿈 자리도 여기서 계산한다.
규정 근거: 「한국 점자 규정」 한글·로마자·숫자·문장 부호 전반. 코드에 자주 적힌 조항은 제29항(로마자표) · 제49항(문장 부호) · 제56항(드러냄표) · 제57항(숨김표) · 제69항(단위) · 제72항(글머리표)이다.

| 함수 | 인자 | 반환 | 하는 일 |
|---|---|---|---|
| `translate_tagged_text` | `text: str`, `force_roman: bool = False`, `qnum_period: bool = True` | `str` | 3.1 |
| `translate_body` | `text: str` | `(list[str], list[list[int]])` | 3.2. 본문 요소 정본 입구 |
| `translate_with_breaks` | `text: str`, `force_roman: bool = False`, `qnum_period: bool = True` | `(list[str], list[list[int]])` | `translate_body` 의 속. 인자를 직접 정하고 싶을 때 |
| `translate_visual` | `text: str` | `(list[str], list[list[int]])` | 시각 자료 설명용 입구. 문항 번호 마침표 관행을 끈다 |
| `translate_plain` | `text: str` | `str` | 꼬리말처럼 짧은 글을 한 줄로. 한글이 없는 조각의 로마자에도 로마자표를 붙인다 |
| `sanitize_for_braille` | `text: str` | `str` | 점자로 못 옮기는 글자(글꼴 전용 영역 등)를 걷어 낸다 |

엔진 안에서만 쓰는 이름: `substitute_tags` · `normalize_print_draft` · `strip_leader_dots` · `merge_hidden_runs` · `dropped_pua` · `isolate_border_tags` · `box_borders_from_source` · `border_marker_spans` · `blank_marker_spans` · `tn_marker_spans` · `emphasis_marker_spans` · `source_has_tn`

### text_braille · 본문 요소
본문·제목·목록·캡션 요소를 `BrailleOutput` 으로 옮기고, 점역사가 판단할 자리(점역자 주·글상자·빈칸·드러냄표·판단이 갈리는 기호)를 근거(`rule_trail`)로 남긴다.
규정 근거: 「점자 도서 제작 지침」 1.2.5(글상자) · 1.2.6(점역자 주), 「한국 점자 규정」 제56항 · 제73항.

| 이름 | 인자 | 반환 | 하는 일 |
|---|---|---|---|
| `TextBraille().translate` | `optimized: list[LLMOutput]` | `list[BrailleOutput]` | 요소마다 `translate_body` 를 부르고 근거를 붙인다 |
| `content_rules` | `source: str`, `lines: list[str]` | `list[RuleApplication]` | 내용 규정 근거 목록. 지금은 빈 목록을 돌려준다(2026-08-08 결정) |

### formula_braille · 수식 요소
`LLMOutput.corrected_text` 의 LaTeX 를 수학 점자로 옮긴다.
규정 근거: 「한국 점자 규정」 수학 점자.

| 이름 | 인자 | 반환 | 하는 일 |
|---|---|---|---|
| `FormulaBraille().translate` | `optimized: list[LLMOutput]` | `list[BrailleOutput]` | 요소마다 LaTeX 를 점자 한 줄로. 분수·근호·첨자 같은 구조를 근거로 남긴다 |

실제 변환은 `kor_math_rules.convert_latex(latex: str) -> str` 이 한다.

### inline_math · 본문 속 수식 찾기
구분자 없이 본문에 섞인 수식(`x+1=3` 등)을 찾아 `<!수식>` 태그로 감싼다.
규정 근거: 「한국 점자 규정」 수학 점자.

| 함수 | 인자 | 반환 | 하는 일 |
|---|---|---|---|
| `wrap` | `text: str` | `str` | 평문 수식 구간을 `<!수식>…<!/수식>` 로 감싼 글 |
| `normalize` | `span: str` | `str` | 평문 수식 표기를 LaTeX 로 맞춘다 |

### eng_braille · 영어 구간
국어 문장 속 영어 구간을 영어 점자 약자(Grade 2)로 옮긴다.
규정 근거: 「한국 점자 규정」 제4장 로마자와 그리스 문자(제28항~제39항). `ebae=True` 는 역점역이 옛 영어 점자(EBAE) 책 줄을 되짚을 때만 쓴다.

| 함수 | 인자 | 반환 | 하는 일 |
|---|---|---|---|
| `translate` | `text: str`, `ebae: bool = False` | `str` | 영어 구간 문자열을 점자로. 낱말 밖 글자는 그대로 둔다 |
| `translate_word` | `word: str`, `ebae: bool = False` | `str` | 영어 낱말 하나를 점자로 |
| `iter_words` | `text: str` | 낱말 반복자 | 약자를 적용하는 단위 그대로 낱말을 뽑는다 |

### symbol_rules · 특수 기호
기호표(`symbol_table.json`)로 특수 기호를 점자로 바꾸고, 규정과 관행이 갈리는 기호의 자리를 근거로 남긴다.
규정 근거: 「한국 점자 규정」 제49항(문장 부호) · 제57항 · 제69항 · 제70항 · 제72항.

| 함수 | 인자 | 반환 | 하는 일 |
|---|---|---|---|
| `substitute_symbols` | `text: str` | `str` | 기호표로 특수 기호를 점자로 직접 바꾼다 |
| `symbol_rule_spans` | `source_text: str`, `braille: str` | `list[(start, end, rule_id)]` | 판단이 갈리는 기호가 점자 어디에 나왔는지 |

엔진 안에서만 쓰는 이름: `preprocess` · `postprocess`

### table_braille · 표 요소
표를 격자·전치·선형 가운데 `render_mode` 로 정한 모양으로 옮긴다.
규정 근거: 「점자 도서 제작 지침」 3.1(표) · 1.2.5 · 1.2.6.

| 이름 | 인자 | 반환 | 하는 일 |
|---|---|---|---|
| `TableBraille().translate` | `optimized: list[LLMOutput]` | `list[BrailleOutput]` | `corrected_text` 의 표를 `render_mode`(`table_grid` · `transposed` · `linear` 등)대로 옮긴다 |
| `build_table_tags` | `rows: list[list[str]]` | `str` | 행렬을 `<!표><!행><!칸>…` 태그 글로 |
| `parse_table_tags` | `text: str` | `list[list[str]]` 또는 None | 태그 글을 행렬로. 태그가 없으면 None |
| `print_layout` | `corrected_text: str`, `mode: str` | `str` | 표 초안의 묵자 배치 |

엔진 안에서만 쓰는 이름: `parse_print_frames` · `record_rows_enabled`

### layout_braille · 조판
요소들을 32칸 × 25줄 쪽으로 조판하고, 서버 응답용 통 문자열을 만든다.
규정 근거: 「점자 도서 제작 지침」 1장·2장(쪽 형식, 제목·문단 들여쓰기, 글상자 1.2.5, 글머리표), 「한국 점자 규정」 제72항 · 제73항.

| 이름 | 인자 | 반환 | 하는 일 |
|---|---|---|---|
| `flatten_elements` | `braille_outputs: list[BrailleOutput]`, `layout_result=None` | `dict[UUID, FlatElement]` | 요소별 통 문자열(서버 `contents`). **조판 전에** 부른다 |
| `LayoutBraille().render` | `braille_outputs`, `page_no: int`, `layout_result=None` | `(list[list[str]], float)` | 쪽별 조판 줄과 강제 분리 비율. 파일을 안 쓴다 |
| `LayoutBraille().layout` | `braille_outputs`, `page_no: int`, `job_id: str`, `layout_result=None` | `float` | `render` 뒤 파일로 저장한다 |
| `LayoutBraille().finalize` | `blocks: list[dict]`, `page_no: int = 1` | `list[list[str]]` | 점역사가 고친 블록(이미 32칸 줄)을 쪽으로 조립한다 |
| `render_page_text` | `braille_outputs`, `page_no: int`, `layout_result=None` | `list[list[str]]` | `render` 의 쪽 줄만 |
| `wordwrap_by_word` | 없음 | `bool` | 어절 단위 줄바꿈 스위치(`BRAILLE_WORDWRAP=word`)가 켜졌나 |
| `FlatElement` | | | `text` · `trail` · `prefix` · `suffix` · `draft_texts` 를 가진 튜플 |

⚠ `layout_result` 는 `elements` 속성을 가진 아무 객체면 된다. 엔진은 요소마다 `element_id` · `type` · `reading_order` · `heading_level` 넷만 읽는다. **넘기지 않아도 예외가 나지 않는다.** 대신 요소 종류와 제목 단계를 모른 채 조판한다.

엔진 안에서만 쓰는 이름: `format_underline_blank` · `format_citation` · `format_paragraph_start` · `format_bullet_item` · `format_page_change_line` · `format_box_top` · `format_box_bottom` · `format_overflow_page_number`

### visual_braille · 시각 자료
그림·그래프·도표·만화 설명을 점자로 옮긴다. 설명 초안이 여럿이면 초안마다 옮긴다.
규정 근거: 「점자 도서 제작 지침」 1.2.1 · 1.2.5 · 1.2.6, 「점자 자료 제작 지침」 시각 자료 장.

| 이름 | 인자 | 반환 | 하는 일 |
|---|---|---|---|
| `VisualBraille().translate` | `optimized: list[LLMOutput]` | `list[BrailleOutput]` | 초안별로 점역한다. 초안은 `BrailleOutput.drafts` 에 담긴다 |
| `ImageBraille` · `ChartGraphBraille` | 같음 | 같음 | 그림·그래프용. 하는 일은 `VisualBraille` 와 같다 |
| `DiagramBraille` | 같음 | 같음 | 개념도·흐름도. 줄별 들여쓰기를 가진 골격 하나를 낸다 |
| `CartoonBraille` | 같음 | 같음 | 만화. 장면·대사 들여쓰기 골격(`line_indents`)을 따른다 |

### regulations · 규정 근거표
규정 조항표(`regulations.json`, 239조항)를 읽어 근거(`RuleApplication`)를 만든다. 184조항이 「한국 점자 규정」, 42조항이 「점자 도서 제작 지침」, 13조항이 「점자 자료 제작 지침」이다.

| 함수 | 인자 | 반환 | 하는 일 |
|---|---|---|---|
| `make_rule` | `rule_id: str`, `line_no: int = -1`, `col_start: int = 0`, `col_end: int = 0`, `tag: str = ""`, `priority: str = "primary"` | `RuleApplication` | 조항 번호로 근거 하나를 만든다 |
| `make_rule_at` | `rule_id: str`, `lines: list[str]`, `start: int`, `end: int`, `tag: str = ""`, `priority: str = "primary"` | `RuleApplication` | 점자 문자열 오프셋을 요소 좌표로 바꿔 근거를 만든다 |
| `rule_meta` | `rule_id: str` | `dict` 또는 None | 조항 원본 메타(발행처·판·절 위계) |
| `section_text` | `section: dict[str, str]` | `str` | 절 위계를 한 줄 글로 |
| `all_rule_ids` | 없음 | `frozenset[str]` | 등록된 조항 번호 전부 |

### schemas · 데이터 모델
엔진이 주고받는 다섯 타입(pydantic 모델)이다.

| 타입 | 주요 필드 | 쓰임 |
|---|---|---|
| `LLMOutput` | `element_id: UUID` · `corrected_text: str` · `routing_tier: str`(필수, 예 `"ZERO"`) · `render_mode: str = "text_only"` · `tn_text: str | None` | 요소 하나의 입력 |
| `BrailleOutput` | `element_id` · `braille_lines: list[str]` · `break_points: list[list[int]]` · `rule_trail: list[RuleApplication]` · `box_borders` · `drafts` · `line_indents` | 요소 하나의 출력. `break_points` 는 줄마다 줄을 바꿔도 되는 자리 |
| `RuleApplication` | `rule_id` · `source` · `section` · `rule_name` · `contents` · `line_no` · `col_start` · `col_end` · `tag` | 근거 하나. 점역사 화면에서 "왜 이렇게 옮겼나" 로 보인다 |
| `Draft` | `option` · `text` · `braille_lines` · `break_points` · `label` | 시각 자료 설명 초안 하나 |
| `BoxBorder` | `kind` · `level` · `title` | 글상자 테두리 메타 |

### 그 밖의 모듈
엔진 안에서 쓰는 모듈이다. 밖에서 부를 일은 드물다.

| 모듈 | 하는 일 |
|---|---|
| `kor_math_rules` | LaTeX 를 수학 점자로(`convert_latex(latex: str) -> str`) |
| `number_sign` | `⠼` 가 수표인지 영어 약자인지 가른다(「한국 점자 규정」 제40항) |
| `nested_block` | 시각 자료 안의 시각 자료를 글상자로 묶는다 |
| `isolation` | 요소별 격리 점역(`safe_translate`) |
| `tag_names` | 인라인 태그 이름 정본(`<!점역자주>` 등) |
| `tn_notices` | 점역자 주 문구 정본 |
| `gates` | 걸러 낸 자리를 쪽마다 센다(품질 플래그용) |
| `constants` | 조판 상수(32칸 등) |

---

## 5. 쓰는 쪽이 알아야 할 것

### 5.1 파이썬 판

- **앱에는 파이썬 3.13 을 넣는다.** 설치 하한은 3.10 이다(`requires-python >=3.10`). AI 서버가 3.10 이라 하한을 올리지 않았다.
- 3.10 · 3.12 · 3.13 에서 시험 전수(엔진 857 통과)와 출력(2027 주자 8권 45,534요소 바이트 비교)이 같다.
- 3.13 을 고른 까닭: 설치본에 넣을 Windows 임베더블 파이썬은 판마다 바이너리가 나오는 기간이 정해져 있다. 3.12 는 3.12.10(2025-04)에서 멈췄다. 3.13 은 3.13.15(2026-08)가 나와 있고, 2026-10 무렵부터는 소스로만 나온다. **어느 판이든 설치본 파이썬은 2년마다 올려야 한다.** 앱 릴리스 일정에 넣는다.
- 3.14 는 지금 의존 판(numpy 2.2.6)에 Windows 휠이 없어 쓰지 않는다.

### 5.2 의존과 크기

| 묶음 | 들어가는 것 | 크기 |
|---|---|---:|
| 파이썬 | Windows 임베더블 3.13.15 | 압축 11.0MB, 풀면 21.3MB |
| 점역 엔진 | `braillify==2.0.1`(Rust 확장, 한글 약자) · `pydantic>=2.9,<3`(pydantic-core Rust 확장) · 이 패키지 0.76MB | 약 23MB |
| 역점역 | 역점역 패키지 0.55MB, kiwi 를 넣으면 +213MB | 아래 5.3 |

크기는 리눅스 설치 크기다. Windows 값은 빌드 러너에서 다시 잰다. `braillify` 는 패키지 메타데이터의 라이선스 칸이 비어 있다. 배포 전에 확인한다.

### 5.3 역점역에 kiwi 를 넣을지 (결정 전이라 둘 다 적는다)

역점역은 영어책에서 "이 한글 읽기가 실제 한국어 낱말인가" 를 가르려고 형태소 분석기 kiwi(`kiwipiepy`)를 쓴다. 넣으면 크고, 안 넣으면 대체 판정이 필요하다.

| 판정 방식 | 지킨 한국어 줄 | 막은 영어 줄 | 순이득 | 추가 크기 |
|---|---:|---:|---:|---:|
| kiwi (지금) | 278 | 147 | +131 | 213MB |
| 낱말 목록(입력 묵자에서 뽑은 27,790개) | 196 | 7 | +189 | 0.38MB |
| 폴백 없음 | 0 | 0 | 0 | 0 |

- 역점역 코퍼스 94권 18,892쪽 실측(2026-09-29). 영어 사전으로 갈랐고, 쪽마다 앞 세 줄을 셌다. 자세한 것은 역점역 저장소 README.
- ⚠ **지금 코드는 kiwi 가 필수다.** 빼면 kiwi 판정이 불리는 쪽(영어책의 67%)에서 역점역이 오류를 낸다. 낱말 목록으로 바꾸는 것은 결정 뒤에 넣는다.
- 점역(묵자 → 점자)은 kiwi 를 쓰지 않는다. 사이드카의 `translate` 는 kiwi 와 상관없다.

### 5.4 문자와 파일
- 점자는 유니코드 점자 블록(U+2800~U+28FF) 글자다. 점자 빈칸은 `⠀`(U+2800)이다. ASCII 점자(BRF)가 아니다.
- 파일은 모두 UTF-8 로 읽고 쓴다.

### 5.5 스레드
- 스레드 안전을 **시험하지는 않았다.** 코드에서 확인한 공유 상태는 이렇다. 걸러 낸 자리 계수기(`gates`)는 ContextVar 라 스레드·작업마다 따로 센다. 캐시 둘(`functools.lru_cache`)은 CPython 에서 스레드 안전하다. 역점역의 kiwi·음절표는 처음 부를 때 적재하는데 잠금이 없어, 동시에 처음 부르면 두 번 적재될 수 있다(결과는 같다).
- 점역은 CPU 계산이라 스레드를 늘려도 빨라지지 않는다(GIL). **사이드카 하나가 요청을 차례로 처리하게 두고**, 동시에 여러 건이 필요하면 사이드카를 여럿 띄운다.

### 5.6 환경 변수 스위치는 임포트할 때 굳는다

모듈 전역으로 읽는 스위치는 **처음 임포트할 때 한 번 읽는다.** 사이드카를 띄운 뒤 바꾸면 안 먹는다. 필요하면 사이드카를 띄울 때 환경 변수로 준다.

| 스위치 | 읽는 때 | 기본값 | 뜻 |
|---|---|---|---|
| `BRAILLE_STYLE` | 임포트 | `book` | `book` 은 도서 관행, `regulation` 은 규정형(원장 판정 항목들) |
| `TABLE_SHORTEN` | 임포트 | `1` | 표 줄이기. `0` 이면 끈다 |
| `TABLE_RECORD_MIN_CELL` | 임포트 | `42` | 칸 기록 모드로 넘어가는 칸 길이 문턱 |
| `BRAILLE_WORDWRAP` | 부를 때 | `syllable` | `word` 면 어절 단위 줄바꿈 |
| `TABLE_GRID_SEP` | 부를 때 | 없음 | `colon` 이면 표 격자 칸을 쌍점으로 가른다 |
| `TABLE_RECORD_ROWS` | 부를 때 | `0` | `1` 이면 칸이 길 때 한 줄에 칸 하나로 적는다 |
| `LLM_TEXT_GUARD` | 부를 때 | `1` | `0` 이면 입력 정화 관문을 끈다 |

역점역 패키지의 스위치는 그 저장소 README 에 있다.

### 5.7 역점역 패키지와 짝 맞추기
역점역 패키지는 이 엔진의 내부 표를 쓴다. 그래서 `semojum-braille-back` 이 이 엔진 판을 `==` 로 묶는다(지금 `==0.1.1`). pip 로 깔면 판이 어긋날 때 설치가 막힌다. **소스를 통째로 복사해 넣는다면 두 저장소를 같은 동기화 커밋끼리 넣는다.** 어긋나면 임포트 때가 아니라 영어가 섞인 입력이 올 때 `TypeError` 가 난다.

### 5.8 설치와 시험
```
pip install -e .            # 개발용
pip install -e .[test]      # 시험 도구까지
pytest                      # 857 통과 · 3 xfail (2026-09-29, 3.10·3.12·3.13 같음)
```

이 저장소는 AI 서버 저장소(`Semojum/AI`)의 `app/ai/braille/` 에서 동기화해 만든다. 규정을 고칠 때는 AI 저장소에서 고치고 다시 동기화한다.
