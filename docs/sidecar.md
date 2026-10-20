# 파이썬이 아닌 곳에서 쓰기 · 사이드카

C#·자바스크립트처럼 파이썬이 아닌 프로그램은 이 엔진을 담은 파이썬 프로세스(**사이드카**)를 띄워 두고
표준입출력으로 말을 건다. 파이썬에서 쓸 때는 [encoder.md](encoder.md) · [decoder.md](decoder.md) 를 본다.

| 절 | 내용 |
|---|---|
| 1 | 띄우기 |
| 2 | 문자와 인코딩 |
| 3 | 실제로 오간 줄 |
| 4 | 필드 |
| 5 | 32칸 접기(부르는 쪽이 할 일) |
| 6 | `breaks` 를 꼭 써야 하는 까닭 |
| 7 | 오류와 사이드카가 죽었을 때 |
| 8 | 윈도우 · .NET 앱에서 띄우기 |

C#·자바스크립트처럼 파이썬이 아닌 프로그램은 이 엔진을 담은 파이썬 프로세스(**사이드카**)를 띄워 두고 표준입출력으로 말을 건다.

## 1. 띄우기

```
python -m semojum_braille.sidecar
```

- 부르는 쪽이 이 명령으로 프로세스를 **하나 띄워 두고 계속 쓴다.** 부를 때마다 새로 띄우지 않는다.
- 표준입력으로 요청 JSON 을 **한 줄에 하나** 보낸다. 표준출력으로 응답 JSON 이 **한 줄에 하나** 온다. 받은 순서대로 답한다.
- 표준오류에는 엔진 로그(경고)가 나온다. 응답은 표준출력에만 쓴다.
- 표준입력을 닫으면 사이드카가 끝난다.
- 점역(`translate`)과 역점역(`decode`)을 함께 받는다.
- 기동하자마자 뒤에서 역점역을 한 번 불러 낱말 판정기를 미리 올린다. `[kiwi]` 를 깔았으면 영어책 역점역의 첫 호출이 약 2초 멈추는데, 그것을 가리려는 것이다.
- 앱에 실어 낼 때는 site-packages 를 통째로 싣는다. `semojum_braille/third_party/` 에 braillify 의 `LICENSE` 가 들어 있다. braillify 휠에는 고지 파일이 없어 여기 실었다([NOTICE.md](../NOTICE.md) ②). 빼지 말고 같이 싣는다.

