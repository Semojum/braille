# 라이선스

이 저장소는 **MIT 와 Apache License 2.0 중 받는 쪽이 고르는** 이중 라이선스다.
`LICENSE-MIT` · `LICENSE-APACHE` 둘 다 저장소에 있다.

## 기여

따로 밝히지 않는 한, 기여한 것도 같은 두 라이선스로 받는다.

## ⚠ 의존 라이선스 — 배포 전에 확인해야 하는 것 둘

우리 라이선스와 별개로 **의존이 걸린다.** 실측(2026-09-29, 설치된 `dist-info/METADATA` · braillify 는 2026-10-09 다시 잼):

| 의존 | 라이선스 | |
|---|---|---|
| `pydantic` · `pydantic-core` | MIT | 문제 없다 |
| `kiwipiepy` | **LGPL v3** | 아래 ① |
| `braillify` | **Apache-2.0**(파이썬 휠에는 표기 · 고지 파일 없음) | 아래 ② |

**① `kiwipiepy` 가 LGPL v3 다.**
별도 패키지로 설치해 임포트하는 꼴은 대체로 문제가 없다고 본다. 그러나 **사이드카를 한 덩어리
실행 파일로 묶으면**(PyInstaller 등) LGPL 의 "받는 사람이 그 라이브러리를 바꿔 끼울 수 있어야
한다" 는 조항이 걸린다. 그래서 `[kiwi]` 를 **선택 의존**으로 두고 기본 설치에서 뺀다.
기본은 낱말 목록(`kor_words.json`, 0.38MB)을 쓴다.
★ 실측으로도 낱말 목록이 낫다 — 12권 중 8권에서 이기고 순이득 +204 대 +149 다.

**② `braillify` 는 Apache License 2.0 이다(2026-10-09 다시 잼, #15 · Semojum/AI#1255).**
PyPI 메타데이터와 설치본 `METADATA` 의 라이선스 칸은 비어 있다. 09-29 판은 이 칸만 보고 "없다" 고 적었다.
그러나 같은 `dist-info` 의 `sboms/python.cyclonedx.json`, crates.io 의 braillify 2.0.1, 원 저장소
github.com/dev-five-git/braillify 의 `LICENSE` · `NOTICE` 가 모두 Apache-2.0 이다. 비어 있는 것은 파이썬
바인딩 패키지(`packages/python`) 표기뿐이다.

- 이 저장소는 braillify 를 품지 않고 `pyproject.toml` 에 의존으로 적기만 한다. 공개는 재배포가 아니다.
- **앱에 실어 배포하는 시점에 걸린다.** 사이드카를 묶어 내면 braillify 를 재배포하는 셈이다. Apache-2.0 은
  그때 라이선스 사본과 NOTICE 내용을 함께 실으라고 한다(4조 (a) · (d)). 휠에는 그 파일이 없으므로 앱 제3자
  고지에 braillify `LICENSE` · `NOTICE`(그 안의 Unihan 자료 고지 포함)를 우리가 넣는다.
- 쓰는 범위와 의존 크기는 Semojum/AI#1255 에서 잰다.
