"""세모점 점역·역점역 엔진.

- `semojum_braille.encoder`: 묵자(한국어 글·수식·표·시각 자료 설명)를 한국어 점자로 옮긴다.
- `semojum_braille.decoder`: 한국어 점자를 묵자로 되돌린다. 검수용 근사다.
- `semojum_braille.schemas`: 둘이 함께 쓰는 데이터 타입.
- `semojum_braille.assist`: 점역된 점자를 면으로 나누고 페이지행 · 원본 페이지 변경선을 넣는다(옛 braille-assist).
- `semojum_braille.brf`: 점자 면을 현장 꼴 `.brf` 바이트로 내고, `.brf` 를 점자 면으로 읽는다.
- `semojum_braille.sidecar`: 파이썬이 아닌 프로그램이 표준입출력으로 부르는 입구.
"""
