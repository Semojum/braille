"""점자 조판 공용 함수: 면 나누기 · 줄 자르기 · 페이지행 · 원본 페이지 변경선 · BRF 조립.

braille-assist(`python/braille_assist/core.py`, develop 2c41d8d)에서 옮겨 왔다(2026-10-04). 파이썬 기준 구현은
이제 여기다. 같은 함수의 ts(`ts/`) · java(`java/`) 판도 braille-assist develop 38e21e2 에서 이 저장소로 옮겨 왔다
(2026-10-09). 동작 명세는 루트 `vectors.json`(0.3.0) 하나다. 파이썬은 `test/test_assist_vectors.py`,
ts · java 는 `.github/workflows/assist.yml` 이 같은 파일로 맞춘다. 규칙을 바꾸면 세 구현과 벡터를 한 PR 로 고친다.

이 모듈은 한글을 점역하지 않는다. 이미 점역된 점자를 받아 배치만 한다.
근거: 「점자 도서 제작 지침」 1장 2절 2(페이지 구성) · 1장 3(꼬리말) · 2장 2절 2-3(원본 페이지 변경선).

★ 파일로 낼 때는 `build_brf_file` 을 쓴다(현장 꼴 `.brf` 바이트, `semojum_braille.brf`).
  `build_brf` · `to_brf_ascii` 는 벡터가 묶은 옛 꼴(줄 끝 `\n`, FF 없음, `{ | } ~` · `@`)이라 그대로 둔다.
"""

from __future__ import annotations

from dataclasses import dataclass

from .brf import serialize_brf

SPACE = "⠀"          # 공백 셀 ⠀
NUM_SIGN = "⠼"       # 수표 ⠼
CHANGE_MARK = "⠤"    # 원본 페이지 변경선 채움 ⠤

# 숫자·알파벳은 같은 점형을 쓴다(1=a=⠁ … 0=j=⠚). 수표가 앞에 오면 숫자로 읽는다.
_DIGIT_CELLS = "⠚⠁⠃⠉⠙⠑⠋⠛⠓⠊"  # 0..9 = j a b c d e f g h i
_ALPHA_CELLS = (
    "⠁⠃⠉⠙⠑⠋⠛⠓⠊⠚"  # a..j
    "⠅⠇⠍⠝⠕⠏⠟⠗⠎⠞"  # k..t
    "⠥⠧⠺⠭⠽⠵"                          # u..z
)

# BRF Braille ASCII 64셀 표준표(유니코드 오프셋 0..63 순). 출처는 `code/AI/app/utils/braille_ascii.py`와
# 같은 표 — 여기 새로 만들지 않고 그대로 옮겼다(backtick=⠈ 사고 전례가 있어 임의 변형 금지).
_BRAILLE_ASCII = (
    " A1B'K2L@CIF/MSP"
    '"E3H9O6R^DJG>NTQ'
    ",*5<-U8V.%[$+X!&"
    ";:4\\0Z7(_?W]#Y)="
)
assert len(_BRAILLE_ASCII) == 64


