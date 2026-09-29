"""역점역: 한국어 점자를 묵자로 되돌린다.

점역 결과를 사람이 읽을 글로 되돌려 **검수에 쓰는 것**이 목적이다. 원문 복원이 아니다.
정본 진입점은 `decode` 하나다.

    from semojum_braille.decoder import decode
    print(decode("⠊⠗⠚⠒⠑⠟⠈⠍⠁"))
"""
from __future__ import annotations

from semojum_braille.decoder.back import decode

__all__ = ["decode"]
