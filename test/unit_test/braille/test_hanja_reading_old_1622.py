"""중세 국어(훈민정음 언해 꼴)의 한자 뒤 독음 · 첫가끝 음절에 붙은 단독 자모(#1622).

규정 예문 아홉 줄은 `test_regulation_sentences.py` 가 본다(pairs.json pass). 여기서는 규칙을 지어낸 글로 본다 — 예문을 외운
것이 아니라 처음 보는 글에도 같아야 한다. 기대 점형 ⠸⠁ · ⠸⠄ · ⠸⠕ · ⠐⠶ · ⠐⠢⠶ 은 한글 제23항(재추출 1165행) · 제26항(1290행) ·
제19항 [붙임](999행) · 제20항(1018행) 에서 왔다.
"""
from semojum_braille.encoder.translator import dropped_old_jamo, translate_tagged_text as tr


def test_첫가끝_음절_뒤_단독_자음은_받침_꼴로_적는다():
    assert tr("ᄆᆞᆯㄱ") == tr("ᄆᆞᆯ") + "⠸⠁"
    assert tr("ᄀᆞᄅᆞㅅ 말") == tr("ᄀᆞᄅᆞ") + "⠸⠄⠀" + tr("말")


def test_첫가끝_음절_뒤_딴이는_따로_적는다():
    assert tr("ᄇᆞᄅᆞㅣ") == tr("ᄇᆞᄅᆞ") + "⠸⠕"


def test_한자_뒤_첫가끝_독음은_한자를_빼고_한_번만_적는다():
    reading = tr("ᄍᆞᆼ")
    assert reading.endswith("⠶")
    # 뺀 한자의 독음 = 동국정운식 한자음 → 음가 없는 받침 ㅇ 은 ⠐⠶
    assert tr("가字ᄍᆞᆼ나") == tr("가") + reading[:-1] + "⠐⠶" + tr("나")


def test_뒤가_독음이_아니면_한자_독음을_그대로_둔다():
    assert tr("字ᄒᆞᆫ") == tr("字") + tr("ᄒᆞᆫ")


def test_받침_없는_완성형_뒤_옛_받침은_한_음절이다():
    assert tr("두ᇢ") == "⠊⠍⠐⠢⠶"
    assert not dropped_old_jamo("두ᇢ")
