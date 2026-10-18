/**
 * braille-assist — 점자 조판 공용 함수 3개 (TypeScript).
 *
 * python/java 구현과 출력이 같아야 한다. 규칙이 바뀌면 세 구현과 vectors.json을 한 PR로 갱신한다.
 * 이 모듈은 한글을 점역하지 않는다 — 꼬리말은 이미 점역된 점자를 받아 배치만 한다.
 *
 * 근거: 「점자 도서 제작 지침」 1장 2절 2 · 1장 3 · 2장 2절 2-3.
 */

export const SPACE = '⠀'; // 공백 셀 ⠀
const NUM_SIGN = '⠼'; // 수표 ⠼
const CHANGE_MARK = '⠤'; // 변경선 채움 ⠤
/** 줄바꿈 두 갈래(2026-10-10 대표 확정, 기본 음절). 뜻은 `wrap` 에 적었다. */
export const WRAP_MODES = ['syllable', 'word'] as const;
export type WrapMode = typeof WRAP_MODES[number];
const TN_MARK = '⠠⠄'; // 점역자 주 표(두 칸). 강제로 자를 때 가르지 않는다

// 숫자·알파벳은 같은 점형(1=a=⠁ … 0=j=⠚). 수표가 앞에 오면 숫자로 읽는다.
const DIGIT_CELLS = '⠚⠁⠃⠉⠙⠑⠋⠛⠓⠊';
const ALPHA_CELLS = '⠁⠃⠉⠙⠑⠋⠛⠓⠊⠚⠅⠇⠍⠝⠕⠏⠟⠗⠎⠞⠥⠧⠺⠭⠽⠵';

// BRF Braille ASCII 64셀 표준표(유니코드 오프셋 0..63 순).
const BRAILLE_ASCII =
  ' A1B\'K2L@CIF/MSP' +
  '"E3H9O6R^DJG>NTQ' +
  ',*5<-U8V.%[$+X!&' +
  ';:4\\0Z7(_?W]#Y)=';

export interface Options {
  cols: number;
  rows: number;
  showOrigPage: boolean;
  showBraillePage: boolean;
  /**
   * 페이지행을 넣는 면. **기본은 홀수 면만**(2026-08-06 변경).
   * 지침 1장2절2-1이 홀수 면만이라 하고, 점자 도서 82권 실측에서도 페이지행을 가진 면이
   * 100% 홀수였다(원장 C-11 — 규정=관행 확정). 고정이 아니라 기본값이다.
   */
  pageRowOn: 'every' | 'odd' | 'even' | 'none';
  /** 앞에서 이만큼의 **원본 페이지**가 표지. 점자 면 수가 아니다(2026-09-01 결정 C). */
  coverPages: number;
  /** 표지 다음 첫 본문 원본 페이지에 붙일 번호. null이면 준 값 그대로. */
  origPageStart: number | null;
  /** 원본 페이지 변경선을 넣을지. showOrigPage가 꺼지면 함께 꺼진다(결정 D). */
  showChangeLine: boolean;
  /** 꼬리말 정렬. right는 점자 면 번호에서 두 칸 띄운 자리가 오른쪽 끝, left는 원본 번호에서 두 칸 띄운 자리가 시작이다. */
  footerAlign: 'center' | 'right' | 'left';
  /**
   * 원본 쪽에 꽂은 꼬리말(`footersByOrigPage`)을 쓰는 범위(2026-10-19 대표 결정 ②). carry(기본, 이어가기)는 꽂은 쪽이
   * 처음 나오는 면부터 다음 꽂은 쪽 앞 면까지, page(그 쪽만)는 꽂은 쪽이 나오는 면에만. 면 번호 키 footers 와는 상관없다.
   */
  footerMode: 'carry' | 'page';
  /** 32칸을 넘는 줄을 접는 갈래. 블록에 breaks 가 없으면 syllable 이어도 word 로 접는다. */
  wrap: WrapMode;
  /** 홀수 면에서 끝나면 빈 면 하나를 더한다(V4 가이드). 더한 면도 같은 페이지행 규칙을 따른다. */
  padToEven: boolean;
}

/** 1차 PoC 고정값 (조판 가이드 §5). */
export const DEFAULT_OPTIONS: Options = {
  cols: 32,
  rows: 26,
  showOrigPage: true,
  showBraillePage: true,
  pageRowOn: 'odd',
  coverPages: 0,
  origPageStart: null,
  showChangeLine: true,
  footerAlign: 'center',
  footerMode: 'carry',
  wrap: 'syllable',
  padToEven: false,
};