@dataclass(frozen=True)
class Options:
    """조판 옵션. 1차 PoC 고정값이 기본값이다(조판 가이드 §5).

    page_row_on — 페이지행을 넣는 면. **기본은 홀수 면만**이다(2026-08-06 변경).
      지침 1장2절2-1이 홀수 면만이라 하고, 점자 도서 82권 실측에서도 페이지행을 가진 면이
      100% 홀수였다(원장 C-11 — 규정=관행 확정). 종전 기본값 "every"는 규정과 어긋났다.
      `every`·`even`·`none`으로 바꿀 수 있다 — 고정이 아니라 기본값일 뿐이다.

    cover_pages — **원본 페이지 개수**다. 점자 면 수가 아니다(2026-09-01 확정).
      앞에서 이만큼의 원본 페이지를 표지로 보고 ① 페이지행을 넣지 않고 ② 본문 번호를
      그 뒤부터 센다. `orig_page_start`와 함께 계산된다.
      ③ **점자 면 번호도 소비하지 않는다**(2026-09-08). 지침 1장2 3)(1)(도서 335행)
      "점자 페이지 번호는 점자 표지 다음 페이지를 1로 시작"·604행 "점자 표지에는 점자
      페이지 번호를 적지 않는다"·자료지침 §2.1.5(1)(557행). 종전에는 표지 면이 번호를
      먹어 본문 첫 면이 2·3번이 됐다.

    orig_page_start — 표지 다음 첫 본문 원본 페이지에 붙일 번호.
      None이면 `sources`가 준 `orig_page`를 그대로 쓴다(종전 동작).
      값을 주면 **표지 뒤 n번째 원본 페이지 = orig_page_start + n** 으로 다시 매긴다.

    show_change_line — 원본 페이지 변경선(원본 페이지 내용이 끝난 다음 줄, 새 원본 페이지
      번호만 적는 줄). 끄면 그 줄을 아예 넣지 않는다.
      ⚠ `show_orig_page`를 끄면 변경선에 적을 번호가 없어 `⠤`만 남은 빈 줄이 된다.
      그래서 `show_orig_page=False`면 변경선도 함께 꺼진다(2026-09-01 결정 D).

    footer_align — 꼬리말 정렬. `center`(지침 1장3-1 기본)와 `right`.
      right는 점자 페이지 번호 왼쪽에 **두 칸을 띄운 자리**가 오른쪽 끝이다(항목 사이 두 칸 이상).
    """

    cols: int = 32
    rows: int = 26
    show_orig_page: bool = True      # 페이지행 왼쪽의 원본 페이지 번호
    show_braille_page: bool = True   # 페이지행 오른쪽의 점자 페이지 번호
    page_row_on: str = "odd"         # odd | every | even | none
    cover_pages: int = 0             # 앞에서 이만큼의 **원본 페이지**가 표지 (아래 주석)
    orig_page_start: int | None = None   # 본문 첫 원본 페이지에 붙일 번호. None이면 준 값 그대로
    show_change_line: bool = True    # 원본 페이지 변경선을 넣을지
    footer_align: str = "center"     # center | right

    def __post_init__(self) -> None:
        if self.cols < 8:
            raise ValueError(f"cols는 8 이상이어야 한다: {self.cols}")
        if self.page_row_on not in ("every", "odd", "even", "none"):
            raise ValueError(f"page_row_on은 odd|every|even|none: {self.page_row_on!r}")
        if self.footer_align not in ("center", "right"):
            raise ValueError(f"footer_align은 center|right: {self.footer_align!r}")
        if self.cover_pages < 0:
            raise ValueError(f"cover_pages는 0 이상이어야 한다: {self.cover_pages}")


DEFAULT = Options()


def _number(n: int) -> str:
    """정수 → 수표 + 숫자 점형. 예: 12 → ⠼⠁⠃"""
    if n < 0:
        raise ValueError(f"페이지 번호는 0 이상이어야 한다: {n}")
    return NUM_SIGN + "".join(_DIGIT_CELLS[int(d)] for d in str(n))


def _alpha(idx: int) -> str:
    """걸침 순번 → 알파벳 점형. 1→a, 2→b … 26→z, 27→aa(두 글자).

    지침 1장2절2-2(3): 원본 한 쪽이 여러 점자 면에 걸치면 **두 번째 면부터**
    번호 **앞에** 로마자표 없이 알파벳을 순차로 적는다. 그래서 idx는 1부터다.
    실물 [예 1-7]에서 105면(0)·107면(2=b)·109면(4=d) — 면 순번이지 페이지행 순번이 아니다.
    """
    if idx <= 0:
        return ""
    out = ""
    while idx > 0:
        idx, r = divmod(idx - 1, 26)
        out = _ALPHA_CELLS[r] + out
    return out