리눅스 실측: 기동부터 첫 응답 약 0.1초, 한 쪽(35요소·1,318자) 점역 약 0.21초, 역점역 약 0.02초.
윈도우 실측(CI 러너 windows-latest, 8절 C# 예제): 기동부터 첫 응답 0.39 ~ 0.42초, 한 문장 점역 6 ~ 8ms(파이썬 3.13 · 3.10). 사용자 PC 가 아니라 CI 러너 값이다.

## 2. 문자와 인코딩

- 요청은 **UTF-8 바이트**로 받아 줄마다 따로 푼다. 사이드카 프로세스의 표준입력 인코딩(한국어 Windows 는 cp949)과는 상관없다.
- 그래도 **ASCII 로 보내기를 권한다.** 한글과 점자를 `\uXXXX` 로 적는다(.NET `System.Text.Json` 기본 직렬화와 같은 꼴). ASCII 는 어느 인코딩으로 써도 같은 바이트라 앱 쪽 인코딩 설정이 어긋나도 안전하다.
- UTF-8 로 못 푸는 줄(cp949 로 쓴 한글, 깨진 바이트)은 **그 줄만** `error` 로 답하고 다음 줄을 받는다(3절 예). 그 줄에서 `id` 를 읽을 수 있으면 돌려준다. 깨진 글로 점역하지는 않는다. 3.4.10 까지는 이런 줄에서 사이드카가 응답 없이 죽었다(#44).
- 줄 머리의 UTF-8 BOM(`EF BB BF`)은 뗀다. C# `StreamWriter` 를 BOM 있는 `Encoding.UTF8` 로 만들면 첫 줄 앞에 붙는다.
- 줄 끝은 `\n` · `\r\n` 을 다 받는다. 응답은 늘 ASCII 다(한글과 점자는 `\uXXXX`).
- 점자·빈칸·줄바꿈이 모두 BMP 안이라 **UTF-16 문자열(C# `string`, 자바스크립트 문자열)의 인덱스와 이 문서의 오프셋이 같다.** `breaks` 값을 그대로 인덱스로 쓴다.
  단서 하나: 엔진이 점자로 못 옮긴 글자가 `cells` 에 드물게 남을 수 있다. 그 글자가 BMP 밖(이모지 등)이면 UTF-16 에서는 두 칸으로 세어져 뒤 오프셋이 하나씩 밀린다. 그런 요소는 `breaks` 를 버리고 빈칸 자리로 접는다.

## 3. 실제로 오간 줄

아래는 사이드카를 띄워 실제로 주고받은 줄이다(엔진 3.4.19). `→` 가 표준입력, `←` 가 표준출력이다.

**전선 위 모습 그대로** (제목 요소 하나):

```
→ {"id": 3, "op": "translate", "text": "1 \uad6d\uc5b4\uc758 \ud0d0\uad6c\uc640 \ud65c\uc6a9", "type": "title", "heading_level": 2}
← {"cells": "\u2800\u2800\u2800\u2800\u2800\u2800\u283c\u2801\u2832\u2800\u2808\u280d\u2801\u280e\u283a\u2800\u2813\u2822\u2808\u280d\u2827\u2800\u281a\u2827\u2802\u282c\u2836", "breaks": [9, 10, 13, 14, 15, 16, 18, 20, 21, 22, 25], "dropped": [], "blocked": false, "unknown_tags": [], "id": 3}
```

풀어 쓰면 `cells` 는 `⠀⠀⠀⠀⠀⠀⠼⠁⠲⠀⠈⠍⠁⠎⠺⠀⠓⠢⠈⠍⠧⠀⠚⠧⠂⠬⠶` 이다(2단계 제목이라 7칸에서 시작). 아래부터는 `\uXXXX` 를 풀어 적는다.

**ping** (기동 확인 · 판 확인):

```
→ {"id": 1, "op": "ping"}
← {"ok": true, "version": "3.4.19", "protocol": 1, "id": 1}
```

`version` 은 엔진 판, `protocol` 은 프로토콜 판이다(4절). 앱은 기동할 때 `protocol` 이 자기가 아는 값인지 보고, 다르면 쓰지 말고 사용자에게 알린다. `version` 은 로그와 오류 보고에 남긴다.

**translate** (본문 한 요소):

```
→ {"id": 2, "op": "translate", "text": "대한민국의 모든 국민은 법 앞에 평등하며, 누구든지 성별이나 종교 때문에 차별받지 아니한다.", "type": "text", "heading_level": 0}
← {"cells": "⠀⠀⠊⠗⠚⠒⠑⠟⠈⠍⠁⠺⠀⠑⠥⠊⠵⠀⠈⠍⠁⠑⠟⠵⠀⠘⠎⠃⠀⠣⠲⠝⠀⠙⠻⠊⠪⠶⠚⠑⠱⠐⠀⠉⠍⠈⠍⠊⠵⠨⠕⠀⠠⠻⠘⠳⠕⠉⠀⠨⠿⠈⠬⠀⠠⠊⠗⠑⠛⠝⠀⠰⠣⠘⠳⠘⠔⠨⠕⠀⠣⠉⠕⠚⠒⠊⠲", "breaks": [4, 6, 8, 11, 12, 13, 15, 17, 18, 21, 23, 24, 25, 28, 29, 31, 32, 33, 35, 38, 39, 42, 43, 45, 47, 49, 51, 52, 54, 56, 57, 58, 59, 61, 63, 64, 67, 69, 70, 71, 73, 75, 77, 79, 80, 81, 83, 85], "dropped": [], "blocked": false, "unknown_tags": [], "id": 2}
```

`cells` 앞 두 칸(`⠀⠀`)은 문단 들여쓰기다(3칸에서 시작). 85칸짜리 한 줄이고 아직 32칸으로 접지 않았다. 접는 법은 5절.

**decode** (위 `cells` 를 그대로 되돌린다):

```
→ {"id": 4, "op": "decode", "braille": "⠀⠀⠊⠗⠚⠒⠑⠟⠈⠍⠁⠺⠀⠑⠥⠊⠵⠀⠈⠍⠁⠑⠟⠵⠀⠘⠎⠃⠀⠣⠲⠝⠀⠙⠻⠊⠪⠶⠚⠑⠱⠐⠀⠉⠍⠈⠍⠊⠵⠨⠕⠀⠠⠻⠘⠳⠕⠉⠀⠨⠿⠈⠬⠀⠠⠊⠗⠑⠛⠝⠀⠰⠣⠘⠳⠘⠔⠨⠕⠀⠣⠉⠕⠚⠒⠊⠲"}
← {"text": "  대한민국의 모든 국민은 법 앞에 평등하며, 누구든지 성별이나 종교 때문에 차별받지 아니한다.", "id": 4}
```

**decode**, 영어 책 꼴의 한 줄(지은 줄):

```
→ {"id": 5, "op": "decode", "braille": "⠀⠀⠼⠉⠲⠀⠴⠍⠥⠎⠊⠉⠀⠸⠌⠀⠠⠩⠑⠒", "english": true}
← {"text": "  3. music / 슈만", "id": 5}
```

`[kiwi]` 를 깐 환경의 결과다. 기본 설치(낱말 목록)에서는 이 줄이 `  3. music / She:` 로 온다([decoder.md](decoder.md) 1절).

**translate**, 한글 정자로 · 점자 기호가 없는 글자가 섞인 요소:

```
→ {"id": 7, "op": "translate", "text": "가▶나", "korean_grade": 1}
← {"cells": "⠀⠀⠈⠣⠉⠣", "breaks": [4], "dropped": [{"text": "▶", "count": 1, "flag": "R17"}], "blocked": false, "unknown_tags": [], "id": 7}
```

`korean_grade: 1`(정자)이라 `가` 를 약자 `⠫` 가 아니라 `⠈⠣` 로 적었다. `▶` 는 점자 기호가 없어 `cells` 에서 빠졌고, 그 사실이 `dropped` 로 온다. 앱은 이 요소에 검토 표시를 띄운다(4절).

**translate**, 점자로 옮길 글자가 하나도 없는 요소:

```
→ {"id": 9, "op": "translate", "text": "😀"}
← {"cells": "⠀⠀⠠⠄⠨⠎⠢⠱⠁⠀⠑⠥⠄⠀⠚⠢⠠⠄", "breaks": [9, 13], "dropped": [], "blocked": true, "unknown_tags": [], "id": 9}
```

원문은 있는데 점자가 0셀이 되는 요소는 빈 점자 대신 점역자 주 꼴 '점역 못 함'(`⠠⠄` … `⠠⠄`)으로 오고 `blocked` 가 `true` 다. AI 서버가 같은 요소에 내는 점자와 같다. 까닭(`점역 불가 문자 😀`)은 점자에 싣지 않고 표준오류 로그로 나간다. 앱은 이 요소에 검토 표시를 띄우고 묵자 창에서 원문을 보여 준다(4절). 3.4.13 까지는 이런 요소가 빈 `cells` 로 와서 조용히 사라졌다(#52).

**오류** (모르는 op, JSON 이 아닌 줄, UTF-8 이 아닌 줄):

```
→ {"id": 6, "op": "fold"}
← {"error": "모르는 op: 'fold'", "code": "BAD_FIELD", "id": 6}
→ not json
← {"error": "JSON 이 아닌 줄이다: Expecting value: line 1 column 1 (char 0)", "code": "BAD_JSON", "id": null}
→ (cp949 로 쓴 줄) {"id": 8, "op": "translate", "text": "가"}
← {"error": "UnicodeDecodeError: 표준입력은 UTF-8 이어야 한다(38번째 바이트 0xb0)", "code": "BAD_JSON", "id": 8}
```

## 4. 필드

**요청**

| op | 필드 | 타입 | 기본값 | 뜻 | 예 |
|---|---|---|---|---|---|
| 모두 | `id` | 아무 JSON 값 | 없음 | 응답에 그대로 돌아온다. 요청과 응답을 짝짓는 데 쓴다 | `2` |
| 모두 | `op` | 문자열 | 없음 | `translate` · `table` · `decode` · `build_brf` · `read_brf` · `grade` · `symbols` · `ping` | `"translate"` |
| translate | `text` | 문자열 | `""` | 묵자 요소 하나. 줄바꿈은 `\n`. 인라인 태그([encoder.md](encoder.md) 2.1)를 그대로 넣는다 | `"대한민국의 모든…"` |
| translate | `type` | 문자열 | `"text"` | 요소 종류. `text` · `title` · `list_item` · `caption` · `header_footer` · `table` 중 하나. 들여쓰기가 이것에 따라 달라진다. `table` 이면 표 길로 간다(아래 '표도 `translate` 로'). `header_footer` 면 로마자 강제(`force_roman`)가 저절로 켜진다(#60) | `"title"` |
| translate | `heading_level` | 정수 | `0` | 0 은 본문. 1~4 는 제목 단계다. 1단계는 가운데 정렬, 2단계는 7칸, 3·4단계는 5칸에서 시작한다. 문자열 `"1"` 같은 값은 `BAD_FIELD` | `2` |
| translate | `korean_grade` | 정수 | `2` | 한글 급수. `1` 정자(약자 · 약어「한국 점자 규정」 제13~18항을 쓰지 않는다. 받침 ㅆ `⠌` 는 자모 규정 제4항이라 그대로) · `2` 약자. `0` 은 안 보낸 것으로 보고 `2` 다. 그 밖은 `BAD_FIELD`. AI proto `korean_grade`(10)와 같다 | `1` |
| translate | `english_grade` | 정수 | `2` | 영어 급수. `1` 정자(약자 없이 글자대로, 문단 전체가 영어여도 로마자표 `⠴` · 종료표 `⠲` 를 생략하지 않는다) · `2` 약자. `0` 은 `2`. AI proto `english_grade`(11)와 같다 | `1` |
| translate | `math_page` | 참거짓 | `false` | 그 요소가 든 쪽이 **수식 쪽**이면 `true`. 평문 속 `(1, 0)` · `p-q` 를 수식으로 적는다(수식 소괄호 `⠦…⠴`). AI 서버는 쪽 PDF 의 한컴 수식 글꼴 비율로 정한다. 서버가 낸 점자와 같게 다시 점역하려면 그 쪽의 값을 넘긴다(아래 '수식 쪽 값') | `true` |
| translate | `split_choices` | 참거짓 | `false` | 선택지를 한 줄에 하나씩 적는다. 안 보내면(`false`) 짧은 선택지를 한 줄에 합친다(종전 동작). AI proto `split_choices`(12)와 같다 | `true` |
| translate | `force_roman` | 참거짓 | `false` | 옛 호출용. `type: "header_footer"` 면 저절로 켜지므로 보낼 일이 없다(#60, V4 가이드에 없음). 켜면 꼬리말처럼 한글이 없는 로마자 조각에도 로마자표 `⠴` 를 붙인다(「한국 점자 규정」 제29항) | `true` |
| translate | `render_mode` · `tn_text` · `box_level` | 문자열 · 문자열 · 정수 | `""` · `""` · `0` | 표일 때만 쓴다. 뜻은 아래 `table` 의 같은 이름 필드와 같다. 표가 아니면 무시한다 | `"table_grid"` |
| table | `table_source` | 문자열 | `""` | 표 요소 하나의 태그 글(`<!표><!행><!칸>…`, [encoder.md](encoder.md) 1.6). AI 응답 `text_list` 표 요소의 `table_source` 가 이 값이다. 점역사가 칸 글을 고쳤으면 고친 태그 글을 넣는다. 사람이 읽는 테두리 글(`contents`)은 표 구조를 잃어 넣으면 안 된다 | `"<!표>\n<!행><!칸>구분<!칸>가<!/행>\n<!/표>"` |
| table | `render_mode` | 문자열 | `""` | 고를 안. `unfold`(테두리 없음) · `table_grid`(테두리+구분선) · `transposed`(행열 바꿈) · `linear`(테두리만, 정답 상자) · `numbered`(번호 체계). AI 응답 표 요소의 같은 이름 필드다. 없거나 모르는 값이면 `unfold` | `"table_grid"` |
| table | `tn_text` | 문자열 | `""` | 태그가 표로 안 풀리는 글일 때 대신 점역할 점역자 주 글. AI 응답 표 요소의 같은 이름 필드를 그대로 넘긴다 | `"<!주>표. …<!/주>"` |
| table | `box_level` | 정수 | `0` | 그 표를 감싼 글상자 위계. 1 이상이면 테두리를 한 단계 아래 꼴(`⠖⠒…⠲`)로 그린다. AI 응답 `text_list` 표 요소의 `table_box_level`(AI #1369)을 그대로 넘긴다 | `1` |
| table | `korean_grade` · `english_grade` · `math_page` | 정수 · 정수 · 참거짓 | `2` · `2` · `false` | `translate` 와 같다 | `1` |
| decode | `braille` | 문자열 | `""` | 점자. 여러 줄이면 `\n` 으로 잇는다 | `"⠊⠗⠚⠒…"` |
| decode | `english` | 참거짓 | `false` | 영어 교과 책이면 `true`. 한글로 잘못 읽힌 영어 토막을 되찾는다. 다른 책에서는 켜지 않는다 | `true` |
| decode | `korean_grade` | 정수 | `2` | 그 점자가 점역된 급수. `1`(정자)이면 정자 음절로 읽는다. 정자 점자를 `2` 로 읽으면 받침 ㄹ 을 쉼표로 읽는 등 글이 깨진다 | `1` |
| build_brf | `job` | 객체 | `{}` | 조판할 문서. 원본 쪽마다 점역된 블록(translate 의 `cells` · `breaks`)을 담는다(아래). 조판 옵션은 `opts` 에 | `{"sources": […]}` |
| read_brf | `brf` | 문자열 | `""` | `.brf` 파일 내용(ASCII 그대로). 소문자+백틱 · 대문자+`@` 두 꼴을 다 받는다. 백틱은 ⠈(초성 ㄱ)로 읽는다 | `"#a\r\nab\r\n\x0c"` |
| grade | `braille` | 문자열 | `""` | 그 요소의 점역 결과(`translate` 의 `cells`) | `"⠊⠗⠚⠒…"` |
| grade | `source` | 문자열 | `""` | 그 요소의 묵자 원문(`translate` 에 넣은 `text`) | `"대한민국의 모든…"` |
| grade | `type` | 문자열 | `"text"` | 요소 종류. `table` · `formula` 는 늘 `low` 다 | `"table"` |
| grade | `ocr_confidence` | 수 | 없음 | 추출 신뢰도(0~1). 0.7 미만이면 `low`. 모르면 넣지 않는다 | `0.95` |
| grade | `korean_grade` | 정수 | `2` | `braille` 이 점역된 급수. `1` 이면 왕복 일치도를 잴 때 정자로 역점역한다. **정자 문서는 꼭 넣는다** — 안 넣으면 요소 대부분이 `low` 가 된다(AI #1276) | `1` |
| symbols | `group` | 문자열 | `""` | 묶음 이름으로 거른다(`문장부호` · `기타부호` · `단위기호` · `화폐기호` · `화살표` · `그리스문자` · `수학…` 등 기호표 묶음). 비우면 전부 | `"화살표"` |

**응답**

| op | 필드 | 타입 | 뜻 |
|---|---|---|---|
| 모두 | `id` | 요청과 같음 | 요청의 `id`. JSON 이 아닌 줄을 받으면 `null`. UTF-8 로 못 푸는 줄은 `id` 를 읽을 수 있으면 그 값, 아니면 `null` |
| translate | `cells` | 문자열 | 점역 결과. `flatten_elements` 가 내는 요소 통 문자열([encoder.md](encoder.md) 1.7)에서 앞뒤 빈 줄(`prefix`·`suffix`)을 뺀 본문과 같다. 들여쓰기 칸과 가운데 여백이 들어 있고, 논리 줄은 `\n` 으로 잇는다. **32칸으로 접지 않았다.** 제목·표 둘레의 앞뒤 빈 줄은 이웃 요소에 따라 정해지므로 부르는 쪽의 조판이 넣는다 |
| translate | `breaks` | 정수 배열 | `cells` 안에서 줄을 바꿔도 되는 자리. 값 `b` 는 "`cells[b]` 앞에서 끊어도 된다" 는 뜻이다. 음절 경계와 빈칸 자리가 모두 들어 있다. 오름차순이고 겹치지 않는다. `flatten_elements` 의 `breaks`(AI 응답 `TextElement.breaks` 와 같은 함수)에서 `prefix` 길이만큼 뺀 값이라 따로 세지 않는다(#30). 여는 괄호 · 따옴표 바로 뒤는 들지 않는다(AI #1245). 닫는 따옴표 · 괄호 · 로마자 종료표 바로 앞과 빈 괄호 `( )` 안 빈칸도 들지 않는다(「한국 점자 규정」 제54항 · 제55항, AI #1398 · #1402 · #1405, 3.4.25 부터). 수식 구간(`<!수식>…<!/수식>` · `$…$`) 안 자리는 「한국 점자 규정」 수학 점자 제66항대로 사칙연산 · 등호 · 분수표 뒤다(AI #1393 · #1396 · #1397, 3.4.24 부터). 수식 요소는 `type` 을 `"text"` 로 두고 `<!수식>LaTeX<!/수식>` 를 넣으면 셀과 자리가 AI 수식 요소와 같다 |
| translate | `dropped` | 객체 배열 | 점자 기호가 없어 `cells` 에서 **조용히 빠진 글자**. `[{"text": 글자, "count": 횟수, "flag": 갈래}]`. 갈래는 AI 서버 검수 플래그와 같은 이름이다. `R15` 글꼴 사설영역(PUA) 글리프 · `R17` 기호표에 없는 기호 · `R18` 규정에 점형이 없는 옛한글 음절(이때 `text` 는 자모 여럿으로 된 음절 하나). 빠진 것이 없으면 `[]`. 앱은 이 배열이 빈 배열이 아닌 요소에 검토 표시를 띄운다. AI 서버가 쪽 플래그를 세는 함수를 그대로 써서 같은 원문이면 같은 결과다 |
| translate | `blocked` | 참거짓 | 점역 못 한 요소면 `true`. 원문은 있는데 점자가 0셀이 되거나(점자로 옮길 글자가 없는 요소: 이모지 · 아랍 문자의 숫자(١٢٣) · 다른 문자권 글자 등) 엔진이 예외를 던지면, `cells` 가 점역자 주 꼴 '점역 못 함'이 되고 이 값이 `true` 다. AI 서버의 점역 체인(`isolation.safe_translate`)과 검토 표시(C2 · R1, `is_blocked_braille`)와 같은 판정이다. 한자만 있는 요소는 빈 `cells` 가 정답이라(도서 관행) `false` 다. 앱은 `true` 인 요소에 검토 표시를 띄운다 |
| translate | `unknown_tags` | 문자열 배열 | 엔진이 모르는 태그 이름(나온 차례, 겹침 없이). 예 `<!없는태그>` → `"없는태그"`. 목록표 글자 태그 넷(색강조 · 취소선 · 밑줄빈칸 · 네모빈칸)은 3.4.22 부터 아는 태그다. 점역에서는 지우고 나머지를 점역한다. 앱은 이 배열이 비지 않은 요소에 검토 표시를 띄운다 |
| translate | (조판 태그) | | 목록표의 조판 태그는 아는 태그다(#66). 줄 태그(점자 줄 다섯 · 표 테두리 일곱)만 든 요소는 32칸 미리보기 한 줄, `<!쪽바꿈>` · `<!장바꿈>` 만 든 요소는 빈 `cells` 를 낸다(종전엔 '점역 못 함' 주가 나갔다). 정렬 셋 · `<!머리말>…<!/머리말>` 은 글에서 빼고 점역한다. `<!묵자쪽번호>` · `<!점자면번호>` 는 `cells` 에 태그 그대로 남고 그 안쪽엔 끊을 자리가 없다. 조판(`build_brf`)이 펼치고 채운다([assist.md](assist.md) 조판 태그) |
| table | `cells` · `breaks` | 문자열 · 정수 배열 | 고른 안의 점역 결과와 줄을 바꿔도 되는 자리. 뜻은 `translate` 와 같다(요소 통 문자열에서 앞뒤 빈 줄을 뺀 본문, 32칸으로 안 접음) |
| table | `render_mode` | 문자열 | 고른 안. 태그가 표로 안 풀려 점역자 주 한 안이면 `""` |
| table | `drafts` | 객체 배열 | 다섯 안 전부. `[{"render_mode", "label", "cells", "breaks"}]` 이고 순서는 `unfold` · `table_grid` · `transposed` · `linear` · `numbered` 다. 안을 바꾸기만 할 때는 다시 부를 필요 없이 이 배열에서 고른다. 점역자 주 한 안이면 `[]` |
| table | `dropped` · `blocked` | 객체 배열 · 참거짓 | `translate` 와 같다. `dropped` 는 `table_source` 의 글자로 센다(태그는 세지 않는다) |
| translate | `render_mode` · `drafts` | 문자열 · 객체 배열 | **표일 때만 붙는다**(#60). 뜻은 `table` 의 같은 이름 필드와 같다. 표가 아니면 응답은 `cells` · `breaks` · `dropped` · `blocked` 넷뿐이다 |
| decode | `text` | 문자열 | 역점역한 글. 원문 복원이 아니라 **검수용 근사**다. 줄바꿈은 그대로 둔다 |
| build_brf | `brf` | 문자열 | `.brf` 파일 내용 그대로. 줄 끝 `\r\n`, 26줄 쪽마다 끝에 `\x0c`(마지막 쪽 포함), 소문자 BRF ASCII, 32칸. 부르는 쪽은 이 문자열을 ASCII 로 그대로 파일에 쓴다 |
| build_brf | `replaced` | 객체 | 점자로 못 옮겨 **빈칸으로 바꾼 글자**와 횟수(`{"U+2009": 2}`). 없으면 `{}`. 파일은 그래도 나온다. 비어 있지 않으면 점역사에게 알린다(그 자리 점자가 빠졌다). 3.4.23 부터다. 종전에는 이런 글자 하나에 파일 전체가 `BAD_FIELD` 였다 |
| read_brf | `pages` | 문자열 배열의 배열 | 쪽마다 유니코드 점자 줄 목록. 빈칸은 `⠀`, 탭은 4칸 자리로 펼친다. 역점역하려면 줄(또는 `\n` 으로 이은 쪽)을 `decode` 에 넘긴다. BRF ASCII 가 아닌 글자가 있으면 `error` |
| grade | `grade` | 문자열 | 검수 순서 등급. `low` · `medium` · `high`. **아래 '검수 등급의 뜻'을 반드시 읽을 것** |
| grade | `round_trip` | 수 또는 `null` | 왕복 일치도(0~1). 점역 결과를 역점역해 원문과 대조한 값. 잴 수 없거나(원문이 짧음 · 표 · 수식 · 영문) 등급을 규칙으로 정했으면 `null` |
| symbols | `symbols` | 객체 배열 | 삽입할 수 있는 기호. `[{"char", "cells", "group"}]`. `cells` 는 **문맥 없는 기호표 값**이다(엔진 `symbol_table.json`, 302개). 실제 점자는 글에 넣은 뒤 `translate` 가 문맥으로 정한다 — 예 `×` 는 표 값이 곱셈 `⠡` 인데 OX 문항의 `×` 는 `⠴⠠⠭` 로, 참고표 `※`(`⠐⠔`)는 앞뒤 한 칸을 띄워 적는다(「한국 점자 규정」 제60항) |
| ping | `ok` | 참거짓 | 늘 `true` |
| ping | `version` | 문자열 | 엔진 판(`semojum_braille.__version__`). 예 `"3.4.11"` |
| ping | `protocol` | 정수 | 프로토콜 판. 요청 · 응답 꼴이 앞 판과 **호환되지 않게** 바뀔 때만 올린다. 필드나 op 를 더하는 것은 올리지 않는다. 지금 `1` |
| 실패 | `error` · `code` | 문자열 · 문자열 | 설명과 오류 코드. 이때 다른 필드는 없다(`id` 는 있다). 코드는 다섯이다(아래 '오류 코드') |

- **수식 쪽 값**(`math_page`): AI 응답에는 아직 쪽 표지가 없다(proto 묶음 대기). 그동안은 그 쪽에 수식(`formula`) 요소가 하나라도 있으면 `true` 로 넘긴다. 2027 dev · val 1,746쪽에서 이 근사는 쪽 판정이 서버와 1,718쪽 같고(28쪽 다름), 글 요소로는 39,564 중 39,558이 서버 점자와 같다(6 다름). 서버 판정을 그대로 넘기면 39,564 전부 같다(하네스 ⑥, #38).
- **표 왕복**(`table`): AI 2027 dev · val 1,746쪽 응답의 표 900개를 `table_source` · `render_mode` · `tn_text` 로 이 op 에 넣으면 828(92.0%)이 서버 점자와 바이트로 같다(고른 안 · 다섯 안 · 끊을 자리). 정답 상자 89/89 · 번호 체계 61/62 · 격자 678/749 다. 응답의 `table_box_level` 을 `box_level` 로 같이 넘기면 899(99.9%), 수식 쪽 값(`math_page`)까지 넘기면 900 이다. 묵자 테두리 글을 표로 되돌려 넣는 길은 70%(정답 상자 1/88 · 번호 체계 0/61)라 쓰지 않는다(#56).
- **표도 `translate` 로**(#60): `type` 이 `table` 이거나 `text` 가 표 태그(`<!표>`)로 읽히면 `table` op 와 같은 함수로 가서 같은 응답(`render_mode` · `drafts` 포함)을 낸다. 표 900개 전부 `table` op 와 바이트로 같다. 앱은 창구 하나만 써도 된다. `table` op 는 한동안 같이 둔다. ★ 갈림은 **엔진과 요소 type 을 둘 다** 표로 바꾼다. 엔진만 표로 바꾸고 `flatten_elements` 의 요소 type 을 `text` 로 두면 표 줄마다 문단 들여쓰기 2칸이 더 붙어(`⠀⠀⠿⠿` → `⠀⠀⠀⠀⠿⠿`) 900/900 다르다(`list_item` 도 900/900). 2027 dev · val 에서 `<!표>` 가 든 요소는 표 요소 900개와 정확히 같았다(표 아닌 요소 43,772개 중 0).
- 정자로 점역한 문서는 `translate` · `decode` · `grade` 세 op 모두에 `korean_grade: 1` 을 넣는다. 한 op 에만 넣으면 점역과 되읽기가 어긋난다.
- `korean_grade` · `english_grade` · `split_choices` 는 그 요청 하나에만 걸린다. 다음 요청으로 이어지지 않는다. 급수는 정수 `0` · `1` · `2` 와 `null`(= `2`)만, 참거짓 칸은 `true` · `false` · `null`(= `false`)만 받는다. 문자열 `"1"` · `"true"` 같은 값은 `BAD_FIELD` 로 돌려준다(조용히 켜거나 끄지 않는다).
- **오류 코드**(V4 엔진 가이드 오류 표): `BAD_JSON` JSON 이 아닌 줄(UTF-8 이 아닌 줄 포함, `id` 가 `null` 일 수 있다) · `BAD_FIELD` 필드 타입 · 값 범위가 맞지 않음(모르는 op 포함, 그 밖의 예외도 요청 값 탓으로 이 코드) · `TOO_LONG` translate 묵자 1,000자 초과(**태그를 뺀 글자 수**. 태그째 세면 2027 dev · val 표 2개가 걸리는데 표는 문장으로 못 쪼갠다) · `BAD_LATEX` `<!수식>…<!/수식>` 안 LaTeX 가 중괄호 10중첩 또는 1,000자 초과(묵자 상한보다 먼저 본다) · `BAD_BRF` `read_brf` 입력에 BRF ASCII 가 아닌 글자.
- `decode` 는 `math` 를 받지 않는다. 수식 요소를 수식으로 되돌리려면 파이썬에서 `decode(…, math=True)` 를 부른다([decoder.md](decoder.md) 2.1).

`build_brf` 의 `job`: `{"sources": [{"orig_page": 정수, "blocks": [{"order": 정수, "braille": 점자, "breaks": [정수, …]}, …]}, …], "footer": 점자, "footers": {면 번호: 점자}, "footers_by_orig_page": {원본 쪽 번호: 점자}, "opts": {…}}`(V4 엔진 가이드). `footer` 는 이미 점역된 꼬리말이다. `footers` 는 그 면만이고, `footers_by_orig_page` 는 점역사가 묵자 쪽에 꽂은 꼬리말이라 `opts.footer_mode` 가 범위를 정한다(`carry` 이어가기 기본 · `page` 그 쪽만, 그 밖은 `BAD_FIELD`, 3.4.27 · #78). 꼬리말 글은 `translate` 에 `type: "header_footer"` 로 넣어 받은 `cells` 를 넘긴다(로마자 강제가 저절로 켜진다). `blocks` 는 `order` 로 정렬하고, `breaks` 는 그 블록의 translate `breaks` 그대로다(없으면 그 블록은 빈칸에서 접는다). `opts` 는 `cols` · `rows` · `wrap`(`syllable` · `word`) · `footer_align`(`left` · `center` · `right`) · `footer_mode`(`carry` · `page`) · `first_braille_page` · `cover_orig_page_count` · `orig_page_first_no` · `page_row_pages`(`odd` · `every` · `even` · `none`, 뒤 둘은 3.4.29) · `footer_pages`(같은 네 값, 꼬리말을 넣는 면. 없으면 `page_row_pages` 와 같다, 3.4.30) · `number_ranges` · `footer_ranges`(`[[시작 면, 끝 면], …]`, 점자 면 번호 기준 양끝 포함, 끝이 `null` 이면 문서 끝까지, 없으면 전체, 3.4.30). 번호도 꼬리말도 없는 면에는 페이지행 줄이 없고, 꼬리말 면을 켰어도 적을 글이 없으면 줄을 넣지 않는다(3.4.31) · `show_orig_page`(끄면 원본 페이지 변경선도 꺼진다) · `show_braille_page` · `show_change_line`(원본 페이지 변경선, 3.4.27) · `pad_to_even` 이고 모두 생략할 수 있다. 참거짓 칸 넷(`show_orig_page` · `show_braille_page` · `show_change_line` · `pad_to_even`)은 `true` · `false` · `null`(= 기본값)만, `cols` · `rows` 는 1 이상의 정수와 `null`(= 기본값)만 받고 그 밖은 `BAD_FIELD` 다(3.4.25부터. 종전에는 문자열 `"false"` 가 켜고 `rows: 0` 은 26줄이 됐다). 면 나누기와 페이지행은 「점자 도서 제작 지침」 1장 2절 2를 따른다(`semojum_braille.assist`, [assist.md](assist.md)).

**파이썬에서 같은 일을 하는 함수**: `semojum_braille.sidecar` 의 `translate(text, etype="text", hlevel=0, korean_grade=2, english_grade=2, math_page=False, split_choices=False, render_mode="", tn_text="", box_level=0, force_roman=False) -> dict`(`{"cells", "breaks", "dropped", "blocked", "unknown_tags"}` 를 내고, 표면 `table` 과 같은 것을 낸다) · `table(source, render_mode="", tn_text="", box_level=0, korean_grade=2, english_grade=2, math_page=False) -> dict`(`{"cells", "breaks", "render_mode", "drafts", "dropped", "blocked"}` 를 낸다) · `handle(req: dict) -> dict`(요청 하나를 처리한다) · `main() -> None`(표준입출력 고리). 판 번호는 `semojum_braille.__version__` · `semojum_braille.sidecar.PROTOCOL` 이다. `build_brf` 는 `semojum_braille.assist.build_brf_file(job, replaced=None) -> bytes`(`replaced` 에 `Counter` 를 주면 빈칸으로 바꾼 글자를 채운다), `read_brf` 는 `semojum_braille.brf.parse_brf(data) -> list[list[str]]` 다.

## 5. 32칸 접기 (부르는 쪽이 할 일)

사이드카는 32칸으로 접지 않는다. 부르는 쪽이 아래 함수로 접는다. 파이썬으로 적었지만 **다른 언어로 옮길 몫은 이 함수 하나다.**

```python
W, BLANK = 32, "⠀"


def fold(cells, breaks, center=False, cuts=None):
    """cells(논리 줄을 \\n 으로 이은 통 문자열)를 32칸 줄로 접는다. 부르는 쪽이 할 몫이다.

    breaks 자리(그 셀 앞)에서만 끊고, 32칸 안에 자리가 없을 때만 32칸째에서 강제로 자른다.
    자리 목록이 없는 줄(사람이 점자를 직접 고친 요소 등)은 빈칸 자리에서 끊는다. 끊은 자리 앞뒤 빈칸(줄 끝 · 이어지는 줄 머리)은 버린다.
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
            seg.append(line[start:b].rstrip(" " + BLANK) or line[start:b])   # 줄 끝 빈칸은 걷는다
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

3절의 translate 응답(85칸)을 이 함수로 접은 실제 결과:

```
⠀⠀⠊⠗⠚⠒⠑⠟⠈⠍⠁⠺⠀⠑⠥⠊⠵⠀⠈⠍⠁⠑⠟⠵⠀⠘⠎⠃⠀⠣⠲⠝| 32칸
⠙⠻⠊⠪⠶⠚⠑⠱⠐⠀⠉⠍⠈⠍⠊⠵⠨⠕⠀⠠⠻⠘⠳⠕⠉⠀⠨⠿⠈⠬   | 30칸
⠠⠊⠗⠑⠛⠝⠀⠰⠣⠘⠳⠘⠔⠨⠕⠀⠣⠉⠕⠚⠒⠊⠲         | 23칸
```

둘째 줄은 빈칸 바로 뒤 자리에서 끊었고, 줄 끝에 남은 빈칸 `⠀` 는 걷었다(3.4.25부터). 끊는 자리는 엔진 조판([encoder.md](encoder.md) 1.7)과 같다. 엔진 조판은 줄 끝 빈칸을 그대로 둔다.

**다른 언어로 옮길 때 지킬 것**

1. 32칸 안에서 **가장 먼** `breaks` 자리에서 끊는다. 그런 자리가 없을 때만 32칸째에서 강제로 자른다. 강제로 자를 때 점역자 주 표 `⠠⠄`(두 칸)는 가르지 않고 한 칸 앞에서 자른다.
2. 끊은 자리의 빈칸(`⠀`, 공백)은 버린다. 줄 끝에 남는 빈칸도, 이어지는 줄의 머리에 오는 빈칸도 남기지 않는다.
3. `breaks` 가 하나도 없는 줄은 빈칸 무리의 첫 자리에서 끊는다. **이때도 줄 머리 들여쓰기는 지킨다.** 줄 맨 앞의 빈칸 무리는 끊는 자리로 치지 않는다.
4. 1단계 제목(`heading_level` 1)은 32칸을 넘어 접힌 줄만 조각마다 가운데로 놓는다. 안 접힌 줄은 `cells` 에 이미 가운데 여백이 있다.
5. `breaks` 값은 `cells` 전체 기준이다. 줄마다 그 줄의 시작 오프셋을 빼서 쓴다.
6. 사람이 어떤 요소의 **점자를 직접 고치면** 그 요소의 `breaks` 는 낡는다. 그 요소는 `breaks` 를 버리고 3번(빈칸 자리)으로 접는다.

**검증**: 2027 수능특강 8권(39,562요소)에서 이 함수로 접은 결과를 엔진 조판과 견줬다. 다른 요소가 0이다.

## 6. `breaks` 를 꼭 써야 하는 까닭

한국어 점자는 **한글을 음절 단위로 줄바꿈하는 것이 원칙**이다(「점자 자료 제작 지침」 2.1.1(2), 「점자 도서 제작 지침」 1장 2절 1). 그런데 셀만 봐서는 음절 경계를 알 수 없다. `⠉` 는 `나`(약자)이기도 하고 초성 ㄴ 이기도 하다. `나이`(⠉⠣⠕)에서 ⠉|⠣ 는 음절 안이고 ⠉⠣|⠕ 가 음절 경계다. 묵자를 아는 엔진만 이것을 가른다. 그래서 엔진이 자리를 알려 주고 부르는 쪽은 그 자리에서만 끊는다.

- 2027 수능특강 8권 39,562요소 실측: `breaks` 없이 **빈칸에서만 접으면 66.7% 가 엔진과 다르게 접힌다.** `breaks` 로 접으면 다른 요소가 0이다.
- 지침은 시험 문제지처럼 특별한 경우 **어절 단위** 줄바꿈도 허용한다. 어절 단위로 접으려면 `breaks` 중 빈칸 자리만 쓰면 된다.

## 7. 오류와 사이드카가 죽었을 때

- 한 요청이 실패하면 `error` 응답이 오고 사이드카는 계속 돈다(3절 예). UTF-8 로 못 푸는 줄도 그 줄만 `error` 다(2절).
- `translate` 안에서 엔진이 예외를 던지면 `error` 가 아니라 그 요소만 '점역 못 함'(`blocked: true`)으로 온다. AI 서버가 요소 하나의 실패로 나머지를 잃지 않는 것과 같은 길이다. 까닭은 표준오류에 찍힌다(#52). 요청 꼴이 틀린 것(옵션 값이 참거짓이 아님 등)은 종전대로 `error` 다.
- **빈 줄 · 공백뿐인 줄에는 응답이 없다.** 요청과 응답은 줄 수가 아니라 `id` 로 짝짓는다.
- **표준오류를 반드시 비운다.** 엔진이 경고를 표준오류로 쓴다. 표준오류를 파이프로 받고 읽지 않으면 파이프가 차서 사이드카가 멈춘다. C# 이면 `RedirectStandardError = true` 로 두고 `BeginErrorReadLine` 으로 비동기로 읽어 버리거나, 리디렉트를 끈다.
- 사이드카가 죽으면 표준출력이 닫힌다(C# `ReadLine()` 이 `null`). 부르는 쪽은 다시 띄우고, 답을 못 받은 요청을 다시 보낸다. translate 와 decode 는 같은 입력에 늘 같은 출력을 내므로 다시 보내도 된다. 짧은 사이에 거듭 죽으면(예: 1분에 세 번) 다시 띄우기를 멈추고 사용자에게 알린다.
- 부르는 프로그램이 끝날 때 사이드카도 함께 끝나게 하려면 Windows 에서는 Job Object(`JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`)에 넣는다. 평소에는 표준입력을 닫으면 스스로 끝난다.
- C# 예제 [`examples/csharp-sidecar/Program.cs`](../examples/csharp-sidecar/Program.cs) 가 표준오류 비우기(`BeginErrorReadLine`) · `id` 로 짝짓기 · 빈 줄 · 표준입력 닫아 끝내기를 그대로 한다. CI 가 윈도우에서 돌린다(8절). Job Object 와 죽은 사이드카 다시 띄우기는 예제에 없고 시험하지 않았다.
- 스레드: 점역은 CPU 계산이라 한 프로세스 안에서 스레드를 늘려도 빨라지지 않는다. 사이드카 하나가 요청을 차례로 처리하게 두고, 동시에 여러 건이 필요하면 사이드카를 여럿 띄운다.

## 8. 윈도우 · .NET 앱에서 띄우기

**앱은 표준입출력 인코딩을 UTF-8 로 정해 주어야 한다.** .NET 은 따로 안 주면 콘솔 인코딩을 쓰는데 한국어 윈도우 기본이 cp949 다. 그러면 한글이 든 요청이 전부 `error` 로 돌아온다(아래 표 A).

```csharp
var psi = new ProcessStartInfo {
    FileName  = pythonPath,
    Arguments = "-m semojum_braille.sidecar",
    RedirectStandardInput  = true,
    RedirectStandardOutput = true,
    RedirectStandardError  = true,          // 7절대로 비동기로 읽어 비운다
    UseShellExecute = false,
    CreateNoWindow  = true,
    StandardInputEncoding  = new UTF8Encoding(false),   // BOM 없이. 이 둘이 핵심이다
    StandardOutputEncoding = new UTF8Encoding(false),
};
psi.Environment["PYTHONUTF8"] = "1";
```

이 설정은 C# 예제 [`examples/csharp-sidecar`](../examples/csharp-sidecar/Program.cs) 에 그대로 있다. CI([`windows.yml`](../.github/workflows/windows.yml))가 windows-latest 에서 파이썬 3.10 · 3.13 으로 패키지를 깔고 시험을 돈 뒤, 이 예제를 `dotnet run` 으로 돌려 실제 사이드카를 부른다. 예제가 보는 것:

- ping 의 `protocol` 1 · 한글 translate 를 ASCII(`System.Text.Json` 기본)로 보낸 것과 UTF-8 그대로 보낸 것이 둘 다 README 와 같은 점자 · `breaks` 가 C# `string` 인덱스 그대로 쓸 수 있는 오름차순 · decode · 빈 줄 뒤 요청도 `id` 로 바로 짝지어짐 · 표준입력을 닫으면 종료 코드 0
- 표준입력을 cp949 로 둔 잘못된 설정(아래 표 F)에서 한글 요청이 깨진 점자가 아니라 `error` 로 오고, 같은 설정이라도 ASCII 로 보내면 맞는 것

CI 러너는 영어 로캘이라 한국어 윈도우 콘솔 기본(cp949)은 예제가 `Encoding.GetEncoding(949)` 로 직접 지정해 재현한다. **한국어 로캘 PC · 앱에 파이썬을 실어 낸 꼴 · 프로세스 죽임은 아직 재지 않았다.** 아래 표는 리눅스에서 **윈도우라서 달라지는 것만**(앱이 쓰는 인코딩 · 줄 끝 · BOM · 파이썬 표준입력 기본 인코딩) 바꿔 가며 실제 사이드카 프로세스에 보낸 결과다. 그중 D(권장)와 F(앱 cp949 · 파이썬 UTF-8 모드) 줄은 윈도우 CI 에서도 같게 나왔다. A(파이썬 기본 인코딩)는 윈도우에서 돌리지 않았다.

| | 앱이 쓰는 인코딩 | 파이썬 쪽 | 줄 끝 | 3.4.10 | 3.4.11 부터 |
|---|---|---|---|---|---|
| A | cp949(.NET 기본) | 기본(cp949) | CRLF | 정상 | **한글 요청 `error`**(id 돌려줌) |
| B | UTF-8 | 기본(cp949) | CRLF | **죽음 · 응답 0줄** | 정상 |
| C | UTF-8 + BOM | 기본(cp949) | CRLF | **죽음 · 응답 0줄** | 정상 |
| D | UTF-8 | UTF-8 모드(`PYTHONUTF8=1`) | CRLF | 정상 | 정상 |
| E | UTF-8 | UTF-8 모드 | LF | 정상 | 정상 |
| F | cp949 | UTF-8 모드 | CRLF | **깨진 점자 · 오류 없음** | 한글 요청 `error` |
| G | UTF-16LE | UTF-8 모드 | CRLF | 전부 `error` | 전부 `error` |

- 3.4.10 까지는 앱과 파이썬이 **둘 다 cp949** 일 때(A)만 맞았다. 앱이 아무것도 안 정하면 우연히 맞던 셈이다. 3.4.11 부터 표준입력을 바이트로 받아 UTF-8 로만 풀기 때문에(2절) A 가 `error` 로 바뀐다. **앱이 이미 있다면 지금 어느 설정으로 부르는지부터 본다.**
- F 는 3.4.10 에서 **글이 깨진 점자를 오류 없이** 돌려줬다(`다음 글을 읽고 물음에 답하시오.` → `cells` 7칸 `⠀⠀⠽⠈⠲⠲⠲`). 앱은 점역됐다고 믿는다. 3.4.11 부터 `error` 로 드러난다.
- 줄 끝은 CRLF · LF 둘 다 된다. BOM 은 붙어도 된다(2절). UTF-16 은 안 된다.
- 기동하면 `ping` 의 `protocol` 이 앱이 아는 값인지 본다(3절). `version` 은 로그에 남긴다.

**아직 남은 것**
- 줄 하나가 길면 오래 걸린다. 사이드카는 요청을 차례로 처리하니 뒤 요청이 다 기다린다. 3.4.12 에서 같은 글 되풀이 순한글 1,000자는 새 프로세스 첫 요청까지 약 1초다(kiwi 없음). 숫자 · 괄호가 든 긴 산문 줄은 아직 줄 길이의 제곱으로 늘어난다(AI#1323). 앱은 긴 요청에 시간 제한을 두고 넘으면 사용자에게 알린다.
- 엔진이 `os.environ` 으로 읽는 스위치가 있다(A/B 용). 앱 프로세스 환경이 그대로 넘어가므로 필요한 것만 남긴 환경으로 띄우는 쪽이 안전하다.
- 형태소 분석기(`[kiwi]`)는 앱에 넣지 않는다([NOTICE.md](../NOTICE.md) ①). 깔면 기동 직후 첫 요청이 판정기 올리는 시간(약 2.7초)과 겹친다.

**윈도우 휠**: `braillify` 2.0.1 은 cp310~cp314 `win_amd64`, `pydantic-core` 는 `win32` · `win_amd64` 휠이 PyPI 에 있다. 윈도우 CI 가 `pip install` 로 이 휠을 받아 깐다(2026-10-14 실측: `braillify-2.0.1-cp313-cp313-win_amd64` · `pydantic_core-2.50.1-cp313-cp313-win_amd64`).

---

## 검수 등급의 뜻 (`grade` op, 화면 문구를 쓰기 전에 읽을 것)

등급은 **점역사가 어느 요소부터 볼지 정하는 순서**다. 맞다 · 틀리다의 판정이 아니다.

| 등급 | 뜻 | 정하는 법 |
|---|---|---|
| `low` | 먼저 볼 것 | 표 · 수식 · 원문에 영문(3자 이상)이나 LaTeX 명령이 있는 요소 · 추출 신뢰도 0.7 미만 · 왕복 일치도 0.98 미만 |
| `medium` | 보통 | 왕복 일치도를 잴 수 없는 요소(원문이 짧다 등) · 0.98 이상 0.999 미만 · 120칸 이상 |
| `high` | **나중에 봐도 되는 것** | 왕복 일치도 0.999 이상이고 120칸 미만 |

- ⚠ **`high` 는 '확인 불필요'가 아니다.** 실측에서 `high` 요소도 정확도 89%다(오프라인 전 코퍼스 22,384요소). AI 서버 경로로 다시 잰 dev+val 839쪽에서는 `high` 의 71.1% 가 정답과 편집 0칸이었다. 즉 열에 하나는 틀린다.
- 화면 문구는 순서로만 쓴다. 쓸 만한 말: `먼저 확인` · `확인` · `나중에 확인`. **쓰면 안 되는 말: `확인 불필요` · `검수 완료` · `정확` · `통과` · 퍼센트 점수.** 숫자를 보이면 "89%면 안 봐도 되나"로 읽힌다.
- 표 · 수식 · 영문이 늘 `low` 인 것은 그 갈래의 실측 정확도가 가장 낮아서다(표 2.0% · 영문 23.7% · 수식 25.9%, 전체 55.6%).
- 왕복 일치도는 정답 없이 런타임에 잰다. 역점역기가 틀리게 되돌리면 맞는 점역도 `low` 가 될 수 있다.
- 기준과 실측의 출처는 `semojum_braille.confidence` 모듈 설명이다(AI 저장소 `app/ai/quality/confidence.py` 를 옮긴 것). 파이썬에서는 `semojum_braille.sidecar.grade(braille, source, etype="text", ocr_confidence=None, korean_grade=2) -> dict` 다.
