package com.semojum.brailleassist;

/**
 * braille-assist — 점자 조판 공용 함수 3개 (Java).
 *
 * <p>python/ts 구현과 출력이 같아야 한다. 규칙이 바뀌면 세 구현과 vectors.json을 한 PR로 갱신한다.
 * 이 클래스는 한글을 점역하지 않는다 — 꼬리말은 이미 점역된 점자를 받아 배치만 한다.
 *
 * <p>근거: 「점자 도서 제작 지침」 1장 2절 2 · 1장 3 · 2장 2절 2-3.
 */
public final class BrailleAssist {

    /** 공백 셀 ⠀ */
    public static final char SPACE = '⠀';
    private static final char NUM_SIGN = '⠼';    // 수표 ⠼
    private static final char CHANGE_MARK = '⠤'; // 변경선 채움 ⠤
    /** 줄바꿈 세 갈래(대표 결재 2026-10-09, 기본 음절). 뜻은 {@link #wrap(String, int, String, int[], boolean)}. */
    public static final java.util.List<String> WRAP_MODES = java.util.List.of("syllable", "word", "cell");
    private static final String TN_MARK = "⠠⠄";   // 점역자 주 표(두 칸). 강제로 자를 때 가르지 않는다

    // 숫자·알파벳은 같은 점형(1=a=⠁ … 0=j=⠚). 수표가 앞에 오면 숫자로 읽는다.
    private static final String DIGIT_CELLS = "⠚⠁⠃⠉⠙⠑⠋⠛⠓⠊";
    private static final String ALPHA_CELLS = "⠁⠃⠉⠙⠑⠋⠛⠓⠊⠚⠅⠇⠍⠝⠕⠏⠟⠗⠎⠞⠥⠧⠺⠭⠽⠵";

    /** BRF Braille ASCII 64셀 표준표(유니코드 오프셋 0..63 순). */
    private static final String BRAILLE_ASCII =
            " A1B'K2L@CIF/MSP"
            + "\"E3H9O6R^DJG>NTQ"
            + ",*5<-U8V.%[$+X!&"
            + ";:4\\0Z7(_?W]#Y)=";

    private BrailleAssist() {}

    /** 조판 옵션. 1차 PoC 고정값이 기본값이다(조판 가이드 §5). */
    public static final class Options {
        public final int cols;
        public final int rows;
        public final boolean showOrigPage;
        public final boolean showBraillePage;
        /**
         * 페이지행을 넣는 면. <b>기본은 홀수 면만</b>(2026-08-06 변경).
         * 지침 1장2절2-1이 홀수 면만이라 하고, 점자 도서 82권 실측에서도 페이지행을 가진 면이
         * 100% 홀수였다(원장 C-11 — 규정=관행 확정). 고정이 아니라 기본값이다.
         * 값: odd | every | even | none
         */
        public final String pageRowOn;
        /** 앞에서 이만큼의 <b>원본 페이지</b>가 표지. 점자 면 수가 아니다(2026-09-01 결정 C). */
        public final int coverPages;
        /** 표지 다음 첫 본문 원본 페이지에 붙일 번호. null이면 준 값 그대로. */
        public final Integer origPageStart;
        /** 원본 페이지 변경선을 넣을지. showOrigPage가 꺼지면 함께 꺼진다(결정 D). */
        public final boolean showChangeLine;
        /** 꼬리말 정렬. right는 점자 면 번호에서 두 칸 띄운 자리가 오른쪽 끝이다. */
        public final String footerAlign;
        /** 32칸을 넘는 줄을 접는 갈래. syllable(기본) | word | cell. 블록에 breaks 가 없으면 syllable 이어도 word. */
        public final String wrap;

        public Options(int cols, int rows, boolean showOrigPage, boolean showBraillePage,
                       String pageRowOn, int coverPages,
                       Integer origPageStart, boolean showChangeLine, String footerAlign, String wrap) {
            if (cols < 8) throw new IllegalArgumentException("cols는 8 이상이어야 한다: " + cols);
            if (!pageRowOn.equals("every") && !pageRowOn.equals("odd")
                    && !pageRowOn.equals("even") && !pageRowOn.equals("none"))
                throw new IllegalArgumentException("pageRowOn은 odd|every|even|none: " + pageRowOn);
            if (!footerAlign.equals("center") && !footerAlign.equals("right"))
                throw new IllegalArgumentException("footerAlign은 center|right: " + footerAlign);
            if (coverPages < 0)
                throw new IllegalArgumentException("coverPages는 0 이상이어야 한다: " + coverPages);
            if (!WRAP_MODES.contains(wrap))
                throw new IllegalArgumentException("wrap은 syllable|word|cell: " + wrap);
            this.cols = cols;
            this.rows = rows;
            this.showOrigPage = showOrigPage;
            this.showBraillePage = showBraillePage;
            this.pageRowOn = pageRowOn;
            this.coverPages = coverPages;
            this.origPageStart = origPageStart;
            this.showChangeLine = showChangeLine;
            this.footerAlign = footerAlign;
            this.wrap = wrap;
        }