def page_row(
    orig_page: int,
    cont_idx: int,
    braille_page: int,
    footer: str = "",
    opts: Options = DEFAULT,
) -> str:
    """페이지행 1줄(폭 = opts.cols)을 만든다.

    지침 1장2절2·1장3:
      · 원본 쪽 번호 — 왼쪽 정렬, 첫 칸. cont_idx≥1이면 번호 **앞에** 알파벳(로마자표 없이)
      · 꼬리말 — 가운데 정렬, 항목 사이 **두 칸 이상**
      · 점자 면 번호 — 오른쪽 정렬

    ★ 가운데 정렬은 **올림**이다: start = (cols - len(footer) + 1) // 2.
    지침 실물 4건([예 1-6]·[예 1-7]×3·[예 1-8])이 전부 이 값과 일치한다.
    내림으로 하면 [예 1-6](꼬리말 13칸)이 1칸 어긋난다.
    ⚠ 조판 가이드(2026-08-05) §4의 호출 예 두 개는 이 규칙과 다르다 — 예1은 33칸이라
    폭 자체가 틀렸고 예2는 시작 칸이 2 어긋난다. **지침 실물이 정본이다.**

    footer는 이미 점역된 점자 문자열이다(이 함수는 점역하지 않는다).
    자리에 안 들어가면 지침 1장3-4)에 따라 **뒤에서 잘라** 넣는다.
    """
    n = opts.cols
    left = ""
    if opts.show_orig_page:
        left = _alpha(cont_idx) + _number(orig_page)
    right = _number(braille_page) if opts.show_braille_page else ""

    if len(left) + len(right) > n:
        raise ValueError(f"쪽 번호만으로 {n}칸을 넘는다: 원본 {len(left)} + 점자 {len(right)}")

    cells = [SPACE] * n
    for i, c in enumerate(left):
        cells[i] = c
    for i, c in enumerate(right):
        cells[n - len(right) + i] = c

    if footer:
        # 항목 사이 두 칸 이상(지침 1장3-1). 좌우 여백을 뺀 자리에만 놓는다.
        lo = len(left) + 2 if left else 0
        hi = n - len(right) - 2 if right else n
        room = hi - lo
        f = footer[:room] if len(footer) > room else footer
        if f:
            if opts.footer_align == "right":
                start = hi - len(f)                # 오른쪽 끝(번호와 두 칸 띄운 자리)에 붙인다
            else:
                start = (n - len(f) + 1) // 2      # ★ 올림 — 지침 실물로 확정
            start = min(max(start, lo), hi - len(f))
            for i, c in enumerate(f):
                cells[start + i] = c

    return "".join(cells)


def page_change_line(orig_page: int, opts: Options = DEFAULT) -> str:
    """원본 페이지 변경선 1줄. 지침 2장2절2-3: 첫 칸부터 ⠤로 채우고 오른쪽 끝에 새 원본 쪽 번호.

    실물 [예 1-7]·[예 1-8]: `-----------------------------#gb` — 채움 29칸 + 번호 3칸 = 32.
    """
    n = opts.cols
    num = _number(orig_page) if opts.show_orig_page else ""
    if len(num) > n:
        raise ValueError(f"쪽 번호가 {n}칸을 넘는다: {len(num)}")
    return CHANGE_MARK * (n - len(num)) + num


_CELL_TO_ASCII = {chr(0x2800 + i): ch for i, ch in enumerate(_BRAILLE_ASCII)}
# 표준 ASCII `[ \ ] ^` 는 지침 표기에서 시프트형 `{ | } ~` 로 나온다.
_UNSHIFT = {"[": "{", "\\": "|", "]": "}", "^": "~"}


def to_brf_ascii(braille: str) -> str:
    """유니코드 점자 → BRF-ASCII(소문자). 파일에 쓰기 직전에 한 번 호출한다.

    공백 셀 ⠀는 **리터럴 스페이스**로 낸다(조판 가이드 §3: `⠼⠛⠀⠀…` → `#g  …`).
    ⚠ 코퍼스 `.brl` 관례의 백틱(``` ` ``` = ⠈ = 초성 ㄱ)과 혼동 금지 — 여기서 백틱을 공백으로
    쓰면 초성 ㄱ이 통째로 사라진다(2026-07-13 채점 붕괴 전례).
    줄바꿈은 보존한다. 못 푸는 셀은 `⟨XXXX⟩`로 남긴다(조용히 버리지 않는다).
    """
    out: list[str] = []
    for ch in braille:
        if ch == "\n":
            out.append("\n")
        elif ch == SPACE or ch == " ":
            out.append(" ")
        else:
            a = _CELL_TO_ASCII.get(ch)
            out.append(f"⟨{ord(ch):04X}⟩" if a is None else _UNSHIFT.get(a, a.lower()))
    return "".join(out)


