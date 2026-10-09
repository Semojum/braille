# 조판 세 구현 (`semojum_braille.assist` · `ts/` · `java/`)

> braille-assist develop 38e21e2 에서 `ts/` · `java/` · `vectors.json` · `tools/gen_vectors.py` 를 구조 그대로 옮겨 왔다(2026-10-09).
> 파이썬 기준 구현은 10-04 에 먼저 옮겨 와 `semojum_braille/assist.py` 에 있다. braille-assist 저장소는 지우지 않고 얼려 둔다.
> 아래는 braille-assist README 를 옮긴 것이고, 설치 · 시험 · 구현 자리만 이 저장소에 맞게 고쳤다.

점자 조판 라이브러리. 이미 점역된 점자 문자열을 받아 **면으로 나누고, 줄을 자르고,
페이지행과 변경선을 붙인다.** 점역은 하지 않는다.

`python` · `ts` · `java` 세 구현이 같은 출력을 내고, 루트 `vectors.json` 으로 CI 가 그걸 검증한다
(파이썬은 `test.yml` 의 pytest, ts · java 는 `assist.yml`). 규칙이 바뀌면 세 구현과 벡터를 한 PR로 갱신한다.

| 구현 | 자리 | 쓰는 곳 |
|---|---|---|
| python(기준 구현) | `semojum_braille/assist.py` | 앱 엔진 · AI |
| ts | `ts/` | FE 에디터 화면 |
| java | `java/` | BE 다운로드 파일 생성 |

용어 두 개만 미리 짚는다.

- **페이지행**: 점자 면의 맨 아랫줄. 원본 페이지 번호(왼쪽) · 꼬리말(가운데) · 점자 면 번호(오른쪽).
- **원본 페이지 변경선**: 원본 한 쪽이 끝나는 다음 줄. `⠤`로 채우고 오른쪽 끝에 새 원본 페이지 번호만.

---

## 설치

```bash
pip install "semojum-braille @ git+https://github.com/Semojum/braille"   # python
# ts:   이 저장소의 ts/ 를 경로로 쓴다. 패키지 이름 @semojum/braille-assist 0.1.0(npm 에 내지 않았다)
# java: 이 저장소의 java/. com.semojum:braille-assist:0.1.0
```

## 빠른 시작

```py
from semojum_braille.assist import build_brf, build_pages_from_job

brf = build_brf(job)                                    # .brf 파일 내용
pages = build_pages_from_job(job)                       # 면 배열 (화면용)
txt = "\n".join(line for p in pages for line in p)      # .txt 파일 내용
```

```ts
import { buildBrf, buildPagesFromJob } from '@semojum/braille-assist';
const pages = buildPagesFromJob(job);   // string[][]
```

```java
String brf = BrailleAssist.buildBrf(job);
List<List<String>> pages = BrailleAssist.buildPagesFromJob(job);
```

FE와 BE가 같은 Job으로 같은 결과를 얻는다. 화면과 다운로드가 갈라지지 않는다.

---

# 함수

ts는 같은 이름의 camelCase, java는 `BrailleAssist` 클래스의 정적 메서드다.

## build_brf(job)