function resolve(opts?: Partial<Options>): Options {
  const o = { ...DEFAULT_OPTIONS, ...(opts ?? {}) };
  if (o.cols < 8) throw new Error(`cols는 8 이상이어야 한다: ${o.cols}`);
  if (!['every', 'odd', 'even', 'none'].includes(o.pageRowOn))
    throw new Error(`pageRowOn은 odd|every|even|none: ${o.pageRowOn}`);
  if (!WRAP_MODES.includes(o.wrap)) throw new Error(`wrap은 syllable|word: ${o.wrap}`);
  if (o.footerMode !== 'carry' && o.footerMode !== 'page') throw new Error(`footerMode는 carry|page: ${o.footerMode}`);
  return o;
}

/** 정수 → 수표 + 숫자 점형. 예: 12 → ⠼⠁⠃ */
function num(n: number): string {
  if (!Number.isInteger(n) || n < 0) throw new Error(`페이지 번호는 0 이상 정수: ${n}`);
  let s = NUM_SIGN;
  for (const d of String(n)) s += DIGIT_CELLS[Number(d)];
  return s;
}

/**
 * 걸침 순번 → 알파벳 점형. 1→a, 2→b … 26→z, 27→aa.
 * 지침 1장2절2-2(3): 두 번째 점자 면부터 번호 **앞에** 로마자표 없이 알파벳.
 * 실물 [예 1-7]에서 105면(0)·107면(2=b)·109면(4=d) — 면 순번이지 페이지행 순번이 아니다.
 */
function alpha(idx: number): string {
  if (idx <= 0) return '';
  let out = '';
  let i = idx;
  while (i > 0) {
    const r = (i - 1) % 26;
    i = Math.floor((i - 1) / 26);
    out = ALPHA_CELLS[r] + out;
  }
  return out;
}

/**
 * 페이지행 1줄(폭 = opts.cols).
 *
 * 지침 1장2절2·1장3: 원본 쪽 번호 왼쪽 정렬 첫 칸(걸침이면 번호 앞에 알파벳) ·
 * 꼬리말 가운데 정렬(항목 사이 두 칸 이상) · 점자 면 번호 오른쪽 정렬.
 *
 * ★ 가운데 정렬은 **올림**: start = (cols - footer.length + 1) >> 1.
 * 지침 실물 4건이 전부 이 값과 일치한다. 내림이면 [예 1-6](꼬리말 13칸)이 1칸 어긋난다.
 * ⚠ 조판 가이드 §4의 호출 예 두 개는 이 규칙과 다르다(예1은 33칸, 예2는 시작 2 어긋남) —
 * **지침 실물이 정본이다.**
 */
export function pageRow(
  origPage: number,
  contIdx: number,
  braillePage: number,
  footer = '',
  opts?: Partial<Options>,
): string {
  const o = resolve(opts);
  const n = o.cols;
  const left = o.showOrigPage ? alpha(contIdx) + num(origPage) : '';
  const right = o.showBraillePage ? num(braillePage) : '';
  if (left.length + right.length > n)
    throw new Error(`쪽 번호만으로 ${n}칸을 넘는다: ${left.length} + ${right.length}`);

  const cells: string[] = new Array(n).fill(SPACE);
  for (let i = 0; i < left.length; i++) cells[i] = left[i];
  for (let i = 0; i < right.length; i++) cells[n - right.length + i] = right[i];

  if (footer) {
    // 항목 사이 두 칸 이상(지침 1장3-1). 자리에 안 들어가면 뒤에서 자른다(1장3-4).
    const lo = left ? left.length + 2 : 0;
    const hi = right ? n - right.length - 2 : n;
    const f = footer.length > hi - lo ? footer.slice(0, hi - lo) : footer;
    if (f) {
      // 우측 정렬이면 번호와 두 칸 띄운 자리가 오른쪽 끝이다.
      let start = o.footerAlign === 'right'
        ? hi - f.length
        : o.footerAlign === 'left'
          ? lo
          : (n - f.length + 1) >> 1;        // ★ 올림 — 지침 실물로 확정
      start = Math.min(Math.max(start, lo), hi - f.length);
      for (let i = 0; i < f.length; i++) cells[start + i] = f[i];
    }
  }
  return cells.join('');
}

/**
 * 원본 페이지 변경선 1줄. 지침 2장2절2-3: 첫 칸부터 ⠤로 채우고 오른쪽 끝에 새 원본 쪽 번호.
 * 실물 [예 1-7]: 채움 29칸 + `#gb` 3칸 = 32.
 */
export function pageChangeLine(origPage: number, opts?: Partial<Options>): string {
  const o = resolve(opts);
  const s = o.showOrigPage ? num(origPage) : '';
  if (s.length > o.cols) throw new Error(`쪽 번호가 ${o.cols}칸을 넘는다: ${s.length}`);
  return CHANGE_MARK.repeat(o.cols - s.length) + s;
}