# ── 문서 조립 (2026-08-05 추가) ──────────────────────────────────────────────
# 왜 여기 있나: ① 어느 면에 페이지행을 넣나 ② 걸침 순번(a·b·c)을 어떻게 세나
# ③ 표지를 어디까지 빼나 — 셋 다 **지침 규칙**이다. 호출자(BE·FE)가 각자 구현하면
# 점자 규정이 레포 밖으로 흩어진다. 이 레포를 만든 이유가 그걸 막으려는 것이다.
# (2026-08-05 사용자 결정으로 함수 3개 → 4개. 초판은 "typeset 엔진 공용화 안 함"이었다.)


def _wrap(line: str, cols: int) -> list[str]:
    """`cols`를 넘으면 **빈칸(어절) 자리에서** 자른다. 어절 하나가 폭보다 길면 그때만 강제 분리.

    종전에는 자리를 안 보고 `line[i:i + cols]`로 잘랐다. 그러면 한글 한 음절을 이루는
    점형이 두 줄로 갈린다 — 「점자 자료 제작 지침」 §2.1.1(2)가 원칙으로 삼는 **음절 단위
    줄바꿈**도, 예외로 허용하는 **어절 단위**도 아닌 값이다. 2026-09-08 대표 지적 ③에서
    사회학습지 예시 제목 '민주주의'가 `⠑⠟⠨⠍⠨` / `⠍⠺`로 갈려 나왔다.

    셀만 보고는 음절 경계를 알 수 없다(초성·종성 점형을 되짚어야 한다). 빈칸 경계는
    음절 경계의 부분집합이라 **음절을 쪼갤 일이 없고**, 정답 도서 실측도 어절이다
    (원장 C-83: 31칸 이상 줄이 gold dev 23.8%·val 24.9%). 지침 §2.1.1(2)의 예외절이
    "시험 문제지"를 집는데 우리 입력이 그것이다.
    """
    if not line:
        return [""]
    out: list[str] = []
    while len(line) > cols:
        cut = line.rfind(SPACE, 0, cols + 1)
        if cut <= 0 or not line[:cut].strip(SPACE):
            out.append(line[:cols])          # 어절 하나가 폭을 넘는다 — 그 자리에서만 강제 분리
            line = line[cols:]
        else:
            out.append(line[:cut].rstrip(SPACE))
            line = line[cut:].lstrip(SPACE)  # 자른 자리의 빈칸은 줄머리로 넘기지 않는다
    out.append(line)
    return out


def _has_page_row(braille_page: int, on: str) -> bool:
    if on == "none":
        return False
    if on == "odd":
        return braille_page % 2 == 1
    if on == "even":
        return braille_page % 2 == 0
    return True


def _renumber(sources: list, opts: Options) -> list:
    """`orig_page_start`가 있으면 원본 페이지 번호를 다시 매긴다.

    표지(`cover_pages`개)는 준 번호를 그대로 두고, 그 뒤 n번째 본문 원본 페이지에
    `orig_page_start + n`을 붙인다. None이면 아무것도 하지 않는다.
    """
    if opts.orig_page_start is None:
        return sources
    out = []
    for i, src in enumerate(sources):
        s = dict(src)
        if i >= opts.cover_pages:
            s["orig_page"] = opts.orig_page_start + (i - opts.cover_pages)
        out.append(s)
    return out


# 쪽바꿈 표식(2026-09-03, FE QA L-2). 편집 화면에서 Ctrl+Enter 로 끼워 넣는 **독립 요소**이고
# 본문은 이 한 줄뿐이다. 조판에서 만나면 요소를 버리고 그 자리에서 면을 끊는다.
# 원본 쪽 경계(orig_page)와 무관하게 쪽 한가운데에서도 올 수 있다.
PAGE_BREAK_TAG = "<!쪽바꿈>"
# flat 안에서 쪽바꿈 자리를 표시하는 내부 값. 점자 텍스트에는 못 나오는 문자를 쓴다.
_BREAK = "\x00brk"


