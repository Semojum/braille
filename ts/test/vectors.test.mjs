// vectors.json 대조 — ts 구현. 빌드 없이 돈다(node --experimental-strip-types).
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { pageRow, pageChangeLine, toBrfAscii, buildPages, buildBrf } from '../src/index.ts';

const here = dirname(fileURLToPath(import.meta.url));
const data = JSON.parse(readFileSync(join(here, '..', '..', 'vectors.json'), 'utf8'));

// vectors.json은 언어 중립으로 snake_case를 쓴다 — ts는 camelCase라 여기서 옮긴다.
const toOpts = (o) => o && {
  cols: o.cols, rows: o.rows,
  showOrigPage: o.show_orig_page, showBraillePage: o.show_braille_page,
  pageRowOn: o.page_row_on, coverPages: o.cover_pages,
  origPageStart: o.orig_page_start ?? null,
  showChangeLine: o.show_change_line ?? true,
  footerAlign: o.footer_align ?? 'center',
};

const call = {
  page_row: (a) => pageRow(a.orig_page, a.cont_idx, a.braille_page, a.footer ?? '', toOpts(a.opts)),
  page_change_line: (a) => pageChangeLine(a.orig_page, toOpts(a.opts)),
  to_brf_ascii: (a) => toBrfAscii(a.braille),
  build_pages: (a) => buildPages(a.sources, a.footer ?? '',
                                 a.start_braille_page ?? 1, toOpts(a.opts),
                                 a.footers ?? null),
  build_brf: (a) => buildBrf(a.job),
};

let total = 0, fails = 0;
for (const [fname, cases] of Object.entries(data.cases)) {
  for (const c of cases) {
    total++;
    const got = call[fname](c.args);
    // build_pages는 면 배열(2차원)이라 값 비교를 JSON으로 한다.
    const same = typeof got === 'string' ? got === c.expect
                                        : JSON.stringify(got) === JSON.stringify(c.expect);
    if (!same) {
      fails++;
      console.error(`FAIL ${fname} — ${c.name}`);
      console.error(`  got    ${JSON.stringify(got)}`);
      console.error(`  expect ${JSON.stringify(c.expect)}`);
    }
  }
}
console.log(`ts: ${total - fails}/${total} 통과${fails ? ` — 실패 ${fails}건` : ''}`);
process.exit(fails ? 1 : 0);
