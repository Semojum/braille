"""번호와 꼬리말을 따로 켜고 끄기 — 기획서 §5 P0 「페이지 번호 출력」·「꼬리말 출력」.

둘 다 다섯 갈래(모든 페이지 / 홀수 페이지 / 없음 / 사용자 지정(모든 페이지) / 사용자 지정(홀수 단위))
이고 서로 독립이다. 종전 엔진은 꼬리말이 페이지행 안에 들어가 **번호가 없는 면에는 꼬리말도
없었다**. FE 「데스크톱 편집기 연동을 위한 백엔드 수정 목록」(2026-10-20) B-06 의 둘째·셋째 줄이다.

★ 새 옵션을 하나도 안 주면 종전과 똑같아야 한다 — 그것이 이 묶음의 첫 시험이다.
"""
import pytest

from semojum_braille import assist

FOOT = "⠋⠕"


def job(on="every", npages=6, **opts):
    return {
        "sources": [{"orig_page": i + 1, "blocks": [{"order": 0, "braille": "⠁"}]} for i in range(npages)],
        "footer": FOOT,
        "opts": {"rows": 3, "page_row_pages": on, **opts},
    }


def rows(j):
    """면마다 (번호 있나, 꼬리말 있나). 페이지행은 면의 마지막 줄이고 32칸을 채운다."""
    out = []
    for p in assist.build_pages_from_job(j):
        line = p[-1] if p else ""
        is_row = len(line) == 32
        out.append((is_row and line.startswith("⠼"), is_row and FOOT in line))
    return out


# ── 1. 기본값은 종전 그대로 ──────────────────────────────────────────────

def test_새_옵션을_안_주면_꼬리말은_번호와_같은_면에만():
    assert rows(job("odd"))[:4] == [(True, True), (False, False), (True, True), (False, False)]
    assert all(r == (True, True) for r in rows(job("every")))
    assert all(r == (False, False) for r in rows(job("none")))


def test_footer_pages_가_null_이면_page_row_pages_를_따른다():
    assert rows(job("odd", footer_pages=None)) == rows(job("odd"))


# ── 2. 꼬리말 면을 번호 면과 따로 고른다 ────────────────────────────────

def test_번호는_홀수_면에_꼬리말은_모든_면에():
    r = rows(job("odd", footer_pages="every"))[:4]
    assert r == [(True, True), (False, True), (True, True), (False, True)]


def test_번호_없이_꼬리말만_있는_면은_꼬리말만_적힌_페이지행이_된다():
    pages = assist.build_pages_from_job(job("none", footer_pages="every"))
    line = pages[0][-1]
    assert len(line) == 32 and "⠼" not in line and FOOT in line


def test_번호도_꼬리말도_없는_면은_페이지행_줄_자체가_없어_본문이_한_줄_더_들어간다():
    none_both = assist.build_pages_from_job(job("none", footer_pages="none"))
    with_row = assist.build_pages_from_job(job("every", footer_pages="every"))
    assert len(none_both) < len(with_row)          # 본문 줄이 늘어 면 수가 준다
    assert all(len(p) == 3 for p in none_both)     # rows=3 을 본문이 다 쓴다


# ── 3. 사용자 지정 범위 ──────────────────────────────────────────────────

def test_번호_범위_밖의_면에는_번호가_없다():
    r = rows(job("every", number_ranges=[[2, 3]]))
    assert [x[0] for x in r][:4] == [False, True, True, False]


def test_끝을_null_로_두면_문서_끝까지다():
    r = rows(job("every", number_ranges=[[3, None]]))
    assert [x[0] for x in r][:4] == [False, False, True, True]


def test_범위와_홀짝을_같이_걸면_둘_다_만족하는_면만():
    r = rows(job("odd", number_ranges=[[3, None]]))
    assert [x[0] for x in r][:5] == [False, False, True, False, True]


def test_꼬리말_범위는_번호_범위와_따로_건다():
    r = rows(job("every", number_ranges=[[1, 2]], footer_ranges=[[3, None]]))
    assert r[:4] == [(True, False), (True, False), (False, True), (False, True)]


# ── 4. 잘못된 값은 BAD_FIELD ────────────────────────────────────────────