def build_pages(
    sources: list,
    footer: str = "",
    start_braille_page: int = 1,
    opts: Options = DEFAULT,
    footers: dict | None = None,
) -> list:
    """원본 쪽별 통 문자열 → **완성된 점자 면 배열**. BRF 변환 직전 상태다.

    sources — `[{"orig_page": int, "blocks": [{"order": int, "text": str}]}]`
      · `text`는 ProcessPage가 낸 통 문자열(조판성 줄바꿈은 `\n`으로 들어 있다)
      · `blocks`는 `order`로 정렬해 이어 붙인다
    footer — 이미 점역된 꼬리말 점자(없으면 빈 문자열). 이 레포는 점역하지 않는다.
    footers — `{점자 면 번호: 꼬리말 점자}`. 그 면만 이 값을 쓰고, 없는 면은 `footer`를 쓴다.
      "이 면부터 끝까지 / 이 면만"은 **편집 시점의 뜻**이라 여기서 풀지 않는다.
      호출자(FE)가 범위를 해석해 면별 값으로 펼쳐 넘긴다(2026-09-01 결정 E).
    start_braille_page — 첫 면의 점자 면 번호. 표지 다음이 1이다(지침 1장2절2-3(1)).

    반환 — 면 배열. 각 면은 줄 배열이고 길이는 `opts.rows`다. 페이지행이 들어가는 면은
    마지막 줄이 페이지행이고 본문이 `rows-1`줄이다.

    ★ 표지 판정은 `sources`의 **순번**이다 — 앞에서 `cover_pages`개가 표지다.
      쪽 번호로 보지 않는다(번호가 1부터가 아니거나 다시 매기면 어긋난다).
    ★ 페이지행의 원본 번호 = **그 면 첫 줄이 속한 원본 쪽**.
      지침 1장2절2-2(4) "점자 한 페이지에 원본 페이지 변경선이 2개 이상 나올 때에는
      해당 페이지에서 가장 먼저 나오는 원본 페이지 번호"와 같은 값이다.
      ⚠ 원장 **C-10**으로 자문 예정 — 면이 원본 쪽 중간에서 시작하면서 변경선이 2개 이상일 때
      두 해석이 갈릴 여지가 있다.
    ★ 걸침 순번(cont_idx) = 그 원본 쪽이 **처음 나온 면부터 센 순번**(0부터).
      지침 [예 1-7] 실물이 105·107·109면에 없음·b·d를 붙이는 근거다 — 페이지행이 홀수 면에만
      찍혀 a(106면)·c(108면)가 건너뛰어진 것이지 순번이 건너뛴 게 아니다.
    """
    # JSON을 거쳐 오면 키가 문자열이다("2"). 세 구현이 같게 굴도록 여기서 정수로 맞춘다.
    fmap = {int(k): v for k, v in (footers or {}).items()}
    # 1) 원본 쪽 경계마다 변경선을 넣고 32칸으로 자른다. 줄마다 소속 원본 쪽을 들고 간다.
    sources = _renumber(sources, opts)
    # 원본 페이지 번호를 끄면 변경선은 ⠤만 남은 빈 줄이 된다 — 함께 끈다(결정 D).
    with_change = opts.show_change_line and opts.show_orig_page
    flat: list = []                       # (줄, 원본 쪽, 표지인가)
    for i, src in enumerate(sources):
        op = int(src["orig_page"])
        # ★ 표지 판정은 **순번**이다(2026-09-01 결정 C). 종전에는 `쪽 번호 <= cover_pages`로
        #   봤는데, 번호가 1부터 시작하지 않거나 orig_page_start로 다시 매기면 어긋난다.
        cover = i < opts.cover_pages
        if i > 0 and with_change:         # 첫 원본 쪽 앞에는 변경선을 두지 않는다
            flat.append((page_change_line(op, opts), op, cover))
        blocks = sorted(src.get("blocks") or [], key=lambda b: b.get("order", 0))
        # 쪽바꿈 표식에서 토막을 낸다. 표식이 없으면 종전과 똑같이 한 토막이다.
        segs: list = []
        cur: list = []
        for b in blocks:
            t = b.get("text", "")
            if t.strip() == PAGE_BREAK_TAG:
                segs.append("".join(cur))
                segs.append(None)
                cur = []
            else:
                cur.append(t)
        segs.append("".join(cur))
        for seg in segs:
            if seg is None:
                flat.append((_BREAK, op, cover))
                continue
            # 통 문자열의 **끝 개행은 마지막 줄을 끝내는 종결자**이지 빈 줄이 아니다.
            # AI `flatten_elements`가 `suffix = "\n" * (after + 1)`로 내보내는데 그 +1이
            # 종결자다(docstring: "본문 마지막 줄을 끝내는 개행"). split("\n")은 그걸 빈
            # 줄로 세어 **원본 쪽마다 유령 빈 줄이 하나씩** 생겼다 — 변경선 바로 위에 늘
            # 빈 줄이 찍혔고, 쪽마다 한 줄씩 밀렸다. AI `_assemble_pages`는 안 그런다.
            if not seg:
                continue      # 내용이 아예 없는 토막(쪽바꿈 표식이 잇달은 자리)은 줄을 안 만든다
            if seg.endswith("\n"):
                seg = seg[:-1]
            for logical in seg.split("\n"):
                for w in _wrap(logical, opts.cols):
                    flat.append((w, op, cover))

    # 2) 면으로 나눈다. 페이지행이 들어가는 면은 본문이 한 줄 줄어든다.
    #
    # ★ 면 첫 줄의 빈 줄은 **버리지 않는다** — 지침 2장2절2 2)(3)(도서 906행)·§2.4.4(3)
    #   (자료 942행) "본문 사이의 빈 줄이 점자 페이지 처음에 위치하더라도 빈 줄을 삭제하지
    #   않는다". 2025 개정 요약 3(도서 145행)이 종전 예외를 없앤 자리다. AI 쪽
    #   `layout_braille._paginate`는 이미 규정대로다(2026-08-08 대표 결정, gold 3.2%).
    #   다만 **문서 맨 앞** 빈 줄은 '본문 사이'가 아니라 버린다.
    pages: list = []
    first_seen: dict = {}                 # 원본 쪽 → 그 쪽이 처음 나온 면 번호(0-based)
    last = -1                             # 마지막 내용 줄 — 뒤쪽 빈 줄로 빈 면을 만들지 않는다
    for k, (ln, _o, _c) in enumerate(flat):
        if ln != _BREAK and ln.strip():
            last = k
    pos = 0
    while pos <= last and flat[pos][0] != _BREAK and not flat[pos][0].strip():
        pos += 1                          # 문서 맨 앞의 빈 줄만 버린다
    bpn = start_braille_page              # 표지 면은 점자 면 번호를 소비하지 않는다
    while pos <= last:
        while pos <= last and flat[pos][0] == _BREAK:
            pos += 1                      # 이미 이룬 쪽바꿈 표식만 버린다
        if pos > last:
            break
        idx = len(pages)
        bp = bpn
        head_page = flat[pos][1]
        # 표지 범위 안이면 페이지행을 생략한다(조판 옵션 §5).
        on_cover = flat[pos][2]
        has_row = _has_page_row(bp, opts.page_row_on) and not on_cover
        cap = opts.rows - (1 if has_row else 0)
        # 표식을 만나면 거기서 면을 끊는다 — 남은 칸은 아래에서 빈 줄로 채운다.
        end = pos
        while end < len(flat) and end - pos < cap and flat[end][0] != _BREAK:
            end += 1
        body = [ln for ln, _, _ in flat[pos:end]]
        pos = end
        if pos < len(flat) and flat[pos][0] == _BREAK:
            pos += 1                      # 표식 자체는 본문에 안 싣는다
        first_seen.setdefault(head_page, idx)
        body += [""] * (cap - len(body))
        if has_row:
            f = fmap.get(bp, footer)
            body.append(page_row(head_page, idx - first_seen[head_page], bp, f, opts))
        if not on_cover:
            bpn += 1                      # 지침 1장2 3)(1)·§2.1.5(1): 표지 다음 면이 1이다
        pages.append(body)
    return pages