const CELL_TO_ASCII = new Map<string, string>();
for (let i = 0; i < 64; i++) CELL_TO_ASCII.set(String.fromCharCode(0x2800 + i), BRAILLE_ASCII[i]);
// 표준 ASCII `[ \ ] ^` 는 지침 표기에서 시프트형 `{ | } ~` 로 나온다.
const UNSHIFT: Record<string, string> = { '[': '{', '\\': '|', ']': '}', '^': '~' };

/**
 * 유니코드 점자 → BRF-ASCII(소문자). 파일에 쓰기 직전 한 번 호출한다.
 *
 * 공백 셀 ⠀는 **리터럴 스페이스**로 낸다(가이드 §3: `⠼⠛⠀⠀…` → `#g  …`).
 * ⚠ 코퍼스 .brl 관례의 백틱(` = ⠈ = 초성 ㄱ)과 혼동 금지 — 백틱을 공백으로 쓰면 초성 ㄱ이 사라진다.
 * 줄바꿈은 보존하고, 못 푸는 셀은 `⟨XXXX⟩`로 남긴다(조용히 버리지 않는다).
 */
export function toBrfAscii(braille: string): string {
  let out = '';
  for (const ch of braille) {
    if (ch === '\n') out += '\n';
    else if (ch === SPACE || ch === ' ') out += ' ';
    else {
      const a = CELL_TO_ASCII.get(ch);
      out += a === undefined
        ? `⟨${ch.charCodeAt(0).toString(16).toUpperCase().padStart(4, '0')}⟩`
        : (UNSHIFT[a] ?? a.toLowerCase());
    }
  }
  return out;
}

// ── 문서 조립 (2026-08-05 추가) ──────────────────────────────────────────────
// 왜 여기 있나: ① 어느 면에 페이지행을 넣나 ② 걸침 순번(a·b·c)을 어떻게 세나
// ③ 표지를 어디까지 빼나 — 셋 다 지침 규칙이다. 호출자가 각자 구현하면 점자 규정이
// 레포 밖으로 흩어진다. 이 레포를 만든 이유가 그걸 막으려는 것이다.

/** breaks — 응답 breaks 그대로(그 블록 text 기준, 선택). heading_level 1 — 접힌 줄을 가운데에. */
export interface Block { order: number; text: string; breaks?: number[] | null; heading_level?: number; align?: string }
export interface Source { orig_page: number; blocks: Block[] }

/** cols를 넘으면 **빈칸(어절) 자리에서** 자른다. 어절 하나가 폭보다 길면 그때만 강제 분리.
 *  종전의 무조건 자르기는 한글 한 음절의 점형을 두 줄로 갈랐다 — 지침 §2.1.1(2)의
 *  음절 원칙도 어절 예외도 아니다(2026-09-08 대표 지적 ③). 자세한 근거는 python core._wrap. */
// 해설 정답 목록(`01 ①  02 ③`)은 쌍 안(번호와 답 사이)에서 접지 않는다(#48). 근거와 판정은 python assist._pair_gaps.
const CIRCLED = ['⠼⠂', '⠼⠆', '⠼⠒', '⠼⠲', '⠼⠢'];        // ①~⑤
const isNum = (t: string) => t.length > 1 && t[0] === '⠼' && [...t.slice(1)].every(c => DIGIT_CELLS.includes(c));

function pairGaps(line: string): Set<number> {
  const toks: [number, number][] = [];
  for (const m of line.matchAll(/[^⠀]+/g)) toks.push([m.index!, m.index! + m[0].length]);
  const tok = ([a, b]: [number, number]) => line.slice(a, b);
  for (let s = toks.length % 2; s < toks.length - 3; s += 2) {
    const tail = toks.slice(s);
    const nums = tail.filter((_, k) => k % 2 === 0);
    const anss = tail.filter((_, k) => k % 2 === 1);
    if (!nums.every(t => isNum(tok(t)))) continue;
    if (!anss.every(t => isNum(tok(t)) || CIRCLED.includes(tok(t)))) continue;
    if (!anss.some(t => CIRCLED.includes(tok(t)))) continue;
    const nos = nums.map(t => parseInt([...tok(t).slice(1)].map(c => DIGIT_CELLS.indexOf(c)).join(''), 10));
    if (nos.some((n, k) => k > 0 && n !== nos[k - 1] + 1)) continue;
    const gaps = new Set<number>();
    nums.forEach(([, e], k) => { for (let p = e; p < anss[k][0]; p++) gaps.add(p); });
    return gaps;
  }
  return new Set();
}