Job JSON을 받아 `.brf` 파일에 그대로 쓸 문자열을 돌려준다. 조판부터 BRF-ASCII 변환까지 한 번에 한다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `job` | dict | [Job JSON](#job-json) |

**반환** `str`: 줄바꿈 `\n`으로 이어진 BRF-ASCII.

```py
build_brf(job)   # '#gb         s<togo@!        #aje\n...'
```

## build_pages_from_job(job)

같은 Job을 받아 **유니코드 점자 면 배열**을 돌려준다. 화면에 그리거나 `.txt`를 만들 때 쓴다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `job` | dict | [Job JSON](#job-json) |

**반환** `list[list[str]]`: 면마다 `rows`개의 줄. 페이지행이 들어가는 면은 마지막 줄이 페이지행이다.

`.brf`와 `.txt`는 같은 조판 결과의 다른 표기다. 면 사이에 구분자를 넣지 않는다.
점자 프린터가 면마다 폼피드를 요구하면 `"\f".join("\n".join(p) for p in pages)`처럼 호출부에서 넣는다.

## build_pages(sources, footer, start_braille_page, opts, footers)

Job 형식을 쓰지 않을 때의 저수준 진입점. 원본 쪽별 통 문자열을 받아 면 배열을 만든다.

| 매개변수 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `sources` | list | (필수) | `[{"orig_page": int, "blocks": [{"order": int, "text": str}]}]`. `blocks`는 `order`로 정렬해 이어 붙인다 |
| `footer` | str | `""` | 문서 전체 기본 꼬리말 (이미 점역된 점자) |
| `start_braille_page` | int | `1` | 첫 면의 점자 면 번호 |
| `opts` | Options | 기본값 | [Options](#options) |
| `footers` | dict | `None` | `{점자 면 번호: 꼬리말}`. 그 면만 다르게. 없는 면은 `footer`를 쓴다 |

**반환** `list[list[str]]`

```py
build_pages(
    sources=[{"orig_page": 7, "blocks": [{"order": 1, "text": "…통 문자열…"}]},
             {"orig_page": 8, "blocks": [{"order": 1, "text": "…"}]}],
    footer="⠎⠣⠞⠕⠛⠕⠈⠮",
    footers={3: "⠈⠮"},
)
```

## page_row(orig_page, cont_idx, braille_page, footer, opts)

페이지행 한 줄을 만든다. 줄 하나만 다시 그릴 때 쓴다.

| 매개변수 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `orig_page` | int | (필수) | 원본 페이지 번호 (왼쪽) |
| `cont_idx` | int | (필수) | 걸침 순번. 원본 한 쪽이 여러 면에 걸칠 때 두 번째 면부터 1, 2, 3… 번호 앞에 `a`, `b`, `c`가 붙는다 |
| `braille_page` | int | (필수) | 점자 면 번호 (오른쪽) |
| `footer` | str | `""` | 꼬리말 (이미 점역된 점자). 자리보다 길면 들어가는 만큼만 |
| `opts` | Options | 기본값 | [Options](#options) |

**반환** `str`: 길이가 정확히 `opts.cols`인 한 줄.

```py
page_row(orig_page=72, cont_idx=0, braille_page=105, footer="⠎⠣⠞⠕⠛⠕⠈⠮")
# '⠼⠛⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠎⠣⠞⠕⠛⠕⠈⠮⠀⠀⠀⠀⠀⠀⠀⠀⠼⠁⠚⠑'
```

`cont_idx`는 **점자 면 순번**이지 페이지행 순번이 아니다. 페이지행을 홀수 면에만 찍으면
`a`(2번째 면)·`c`(4번째 면)는 화면에 안 나타나고 `b`·`d`만 보인다. 순번이 건너뛴 게 아니다.

## page_change_line(orig_page, opts)

원본 페이지 변경선 한 줄을 만든다.

| 매개변수 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `orig_page` | int | (필수) | 새로 시작하는 원본 페이지 번호 |
| `opts` | Options | 기본값 | [Options](#options) |

**반환** `str`: 길이가 정확히 `opts.cols`인 한 줄.

```py
page_change_line(orig_page=72)
# '⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠼⠛⠃'
```

## to_brf_ascii(braille)

유니코드 점자를 BRF-ASCII로 바꾼다. 파일에 쓰기 직전에 부른다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `braille` | str | 유니코드 점자 (U+2800–U+28FF) |

**반환** `str`: 소문자 BRF-ASCII. 줄바꿈은 보존한다. 공백 셀 `⠀`는 리터럴 스페이스가 되고,
표에 없는 문자는 버리지 않고 `⟨XXXX⟩`(코드포인트)로 남는다.

```py
to_brf_ascii("⠼⠁⠃")   # '#ab'
```

## options_from_job(job)

Job의 `options`를 `Options`로 바꾼다. 위 함수들이 내부에서 부르므로 직접 쓸 일은 드물다.

## wrap(line, cols, mode, breaks, center)

논리 줄 하나를 `cols` 칸 줄들로 접는다. 줄바꿈 세 갈래(2026-10-09 대표 결재, 기본 음절). `build_pages` 가 줄마다
이것을 부른다. FE 미리보기처럼 면 조립 없이 한 줄만 접을 때 바로 부른다.

| 매개변수 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `line` | str | (필수) | 접을 줄. `\n` 이 없어야 한다 |
| `cols` | int | `32` | 한 줄 칸 수 |
| `mode` | str | `"syllable"` | `syllable` · `word` · `cell` |
| `breaks` | list[int] | `None` | 그 셀 앞에서 끊어도 되는 자리(**이 줄 기준** 오프셋). AI 응답 `breaks` 에서 이 줄 시작 오프셋을 뺀 값 |
| `center` | bool | `False` | 1단계 제목. `cols` 를 넘어 접힌 줄만 조각마다 가운데에 놓는다 |

| 갈래 | 자르는 자리 |
|---|---|
| `syllable`(기본) | `cols` 칸 안에서 가장 먼 `breaks` 자리. 없으면 `cols` 칸째에서 강제로 자르되 점역자 주 표 `⠠⠄` 는 가르지 않는다. 이어지는 줄 머리 빈칸은 버린다. **`breaks` 가 비면 `word` 로 접는다**(옛 응답 · 점자를 직접 고친 요소) |
| `word` | 빈칸(어절) 자리. 어절 하나가 폭을 넘을 때만 강제로 자른다 |
| `cell` | `cols` 칸마다 그대로 자른다. 빈칸을 버리지 않고 가운데에도 놓지 않는다(옛 동작) |

**반환** `list[str]`

`syllable` 의 셈은 앱 사이드카 문서([sidecar.md](sidecar.md) §5)의 `fold` 와 같다. 사이드카 `translate` 로 낸 요소
3,000개를 두 함수로 접어 가운데 놓기 켬 · 끔 6,000가지를 견주니 5,998이 같았다. 다른 2는 한문 시 한 편이 모두 빈 줄로
나온 경우로, 끝 개행을 종결자로 보는 `build_pages` 약속 때문이다.

---

## Options

```py
Options(
    cols=32,                  # 한 줄 칸 수
    rows=26,                  # 한 면 줄 수
    show_orig_page=True,      # 페이지행 왼쪽의 원본 페이지 번호
    show_braille_page=True,   # 페이지행 오른쪽의 점자 면 번호
    page_row_on="odd",        # 페이지행을 넣는 면: odd | every | even | none
    cover_pages=0,            # 앞에서 이만큼의 원본 페이지가 표지
    orig_page_start=None,     # 표지 다음 첫 본문 페이지에 붙일 번호
    show_change_line=True,    # 원본 페이지 변경선
    footer_align="center",    # 꼬리말 정렬: center | right
    wrap="syllable",          # 줄바꿈: syllable | word | cell
)
```

| 항목 | 설명 |
|---|---|
| `cols` · `rows` | 면 규격. 8 미만이면 예외 |
| `show_orig_page` | 끄면 페이지행 왼쪽이 비고, **변경선도 함께 꺼진다**(적을 번호가 없으므로) |
| `show_braille_page` | 페이지행 오른쪽 |
| `page_row_on` | `odd` 홀수 면 · `every` 모든 면 · `even` 짝수 면 · `none` 안 넣음 |
| `cover_pages` | **원본 페이지 개수**다(면 수가 아니다). 표지에는 페이지행을 넣지 않고, 점자 면 번호도 소비하지 않는다(표지 다음 면이 `start_braille_page`). 본문 번호를 그 뒤부터 센다 |
| `orig_page_start` | `None`이면 `sources`가 준 `orig_page`를 그대로 쓴다. 값을 주면 표지 뒤 n번째 = `orig_page_start + n` |
| `show_change_line` | 변경선 켜기·끄기 |
| `footer_align` | `right`면 점자 면 번호에서 두 칸 띄운 자리가 오른쪽 끝이다 |
| `wrap` | 32칸을 넘는 줄을 접는 갈래([wrap](#wraplinecolsmodebreakscenter)). 블록에 `breaks` 가 없으면 `syllable` 이어도 `word` 로 접는다 |

---

## Job JSON

BE가 편집 최종본을 모아 넘기는 형식. `build_brf`와 `build_pages_from_job`이 이걸 받는다.

```jsonc
{
  "job_id": "j1",
  "options": {
    "include_page_number": true,   // 페이지행 켜기·끄기. 끄면 page_row_on 을 무시한다
    "page_row_on": "odd",
    "cols": 32,
    "rows": 26,
    "show_orig_page": true,
    "show_braille_page": true,
    "cover_pages": 0,
    "orig_page_start": null,
    "show_change_line": true,
    "footer_align": "center",
    "wrap": "syllable"              // 줄바꿈 갈래: syllable | word | cell
  },
  "footer_braille": "⠎⠣⠞⠕⠛⠕⠈⠮",       // 문서 전체 기본 꼬리말
  "footers_braille": { "3": "⠈⠮" },   // 면별 꼬리말 (선택)
  "start_braille_page": 1,
  "pages": [
    { "orig_page_no": 7,
      "elements": [
        { "id": "e1", "type": "title", "heading_level": 1, "text": "⠀⠀⠠⠕⠂⠠⠪⠃\n" },
        { "id": "e2", "type": "text",  "heading_level": 0, "text": "⠀⠀⠕⠰⠗⠁⠵⠀⠙⠣⠕\n",
          "breaks": [3, 5, 7] }           // 응답 TextElement.breaks 그대로(선택)
      ] }
  ]
}
```

`options`의 항목은 전부 선택이다. 빠지면 위 기본값이 쓰인다.

**`elements` 배열 순서가 읽기 순서다.** `order` 필드는 없다.

**들여쓰기 · 가운데 정렬 · 구조적 빈 줄은 AI가 이미 `text` 안에 넣어 보낸다.** 여기서 또 넣지 않는다.
`type` 은 쓰지 않는다. `heading_level` 은 **1단계 제목이 32칸을 넘어 접힐 때만** 조각을 가운데에 놓는 데 쓴다.

**`breaks`(선택)는 AI 응답 `TextElement.breaks` 를 그대로 넣는다.** 오프셋은 `text` 기준이라, 응답
`contents[0]` 를 고치지 않고 `text` 에 넣어야 한다(앞뒤 빈 줄을 떼면 어긋난다). 점역사가 점자를 직접 고친 요소는
`breaks` 를 비우고, 그 요소는 `word` 로 접힌다.

---

## 조판 설정 화면과의 대응

| 설정 화면 | Job |
|---|---|
| 페이지행 넣기 | `options.include_page_number` |
| 넣을 페이지 (홀수 · 모든) | `options.page_row_on` |
| 원본 페이지 번호 · 점자 페이지 번호 | `options.show_orig_page` · `options.show_braille_page` |
| 꼬리말 | `footer_braille` |
| 꼬리말 정렬 | `options.footer_align` |
| 꼬리말 수정 범위 | `footers_braille` |
| 원본 페이지 변경선 | `options.show_change_line` |
| 표지 페이지 수 | `options.cover_pages` |
| 원본 페이지 번호 시작 | `options.orig_page_start` |
| 점자 페이지 번호 시작 | `start_braille_page` |
| 한 줄 칸 수 · 한 페이지 줄 수 | `options.cols` · `options.rows` |

### 꼬리말 범위는 FE가 푼다

"이 면부터 끝까지 / 이 면만"은 편집 시점의 뜻이지 조판 규칙이 아니다. 이 라이브러리가
그걸 알려면 편집 이력을 들고 있어야 한다. FE가 범위를 풀어 면별 값으로 넘긴다.

```
5면 꼬리말을 "부록"으로 바꾸고 [이 면부터 끝까지], 문서가 8면이면
  footers_braille = { "5": "⠘⠮", "6": "⠘⠮", "7": "⠘⠮", "8": "⠘⠮" }

[이 면만]이면
  footers_braille = { "5": "⠘⠮" }
```

### 꼬리말은 어디서 오나

이 라이브러리는 점역하지 않는다. 점역사가 묵자로 적으면 BE가 AI 서버의 `TranslateText`로
보내(200자 초과는 거절된다) 점자 문자열을 받고, 그걸 `footer_braille`에 넣는다.

---

## 이 라이브러리가 하지 않는 것

| | 누가 하나 |
|---|---|
| 묵자 → 점자 점역 | AI 서버 (`ProcessPage`, 꼬리말은 `TranslateText`) |
| 들여쓰기 · 가운데 정렬 · 구조적 빈 줄 | AI 서버가 `text` 안에 넣어 보낸다 |
| 꼬리말 "이후 전부 / 이 면만" 해석 | FE |
| 묵자 → 점자 점역·음절 경계 판정 | AI 서버. 응답 `breaks` 로 받는다. 이 레포는 셀만 보므로 `breaks` 가 없으면 **빈칸(어절) 경계**로만 접는다 |

> **`cols`를 32에서 바꿀 때 주의.** 본문은 새 폭으로 다시 접히지만 글상자 테두리와 표 격자는
> AI가 32칸으로 이미 만들어 보낸 뒤라 어긋난다. AI 쪽이 `cols`를 받도록 고치기 전에는
> 화면에서 32 고정으로 두는 편이 안전하다. `rows`는 조판 단계에서만 쓰이므로 바꿔도 된다.

---

## 테스트

```bash
pytest test/test_assist_vectors.py   # python
cd ts && npm install && npm test     # ts (빌드 없이 돈다)
cd java && mvn test                  # java
```

`vectors.json`이 유일한 정답 파일이다(0.4.0, 케이스 70건). 지침 원문에서 사람이 대조한 값은 `source` 필드에
조항이 적혀 있고, 나머지는 회귀 방지용이다. 줄바꿈 세 갈래 사례 17건(0.4.0 에서 더함)의 줄과 끊을 자리는
사이드카 `translate` 로 한 번 뽑아 값으로 굳혔다.
**케이스 정의의 정본은 `tools/gen_vectors.py`다.** 벡터를 손으로만 더하면 재생성할 때 조용히 사라진다
(2026-09-08에 쪽바꿈 3건·어절 줄바꿈 1건이 그렇게 빠질 뻔했다).

벡터를 다시 만들 때는 `python tools/gen_vectors.py`. **다시 만들기 전에 지침 근거 케이스가
그대로 통과하는지 먼저 확인할 것.** 그 값들은 구현의 출력이 아니라 사람이 확인한 정답이다.

---

## 근거

조판 규칙은 전부 「점자 도서 제작 지침」에 근거가 있다. 가정으로 채운 값은 없다.

| 규칙 | 조항 |
|---|---|
| 페이지행 = 면의 마지막 줄, 원본 쪽 번호 · 꼬리말 · 점자 면 번호 순 | 1장 2절 2 |
| 원본 쪽 번호 왼쪽 정렬, 첫 칸 | 1장 2절 2-2(2) |
| 걸침 알파벳은 두 번째 면부터 번호 앞에, 로마자표 없이 | 1장 2절 2-2(3) · [예 1-7] |
| 꼬리말 가운데 정렬, 항목 사이 두 칸 이상 | 1장 3-1) |
| 꼬리말이 자리보다 길면 들어가는 만큼만 | 1장 3-4) |
| 점자 면 번호 오른쪽 정렬 | 1장 2절 2-3(1) |
| 페이지행은 홀수 면에만 (`page_row_on` 기본값) | 1장 2절 2-1 · 원장 C-11 |
| 페이지행의 원본 번호 = 그 면 첫 줄이 속한 원본 쪽 | 1장 2절 2-2(4) |
| 면 규격 32칸 × 26줄 | 1장 3 |
| 변경선은 첫 칸부터 `⠤`, 오른쪽 끝에 새 원본 쪽 번호 | 2장 2절 2-3(1) |
| 면 첫 줄의 빈 줄은 **살린다**(문서 맨 앞만 예외) | 도서지침 2장2절2 2)(3) · 자료지침 §2.4.4(3) |
| 요소 통 문자열의 **끝 개행은 줄 종결자**다. 빈 줄로 세지 않는다 | AI `flatten_elements` 계약(`suffix = "\n" * (after + 1)`) |
| 표지 면은 점자 면 번호를 소비하지 않는다(표지 다음 면이 1) | 도서지침 1장2 3)(1) · 자료지침 §2.1.5(1) |
| 32칸을 넘으면 기본은 **음절** 경계(`breaks`)에서 접는다. 어절 · 셀은 고르는 값이다 | 자료지침 §2.1.1(2)(446~449행 "한글은 음절 단위 줄바꿈을 원칙", 시험 문제지 등은 어절 허용) · 원장 C-83 · 대표 결재 2026-10-09 |

**가운데 정렬은 올림이다** (`(cols - len(footer) + 1) // 2`). 지침 실물 4건([예 1-6] ·
[예 1-7]×3 · [예 1-8])이 전부 이 값과 맞는다. 내림이면 꼬리말이 홀수 칸일 때 한 칸 어긋난다.

**BRF-ASCII 표는 새로 만든 게 아니라 `code/AI/app/utils/braille_ascii.py`를 옮긴 것이다.**
점자 도서 gold 1,251쪽 · 2,546,903셀을 양쪽으로 변환해 불일치 0을 확인했다(2026-08-05).
코퍼스 `.brl` 파일은 백틱을 `⠈`(초성 ㄱ)으로 쓰므로, 백틱을 공백으로 바꾸면 초성 ㄱ이
사라진다. 이 함수는 공백을 스페이스로만 내므로 그 사고가 재현되지 않는다.

> 조판 가이드(2026-08-05) §4의 호출 예 두 개는 틀렸다. 하나는 결과가 33칸이라 규격 위반이고,
> 다른 하나는 꼬리말 시작 칸이 두 칸 어긋난다. 지침 실물이 정본이다.

---

## 버전

서비스 버전(v3.x)과 독립인 semver. `v0.1.0`부터.
