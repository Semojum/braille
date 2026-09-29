# semojum-braille

[![시험](https://github.com/Semojum/braille/actions/workflows/test.yml/badge.svg)](https://github.com/Semojum/braille/actions/workflows/test.yml)
![파이썬](https://img.shields.io/badge/python-3.10%20%7C%203.12%20%7C%203.13-blue)
![판](https://img.shields.io/badge/version-3.4.0-blue)
![라이선스](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-green)

한국어 묵자를 점자로 옮기고(점역), 점자를 묵자로 되돌리는(역점역) 파이썬 라이브러리입니다.

## 빠른 시작

점역:

```python
>>> from semojum_braille.encoder import translate_tagged_text
>>> translate_tagged_text("대한민국의 모든 국민은 법 앞에 평등하다.")
'⠊⠗⠚⠒⠑⠟⠈⠍⠁⠺⠀⠑⠥⠊⠵⠀⠈⠍⠁⠑⠟⠵⠀⠘⠎⠃⠀⠣⠲⠝⠀⠙⠻⠊⠪⠶⠚⠊⠲'
```

역점역:

```python
>>> from semojum_braille.decoder import decode
>>> decode("⠊⠗⠚⠒⠑⠟⠈⠍⠁")
'대한민국'
```

글 속 수식은 `<!수식>` 태그로 감싸 넣습니다.

```python
>>> translate_tagged_text("방정식 <!수식>x+1=3<!/수식>의 해")
'⠘⠶⠨⠻⠠⠕⠁⠀⠀⠭⠢⠼⠁⠒⠒⠼⠉⠀⠀⠺⠀⠚⠗'
```

## 설치

```
pip install "semojum-braille @ git+https://github.com/Semojum/braille"
```

파이썬 3.10 이상에서 돕니다(3.10 · 3.12 · 3.13 에서 시험). PyPI 에는 아직 올리지 않았습니다.

선택 의존:

| 붙이는 것 | 무엇 | 설치 크기 |
|---|---|---:|
| (없음) | 점역과 역점역 전부. 역점역의 한국어 낱말 판정은 낱말 목록으로 합니다 | 약 15MB |
| `[kiwi]` | 역점역의 낱말 판정을 형태소 분석기 kiwi(`kiwipiepy`)로 합니다 | 약 233MB |
| `[test]` | 시험 도구(pytest) | |

```
pip install "semojum-braille[kiwi] @ git+https://github.com/Semojum/braille"
```

설치 크기는 리눅스·파이썬 3.10 에서 잰 값입니다. 둘의 차이는 [docs/decoder.md](docs/decoder.md) 1절에 있습니다.

의존: `braillify==2.0.1`(한글 점역, Rust 확장) · `pydantic>=2.9,<3` · 선택 `kiwipiepy>=0.23,<0.24`.

## 기능

- 한국어 글을 점자로 옮깁니다. 한글 약자, 숫자, 문장 부호, 특수 기호, 글 속 영어(통일영어점자 약자)를 다룹니다.
- LaTeX 수식을 수학 점자로 옮기고, 글에 섞인 평문 수식(`x+1=3`)을 찾아 감쌉니다.
- 표를 다섯 가지 조판 안(풀어쓰기, 격자, 행열 바꿈, 테두리만, 번호 체계)으로 옮깁니다.
- 그림·그래프 설명을 옮깁니다. 설명 초안이 여럿이면 초안마다 옮깁니다.
- 32칸 × 26줄 쪽으로 조판합니다. 제목 단계별 들여쓰기, 문단 들여쓰기, 쪽 번호 줄을 넣습니다.
- 한글을 음절 단위로 줄바꿈할 수 있는 자리를 함께 돌려줍니다.
- 점역한 요소마다 근거가 된 규정 조항(`rule_trail`)을 붙입니다.
- 점자를 묵자로 되돌려 점자 초안을 검토할 때 곁에 둘 글을 만듭니다(한글, 로마자, 숫자, 점역자 주, 수식).
- 파이썬이 아닌 프로그램(C# 등)이 표준입출력으로 부를 수 있는 사이드카를 둡니다.
- 규칙 기반이라 모델이나 네트워크 없이 돌고, 같은 입력에 늘 같은 점자를 냅니다.

## 문서

| 문서 | 내용 |
|---|---|
| [docs/encoder.md](docs/encoder.md) | 점역 API 레퍼런스(공개 함수 전부), 입력 태그 문법, 데이터 타입, 설정, 모듈 구성 |
| [docs/decoder.md](docs/decoder.md) | 역점역 API 레퍼런스, kiwi 가 있을 때와 없을 때, 설정 |
| [docs/sidecar.md](docs/sidecar.md) | 파이썬이 아닌 곳에서 쓰기: 표준입출력 프로토콜, 32칸 접기 |
| [docs/regulations.md](docs/regulations.md) | 규정 근거: 어느 조항을 어느 모듈이 지키나 |

문서의 `>>>` 예는 모두 실제로 돌린 입출력입니다. `python tools/check_docs.py` 가 문서에서 예를 꺼내 다시 돌려 맞춥니다.

## 규정 근거

「한국 점자 규정」(문화체육관광부 2024), 「점자 도서 제작 지침」(국립장애인도서관 2025), 「점자 자료 제작 지침」(국립특수교육원 2025)을 따릅니다. 규정과 점자 도서 관행이 갈리는 몇 자리는 기본값이 도서 관행이고, `BRAILLE_STYLE=regulation` 으로 띄우면 규정 원형을 씁니다. 조항마다 어느 모듈이 지키는지는 [docs/regulations.md](docs/regulations.md) 에 있습니다.

## 한계

- 그림을 보고 설명을 짓거나 글자를 인식(OCR)하지 않습니다. 묵자 글을 받아 옮깁니다.
- 악보(음악 점자)는 옮기지 않습니다.
- 기호표에 없는 기호는 경고 없이 빠집니다.
- 역점역은 검수용 근사입니다. 원문을 되살리지 않고, 점자가 규정대로인지 판정하지도 않습니다.
- 기본 설치의 역점역은 낱말 목록에 없는 한국어 낱말(외래어, 생활 낱말)을 영어로 읽을 수 있습니다. `[kiwi]` 를 깔면 줄어듭니다.
- 시험하지 않은 것: 스레드 안전, Windows, 파이썬 3.11 · 3.14.

자세한 것은 [docs/encoder.md](docs/encoder.md) 5절, [docs/decoder.md](docs/decoder.md) 6절에 있습니다.

## 기여

[CONTRIBUTING.md](CONTRIBUTING.md) 를 봐 주세요. 엔진 코드의 정본은 `Semojum/AI` 저장소이고, 이 저장소는 `tools/sync_from_ai.py` 로 그 코드를 옮겨 옵니다.

## 라이선스

MIT 와 Apache License 2.0 중 **받는 쪽이 고릅니다**. `LICENSE-MIT` · `LICENSE-APACHE` 를 보십시오.

⚠ 의존 라이선스 둘이 배포 전에 걸립니다. `NOTICE.md` 에 적었습니다.
`kiwipiepy` 가 LGPL v3 라 선택 의존(`[kiwi]`)으로 뺐고, `braillify` 는 라이선스 표기가 없습니다.