        /** 종전 9인자 형태(BE `JobDownloadService` 가 쓴다) — 줄바꿈은 기본값 syllable. */
        public Options(int cols, int rows, boolean showOrigPage, boolean showBraillePage,
                       String pageRowOn, int coverPages,
                       Integer origPageStart, boolean showChangeLine, String footerAlign) {
            this(cols, rows, showOrigPage, showBraillePage, pageRowOn, coverPages,
                 origPageStart, showChangeLine, footerAlign, "syllable");
        }

        /** 종전 6인자 형태 — 새 항목은 기본값으로 채운다. */
        public Options(int cols, int rows, boolean showOrigPage, boolean showBraillePage,
                       String pageRowOn, int coverPages) {
            this(cols, rows, showOrigPage, showBraillePage, pageRowOn, coverPages,
                 null, true, "center");
        }

        public static Options defaults() {
            return new Options(32, 26, true, true, "odd", 0);
        }
    }

    /** 정수 → 수표 + 숫자 점형. 예: 12 → ⠼⠁⠃ */
    private static String num(int n) {
        if (n < 0) throw new IllegalArgumentException("페이지 번호는 0 이상이어야 한다: " + n);
        StringBuilder sb = new StringBuilder().append(NUM_SIGN);
        for (char d : String.valueOf(n).toCharArray()) sb.append(DIGIT_CELLS.charAt(d - '0'));
        return sb.toString();
    }

    /**
     * 걸침 순번 → 알파벳 점형. 1→a, 2→b … 26→z, 27→aa.
     *
     * <p>지침 1장2절2-2(3): 두 번째 점자 면부터 번호 <b>앞에</b> 로마자표 없이 알파벳.
     * 실물 [예 1-7]에서 105면(0)·107면(2=b)·109면(4=d) — 면 순번이지 페이지행 순번이 아니다.
     */
    private static String alpha(int idx) {
        if (idx <= 0) return "";
        StringBuilder sb = new StringBuilder();
        int i = idx;
        while (i > 0) {
            int r = (i - 1) % 26;
            i = (i - 1) / 26;
            sb.insert(0, ALPHA_CELLS.charAt(r));
        }
        return sb.toString();
    }

    /**
     * 페이지행 1줄(폭 = opts.cols).
     *
     * <p>지침 1장2절2·1장3: 원본 쪽 번호 왼쪽 정렬 첫 칸(걸침이면 번호 앞에 알파벳) ·
     * 꼬리말 가운데 정렬(항목 사이 두 칸 이상) · 점자 면 번호 오른쪽 정렬.
     *
     * <p>★ 가운데 정렬은 <b>올림</b>: start = (cols - footer.length() + 1) / 2.
     * 지침 실물 4건이 전부 이 값과 일치한다. 내림이면 [예 1-6](꼬리말 13칸)이 1칸 어긋난다.
     * ⚠ 조판 가이드 §4의 호출 예 두 개는 이 규칙과 다르다(예1은 33칸, 예2는 시작 2 어긋남) —
     * <b>지침 실물이 정본이다.</b>
     */
    public static String pageRow(int origPage, int contIdx, int braillePage,
                                 String footer, Options opts) {
        int n = opts.cols;
        String left = opts.showOrigPage ? alpha(contIdx) + num(origPage) : "";
        String right = opts.showBraillePage ? num(braillePage) : "";
        if (left.length() + right.length() > n)
            throw new IllegalArgumentException(
                    "쪽 번호만으로 " + n + "칸을 넘는다: " + left.length() + " + " + right.length());

        char[] cells = new char[n];
        java.util.Arrays.fill(cells, SPACE);
        for (int i = 0; i < left.length(); i++) cells[i] = left.charAt(i);
        for (int i = 0; i < right.length(); i++) cells[n - right.length() + i] = right.charAt(i);

        if (footer != null && !footer.isEmpty()) {
            // 항목 사이 두 칸 이상(지침 1장3-1). 자리에 안 들어가면 뒤에서 자른다(1장3-4).
            int lo = left.isEmpty() ? 0 : left.length() + 2;
            int hi = right.isEmpty() ? n : n - right.length() - 2;
            String f = footer.length() > hi - lo ? footer.substring(0, Math.max(0, hi - lo)) : footer;
            if (!f.isEmpty()) {
                // 우측 정렬이면 번호와 두 칸 띄운 자리가 오른쪽 끝이다.
                int start = "right".equals(opts.footerAlign)
                        ? hi - f.length()
                        : (n - f.length() + 1) / 2;   // ★ 올림 — 지침 실물로 확정
                start = Math.min(Math.max(start, lo), hi - f.length());
                for (int i = 0; i < f.length(); i++) cells[start + i] = f.charAt(i);
            }
        }
        return new String(cells);
    }

