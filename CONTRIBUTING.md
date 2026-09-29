# 기여 안내

## 코드의 정본은 AI 저장소입니다

점역·역점역 엔진은 `Semojum/AI` 저장소에서 개발하고, 이 저장소는 `tools/sync_from_ai.py` 로 그 코드를 옮겨 옵니다.
아래 파일은 동기화할 때 덮어쓰므로 **여기서 직접 고치지 않습니다.** 고칠 것이 있으면 AI 저장소에서 고친 뒤 다시 동기화합니다.

| 이 저장소 | AI 저장소 |
|---|---|
| `semojum_braille/encoder/*.py` · `*.json` (`__init__.py` 빼고) | `app/ai/braille/` |
| `semojum_braille/encoder/gates.py` | `app/ai/gates.py` |
| `semojum_braille/schemas.py` | `app/schemas/content.py` 의 다섯 타입 |
| `semojum_braille/decoder/back.py` | `app/utils/braille_back.py` |
| `semojum_braille/decoder/` 의 역맵 json 셋 | `app/utils/` |
| `test/unit_test/**` · `test/braille_style_equiv.py` · `test/support/braille_ascii.py` | `test/` · `app/utils/braille_ascii.py` |

이 저장소에서 직접 고치는 것은 그 밖의 파일입니다. 패키지 첫머리(`__init__.py` 셋), 사이드카(`sidecar.py`), 낱말 목록(`decoder/wordlist.py` · `decoder/kor_words.json`), 문서, `tools/`, `test/test_*.py` · `test/conftest.py` 입니다. 목록은 `tools/sync_from_ai.py` 의 `OWN` 에 있습니다.

## 개발 환경

```
git clone https://github.com/Semojum/braille && cd braille
python -m venv .venv && . .venv/bin/activate
pip install -e ".[test,kiwi]"
pytest
python tools/check_docs.py
```

kiwi 가 없는 설치도 함께 봅니다. `pip install -e ".[test]"` 만 깐 가상환경을 하나 더 두고 `pytest` 를 돌립니다. kiwi 에 기대는 시험은 그 환경에서 이유를 달고 건너뜁니다(`test/conftest.py` 의 `_NEEDS_KIWI`).

## AI 저장소에서 다시 옮기기

```
python tools/sync_from_ai.py <AI 저장소 경로>
pytest                                   # [kiwi] 를 깐 환경과 안 깐 환경 둘 다
python tools/check_docs.py
```

- 코드는 임포트 경로만 바꿉니다. 그 밖의 변경은 `tools/sync_from_ai.py` 의 패치 목록 둘뿐입니다. `SILENT_FIXES` 는 역맵 파일이 없을 때 빈 맵으로 조용히 돌지 않고 예외를 내게 합니다. `KIWI_OPTIONAL` 은 kiwi 가 없으면 낱말 목록을 보게 합니다. 패치할 자리를 못 찾으면 동기화가 멈춥니다. AI 쪽 원본이 바뀐 것이니 패치를 원본에 맞게 고칩니다.
- 옮길 시험은 `tools/tests_from_ai.txt` 에 적습니다. 엔진을 부르고, AI 서버 모듈이나 정답 코퍼스(`test_data/`)를 부르지 않는 시험만 옮깁니다.
- AI 저장소에서 이미 깨져 있는 시험은 `test/conftest.py` 의 `_BROKEN_IN_AI` 에 적어 xfail(strict)로 둡니다. AI 가 고친 뒤 다시 옮기면 XPASS 가 실패로 드러나니, 그때 목록에서 뺍니다.
- 커밋 메시지에 옮겨 온 AI 커밋을 적습니다(예: `AI develop 8dc7e7b 로 재동기화`).

## 문서

- 코드 예는 실제로 돌린 출력을 붙입니다. `python tools/check_docs.py` 가 README 와 `docs/` 의 `>>>` 예를 모두 다시 돌려 맞춥니다.
- 규정 조항 번호는 규정 원문과 대조해 적습니다.
- 돌려 보지 않은 것, 시험하지 않은 것은 그렇다고 적습니다.
- 공개 계약은 문서에 적은 이름뿐입니다. 밑줄(`_`)로 시작하는 이름과 `docs/encoder.md` 4절의 "계약 아님" 칸의 이름은 판이 오르면 바뀔 수 있습니다.
- 한국어로 씁니다.

## 낱말 목록 다시 만들기

`decoder/kor_words.json` 은 `tools/build_word_list.py <묵자 json 폴더>` 로 만듭니다. 영어 교재는 넣지 않습니다(역점역 판정이 주로 불리는 책을 목록이 미리 보지 않게). 목록을 바꾸면 kiwi 와 견준 측정([docs/decoder.md](docs/decoder.md) 1절)을 다시 합니다.