# ── BE 조립 JSON 진입점 (2026-08-06) ────────────────────────────────────────
# BE가 편집 최종본을 모아 넘기는 형식. BE·FE가 조판 규칙을 다시 짜지 않게 여기서 받는다.
#
#   {"job_id": "...",
#    "options": {"include_page_number": bool, "page_row_on": "odd|every|even|none",
#                "cols": 32, "rows": 26,
#                "show_orig_page": bool, "show_braille_page": bool,
#                "cover_pages": 0, "orig_page_start": null,
#                "show_change_line": bool, "footer_align": "center|right"},
#    "footer_braille": "…",              # 문서 기본 꼬리말(이미 점역됨, 선택)
#    "footers_braille": {"3": "…"},      # 면별 꼬리말(점자 면 번호 → 꼬리말, 선택)
#    "start_braille_page": 1,            # 첫 면 번호(선택, 기본 1)
#    "pages": [{"orig_page_no": 1,
#               "elements": [{"id","type","heading_level","text"}, …]}]}
#
# ★ `elements` 배열 **순서가 읽기 순서**다. `order` 필드는 없다(BE가 정렬해 담는다).
# ★ `type`·`heading_level`은 **조판에 쓰지 않는다.** 들여쓰기·가운데 정렬·구조적 빈 줄은
#   AI가 이미 `text`에 넣어 보낸다(점자 공백 셀·`\n`). 여기서 또 넣으면 두 번 들어간다.
#   두 필드는 오류 지목·나중 확장을 위해 그대로 받아 두기만 한다.
def options_from_job(job: dict) -> Options:
    """BE 조립 JSON의 `options` → `Options`.

    2026-09-01 개편 전에는 `cols·rows·include_page_number` 셋만 읽었다. Options에 있어도
    Job에서 안 읽히면 죽은 값이라, 조판 설정 화면이 쓰는 항목을 전부 여기로 연결했다.

    page_row_on — `include_page_number`(켜기·끄기)와 `page_row_on`(어느 면)이 **같은 스위치**다.
      끄면 `none`, 켜면 `page_row_on`(기본 `odd`). 화면에서도 토글 하나로 합친다(결정 B).
    """
    o = job.get("options") or {}
    on = str(o.get("page_row_on") or "odd")
    if not bool(o.get("include_page_number", True)):
        on = "none"
    start = o.get("orig_page_start")
    return Options(
        cols=int(o.get("cols") or 32),
        rows=int(o.get("rows") or 26),
        show_orig_page=bool(o.get("show_orig_page", True)),
        show_braille_page=bool(o.get("show_braille_page", True)),
        page_row_on=on,
        cover_pages=int(o.get("cover_pages") or 0),
        orig_page_start=None if start in (None, "") else int(start),
        show_change_line=bool(o.get("show_change_line", True)),
        footer_align=str(o.get("footer_align") or "center"),
    )


