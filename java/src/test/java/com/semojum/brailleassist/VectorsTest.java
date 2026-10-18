package com.semojum.brailleassist;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.TestFactory;

/** vectors.json 대조 — java 구현. 세 언어가 같은 벡터로 같은 출력을 내야 한다. */
class VectorsTest {

    /** vectors.json은 언어 중립으로 snake_case를 쓴다 — java는 camelCase라 여기서 옮긴다. */
    private static BrailleAssist.Options toOpts(JsonNode o) {
        if (o == null || o.isNull()) return BrailleAssist.Options.defaults();
        return new BrailleAssist.Options(
                o.get("cols").asInt(),
                o.get("rows").asInt(),
                o.get("show_orig_page").asBoolean(),
                o.get("show_braille_page").asBoolean(),
                o.get("page_row_on").asText(),
                o.get("cover_pages").asInt(),
                o.has("orig_page_start") && !o.get("orig_page_start").isNull()
                        ? o.get("orig_page_start").asInt() : null,
                !o.has("show_change_line") || o.get("show_change_line").asBoolean(),
                o.has("footer_align") ? o.get("footer_align").asText() : "center",
                o.has("wrap") ? o.get("wrap").asText() : "syllable",
                o.has("pad_to_even") && o.get("pad_to_even").asBoolean());
    }

    /** {"면 번호": 점자} → Map. 없거나 null 이면 null. */
    private static java.util.Map<Integer, String> intMap(JsonNode n) {
        if (n == null || n.isNull()) return null;
        java.util.Map<Integer, String> m = new java.util.HashMap<>();
        n.fieldNames().forEachRemaining(k -> m.put(Integer.parseInt(k), n.get(k).asText()));
        return m;
    }

    /** breaks 칸 → int[]. 없거나 null 이면 null(그 블록은 word 로 접는다). */
    private static int[] ints(JsonNode n) {
        if (n == null || n.isNull()) return null;
        int[] out = new int[n.size()];
        for (int i = 0; i < out.length; i++) out[i] = n.get(i).asInt();
        return out;
    }

    private static String joinLines(JsonNode lines) {
        List<String> ls = new ArrayList<>();
        for (JsonNode l : lines) ls.add(l.asText());
        return String.join("\u241F", ls);
    }

    /** 면 배열 → 비교용 문자열. 줄은 \u241F, 면은 \u241E로 잇는다(점자에 안 쓰이는 문자). */
    private static String join(List<List<String>> pages) {
        StringBuilder sb = new StringBuilder();
        for (List<String> p : pages) {
            if (sb.length() > 0) sb.append('\u241E');
            sb.append(String.join("\u241F", p));
        }
        return sb.toString();
    }

    private static String joinNode(JsonNode pages) {
        StringBuilder sb = new StringBuilder();
        for (JsonNode p : pages) {
            if (sb.length() > 0) sb.append('\u241E');
            List<String> ls = new ArrayList<>();
            for (JsonNode l : p) ls.add(l.asText());
            sb.append(String.join("\u241F", ls));
        }
        return sb.toString();
    }

