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
/** 줄바꿈 세 갈래(대표 결재 2026-10-09, 기본 음절). 뜻은 `wrap` 에 적었다. */
export const WRAP_MODES = ['syllable', 'word', 'cell'] as const;
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
  /** 꼬리말 정렬. right는 점자 면 번호에서 두 칸 띄운 자리가 오른쪽 끝이다. */
  footerAlign: 'center' | 'right';
  /** 32칸을 넘는 줄을 접는 갈래. 블록에 breaks 가 없으면 syllable 이어도 word 로 접는다. */
  wrap: WrapMode;
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
  wrap: 'syllable',
};

function resolve(opts?: Partial<Options>): Options {
  const o = { ...DEFAULT_OPTIONS, ...(opts ?? {}) };
  if (o.cols < 8) throw new Error(`cols는 8 이상이어야 한다: ${o.cols}`);
  if (!['every', 'odd', 'even', 'none'].includes(o.pageRowOn))
    throw new Error(`pageRowOn은 odd|every|even|none: ${o.pageRowOn}`);
  if (!WRAP_MODES.includes(o.wrap)) throw new Error(`wrap은 syllable|word|cell: ${o.wrap}`);
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
        : (n - f.length + 1) >> 1;          // ★ 올림 — 지침 실물로 확정
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
export interface Block { order: number; text: string; breaks?: number[] | null; heading_level?: number }
export interface Source { orig_page: number; blocks: Block[] }

/** cols를 넘으면 **빈칸(어절) 자리에서** 자른다. 어절 하나가 폭보다 길면 그때만 강제 분리.
 *  종전의 무조건 자르기는 한글 한 음절의 점형을 두 줄로 갈랐다 — 지침 §2.1.1(2)의
 *  음절 원칙도 어절 예외도 아니다(2026-09-08 대표 지적 ③). 자세한 근거는 python core._wrap. */
function wordWrap(line: string, cols: number): string[] {
  if (!line) return [''];
  const out: string[] = [];
  const trimEnd = (s: string) => s.replace(/⠀+$/, '');
  const trimStart = (s: string) => s.replace(/^⠀+/, '');
  while (line.length > cols) {
    const cut = line.lastIndexOf(SPACE, cols);
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
 * 논리 줄 하나를 cols 칸 줄들로 접는다. 줄바꿈 세 갈래(대표 결재 2026-10-09, 기본 음절). 근거는 python `wrap`.
 * - syllable: breaks(그 셀 앞에서 끊어도 되는 자리, 이 줄 기준) 가운데 cols 칸 안에서 가장 먼 자리에서 끊는다.
 *   없으면 cols 칸째에서 강제로 자르되 점역자 주 표 ⠠⠄ 는 가르지 않는다. 이어지는 줄 머리 빈칸은 버린다.
 *   breaks 가 비면 word 로 접는다(설계 §6-1).
 * - word: 빈칸(어절) 자리에서 자른다.
 * - cell: cols 칸마다 그대로 자른다(빈칸을 버리지 않고 가운데에도 놓지 않는다).
 * - center: 1단계 제목. cols 를 넘어 접힌 줄만 조각마다 가운데에 놓는다(syllable · word).
 */
export function wrap(line: string, cols = 32, mode: WrapMode = 'syllable',
                     breaks?: number[] | null, center = false): string[] {
  if (!WRAP_MODES.includes(mode)) throw new Error(`wrap은 syllable|word|cell: ${mode}`);
  if (mode === 'cell') {
    const out: string[] = [];
    for (let i = 0; i < line.length; i += cols) out.push(line.slice(i, i + cols));
    return out.length ? out : [''];
  }
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
      out.push(line.slice(start, cut));
      start = cut;
      while (start < line.length && (line[start] === SPACE || line[start] === ' ')) start++;
    }
    if (start < line.length || out.length === 0) out.push(line.slice(start));
  }
  if (center && line.length > cols) out = out.map((s) => SPACE.repeat(Math.floor((cols - s.length) / 2)) + s);
  return out;
}

/** 쪽바꿈 표식 사이 한 토막의 블록들을 이어 논리 줄로 나누고 o.wrap 갈래로 접는다. 근거는 python `_fold_blocks`. */
function foldBlocks(blocks: Block[], o: Options): string[] {
  let seg = blocks.map((b) => b.text ?? '').join('');
  if (seg === '') return [];   // 내용이 없는 토막(쪽바꿈 표식이 잇달은 자리)은 줄을 안 만든다
  const starts: number[] = [];
  const centers: boolean[] = [];
  const gbreaks: number[] = [];
  let acc = 0;
  for (const b of blocks) {
    starts.push(acc);
    centers.push((b.heading_level ?? 0) === 1);
    for (const x of b.breaks ?? []) gbreaks.push(acc + x);
    acc += (b.text ?? '').length;
  }
  // 통 문자열의 끝 개행은 마지막 줄을 끝내는 종결자이지 빈 줄이 아니다.
  // split('\n')이 그걸 빈 줄로 세어 원본 쪽마다 유령 빈 줄이 하나씩 생겼다.
  if (seg.endsWith('\n')) seg = seg.slice(0, -1);
  const out: string[] = [];
  let base = 0;
  for (const logical of seg.split('\n')) {
    let k = 0;
    while (k + 1 < starts.length && starts[k + 1] <= base) k++;
    const lb = gbreaks.filter((g) => base < g && g < base + logical.length).map((g) => g - base);
    out.push(...wrap(logical, o.cols, o.wrap, lb, centers[k]));
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
): string[][] {
  const o = resolve(opts);
  // JSON을 거쳐 오면 키가 문자열이다 — 세 구현이 같게 굴도록 정수로 맞춘다.
  const fmap = new Map<number, string>();
  for (const [k, v] of Object.entries(footers ?? {})) fmap.set(Number(k), v);
  // 원본 페이지 번호를 끄면 변경선은 ⠤만 남은 빈 줄이 된다 — 함께 끈다(결정 D).
  const withChange = o.showChangeLine && o.showOrigPage;
  // 1) 원본 쪽 경계마다 변경선을 넣고 32칸으로 자른다. 줄마다 소속 원본 쪽을 들고 간다.
  const flat: Array<[string, number, boolean]> = [];
  sources.forEach((src, i) => {
    // origPageStart가 있으면 표지 뒤 n번째 본문 원본 페이지를 다시 매긴다.
    const op = o.origPageStart !== null && i >= o.coverPages
      ? o.origPageStart + (i - o.coverPages)
      : src.orig_page;
    // ★ 표지 판정은 **순번**이다(결정 C). 쪽 번호로 보면 번호를 다시 매길 때 어긋난다.
    const cover = i < o.coverPages;
    if (i > 0 && withChange) flat.push([pageChangeLine(op, opts), op, cover]);
    const blocks = [...(src.blocks ?? [])].sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
    // 쪽바꿈 표식에서 토막을 낸다. 표식이 없으면 종전과 똑같이 한 토막이다.
    const segs: Array<Block[] | null> = [];
    let cur: Block[] = [];
    for (const b of blocks) {
      if ((b.text ?? '').trim() === PAGE_BREAK_TAG) { segs.push(cur); segs.push(null); cur = []; }
      else cur.push(b);
    }
    segs.push(cur);
    for (const seg of segs) {
      if (seg === null) { flat.push([BREAK, op, cover]); continue; }
      for (const w of foldBlocks(seg, o)) flat.push([w, op, cover]);
    }
  });

  // 2) 면으로 나눈다. 페이지행이 들어가는 면은 본문이 한 줄 줄어든다.
  // ★ 면 첫 줄의 빈 줄은 버리지 않는다 — 지침 2장2절2 2)(3)·§2.4.4(3)
  //   "본문 사이의 빈 줄이 점자 페이지 처음에 위치하더라도 빈 줄을 삭제하지 않는다".
  //   다만 문서 맨 앞 빈 줄은 '본문 사이'가 아니라 버린다.
  const pages: string[][] = [];
  const firstSeen = new Map<number, number>();
  let last = -1;                                  // 마지막 내용 줄 — 뒤쪽 빈 줄로 빈 면을 만들지 않는다
  for (let k = 0; k < flat.length; k++) if (flat[k][0] !== BREAK && flat[k][0].trim() !== '') last = k;
  let pos = 0;
  while (pos <= last && flat[pos][0] !== BREAK && flat[pos][0].trim() === '') pos++;
  let bpn = startBraillePage;                     // 표지 면은 점자 면 번호를 소비하지 않는다
  while (pos <= last) {
    while (pos <= last && flat[pos][0] === BREAK) pos++;   // 이미 이룬 쪽바꿈 표식만 버린다
    if (pos > last) break;
    const idx = pages.length;
    const bp = bpn;
    const head = flat[pos][1];
    const onCover = flat[pos][2];              // 표지 범위는 페이지행 생략
    const hasRow = hasPageRow(bp, o.pageRowOn) && !onCover;
    const cap = o.rows - (hasRow ? 1 : 0);
    // 표식을 만나면 거기서 면을 끊는다 — 남은 칸은 아래에서 빈 줄로 채운다.
    let end = pos;
    while (end < flat.length && end - pos < cap && flat[end][0] !== BREAK) end++;
    const body = flat.slice(pos, end).map(([ln]) => ln);
    pos = end;
    if (pos < flat.length && flat[pos][0] === BREAK) pos++;   // 표식 자체는 본문에 안 싣는다
    if (!firstSeen.has(head)) firstSeen.set(head, idx);
    while (body.length < cap) body.push('');
    if (hasRow) {
      const f = fmap.get(bp) ?? footer;
      body.push(pageRow(head, idx - (firstSeen.get(head) as number), bp, f, opts));
    }
    if (!onCover) bpn++;                          // 지침 1장2 3)(1)·§2.1.5(1): 표지 다음 면이 1이다
    pages.push(body);
  }
  return pages;
}


// ── BE 조립 JSON 진입점 (2026-08-06) ────────────────────────────────────────
// BE가 편집 최종본을 모아 넘기는 형식. BE·FE가 조판 규칙을 다시 짜지 않게 여기서 받는다.
//
// ★ `elements` 배열 **순서가 읽기 순서**다. `order` 필드는 없다(BE가 정렬해 담는다).
// ★ 들여쓰기·가운데 정렬·구조적 빈 줄은 AI가 이미 `text`에 넣어 보낸다(점자 공백 셀·`\n`).
//   `type`은 쓰지 않는다. `heading_level`은 1단계 제목이 32칸을 넘어 접힐 때만 조각을 가운데에 놓는 데 쓴다.
// ★ `breaks`(선택)는 응답 TextElement.breaks 그대로다. `text` 를 고치면 오프셋이 어긋난다.
export interface JobElement {
  id?: string;
  type?: string;
  heading_level?: number;
  text: string;
  breaks?: number[] | null;
}

export interface JobPage {
  orig_page_no: number;
  elements: JobElement[];
}

export interface JobOptions {
  include_page_number?: boolean;
  page_row_on?: 'every' | 'odd' | 'even' | 'none';
  rows?: number;
  cols?: number;
  show_orig_page?: boolean;
  show_braille_page?: boolean;
  cover_pages?: number;
  orig_page_start?: number | null;
  show_change_line?: boolean;
  footer_align?: 'center' | 'right';
  wrap?: WrapMode;
}

export interface Job {
  job_id?: string;
  options?: JobOptions;
  /** 이미 점역된 꼬리말 점자. 이 레포는 점역하지 않는다. */
  footer_braille?: string;
  /** 면별 꼬리말. `{점자 면 번호: 꼬리말 점자}` — 없는 면은 footer_braille를 쓴다. */
  footers_braille?: Record<string, string>;
  start_braille_page?: number;
  pages: JobPage[];
}

/**
 * BE 조립 JSON의 options → Options.
 *
 * include_page_number — 점역사가 Job을 만들 때 고른 값. **끄면 페이지행을 넣지 않는다.**
 * 원본 페이지 변경선은 유지한다 — 그건 쪽 번호가 아니라 쪽 경계 표시다.
 */
export function optionsFromJob(job: Job): Partial<Options> {
  const o = job.options ?? {};
  // include_page_number(켜기·끄기)와 page_row_on(어느 면)은 **같은 스위치**다(결정 B).
  const on = (o.include_page_number ?? true) ? (o.page_row_on ?? 'odd') : 'none';
  return {
    cols: o.cols ?? 32,
    rows: o.rows ?? 26,
    showOrigPage: o.show_orig_page ?? true,
    showBraillePage: o.show_braille_page ?? true,
    pageRowOn: on,
    coverPages: o.cover_pages ?? 0,
    origPageStart: o.orig_page_start ?? null,
    showChangeLine: o.show_change_line ?? true,
    footerAlign: o.footer_align ?? 'center',
    wrap: o.wrap ?? 'syllable',
  };
}

/** BE 조립 JSON → 점자 면 배열. buildPages의 얇은 어댑터다. */
export function buildPagesFromJob(job: Job): string[][] {
  const sources: Source[] = (job.pages ?? []).map((pg, i) => ({
    orig_page: pg.orig_page_no ?? i + 1,
    // 배열 순서가 읽기 순서다 — order를 만들어 붙여 그 순서를 유지한다.
    blocks: (pg.elements ?? []).map((el, k) => ({
      order: k, text: el.text ?? '', breaks: el.breaks ?? null, heading_level: el.heading_level ?? 0,
    })),
  }));
  return buildPages(sources, job.footer_braille ?? '',
                    job.start_braille_page ?? 1, optionsFromJob(job),
                    job.footers_braille ?? null);
}

/**
 * BE 조립 JSON → **.brf 파일 내용**(BRF Braille ASCII, 줄바꿈 \n).
 * 점역은 하지 않는다 — 이미 점역된 통 문자열을 조판만 한다.
 */
export function buildBrf(job: Job): string {
  return buildPagesFromJob(job).flat().map(toBrfAscii).join('\n');
}