function wordWrap(line: string, cols: number): string[] {
  if (!line) return [''];
  const out: string[] = [];
  const trimEnd = (s: string) => s.replace(/⠀+$/, '');
  const trimStart = (s: string) => s.replace(/^⠀+/, '');
  while (line.length > cols) {
    const gaps = pairGaps(line);
    let cut = -1;
    for (let k = cols; k >= 0; k--) if (line[k] === SPACE && !gaps.has(k)) { cut = k; break; }
    if (cut <= 0 || trimEnd(trimStart(line.slice(0, cut))) === '') {
      out.push(line.slice(0, cols));
      line = line.slice(cols);
    } else {
      out.push(trimEnd(line.slice(0, cut)));
      line = trimStart(line.slice(cut));
    }
  }
  out.push(line);
  return out;
}

/**
 * 논리 줄 하나를 cols 칸 줄들로 접는다. 줄바꿈 두 갈래(2026-10-10 대표 확정, 기본 음절). 근거는 python `wrap`.
 * - syllable: breaks(그 셀 앞에서 끊어도 되는 자리, 이 줄 기준) 가운데 cols 칸 안에서 가장 먼 자리에서 끊는다.
 *   없으면 cols 칸째에서 강제로 자르되 점역자 주 표 ⠠⠄ 는 가르지 않는다. 이어지는 줄 머리 빈칸은 버린다.
 *   breaks 가 비면 word 로 접는다(설계 §6-1).
 * - word: 빈칸(어절) 자리에서 자른다.
 * - center: 1단계 제목. cols 를 넘어 접힌 줄만 조각마다 가운데에 놓는다.
 */
export function wrap(line: string, cols = 32, mode: WrapMode = 'syllable',
                     breaks?: number[] | null, center = false): string[] {
  if (!WRAP_MODES.includes(mode)) throw new Error(`wrap은 syllable|word: ${mode}`);
  let out: string[];
  if (mode === 'word' || !breaks || breaks.length === 0) {
    out = wordWrap(line, cols);
  } else {
    out = [];
    let start = 0;
    while (line.length - start > cols) {
      const ok = breaks.filter((b) => start < b && b <= start + cols);
      let cut = ok.length ? Math.max(...ok) : start + cols;
      if (!ok.length && line.slice(cut - 1, cut + 1) === TN_MARK) cut -= 1;
      const piece = line.slice(start, cut);
      out.push(piece.replace(/[⠀ ]+$/u, '') || piece);   // 줄 끝 빈칸도 걷는다(어절 갈래와 같다, #72 E)
      start = cut;
      while (start < line.length && (line[start] === SPACE || line[start] === ' ')) start++;
    }
    if (start < line.length || out.length === 0) out.push(line.slice(start));
  }
  if (center && line.length > cols) out = out.map((s) => SPACE.repeat(Math.floor((cols - s.length) / 2)) + s);
  return out;
}

/** 쪽바꿈 표식 사이 한 토막의 블록들을 이어 논리 줄로 나누고 o.wrap 갈래로 접는다. 근거는 python `_fold_blocks`.
 *  반환은 [줄, 블록 align] 이다. 정렬은 면을 나눈 뒤(점자 면 번호를 채운 뒤) 놓는다. */
function foldBlocks(blocks: Block[], o: Options): Array<[string, string]> {
  // 블록은 서로 다른 요소다. 끝 개행 없이 이으면 다음 블록 첫 줄과 한 줄로 붙는다(#40 · braille-assist#16,
  // 웹에서 저장한 쪽의 BE 다운로드). 빈 블록은 줄을 더하지 않고, 아래에서 토막 끝 개행을 종결자로 떼므로
  // 마지막 블록은 종전과 같다. breaks 는 그 블록 글 기준이라 끝에 붙인 개행이 오프셋을 안 흔든다.
  const texts = blocks.map((b) => {
    const t = b.text ?? '';
    return t === '' || t.endsWith('\n') ? t : `${t}\n`;
  });
  let seg = texts.join('');
  if (seg === '') return [];   // 내용이 없는 토막(쪽바꿈 표식이 잇달은 자리)은 줄을 안 만든다
  const starts: number[] = [];
  const centers: boolean[] = [];
  const aligns: string[] = [];
  const gbreaks: number[] = [];
  let acc = 0;
  blocks.forEach((b, i) => {
    starts.push(acc);
    centers.push((b.heading_level ?? 0) === 1);
    const al = b.align ?? '';
    if (al && !ALIGNS.includes(al)) throw new Error(`align은 left|center|right: ${al}`);
    aligns.push(al);
    for (const x of b.breaks ?? []) gbreaks.push(acc + x);
    acc += texts[i].length;
  });
  // 통 문자열의 끝 개행은 마지막 줄을 끝내는 종결자이지 빈 줄이 아니다.
  // split('\n')이 그걸 빈 줄로 세어 원본 쪽마다 유령 빈 줄이 하나씩 생겼다.
  if (seg.endsWith('\n')) seg = seg.slice(0, -1);
  const out: Array<[string, string]> = [];
  let base = 0;
  for (const logical of seg.split('\n')) {
    let k = 0;
    while (k + 1 < starts.length && starts[k + 1] <= base) k++;
    const lb = gbreaks.filter((g) => base < g && g < base + logical.length).map((g) => g - base);
    for (const w of wrap(logical, o.cols, o.wrap, lb, centers[k])) out.push([w, aligns[k]]);
    base += logical.length + 1;
  }
  return out;
}

