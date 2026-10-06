# semojum-braille

[![시험](https://github.com/Semojum/braille/actions/workflows/test.yml/badge.svg)](https://github.com/Semojum/braille/actions/workflows/test.yml)
![파이썬](https://img.shields.io/badge/python-3.10%20%7C%203.12%20%7C%203.13-blue)
![판](https://img.shields.io/badge/version-3.4.2-blue)
![라이선스](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-green)

한국어 묵자를 점자로 옮기고(점역), 점자를 묵자로 되돌리는(역점역) 파이썬 라이브러리입니다.

## 빠른 시작

```python
>>> from semojum_braille.encoder import translate_tagged_text
>>> translate_tagged_text("대한민국의 모든 국민은 법 앞에 평등하다.")
'⠊⠗⠚⠒⠑⠟⠈⠍⠁⠺⠀⠑⠥⠊⠵⠀⠈⠍⠁⠑⠟⠵⠀⠘⠎⠃⠀⠣⠲⠝⠀⠙⠻⠊⠪⠶⠚⠊⠲'
```

```python
>>> from semojum_braille.decoder import decode
>>> decode("⠊⠗⠚⠒⠑⠟⠈⠍⠁")
'대한민국'
```

점자 면 배열을 `.brf` 파일 바이트로 냅니다. 줄 끝은 `\r\n`, 쪽(26줄)마다 끝에 `\x0c` 입니다.

```python
>>> from semojum_braille.brf import serialize_brf
>>> serialize_brf([["⠼⠁", "⠁⠃"]], rows=3)
b'#a\r\nab\r\n\r\n\x0c'
```

`.brf` 파일을 거꾸로 읽어 유니코드 점자 면으로 돌립니다(`.brf` 를 열어 역점역할 때). 대소문자 두 꼴을 다 받고, 백틱은 ⠈(초성 ㄱ)로 읽습니다.

```python
>>> from semojum_braille.brf import parse_brf
>>> parse_brf(b"#a\r\nab\r\n\r\n\x0c")
[['⠼⠁', '⠁⠃', '']]
```

글 속 수식은 `<!수식>` 태그로 감쌉니다.

```python
>>> translate_tagged_text("방정식 <!수식>x+1=3<!/수식>의 해")
'⠘⠶⠨⠻⠠⠕⠁⠀⠀⠭⠢⠼⠁⠒⠒⠼⠉⠀⠀⠺⠀⠚⠗'
```

## 설치

```
pip install "semojum-braille @ git+https://github.com/Semojum/braille"
```

파이썬 3.10 이상. PyPI 에는 아직 없습니다.

| 추가 | 무엇 | 설치 크기 |
|---|---|---:|
| (없음) | 점역·역점역 전부. 역점역의 낱말 판정은 낱말 목록 | 약 15MB |
| `[kiwi]` | 역점역의 낱말 판정을 형태소 분석기 `kiwipiepy` 로 | 약 233MB |
| `[test]` | `pytest` | |

```
pip install "semojum-braille[kiwi] @ git+https://github.com/Semojum/braille"
```

의존: `braillify==2.0.1` · `pydantic>=2.9,<3` · 선택 `kiwipiepy>=0.23,<0.24`.

## 기능

- 한글 약자, 숫자, 문장 부호, 특수 기호, 글 속 영어(통일영어점자 약자)
- LaTeX 수식을 수학 점자로. 글에 섞인 평문 수식(`x+1=3`)도 찾아 감쌉니다
- 표를 다섯 가지 조판 안으로: 풀어쓰기, 격자, 행열 바꿈, 테두리만, 번호 체계
- 그림·그래프 설명. 초안이 여럿이면 초안마다
- 32칸 × 26줄 쪽 조판: 제목 들여쓰기, 문단 들여쓰기, 쪽 번호 줄
- 점역된 문서를 면으로 나누고 페이지행 · 원본 페이지 변경선을 넣는 조판(`semojum_braille.assist`, braille-assist 에서 옮김)
- 점자 면을 현장 유통본과 같은 꼴의 `.brf` 바이트로: 줄 끝 `\r\n`, 쪽마다 끝에 `\x0c`, 소문자 BRF ASCII, 32칸
- `.brf` 파일을 유니코드 점자 면으로 읽기(현장 두 꼴 · 탭 맞춤 줄까지). 역점역에 넘길 때 쓴다
- 한글을 음절 단위로 끊을 수 있는 자리를 함께 반환
- 요소마다 근거가 된 규정 조항(`rule_trail`)
- 점자를 묵자로 되돌려 초안 검토용 글로
- 파이썬이 아닌 곳(C# 등)에서 표준입출력으로 부르는 사이드카
- 규칙 기반. 모델도 네트워크도 없이 돌고, 같은 입력에 늘 같은 점자

## 문서

| | |
|---|---|
| [docs/encoder.md](docs/encoder.md) | 점역 API, 태그 문법, 데이터 타입, 설정, 모듈 구성 |
| [docs/decoder.md](docs/decoder.md) | 역점역 API, 설정 |
| [docs/sidecar.md](docs/sidecar.md) | 표준입출력 프로토콜, 32칸 접기 |
| [docs/regulations.md](docs/regulations.md) | 어느 조항을 어느 모듈이 지키나 |

## 규정 근거

「한국 점자 규정」(문화체육관광부 2024) · 「점자 도서 제작 지침」(국립장애인도서관 2025) ·
「점자 자료 제작 지침」(국립특수교육원 2025).

규정과 점자 도서 관행이 갈리는 자리는 기본값이 도서 관행입니다. `BRAILLE_STYLE=regulation` 이면 규정 원형을 씁니다.

## 한계

- 그림을 보고 설명을 짓거나 글자를 인식(OCR)하지 않습니다
- 악보(음악 점자)는 옮기지 않습니다
- 기호표에 없는 기호는 경고 없이 빠집니다
- 역점역은 검수용 근사입니다. 원문을 되살리지 않고, 점자가 규정대로인지 판정하지도 않습니다
- 기본 설치의 역점역은 낱말 목록에 없는 한국어 낱말을 영어로 읽을 수 있습니다. `[kiwi]` 를 깔면 줄어듭니다
- 스레드 안전, Windows, 파이썬 3.11 · 3.14 는 시험하지 않았습니다

## 기여

[CONTRIBUTING.md](CONTRIBUTING.md)

## 라이선스

MIT 또는 Apache License 2.0 중 받는 쪽이 고릅니다. 의존 라이선스는 [NOTICE.md](NOTICE.md) 를 보십시오.