@pytest.mark.parametrize("opts", [
    {"footer_pages": "홀수"},
    {"number_ranges": []},
    {"number_ranges": [[0, 3]]},            # 면 번호는 1부터다
    {"number_ranges": [[5, 3]]},            # 끝이 시작보다 앞
    {"number_ranges": [[1]]},               # 두 값이 아니다
    {"number_ranges": [[1, "셋"]]},
    {"number_ranges": [[True, 3]]},         # 참거짓은 정수가 아니다
    {"footer_ranges": {"1": 3}},
])
def test_잘못된_범위_값은_거절한다(opts):
    with pytest.raises(ValueError):
        assist.build_pages_from_job(job("every", **opts))


def test_정수_꼴_문자열_면_번호는_받는다():
    """JSON 을 거쳐 오면 숫자가 문자열일 수 있다(`footers` 키와 같은 사정)."""
    assert rows(job("every", number_ranges=[["2", "3"]])) == rows(job("every", number_ranges=[[2, 3]]))


# ── 5. 꼬리말이 비면 페이지행 줄을 넣지 않는다 (#92) ──────────────────────
#
# 3.4.30 에서 번호와 꼬리말을 가르면서 생긴 결함이다. 꼬리말 면이 켜져 있어도 **적을 글이 없으면**
# 32칸이 전부 공백인 페이지행 줄이 남아 본문 한 줄을 먹었다. 종전에는 꼬리말이 켜지면 번호도
# 켜져서(한 스위치였다) 이 꼴이 안 나왔다. 위 네 묶음이 전부 꼬리말 글을 깔고 돌아 못 잡았다.
# 「번호 출력 = 없음 · 사용자 지정」 + 꼬리말 미기입은 가장 흔한 조합이다.

BLANK_ROW = "⠀" * 32


def pages(footer="", **opts):
    src = [{"orig_page": i + 1, "blocks": [{"order": 0, "braille": "⠁"}]} for i in range(6)]
    o = {"rows": 3, "page_row_pages": "every"}
    o.update(opts)
    return assist.build_pages_from_job({"sources": src, "footer": footer, "opts": o})


def test_꼬리말이_비고_번호도_없는_면엔_공백_페이지행이_남지_않는다():
    """#92 재현 조건 그대로. 면 1·2 는 번호 범위 밖이고 꼬리말도 비어 있다."""
    ps = pages(footer="", number_ranges=[[3, None]])
    assert all(BLANK_ROW not in p for p in ps)
    assert all(len(p) == 3 for p in ps)              # 본문이 세 줄을 다 쓴다


def test_꼬리말이_비면_본문_줄을_안_먹는다():
    """번호를 끄고 꼬리말만 켠 자리. 꼬리말을 채우면 페이지행이 생겨 면 수가 는다 — 그 차이가 먹히던 줄이다."""
    off = dict(page_row_pages="none", footer_pages="every")
    assert len(pages(footer="", **off)) < len(pages(footer=FOOT, **off))


def test_번호가_있으면_꼬리말이_비어도_페이지행은_남는다():
    """번호를 적어야 하는 면은 꼬리말이 비어도 줄이 있어야 한다 — 종전 동작이다."""
    ps = pages(footer="", page_row_pages="every")
    assert all(len(p[-1]) == 32 and p[-1].startswith("⠼") for p in ps)


def test_꽂은_꼬리말을_빈_값으로_두면_그_쪽부터_페이지행이_사라진다():
    """빈 문자열을 꽂는 것이 '그 쪽부터 숨기기' 관용이다(v3.4.27). 번호가 없으면 줄째 사라져야 한다."""
    src = [{"orig_page": i + 1, "blocks": [{"order": 0, "braille": "⠁"}]} for i in range(6)]
    job = {"sources": src, "footer": FOOT, "footers_by_orig_page": {3: ""},
           "opts": {"rows": 3, "page_row_pages": "none", "footer_pages": "every"}}
    ps = assist.build_pages_from_job(job)
    assert any(FOOT in p[-1] for p in ps)            # 꽂기 전 면엔 꼬리말이 있고
    assert all(BLANK_ROW not in p for p in ps)       # 꽂은 뒤 면엔 공백 줄이 안 남는다


def test_장바꿈_빈_면도_같은_규칙이다():
    """`blank()` 도 같은 자리를 지난다 — 빈 면에 공백 페이지행만 남으면 안 된다."""
    src = [{"orig_page": 1, "blocks": [{"order": 0, "braille": "⠁"},
                                       {"order": 1, "braille": assist.CHAPTER_TAG},
                                       {"order": 2, "braille": "⠃"}]}]
    job = {"sources": src, "footer": "", "opts": {"rows": 3, "page_row_pages": "none",
                                                  "footer_pages": "every", "pad_to_even": True}}
    assert all(BLANK_ROW not in p for p in assist.build_pages_from_job(job))