function hasPageRow(braillePage: number, on: string): boolean {
  if (on === 'none') return false;
  if (on === 'odd') return braillePage % 2 === 1;
  if (on === 'even') return braillePage % 2 === 0;
  return true;
}

/**
 * 원본 쪽별 통 문자열 → 완성된 점자 면 배열. BRF 변환 직전 상태다.
 *
 * ★ 페이지행의 원본 번호 = **그 면 첫 줄이 속한 원본 쪽**(지침 1장2절2-2(4)).
 * ★ 걸침 순번 = 그 원본 쪽이 **처음 나온 면부터 센 순번**(0부터).
 *   지침 [예 1-7]이 105·107·109면에 없음·b·d를 붙이는 근거 — 페이지행이 홀수 면에만
 *   찍혀 a(106)·c(108)가 안 보이는 것이지 순번이 건너뛴 게 아니다.
 */
/**
 * 쪽바꿈 표식(2026-09-03, FE QA L-2). 편집 화면에서 Ctrl+Enter 로 끼워 넣는 **독립 요소**이고
 * 본문은 이 한 줄뿐이다. 조판에서 만나면 요소를 버리고 그 자리에서 면을 끊는다.
 * 원본 쪽 경계(orig_page)와 무관하게 쪽 한가운데에서도 올 수 있다.
 */
export const PAGE_BREAK_TAG = '<!쪽바꿈>';
/** flat 안에서 쪽바꿈 자리를 표시하는 내부 값. 점자 텍스트에는 못 나오는 문자를 쓴다. */
const BREAK = '\u0000brk';

// ── 조판 태그(V4 점자 태깅 목록표, #66). 근거와 뜻은 python assist 의 같은 이름 ──────────────────
/** 장바꿈: 그 자리에서 면을 끊고 다음 내용은 홀수 면에서 시작한다(도서지침 용어 ⑫ 재추출 4534~4537행). */
export const CHAPTER_TAG = '<!장바꿈>';
const CHAPTER = '\u0000chp';
const MARKS = [BREAK, CHAPTER];
/** 줄을 먹는 태그 → [머리 셀, 채움 셀, 끝 셀]. 그 태그 하나뿐인 블록을 cols 폭 한 줄로 펼친다. */
export const RULE_TAGS: Record<string, [string, string, string]> = {
  '<!상단줄>': ['', '⠉', ''], '<!중단줄>': ['', '⠒', ''], '<!하단줄>': ['', '⠤', ''],
  '<!상단굵은줄>': ['', '⠛', ''], '<!하단굵은줄>': ['', '⠶', ''],
  '<!표시작>': ['⠖', '⠒', '⠲'], '<!표중앙>': ['⠗', '⠒', '⠺'], '<!표끝>': ['⠓', '⠒', '⠚'],
  '<!표구분선>': ['', '⠐', ''],
  '<!표지시작>': ['⠿', '⠛', '⠿'], '<!표지세로>': ['⠿', SPACE, '⠿'], '<!표지끝>': ['⠿', '⠶', '⠿'],
};
/** 쪽 번호 자리표시. 묵자 쪽 번호 = 그 줄의 원본 쪽, 점자 면 번호 = 그 줄이 놓인 면(표지 면은 비움). */
export const ORIG_PAGE_TAG = '<!묵자쪽번호>';
export const BRAILLE_PAGE_TAG = '<!점자면번호>';
export const ALIGNS = ['left', 'center', 'right'];

export function ruleLine(tag: string, cols = 32): string {
  const [a, f, z] = RULE_TAGS[tag];
  return a + f.repeat(cols - a.length - z.length) + z;
}

const stripCells = (s: string) => s.replace(/^[⠀ ]+|[⠀ ]+$/g, '');

function alignLine(line: string, cols: number, how: string): string {
  if (!how) return line;
  const s = stripCells(line);
  if (!s || how === 'left') return s;
  const pad = Math.max(cols - s.length, 0);
  return SPACE.repeat(how === 'center' ? Math.floor(pad / 2) : pad) + s;
}

function fillPageNo(line: string, n: string): string {
  if (!line.includes(BRAILLE_PAGE_TAG)) return line;
  const out = line.split(BRAILLE_PAGE_TAG).join(n);
  return n ? out : out.replace(/⠀+$/, '');
}