def build_pages_from_job(job: dict) -> list:
    """BE 조립 JSON → 점자 면 배열. `build_pages`의 얇은 어댑터다."""
    sources = [
        {
            "orig_page": int(pg.get("orig_page_no", i + 1)),
            # 배열 순서가 읽기 순서다 — order를 만들어 붙여 그 순서를 유지한다.
            "blocks": [{"order": k, "text": el.get("text", "")}
                       for k, el in enumerate(pg.get("elements") or [])],
        }
        for i, pg in enumerate(job.get("pages") or [])
    ]
    # 면별 꼬리말 — 키가 문자열로 올 수 있어(JSON) 정수로 맞춘다.
    raw = job.get("footers_braille") or {}
    footers = {int(k): v for k, v in raw.items()} if raw else None
    return build_pages(
        sources,
        footer=job.get("footer_braille", "") or "",
        start_braille_page=int(job.get("start_braille_page") or 1),
        opts=options_from_job(job),
        footers=footers,
    )


def build_brf(job: dict) -> str:
    """BE 조립 JSON → **.brf 파일 내용**(BRF Braille ASCII, 줄바꿈 `\n`).

    BE는 이 문자열을 그대로 파일로 쓰면 된다. 점역은 하지 않는다 — 이미 점역된
    통 문자열을 조판만 한다.
    """
    return "\n".join(to_brf_ascii(line)
                      for page in build_pages_from_job(job)
                      for line in page)


def build_brf_file(job: dict) -> bytes:
    """BE 조립 JSON → **.brf 파일 바이트**(현장 꼴: 줄 끝 `\r\n`, 쪽마다 끝에 `\x0c`, 소문자 BRF ASCII).

    면 나누기는 `build_pages_from_job` 과 같고, 바이트 꼴만 `semojum_braille.brf.serialize_brf` 를 따른다.
    """
    o = options_from_job(job)
    return serialize_brf(build_pages_from_job(job), rows=o.rows, cols=o.cols)