    private static String call(String fname, JsonNode a) {
        switch (fname) {
            case "page_row":
                return BrailleAssist.pageRow(
                        a.get("orig_page").asInt(),
                        a.get("cont_idx").asInt(),
                        a.get("braille_page").asInt(),
                        a.has("footer") ? a.get("footer").asText() : "",
                        toOpts(a.get("opts")));
            case "page_change_line":
                return BrailleAssist.pageChangeLine(a.get("orig_page").asInt(), toOpts(a.get("opts")));
            case "to_brf_ascii":
                return BrailleAssist.toBrfAscii(a.get("braille").asText());
            case "build_pages": {
                List<BrailleAssist.Source> srcs = new ArrayList<>();
                for (JsonNode s : a.get("sources")) {
                    List<BrailleAssist.Block> bs = new ArrayList<>();
                    for (JsonNode b : s.get("blocks")) {
                        bs.add(new BrailleAssist.Block(b.get("order").asInt(), b.get("text").asText(),
                                ints(b.get("breaks")),
                                b.has("heading_level") ? b.get("heading_level").asInt() : 0,
                                b.has("align") ? b.get("align").asText() : ""));
                    }
                    srcs.add(new BrailleAssist.Source(s.get("orig_page").asInt(), bs));
                }
                // 면 배열은 JSON으로 견줘야 해서 문자열로 직렬화해 비교한다.
                java.util.Map<Integer, String> footers = new java.util.HashMap<>();
                if (a.has("footers") && !a.get("footers").isNull()) {
                    JsonNode fs = a.get("footers");
                    fs.fieldNames().forEachRemaining(
                            k -> footers.put(Integer.parseInt(k), fs.get(k).asText()));
                }
                return join(BrailleAssist.buildPages(srcs,
                        a.has("footer") ? a.get("footer").asText() : "",
                        a.has("start_braille_page") ? a.get("start_braille_page").asInt() : 1,
                        toOpts(a.get("opts")), footers,
                        a.has("header") ? a.get("header").asText() : "", intMap(a.get("headers")),
                        intMap(a.get("footers_by_orig_page")),
                        a.has("opts") && a.get("opts").has("footer_mode") ? a.get("opts").get("footer_mode").asText() : "carry"));
            }
            case "build_brf": {
                // V4 엔진 가이드 job: sources[].blocks[].{order, braille, breaks} · footer · footers · opts.
                // java Job 은 BE 용 필드 이름 그대로라 여기서 옮긴다(V4 에서 java 조판은 BE 와 함께 빠진다).
                JsonNode j = a.get("job");
                JsonNode o = j.has("opts") ? j.get("opts") : null;
                List<BrailleAssist.JobPage> pages = new ArrayList<>();
                if (j.has("sources")) {
                    int i = 0;
                    for (JsonNode src : j.get("sources")) {
                        List<JsonNode> blocks = new ArrayList<>();
                        if (src.has("blocks")) src.get("blocks").forEach(blocks::add);
                        final int[] k = {0};
                        List<int[]> keyed = new ArrayList<>();
                        for (JsonNode b : blocks) keyed.add(new int[]{b.has("order") ? b.get("order").asInt() : k[0], k[0]++});
                        keyed.sort((x, y) -> x[0] != y[0] ? Integer.compare(x[0], y[0]) : Integer.compare(x[1], y[1]));
                        List<BrailleAssist.JobElement> els = new ArrayList<>();
                        for (int[] kk : keyed) {
                            JsonNode b = blocks.get(kk[1]);
                            els.add(new BrailleAssist.JobElement(null, "text",
                                    b.has("heading_level") ? b.get("heading_level").asInt() : 0,
                                    b.has("braille") ? b.get("braille").asText() : "",
                                    ints(b.get("breaks")),
                                    b.has("align") ? b.get("align").asText() : ""));
                        }
                        pages.add(new BrailleAssist.JobPage(
                                src.has("orig_page") ? src.get("orig_page").asInt() : i + 1, els));
                        i++;
                    }
                }
                java.util.Map<Integer, String> jf = new java.util.HashMap<>();
                if (j.has("footers") && !j.get("footers").isNull()) {
                    JsonNode fs = j.get("footers");
                    fs.fieldNames().forEachRemaining(
                            kk -> jf.put(Integer.parseInt(kk), fs.get(kk).asText()));
                }
                BrailleAssist.Job job = new BrailleAssist.Job(
                        null, true,
                        o != null && o.has("page_row_pages") ? o.get("page_row_pages").asText() : "odd",
                        o != null && o.has("rows") ? o.get("rows").asInt() : 26,
                        o != null && o.has("cols") ? o.get("cols").asInt() : 32,
                        o == null || !o.has("show_orig_page") || o.get("show_orig_page").asBoolean(),
                        o == null || !o.has("show_braille_page")
                                || o.get("show_braille_page").asBoolean(),
                        o != null && o.has("cover_orig_page_count") ? o.get("cover_orig_page_count").asInt() : 0,
                        o != null && o.has("orig_page_first_no") && !o.get("orig_page_first_no").isNull()
                                ? o.get("orig_page_first_no").asInt() : null,
                        o == null || !o.has("show_change_line") || o.get("show_change_line").asBoolean(),
                        o != null && o.has("footer_align") ? o.get("footer_align").asText() : "center",
                        j.has("footer") ? j.get("footer").asText() : "",
                        jf,
                        o != null && o.has("first_braille_page") ? o.get("first_braille_page").asInt() : 1,
                        pages,
                        o != null && o.has("wrap") ? o.get("wrap").asText() : "syllable",
                        o != null && o.has("pad_to_even") && o.get("pad_to_even").asBoolean(),
                        j.has("header") ? j.get("header").asText() : "",
                        intMap(j.get("headers")),
                        intMap(j.get("footers_by_orig_page")),
                        o != null && o.has("footer_mode") ? o.get("footer_mode").asText() : "carry");
                return BrailleAssist.buildBrf(job);
            }
            case "wrap":
                return String.join("\u241F", BrailleAssist.wrap(
                        a.get("line").asText(),
                        a.has("cols") ? a.get("cols").asInt() : 32,
                        a.has("mode") ? a.get("mode").asText() : "syllable",
                        ints(a.get("breaks")),
                        a.has("center") && a.get("center").asBoolean()));
            default:
                throw new IllegalArgumentException("모르는 함수: " + fname);
        }
    }

    @TestFactory
    List<DynamicTest> vectors() throws Exception {
        Path p = Path.of("..", "vectors.json");
        JsonNode root = new ObjectMapper().readTree(Files.readString(p));
        List<DynamicTest> tests = new ArrayList<>();
        root.get("cases").fields().forEachRemaining(e -> {
            String fname = e.getKey();
            for (JsonNode c : e.getValue()) {
                tests.add(DynamicTest.dynamicTest(
                        fname + " — " + c.get("name").asText(),
                        () -> assertEquals(
                                fname.equals("build_pages") ? joinNode(c.get("expect"))
                                : fname.equals("wrap") ? joinLines(c.get("expect"))
                                : c.get("expect").asText(),
                                call(fname, c.get("args")))));
            }
        });
        return tests;
    }
}