function headerLine(text: string, origPage: number, n: string, cols: number): string {
  const t = stripCells(text.split(BRAILLE_PAGE_TAG).join(n).split(ORIG_PAGE_TAG).join(num(origPage))).slice(0, cols);
  return SPACE.repeat(Math.floor((cols - t.length + 1) / 2)) + t;
}

export function buildPages(
  sources: Source[],
  footer = '',
  startBraillePage = 1,
  opts?: Partial<Options>,
  /**
   * `{점자 면 번호: 꼬리말 점자}`. 그 면만 이 값을 쓰고, 없는 면은 `footer`를 쓴다.
   * "이 면부터 끝까지 / 이 면만"은 편집 시점의 뜻이라 여기서 풀지 않는다 — 호출자(FE)가
   * 범위를 해석해 면별 값으로 펼쳐 넘긴다(2026-09-01 결정 E).
   */
  footers?: Record<number | string, string> | null,
  /** 머리말(이미 점역됨). footer · footers 와 같은 꼴. 머리말이 있는 면은 첫 줄을 먹는다. 표지 · 더한 빈 면에는 없다. */
  header = '',
  headers?: Record<number | string, string> | null,
  /**
   * `{원본 쪽 번호: 꼬리말 점자}`. 점역사가 묵자 쪽에 꽂은 꼬리말(2026-10-19 대표 결정 ②). 번호는 페이지행에 찍히는 원본
   * 번호(origPageStart 로 다시 매겼으면 그 번호)다. 범위는 footerMode. 한 면에 꽂은 쪽이 둘 이상 나오면 뒤의 것이고,
   * 면 번호 키 footers 가 있는 면은 그 값이 이긴다.
   */
  footersByOrigPage?: Record<number | string, string> | null,
): string[][] {
  const o = resolve(opts);
  // JSON을 거쳐 오면 키가 문자열이다 — 세 구현이 같게 굴도록 정수로 맞춘다.
  const fmap = new Map<number, string>();
  for (const [k, v] of Object.entries(footers ?? {})) fmap.set(Number(k), v);
  const hmap = new Map<number, string>();
  for (const [k, v] of Object.entries(headers ?? {})) hmap.set(Number(k), v);
  const omap = new Map<number, string>();
  for (const [k, v] of Object.entries(footersByOrigPage ?? {})) omap.set(Number(k), v);
  let carried = footer;                           // 이어가기 꼬리말(지금까지 실은 면에서 마지막으로 나온 꽂은 쪽의 것)
  /** 그 면 꼬리말: 면 키 footers > 원본 쪽 키(footerMode) > 기본 footer. 이어가기 상태도 여기서 민다. */
  const faceFooter = (bp: number, ops: number[]): string => {
    const pinned = ops.filter((x) => omap.has(x)).map((x) => omap.get(x) as string);
    if (pinned.length) carried = pinned[pinned.length - 1];
    const own = fmap.get(bp);
    if (own !== undefined) return own;
    if (o.footerMode === 'page') return pinned.length ? pinned[pinned.length - 1] : footer;
    return carried;
  };
  // 원본 페이지 번호를 끄면 변경선은 ⠤만 남은 빈 줄이 된다 — 함께 끈다(결정 D).
  const withChange = o.showChangeLine && o.showOrigPage;
  // 1) 원본 쪽 경계마다 변경선을 넣고 32칸으로 자른다. 줄마다 소속 원본 쪽을 들고 간다.
  const flat: Array<[string, number, boolean, string]> = [];   // [줄, 원본 쪽, 표지인가, 정렬]
  sources.forEach((src, i) => {
    // origPageStart가 있으면 표지 뒤 n번째 본문 원본 페이지를 다시 매긴다.
    const op = o.origPageStart !== null && i >= o.coverPages
      ? o.origPageStart + (i - o.coverPages)
      : src.orig_page;
    // ★ 표지 판정은 **순번**이다(결정 C). 쪽 번호로 보면 번호를 다시 매길 때 어긋난다.
    const cover = i < o.coverPages;
    if (i > 0 && withChange) flat.push([pageChangeLine(op, opts), op, cover, '']);
    const blocks = [...(src.blocks ?? [])].sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
    // 쪽바꿈 · 장바꿈 표식에서 토막을 낸다. 표식이 없으면 종전과 똑같이 한 토막이다.
    const segs: Array<Block[] | string> = [];
    let cur: Block[] = [];
    for (const b of blocks) {
      const t = (b.text ?? '').trim();
      if (t === PAGE_BREAK_TAG || t === CHAPTER_TAG) { segs.push(cur); segs.push(t === PAGE_BREAK_TAG ? BREAK : CHAPTER); cur = []; }
      else if (t in RULE_TAGS) cur.push({ order: b.order, text: ruleLine(t, o.cols) });   // 폭이 꼭 cols 라 안 접힌다
      else cur.push(b);
    }
    segs.push(cur);
    for (const seg of segs) {
      if (typeof seg === 'string') { flat.push([seg, op, cover, '']); continue; }
      for (const [w, al] of foldBlocks(seg, o)) flat.push([w.split(ORIG_PAGE_TAG).join(num(op)), op, cover, al]);
    }
  });

  // 2) 면으로 나눈다. 페이지행이 들어가는 면은 본문이 한 줄 줄어든다.
  // ★ 면 첫 줄의 빈 줄은 버리지 않는다 — 지침 2장2절2 2)(3)·§2.4.4(3)
  //   "본문 사이의 빈 줄이 점자 페이지 처음에 위치하더라도 빈 줄을 삭제하지 않는다".
  //   다만 문서 맨 앞 빈 줄은 '본문 사이'가 아니라 버린다.
  const pages: string[][] = [];
  const firstSeen = new Map<number, number>();
  let last = -1;                                  // 마지막 내용 줄 — 뒤쪽 빈 줄로 빈 면을 만들지 않는다
  for (let k = 0; k < flat.length; k++) if (!MARKS.includes(flat[k][0]) && flat[k][0].trim() !== '') last = k;
  let pos = 0;
  while (pos <= last && !MARKS.includes(flat[pos][0]) && flat[pos][0].trim() === '') pos++;
  /** 빈 면(장바꿈 · 짝수 면 채우기). 페이지행은 다른 면과 같은 규칙이고 원본 번호는 앞 내용의 원본 쪽을 잇는다. */
  const blank = (bp: number, head: number, cover: boolean): string[] => {
    const hasRow = hasPageRow(bp, o.pageRowOn) && !cover;
    const body: string[] = new Array(o.rows - (hasRow ? 1 : 0)).fill('');
    if (hasRow) {
      const idx = pages.length;
      body.push(pageRow(head, idx - (firstSeen.get(head) ?? idx), bp, faceFooter(bp, []), opts));
    }
    return body;
  };
  let bpn = startBraillePage;                     // 표지 면은 점자 면 번호를 소비하지 않는다
  let needOdd = false;                            // 장바꿈 뒤 — 다음 내용은 홀수 면에서 시작한다
  let prevOp: number | null = null;               // 마지막으로 실은 줄의 원본 쪽(장바꿈 빈 면의 페이지행)
  while (pos <= last) {
    while (pos <= last && MARKS.includes(flat[pos][0])) {   // 이미 이룬 쪽바꿈 · 장바꿈 표식만 버린다
      needOdd = needOdd || flat[pos][0] === CHAPTER;
      pos++;
    }
    if (pos > last) break;
    const onCover = flat[pos][2];              // 표지 범위는 페이지행 생략
    if (needOdd && !onCover && bpn % 2 === 0) {
      pages.push(blank(bpn, prevOp ?? flat[pos][1], false));
      bpn++;
    }
    needOdd = false;
    const idx = pages.length;
    const bp = bpn;
    const head = flat[pos][1];
    const hasRow = hasPageRow(bp, o.pageRowOn) && !onCover;
    const hd = onCover ? '' : (hmap.get(bp) ?? header);
    const cap = o.rows - (hasRow ? 1 : 0) - (hd ? 1 : 0);
    if (cap < 1) throw new Error(`rows ${o.rows}줄에서 머리말 · 페이지행을 빼면 본문 줄이 남지 않는다`);
    // 표식을 만나면 거기서 면을 끊는다 — 남은 칸은 아래에서 빈 줄로 채운다.
    let end = pos;
    while (end < flat.length && end - pos < cap && !MARKS.includes(flat[end][0])) end++;
    const n = onCover ? '' : num(bp);
    const body = flat.slice(pos, end).map(([ln, , , al]) => alignLine(fillPageNo(ln, n), o.cols, al));
    const ops = flat.slice(pos, end).map(([, x]) => x);
    prevOp = flat[end - 1][1];
    pos = end;
    if (pos < flat.length && MARKS.includes(flat[pos][0])) {   // 표식 자체는 본문에 안 싣는다
      needOdd = flat[pos][0] === CHAPTER;
      pos++;
    }
    if (!firstSeen.has(head)) firstSeen.set(head, idx);
    while (body.length < cap) body.push('');
    if (hd) body.unshift(headerLine(hd, head, n, o.cols));
    const f = faceFooter(bp, ops);                 // 페이지행이 없는 면도 이어가기 상태는 민다
    if (hasRow) body.push(pageRow(head, idx - (firstSeen.get(head) as number), bp, f, opts));
    if (!onCover) bpn++;                          // 지침 1장2 3)(1)·§2.1.5(1): 표지 다음 면이 1이다
    pages.push(body);
  }
  if (o.padToEven && pages.length % 2 === 1) pages.push(blank(bpn, flat[last][1], flat[last][2]));
  return pages;
}