    public static String pageRow(int origPage, int contIdx, int braillePage, String footer) {
        return pageRow(origPage, contIdx, braillePage, footer, Options.defaults());
    }

    /**
     * 원본 페이지 변경선 1줄. 지침 2장2절2-3: 첫 칸부터 ⠤로 채우고 오른쪽 끝에 새 원본 쪽 번호.
     * 실물 [예 1-7]: 채움 29칸 + {@code #gb} 3칸 = 32.
     */
    public static String pageChangeLine(int origPage, Options opts) {
        String s = opts.showOrigPage ? num(origPage) : "";
        if (s.length() > opts.cols)
            throw new IllegalArgumentException("쪽 번호가 " + opts.cols + "칸을 넘는다: " + s.length());
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < opts.cols - s.length(); i++) sb.append(CHANGE_MARK);
        return sb.append(s).toString();
    }

    public static String pageChangeLine(int origPage) {
        return pageChangeLine(origPage, Options.defaults());
    }

    /**
     * 유니코드 점자 → BRF-ASCII(소문자). 파일에 쓰기 직전 한 번 호출한다.
     *
     * <p>공백 셀 ⠀는 <b>리터럴 스페이스</b>로 낸다(가이드 §3: {@code ⠼⠛⠀⠀…} → {@code #g  …}).
     * ⚠ 코퍼스 .brl 관례의 백틱(` = ⠈ = 초성 ㄱ)과 혼동 금지 — 백틱을 공백으로 쓰면 초성 ㄱ이 사라진다.
     * 줄바꿈은 보존하고, 못 푸는 셀은 {@code ⟨XXXX⟩}로 남긴다(조용히 버리지 않는다).
     */
    public static String toBrfAscii(String braille) {
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < braille.length(); i++) {
            char ch = braille.charAt(i);
            if (ch == '\n') {
                out.append('\n');
            } else if (ch == SPACE || ch == ' ') {
                out.append(' ');
            } else if (ch >= 0x2800 && ch < 0x2840) {
                char a = BRAILLE_ASCII.charAt(ch - 0x2800);
                out.append(unshift(a));
            } else {
                out.append(String.format("⟨%04X⟩", (int) ch));
            }
        }
        return out.toString();
    }

    /** 표준 ASCII {@code [ \ ] ^} 는 지침 표기에서 시프트형 {@code { | } ~} 로 나온다. */
    private static char unshift(char a) {
        switch (a) {
            case '[': return '{';
            case '\\': return '|';
            case ']': return '}';
            case '^': return '~';
            default: return Character.toLowerCase(a);
        }
    }

    // ── 문서 조립 (2026-08-05 추가) ─────────────────────────────────────────
    // 왜 여기 있나: ① 어느 면에 페이지행을 넣나 ② 걸침 순번(a·b·c)을 어떻게 세나
    // ③ 표지를 어디까지 빼나 — 셋 다 지침 규칙이다. 호출자가 각자 구현하면 점자 규정이
    // 레포 밖으로 흩어진다. 이 레포를 만든 이유가 그걸 막으려는 것이다.

    /** 원본 쪽 하나의 통 문자열 묶음. blocks는 order로 정렬해 이어 붙인다. */
    public static final class Source {
        public final int origPage;
        public final java.util.List<Block> blocks;

        public Source(int origPage, java.util.List<Block> blocks) {
            this.origPage = origPage;
            this.blocks = blocks;
        }
    }

    public static final class Block {
        public final int order;
        public final String text;
        /** 응답 breaks 그대로(그 블록 text 기준). null 이면 이 블록은 word 로 접는다. */
        public final int[] breaks;
        /** 1이면 32칸을 넘어 접힌 줄을 가운데에 놓는다(1단계 제목). */
        public final int headingLevel;

        public Block(int order, String text, int[] breaks, int headingLevel) {
            this.order = order;
            this.text = text;
            this.breaks = breaks;
            this.headingLevel = headingLevel;
        }

        public Block(int order, String text) { this(order, text, null, 0); }
    }

    /** cols를 넘으면 <b>빈칸(어절) 자리에서</b> 자른다. 어절 하나가 폭보다 길면 그때만 강제 분리.
     *  종전의 무조건 자르기는 한글 한 음절의 점형을 두 줄로 갈랐다 — 지침 §2.1.1(2)의
     *  음절 원칙도 어절 예외도 아니다(2026-09-08 대표 지적 ③). 근거는 python core._wrap. */
    private static java.util.List<String> wordWrap(String line, int cols) {
        java.util.List<String> out = new java.util.ArrayList<>();
        if (line.isEmpty()) {
            out.add("");
            return out;
        }
        while (line.length() > cols) {
            int cut = line.lastIndexOf(SPACE, cols);
            if (cut <= 0 || trimCells(line.substring(0, cut)).isEmpty()) {
                out.add(line.substring(0, cols));
                line = line.substring(cols);
            } else {
                out.add(trimEndCells(line.substring(0, cut)));
                line = trimStartCells(line.substring(cut));
            }
        }
        out.add(line);
        return out;
    }

    /**
     * 논리 줄 하나를 cols 칸 줄들로 접는다. 줄바꿈 세 갈래(대표 결재 2026-10-09, 기본 음절). 근거는 python {@code wrap}.
     * <ul>
     * <li>syllable — breaks(그 셀 앞에서 끊어도 되는 자리, 이 줄 기준) 가운데 cols 칸 안에서 가장 먼 자리에서 끊는다.
     *     없으면 cols 칸째에서 강제로 자르되 점역자 주 표 ⠠⠄ 는 가르지 않는다. 이어지는 줄 머리 빈칸은 버린다.
     *     breaks 가 비면 word 로 접는다(설계 §6-1).</li>
     * <li>word — 빈칸(어절) 자리에서 자른다.</li>
     * <li>cell — cols 칸마다 그대로 자른다(빈칸을 버리지 않고 가운데에도 놓지 않는다).</li>
     * <li>center — 1단계 제목. cols 를 넘어 접힌 줄만 조각마다 가운데에 놓는다(syllable · word).</li>
     * </ul>
     */
    public static java.util.List<String> wrap(String line, int cols, String mode, int[] breaks, boolean center) {
        if (!WRAP_MODES.contains(mode)) throw new IllegalArgumentException("wrap은 syllable|word|cell: " + mode);
        java.util.List<String> out = new java.util.ArrayList<>();
        if (mode.equals("cell")) {
            for (int i = 0; i < line.length(); i += cols) out.add(line.substring(i, Math.min(line.length(), i + cols)));
            if (out.isEmpty()) out.add("");
            return out;
        }
        if (mode.equals("word") || breaks == null || breaks.length == 0) {
            out = wordWrap(line, cols);
        } else {
            int start = 0;
            while (line.length() - start > cols) {
                int cut = -1;
                for (int b : breaks) if (start < b && b <= start + cols && b > cut) cut = b;
                if (cut < 0) {
                    cut = start + cols;
                    if (line.startsWith(TN_MARK, cut - 1)) cut -= 1;
                }
                out.add(line.substring(start, cut));
                start = cut;
                while (start < line.length() && (line.charAt(start) == SPACE || line.charAt(start) == ' ')) start++;
            }
            if (start < line.length() || out.isEmpty()) out.add(line.substring(start));
        }
        if (center && line.length() > cols) {
            java.util.List<String> c = new java.util.ArrayList<>();
            for (String piece : out) c.add(String.valueOf(SPACE).repeat((cols - piece.length()) / 2) + piece);
            out = c;
        }
        return out;
    }

    /** 쪽바꿈 표식 사이 한 토막의 블록들을 이어 논리 줄로 나누고 opts.wrap 갈래로 접는다. 근거는 python {@code _fold_blocks}. */
    private static java.util.List<String> foldBlocks(java.util.List<Block> blocks, Options opts) {
        StringBuilder sb = new StringBuilder();
        java.util.List<Integer> starts = new java.util.ArrayList<>();
        java.util.List<Boolean> centers = new java.util.ArrayList<>();
        java.util.List<Integer> gbreaks = new java.util.ArrayList<>();
        for (Block b : blocks) {
            starts.add(sb.length());
            centers.add(b.headingLevel == 1);
            if (b.breaks != null) for (int x : b.breaks) gbreaks.add(sb.length() + x);
            sb.append(b.text == null ? "" : b.text);
        }
        java.util.List<String> out = new java.util.ArrayList<>();
        String seg = sb.toString();
        if (seg.isEmpty()) return out;   // 내용 없는 토막(쪽바꿈 표식이 잇달은 자리)
        // 통 문자열의 끝 개행은 마지막 줄을 끝내는 종결자이지 빈 줄이 아니다.
        // split 이 그걸 빈 줄로 세어 원본 쪽마다 유령 빈 줄이 하나씩 생겼다.
        if (seg.endsWith("\n")) seg = seg.substring(0, seg.length() - 1);
        int base = 0;
        for (String logical : seg.split("\n", -1)) {
            int k = 0;
            while (k + 1 < starts.size() && starts.get(k + 1) <= base) k++;
            java.util.List<Integer> lb = new java.util.ArrayList<>();
            for (int g : gbreaks) if (base < g && g < base + logical.length()) lb.add(g - base);
            out.addAll(wrap(logical, opts.cols, opts.wrap,
                            lb.stream().mapToInt(Integer::intValue).toArray(), centers.get(k)));
            base += logical.length() + 1;
        }
        return out;
    }

    private static String trimEndCells(String s) {
        int e = s.length();
        while (e > 0 && s.charAt(e - 1) == SPACE) e--;
        return s.substring(0, e);
    }

    private static String trimStartCells(String s) {
        int b = 0;
        while (b < s.length() && s.charAt(b) == SPACE) b++;
        return s.substring(b);
    }

    private static String trimCells(String s) {
        return trimEndCells(trimStartCells(s));
    }

    private static boolean hasPageRow(int braillePage, String on) {
        if (on.equals("none")) return false;
        if (on.equals("odd")) return braillePage % 2 == 1;
        if (on.equals("even")) return braillePage % 2 == 0;
        return true;
    }

    /**
     * 원본 쪽별 통 문자열 → 완성된 점자 면 배열. BRF 변환 직전 상태다.
     *
     * <p>★ 페이지행의 원본 번호 = <b>그 면 첫 줄이 속한 원본 쪽</b>(지침 1장2절2-2(4)).
     * <p>★ 걸침 순번 = 그 원본 쪽이 <b>처음 나온 면부터 센 순번</b>(0부터).
     * 지침 [예 1-7]이 105·107·109면에 없음·b·d를 붙이는 근거 — 페이지행이 홀수 면에만
     * 찍혀 a(106)·c(108)가 안 보이는 것이지 순번이 건너뛴 게 아니다.
     */
    public static java.util.List<java.util.List<String>> buildPages(
            java.util.List<Source> sources, String footer, int startBraillePage, Options opts) {
        return buildPages(sources, footer, startBraillePage, opts, null);
    }

    /**
     * footers — {점자 면 번호: 꼬리말 점자}. 그 면만 이 값을 쓰고, 없는 면은 footer를 쓴다.
     * "이 면부터 끝까지 / 이 면만"은 편집 시점의 뜻이라 여기서 풀지 않는다 — 호출자(FE)가
     * 범위를 해석해 면별 값으로 펼쳐 넘긴다(2026-09-01 결정 E).
     */
    /**
     * 쪽바꿈 표식(2026-09-03, FE QA L-2). 편집 화면에서 Ctrl+Enter 로 끼워 넣는 <b>독립 요소</b>이고
     * 본문은 이 한 줄뿐이다. 조판에서 만나면 요소를 버리고 그 자리에서 면을 끊는다.
     * 원본 쪽 경계(origPage)와 무관하게 쪽 한가운데에서도 올 수 있다.
     */
    public static final String PAGE_BREAK_TAG = "<!쪽바꿈>";
    /** lines 안에서 쪽바꿈 자리를 표시하는 내부 값. 점자 텍스트에는 못 나오는 문자를 쓴다. */
    private static final String BREAK = "\u0000brk";

    public static java.util.List<java.util.List<String>> buildPages(
            java.util.List<Source> sources, String footer, int startBraillePage, Options opts,
            java.util.Map<Integer, String> footers) {
        java.util.Map<Integer, String> fmap =
                footers == null ? java.util.Collections.emptyMap() : footers;
        // 원본 페이지 번호를 끄면 변경선은 ⠤만 남은 빈 줄이 된다 — 함께 끈다(결정 D).
        boolean withChange = opts.showChangeLine && opts.showOrigPage;
        // 1) 원본 쪽 경계마다 변경선을 넣고 32칸으로 자른다. 줄마다 소속 원본 쪽·표지 여부를 들고 간다.
        java.util.List<String> lines = new java.util.ArrayList<>();
        java.util.List<Integer> owner = new java.util.ArrayList<>();
        java.util.List<Boolean> coverOf = new java.util.ArrayList<>();
        for (int i = 0; i < sources.size(); i++) {
            Source src = sources.get(i);
            // origPageStart가 있으면 표지 뒤 n번째 본문 원본 페이지를 다시 매긴다.
            int op = (opts.origPageStart != null && i >= opts.coverPages)
                    ? opts.origPageStart + (i - opts.coverPages)
                    : src.origPage;
            // ★ 표지 판정은 **순번**이다(결정 C). 쪽 번호로 보면 번호를 다시 매길 때 어긋난다.
            boolean cover = i < opts.coverPages;
            if (i > 0 && withChange) {         // 첫 원본 쪽 앞에는 변경선을 두지 않는다
                lines.add(pageChangeLine(op, opts));
                owner.add(op);
                coverOf.add(cover);
            }
            java.util.List<Block> bs = new java.util.ArrayList<>(
                    src.blocks == null ? java.util.Collections.emptyList() : src.blocks);
            bs.sort(java.util.Comparator.comparingInt(b -> b.order));
            // 쪽바꿈 표식에서 토막을 낸다. 표식이 없으면 종전과 똑같이 한 토막이다.
            java.util.List<java.util.List<Block>> segs = new java.util.ArrayList<>();
            java.util.List<Block> cur = new java.util.ArrayList<>();
            for (Block b : bs) {
                String t = b.text == null ? "" : b.text;
                if (t.trim().equals(PAGE_BREAK_TAG)) {
                    segs.add(cur);
                    segs.add(null);
                    cur = new java.util.ArrayList<>();
                } else {
                    cur.add(b);
                }
            }
            segs.add(cur);
            for (java.util.List<Block> seg : segs) {
                if (seg == null) {
                    lines.add(BREAK);
                    owner.add(op);
                    coverOf.add(cover);
                    continue;
                }
                for (String w : foldBlocks(seg, opts)) {
                    lines.add(w);
                    owner.add(op);
                    coverOf.add(cover);
                }
            }
        }

        // 2) 면으로 나눈다. 페이지행이 들어가는 면은 본문이 한 줄 줄어든다.
        // ★ 면 첫 줄의 빈 줄은 버리지 않는다 — 지침 2장2절2 2)(3)·§2.4.4(3)
        //   "본문 사이의 빈 줄이 점자 페이지 처음에 위치하더라도 빈 줄을 삭제하지 않는다".
        //   다만 문서 맨 앞 빈 줄은 '본문 사이'가 아니라 버린다.
        java.util.List<java.util.List<String>> pages = new java.util.ArrayList<>();
        java.util.Map<Integer, Integer> firstSeen = new java.util.HashMap<>();
        int last = -1;   // 마지막 내용 줄 — 뒤쪽 빈 줄로 빈 면을 만들지 않는다
        for (int k = 0; k < lines.size(); k++) {
            if (!BREAK.equals(lines.get(k)) && !lines.get(k).trim().isEmpty()) last = k;
        }
        int pos = 0;
        while (pos <= last && !BREAK.equals(lines.get(pos)) && lines.get(pos).trim().isEmpty()) pos++;
        int bpn = startBraillePage;   // 표지 면은 점자 면 번호를 소비하지 않는다
        while (pos <= last) {
            while (pos <= last && BREAK.equals(lines.get(pos))) pos++;  // 이미 이룬 쪽바꿈만 버린다
            if (pos > last) break;
            int idx = pages.size();
            int bp = bpn;
            int head = owner.get(pos);
            boolean onCover = coverOf.get(pos);           // 표지 범위는 페이지행 생략
            boolean hasRow = hasPageRow(bp, opts.pageRowOn) && !onCover;
            int cap = opts.rows - (hasRow ? 1 : 0);
            // 표식을 만나면 거기서 면을 끊는다 — 남은 칸은 아래에서 빈 줄로 채운다.
            int end = pos;
            while (end < lines.size() && end - pos < cap && !BREAK.equals(lines.get(end))) end++;
            java.util.List<String> body = new java.util.ArrayList<>(lines.subList(pos, end));
            pos = end;
            if (pos < lines.size() && BREAK.equals(lines.get(pos))) pos++;  // 표식은 본문에 안 싣는다
            firstSeen.putIfAbsent(head, idx);
            while (body.size() < cap) body.add("");
            if (hasRow) {
                String f = fmap.getOrDefault(bp, footer);
                body.add(pageRow(head, idx - firstSeen.get(head), bp, f, opts));
            }
            if (!onCover) bpn++;   // 지침 1장2 3)(1)·§2.1.5(1): 표지 다음 면이 1이다
            pages.add(body);
        }
        return pages;
    }

    public static java.util.List<java.util.List<String>> buildPages(
            java.util.List<Source> sources, String footer) {
        return buildPages(sources, footer, 1, Options.defaults());
    }

    // ── BE 조립 JSON 진입점 (2026-08-06) ────────────────────────────────────
    // BE가 편집 최종본을 모아 넘기는 형식. BE·FE가 조판 규칙을 다시 짜지 않게 여기서 받는다.
    //
    // ★ elements 배열 **순서가 읽기 순서**다. order 필드는 없다(BE가 정렬해 담는다).
    // ★ 들여쓰기·가운데 정렬·구조적 빈 줄은 AI가 이미 text에 넣어 보낸다(점자 공백 셀·\n).
    //   type은 쓰지 않는다. headingLevel은 1단계 제목이 32칸을 넘어 접힐 때만 조각을 가운데에 놓는 데 쓴다.
    // ★ breaks(선택)는 응답 TextElement.breaks 그대로다. text 를 고치면 오프셋이 어긋난다.

    /** 조립 JSON의 요소 하나. */
    public static final class JobElement {
        public final String id;
        public final String type;
        public final int headingLevel;
        public final String text;
        /** 응답 TextElement.breaks 그대로(선택). null 이면 그 요소는 word 로 접는다. */
        public final int[] breaks;

        public JobElement(String id, String type, int headingLevel, String text, int[] breaks) {
            this.id = id;
            this.type = type;
            this.headingLevel = headingLevel;
            this.text = text == null ? "" : text;
            this.breaks = breaks;
        }

        public JobElement(String id, String type, int headingLevel, String text) {
            this(id, type, headingLevel, text, null);
        }

        public JobElement(String text) { this(null, "text", 0, text); }
    }

    /** 원본 쪽 하나. elements 배열 순서가 읽기 순서다. */
    public static final class JobPage {
        public final int origPageNo;
        public final java.util.List<JobElement> elements;

        public JobPage(int origPageNo, java.util.List<JobElement> elements) {
            this.origPageNo = origPageNo;
            this.elements = elements == null ? java.util.Collections.emptyList() : elements;
        }
    }

    /** 조립 JSON 전체. */
    public static final class Job {
        public final String jobId;
        /**
         * 점역사가 Job을 만들 때 고른 값. 끄면 페이지행을 넣지 않는다.
         * pageRowOn(어느 면)과 <b>같은 스위치</b>다 — 끄기가 이긴다(2026-09-01 결정 B).
         */
        public final boolean includePageNumber;
        public final String pageRowOn;
        public final int rows;
        public final int cols;
        public final boolean showOrigPage;
        public final boolean showBraillePage;
        public final int coverPages;
        public final Integer origPageStart;
        public final boolean showChangeLine;
        public final String footerAlign;
        /** 이미 점역된 꼬리말 점자. 이 레포는 점역하지 않는다. */
        public final String footerBraille;
        /** 면별 꼬리말. {점자 면 번호: 꼬리말 점자} — 없는 면은 footerBraille를 쓴다. */
        public final java.util.Map<Integer, String> footersBraille;
        public final int startBraillePage;
        public final java.util.List<JobPage> pages;
        /** 줄바꿈 갈래. syllable(기본) | word | cell. */
        public final String wrap;

        public Job(String jobId, boolean includePageNumber, String pageRowOn, int rows, int cols,
                   boolean showOrigPage, boolean showBraillePage, int coverPages,
                   Integer origPageStart, boolean showChangeLine, String footerAlign,
                   String footerBraille, java.util.Map<Integer, String> footersBraille,
                   int startBraillePage, java.util.List<JobPage> pages, String wrap) {
            this.jobId = jobId;
            this.includePageNumber = includePageNumber;
            this.pageRowOn = pageRowOn == null || pageRowOn.isEmpty() ? "odd" : pageRowOn;
            this.rows = rows <= 0 ? 26 : rows;
            this.cols = cols <= 0 ? 32 : cols;
            this.showOrigPage = showOrigPage;
            this.showBraillePage = showBraillePage;
            this.coverPages = Math.max(0, coverPages);
            this.origPageStart = origPageStart;
            this.showChangeLine = showChangeLine;
            this.footerAlign = footerAlign == null || footerAlign.isEmpty() ? "center" : footerAlign;
            this.footerBraille = footerBraille == null ? "" : footerBraille;
            this.footersBraille = footersBraille == null
                    ? java.util.Collections.emptyMap() : footersBraille;
            this.startBraillePage = startBraillePage <= 0 ? 1 : startBraillePage;
            this.pages = pages == null ? java.util.Collections.emptyList() : pages;
            this.wrap = wrap == null || wrap.isEmpty() ? "syllable" : wrap;
        }

        /** 종전 15인자 형태 — 줄바꿈은 기본값 syllable. */
        public Job(String jobId, boolean includePageNumber, String pageRowOn, int rows, int cols,
                   boolean showOrigPage, boolean showBraillePage, int coverPages,
                   Integer origPageStart, boolean showChangeLine, String footerAlign,
                   String footerBraille, java.util.Map<Integer, String> footersBraille,
                   int startBraillePage, java.util.List<JobPage> pages) {
            this(jobId, includePageNumber, pageRowOn, rows, cols, showOrigPage, showBraillePage,
                 coverPages, origPageStart, showChangeLine, footerAlign, footerBraille,
                 footersBraille, startBraillePage, pages, "syllable");
        }

        /** 종전 7인자 형태 — 새 항목은 기본값으로 채운다. */
        public Job(String jobId, boolean includePageNumber, int rows, int cols,
                   String footerBraille, int startBraillePage, java.util.List<JobPage> pages) {
            this(jobId, includePageNumber, "odd", rows, cols, true, true, 0, null, true,
                 "center", footerBraille, null, startBraillePage, pages);
        }

        public Job(java.util.List<JobPage> pages) { this(null, true, 26, 32, "", 1, pages); }
    }

    /**
     * 조립 JSON → Options.
     *
     * <p>includePageNumber를 끄면 <b>페이지행을 넣지 않는다.</b> 원본 페이지 변경선은
     * showChangeLine이 따로 정한다(2026-09-01 결정 D).
     */
    public static Options optionsFromJob(Job job) {
        String on = job.includePageNumber ? job.pageRowOn : "none";
        return new Options(job.cols, job.rows, job.showOrigPage, job.showBraillePage,
                           on, job.coverPages,
                           job.origPageStart, job.showChangeLine, job.footerAlign, job.wrap);
    }

    /** 조립 JSON → 점자 면 배열. buildPages의 얇은 어댑터다. */
    public static java.util.List<java.util.List<String>> buildPagesFromJob(Job job) {
        java.util.List<Source> sources = new java.util.ArrayList<>();
        for (int i = 0; i < job.pages.size(); i++) {
            JobPage pg = job.pages.get(i);
            java.util.List<Block> blocks = new java.util.ArrayList<>();
            for (int k = 0; k < pg.elements.size(); k++) {
                // 배열 순서가 읽기 순서다 — order를 만들어 붙여 그 순서를 유지한다.
                JobElement el = pg.elements.get(k);
                blocks.add(new Block(k, el.text, el.breaks, el.headingLevel));
            }
            sources.add(new Source(pg.origPageNo > 0 ? pg.origPageNo : i + 1, blocks));
        }
        return buildPages(sources, job.footerBraille, job.startBraillePage, optionsFromJob(job),
                          job.footersBraille);
    }

    /**
     * 점자 면 배열 → <b>.brf 파일 내용</b>(BRF Braille ASCII). 줄마다 {@code \r\n}, 면마다 끝에
     * {@code \f}(마지막 면 포함).
     *
     * <p>현장 BRF 와 같은 바이트 규격이다(점자 대체교과서 BRF 51권: 줄마다 CRLF, 26줄 면마다 폼 피드).
     * {@code \n} 으로만 잇고 면 구분자를 안 넣으면 실로암브레일이 34KB 파일을 못 열었다(braille-assist#10).
     * 파일은 이 문자열을 그대로 쓴다. 6점 밖 글자는 {@link #toBrfAscii} 대로 {@code ⟨XXXX⟩} 가 남는다.
     */
    public static String pagesToBrf(java.util.List<java.util.List<String>> pages) {
        StringBuilder sb = new StringBuilder();
        for (java.util.List<String> page : pages) {
            for (String line : page) {
                sb.append(toBrfAscii(line)).append("\r\n");
            }
            sb.append('\f');
        }
        return sb.toString();
    }

    /**
     * 조립 JSON → <b>.brf 파일 내용</b>({@link #pagesToBrf} 규격).
     * 점역은 하지 않는다 — 이미 점역된 통 문자열을 조판만 한다.
     */
    public static String buildBrf(Job job) {
        return pagesToBrf(buildPagesFromJob(job));
    }
}