// ── 조판 job 진입점 (V4 엔진 가이드 build_brf, 2026-10-14) ─────────────────────────
// ★ `blocks` 는 `order` 로 정렬한다(없으면 배열 순서). `braille` 은 translate 의 `cells`, `breaks` 는 그 `breaks` 그대로다.
// ★ 들여쓰기 · 가운데 정렬 · 구조적 빈 줄은 이미 `braille` 에 들어 있다. `heading_level`(가이드 밖, 받기는 한다)이 1이면
//   32칸을 넘어 접힌 1단계 제목 조각을 가운데에 놓는다. 원본 페이지 변경선은 `show_orig_page` 를 따른다.
export interface JobBlock {
  order?: number;
  braille: string;
  breaks?: number[] | null;
  heading_level?: number;
  /** 정렬 태그 셋(목록표). 없으면 받은 그대로. */
  align?: 'left' | 'center' | 'right' | '';
}

export interface JobSource {
  orig_page?: number;
  blocks: JobBlock[];
}

export interface JobOptions {
  cols?: number;
  rows?: number;
  wrap?: WrapMode;
  footer_align?: 'left' | 'center' | 'right';
  /** 원본 쪽에 꽂은 꼬리말의 범위. carry(기본, 이어가기) · page(그 쪽만). */
  footer_mode?: 'carry' | 'page';
  first_braille_page?: number;
  cover_orig_page_count?: number;
  orig_page_first_no?: number | null;
  page_row_pages?: 'odd' | 'every';
  show_orig_page?: boolean;
  show_braille_page?: boolean;
  /** 원본 페이지 변경선. 끄면 넣지 않는다(show_orig_page 를 끄면 이 값과 상관없이 꺼진다). */
  show_change_line?: boolean;
  pad_to_even?: boolean;
}

export interface Job {
  sources: JobSource[];
  /** 이미 점역된 꼬리말 점자. 이 레포는 점역하지 않는다. */
  footer?: string;
  /** 면별 꼬리말. `{점자 면 번호: 꼬리말 점자}` — 없는 면은 footer를 쓴다. */
  footers?: Record<string, string> | null;
  /** 이미 점역된 머리말. 머리말이 있는 면은 첫 줄을 먹는다. */
  header?: string;
  /** 면별 머리말. `{점자 면 번호: 머리말 점자}` — 없는 면은 header를 쓴다. */
  headers?: Record<string, string> | null;
  /** 원본 쪽에 꽂은 꼬리말. `{원본 쪽 번호: 꼬리말 점자}` — 범위는 opts.footer_mode(2026-10-19). */
  footers_by_orig_page?: Record<string, string> | null;
  opts?: JobOptions;
}

/** 조판 job 의 opts → Options(V4 가이드 이름). */
export function optionsFromJob(job: Job): Partial<Options> {
  const o = job.opts ?? {};
  const rowsOn = o.page_row_pages ?? 'odd';
  if (rowsOn !== 'odd' && rowsOn !== 'every') throw new Error(`page_row_pages는 odd|every: ${rowsOn}`);
  return {
    cols: o.cols ?? 32,
    rows: o.rows ?? 26,
    showOrigPage: o.show_orig_page ?? true,
    showBraillePage: o.show_braille_page ?? true,
    pageRowOn: rowsOn,
    coverPages: o.cover_orig_page_count ?? 0,
    origPageStart: o.orig_page_first_no ?? null,
    showChangeLine: o.show_change_line ?? true,
    footerAlign: o.footer_align ?? 'center',
    footerMode: o.footer_mode ?? 'carry',
    wrap: o.wrap ?? 'syllable',
    padToEven: o.pad_to_even ?? false,
  };
}

/** 조판 job → 점자 면 배열. buildPages의 얇은 어댑터다. */
export function buildPagesFromJob(job: Job): string[][] {
  const sources: Source[] = (job.sources ?? []).map((src, i) => ({
    orig_page: src.orig_page ?? i + 1,
    blocks: (src.blocks ?? []).map((b, k) => ({
      order: b.order ?? k, text: b.braille ?? '', breaks: b.breaks ?? null, heading_level: b.heading_level ?? 0,
      align: b.align ?? '',
    })),
  }));
  return buildPages(sources, job.footer ?? '', job.opts?.first_braille_page ?? 1,
                    optionsFromJob(job), job.footers ?? null, job.header ?? '', job.headers ?? null,
                    job.footers_by_orig_page ?? null);
}

/**
 * 조판 job → **.brf 파일 내용**(BRF Braille ASCII, 줄바꿈 \n).
 * 점역은 하지 않는다 — 이미 점역된 통 문자열을 조판만 한다.
 */
export function buildBrf(job: Job): string {
  return buildPagesFromJob(job).flat().map(toBrfAscii).join('\n');
}
