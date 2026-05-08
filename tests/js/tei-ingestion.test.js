'use strict';

const { parseTeiXml, extractPlainText, alignTsvWithRefs, _isPhantom, validateTsv } = require('../../app/statics/js/tei-ingestion');

// ── Helpers ──────────────────────────────────────────────────────────────────

function tei(inner) {
  return `<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><ab>${inner}</ab></body></text></TEI>`;
}

// ── validateTsv ───────────────────────────────────────────────────────────────

describe('validateTsv', () => {
  test('returns no errors for a well-formed TSV', () => {
    const tsv = 'form\tlemma\tPOS\tmorph\nDe\tde\tPRE\tNone\nseint\tsaint\tADJqua\tNone';
    const { errors, warnings } = validateTsv(tsv);
    expect(errors).toHaveLength(0);
    expect(warnings).toHaveLength(0);
  });

  test('returns no errors/warnings for empty input', () => {
    const { errors, warnings } = validateTsv('');
    expect(errors).toHaveLength(0);
    expect(warnings).toHaveLength(0);
  });

  test('error when a row has too few columns', () => {
    const tsv = 'form\tlemma\tPOS\nDe\tde\nseint\tsaint\tADJqua';
    const { errors } = validateTsv(tsv);
    expect(errors).toHaveLength(1);
    expect(errors[0]).toMatch(/line 2/);
    expect(errors[0]).toMatch(/expected 3.*got 2/);
  });

  test('error when a row has too many columns', () => {
    const tsv = 'form\tlemma\tPOS\nDe\tde\tPRE\textra\tcol';
    const { errors } = validateTsv(tsv);
    expect(errors).toHaveLength(1);
    expect(errors[0]).toMatch(/line 2/);
    expect(errors[0]).toMatch(/expected 3.*got 5/);
  });

  test('multiple bad rows each produce an error (up to 5)', () => {
    const rows = ['form\tlemma\tPOS', 'a\tb', 'c\td', 'e\tf', 'g\th', 'i\tj'];
    const { errors } = validateTsv(rows.join('\n'));
    expect(errors).toHaveLength(5);
  });

  test('more than 5 bad rows produces a summary line', () => {
    const rows = ['form\tlemma\tPOS'];
    for (let i = 0; i < 7; i++) rows.push('a\tb');
    const { errors } = validateTsv(rows.join('\n'));
    expect(errors).toHaveLength(6); // 5 individual + 1 summary
    expect(errors[5]).toMatch(/2 more/);
  });

  test('"token" is accepted as a valid form column without warning', () => {
    const tsv = 'token\tlemma\tPOS\nDe\tde\tPRE';
    const { errors, warnings } = validateTsv(tsv);
    expect(errors).toHaveLength(0);
    expect(warnings).toHaveLength(0);
  });

  test('error when no form/token/tokens column present', () => {
    const tsv = 'lemma\tPOS\nde\tPRE';
    const { errors } = validateTsv(tsv);
    expect(errors.some(e => /mandatory/i.test(e) || /form/i.test(e))).toBe(true);
  });

  test('blank lines in data are ignored', () => {
    const tsv = 'form\tlemma\tPOS\nDe\tde\tPRE\n\nseint\tsaint\tADJqua';
    const { errors } = validateTsv(tsv);
    expect(errors).toHaveLength(0);
  });

  test('token_reference column alongside form is accepted without warning', () => {
    const tsv = 'token_reference\tform\tlemma\tPOS\nw1\tDe\tde\tPRE';
    const { errors, warnings } = validateTsv(tsv);
    expect(errors).toHaveLength(0);
    expect(warnings).toHaveLength(0);
  });
});

// ── parseTeiXml ───────────────────────────────────────────────────────────────

describe('parseTeiXml', () => {
  test('extracts <w> and <pc> in document order', () => {
    const { tokens, warnings } = parseTeiXml(
      tei('<w xml:id="w1">De</w> <pc xml:id="p1">.</pc>')
    );
    expect(tokens).toHaveLength(2);
    expect(tokens[0]).toEqual({ form: 'De', ref: 'w1' });
    expect(tokens[1]).toEqual({ form: '.', ref: 'p1' });
    expect(warnings).toHaveLength(0);
  });

  test('<w> without xml:id yields ref: null', () => {
    const { tokens } = parseTeiXml(tei('<w>seint</w>'));
    expect(tokens[0]).toEqual({ form: 'seint', ref: null });
  });

  test('mixed: some with xml:id, some without', () => {
    const { tokens } = parseTeiXml(
      tei('<w xml:id="w1">De</w><w>seint</w><pc xml:id="p1">,</pc>')
    );
    expect(tokens).toHaveLength(3);
    expect(tokens[0].ref).toBe('w1');
    expect(tokens[1].ref).toBeNull();
    expect(tokens[2].ref).toBe('p1');
  });

  test('warns when <w> carries annotation attributes', () => {
    const { warnings } = parseTeiXml(
      tei('<w xml:id="w1" lemma="de">De</w>')
    );
    expect(warnings.length).toBeGreaterThan(0);
    expect(warnings[0]).toMatch(/lemma/);
  });

  test('warns on pos, msd, ana attributes', () => {
    const { warnings } = parseTeiXml(
      tei('<w xml:id="w1" pos="PRE" msd="x" ana="#a">De</w>')
    );
    expect(warnings.length).toBe(3);
  });

  test('ignores <w> outside <body> (e.g. in teiHeader)', () => {
    const xml = `<TEI xmlns="http://www.tei-c.org/ns/1.0">
      <teiHeader><fileDesc><titleStmt>
        <title><w xml:id="h1">Title</w></title>
      </titleStmt></fileDesc></teiHeader>
      <text><body><ab>
        <w xml:id="w1">De</w><pc xml:id="p1">.</pc>
      </ab></body></text>
    </TEI>`;
    const { tokens } = parseTeiXml(xml);
    expect(tokens).toHaveLength(2);
    expect(tokens[0].ref).toBe('w1');
    expect(tokens[1].ref).toBe('p1');
  });

  test('finds <w> and <pc> deeply nested inside <div><ab><l>', () => {
    const xml = `<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body>
      <div><ab><l><w xml:id="w1">foo</w><pc xml:id="p1">.</pc></l></ab></div>
    </body></text></TEI>`;
    const { tokens } = parseTeiXml(xml);
    expect(tokens).toHaveLength(2);
    expect(tokens[0].ref).toBe('w1');
    expect(tokens[1].ref).toBe('p1');
  });

  test('<pc> element is included alongside <w>', () => {
    const { tokens } = parseTeiXml(
      tei('<w xml:id="w1">Martin</w><pc xml:id="p1">,</pc><w xml:id="w2">mout</w>')
    );
    expect(tokens).toHaveLength(3);
    expect(tokens[1]).toEqual({ form: ',', ref: 'p1' });
  });
});

// ── extractPlainText ─────────────────────────────────────────────────────────

describe('extractPlainText', () => {
  test('joins forms with a single space', () => {
    const tokens = [
      { form: 'De', ref: 'w1' },
      { form: 'seint', ref: 'w2' },
      { form: 'Martin', ref: 'w3' },
    ];
    expect(extractPlainText(tokens)).toBe('De seint Martin');
  });

  test('single token', () => {
    expect(extractPlainText([{ form: 'foo', ref: null }])).toBe('foo');
  });

  test('includes <pc> forms', () => {
    const tokens = [
      { form: 'De', ref: 'w1' },
      { form: ',', ref: 'p1' },
      { form: 'Martin', ref: 'w2' },
    ];
    expect(extractPlainText(tokens)).toBe('De , Martin');
  });
});

// ── alignTsvWithRefs — exact path ─────────────────────────────────────────────

describe('alignTsvWithRefs — exact alignment', () => {
  const xmlTokens = [
    { form: 'De', ref: 'w1' },
    { form: 'seint', ref: 'w2' },
    { form: '.', ref: 'p1' },
  ];

  test('prepends token_reference column when refs present', () => {
    const tsv = 'form\tlemma\tPOS\nDe\tde\tPRE\nseint\tsaint\tADJqua\n.\t.\tPUN';
    const { tsv: out, method, error } = alignTsvWithRefs(tsv, xmlTokens);
    expect(error).toBeNull();
    expect(method).toBe('exact');
    const lines = out.split('\n');
    expect(lines[0]).toBe('token_reference\tform\tlemma\tPOS');
    expect(lines[1]).toBe('w1\tDe\tde\tPRE');
    expect(lines[2]).toBe('w2\tseint\tsaint\tADJqua');
    expect(lines[3]).toBe('p1\t.\t.\tPUN');
  });

  test('no token_reference column when all refs are null', () => {
    const noRefTokens = [
      { form: 'De', ref: null },
      { form: 'seint', ref: null },
      { form: '.', ref: null },
    ];
    const tsv = 'form\tlemma\tPOS\nDe\tde\tPRE\nseint\tsaint\tADJqua\n.\t.\tPUN';
    const { tsv: out, method } = alignTsvWithRefs(tsv, noRefTokens);
    expect(method).toBe('exact');
    expect(out.split('\n')[0]).toBe('form\tlemma\tPOS');
  });

  test('partial refs: null ref becomes empty string in token_reference column', () => {
    const mixedTokens = [
      { form: 'De', ref: 'w1' },
      { form: 'seint', ref: null },
      { form: '.', ref: 'p1' },
    ];
    const tsv = 'form\tlemma\tPOS\nDe\tde\tPRE\nseint\tsaint\tADJqua\n.\t.\tPUN';
    const { tsv: out } = alignTsvWithRefs(tsv, mixedTokens);
    const lines = out.split('\n');
    expect(lines[0]).toMatch(/^token_reference/);
    expect(lines[2]).toMatch(/^\t/); // empty ref for seint
  });

  test('lemmatizer with only form+lemma+POS (no morph) still aligns', () => {
    const tsv = 'form\tlemma\tPOS\nDe\tde\tPRE\nseint\tsaint\tADJqua\n.\t.\tPUN';
    const { tsv: out, error } = alignTsvWithRefs(tsv, xmlTokens);
    expect(error).toBeNull();
    expect(out.split('\n')[0]).toBe('token_reference\tform\tlemma\tPOS');
  });
});

// ── alignTsvWithRefs — character alignment path ───────────────────────────────

describe('alignTsvWithRefs — character alignment', () => {
  test('lemmatizer merges <w> and <pc> into one row', () => {
    // XML: "seint" + "," → 2 tokens; TSV: "seint," → 1 row
    const xml = [
      { form: 'seint', ref: 'w1' },
      { form: ',', ref: 'p1' },
    ];
    const tsv = 'form\tlemma\tPOS\nseint,\tseint\tNOMpro';
    const { tsv: out, method } = alignTsvWithRefs(tsv, xml);
    expect(method).toBe('char');
    const lines = out.split('\n');
    // merged row gets ref of first XML token
    expect(lines[1]).toMatch(/^w1\t/);
  });

  test('lemmatizer splits one <w> into two rows → _2 suffix (same chars)', () => {
    // XML has "seintMartin" as one token; lemmatizer splits on the word boundary
    // Both produce the same 11 chars → clean char alignment
    const xml = [{ form: 'seintMartin', ref: 'w1' }, { form: '.', ref: 'p1' }];
    const tsv = 'form\tlemma\tPOS\nseint\tsaint\tADJqua\nMartin\tmartin\tNOMpro\n.\t.\tPUN';
    const { tsv: out, method, warning } = alignTsvWithRefs(tsv, xml);
    expect(method).toBe('char');
    expect(warning).toBeNull(); // chars match exactly
    const lines = out.split('\n');
    expect(lines[1]).toMatch(/^w1\t/);    // first split keeps original id
    expect(lines[2]).toMatch(/^w1_2\t/);  // second split gets _2
    expect(lines[3]).toMatch(/^p1\t/);    // pc aligns cleanly
  });

  test('triple split of one token gives _2 and _3 suffixes', () => {
    // XML: "foo" (3 chars) → TSV: "f", "o", "o" (3 rows)
    const xml = [{ form: 'foo', ref: 'w3' }];
    const tsv = 'form\tlemma\tPOS\nf\tf\tX\no\to\tX\no\to\tX';
    const { tsv: out } = alignTsvWithRefs(tsv, xml);
    const lines = out.split('\n');
    expect(lines[1]).toMatch(/^w3\t/);
    expect(lines[2]).toMatch(/^w3_2\t/);
    expect(lines[3]).toMatch(/^w3_3\t/);
  });

  test('<pc> with xml:id aligns correctly', () => {
    const xml = [{ form: 'De', ref: 'w1' }, { form: '.', ref: 'p1' }];
    // Different count: TSV has 3 rows (De split into D + e, then .)
    const tsv = 'form\tlemma\tPOS\nD\tD\tX\ne\te\tX\n.\t.\tPUN';
    const { tsv: out, method } = alignTsvWithRefs(tsv, xml);
    expect(method).toBe('char');
    const lines = out.split('\n');
    expect(lines[1]).toMatch(/^w1\t/);
    expect(lines[2]).toMatch(/^w1_2\t/);
    expect(lines[3]).toMatch(/^p1\t/);
  });

  test('partial mismatch: best-effort still returns TSV (not null)', () => {
    // Row count differs (3 TSV rows vs 2 XML tokens) so char alignment runs.
    // "ab"+"Cd" vs "a"+"b"+"Cd" — 'C' ≠ 'c' at position 2, but walk continues.
    const xml = [{ form: 'ab', ref: 'w1' }, { form: 'cd', ref: 'w2' }];
    const tsv = 'form\tlemma\tPOS\na\ta\tX\nb\tb\tX\nCd\tCd\tX';
    const { tsv: out, error, warning } = alignTsvWithRefs(tsv, xml);
    // Not null — best-effort
    expect(out).not.toBeNull();
    expect(error).toBeNull();
    expect(warning).toMatch(/mismatch/i);
    const lines = out.split('\n');
    // "ab" split into "a" (w1) and "b" (w1_2)
    expect(lines[1]).toMatch(/^w1\t/);
    expect(lines[2]).toMatch(/^w1_2\t/);
    // "Cd" aligns to w2 despite the case mismatch
    expect(lines[3]).toMatch(/^w2\t/);
  });
});

// ── Phantom token handling ────────────────────────────────────────────────────

describe('_isPhantom', () => {
  test('detects curly-brace-wrapped forms', () => {
    expect(_isPhantom('{saisine}')).toBe(true);
    expect(_isPhantom('{ne2}')).toBe(true);
  });

  test('returns false for normal forms', () => {
    expect(_isPhantom('saisine')).toBe(false);
    expect(_isPhantom('')).toBe(false);
    expect(_isPhantom(undefined)).toBe(false);
  });
});

describe('alignTsvWithRefs — phantom tokens', () => {
  test('phantom row gets empty ref and does not shift alignment', () => {
    // Mirrors the real-world case: XML has simpliciter/w121 saisine/w122 ad/w123
    // Lemmatizer inserts {saisine} between saisine and ad
    const xml = [
      { form: 'simpliciter', ref: 'w121' },
      { form: 'saisine',     ref: 'w122' },
      { form: 'ad',          ref: 'w123' },
      { form: 'requestam',   ref: 'w124' },
    ];
    const tsv = [
      'form\tlemma\tPOS',
      'simpliciter\tsimpliciter\tADV',
      'saisine\tsaius\tNOMcom',
      '{saisine}\tne2\tADV',
      'ad\tad2\tPRE',
      'requestam\trequestus\tVER',
    ].join('\n');

    const { tsv: out, error, method } = alignTsvWithRefs(tsv, xml);
    expect(error).toBeNull();
    expect(method).toBe('char');

    const lines = out.split('\n');
    // Real tokens get their refs
    expect(lines[1]).toMatch(/^w121\t/);
    expect(lines[2]).toMatch(/^w122\t/);
    // Phantom gets an empty ref (leading tab)
    expect(lines[3]).toMatch(/^\t/);
    expect(lines[3]).toContain('{saisine}');
    // Tokens after the phantom are not shifted
    expect(lines[4]).toMatch(/^w123\t/);
    expect(lines[5]).toMatch(/^w124\t/);
  });

  test('phantom does not trigger exact alignment when counts accidentally match', () => {
    // 3 XML tokens + 3 TSV rows (1 real + 1 phantom + 1 real) — counts equal
    // but exact alignment would misassign refs; char path must be used
    const xml = [
      { form: 'A', ref: 'w1' },
      { form: 'B', ref: 'w2' },
      { form: 'C', ref: 'w3' },
    ];
    const tsv = [
      'form\tlemma\tPOS',
      'A\ta\tX',
      '{A}\tghost\tX',
      'B\tb\tX',
      'C\tc\tX',
    ].join('\n');

    const { tsv: out, method } = alignTsvWithRefs(tsv, xml);
    // 4 rows vs 3 xml tokens → char alignment
    expect(method).toBe('char');
    const lines = out.split('\n');
    expect(lines[1]).toMatch(/^w1\t/);
    expect(lines[2]).toMatch(/^\t/);   // phantom: empty ref
    expect(lines[3]).toMatch(/^w2\t/);
    expect(lines[4]).toMatch(/^w3\t/);
  });

  test('multiple phantoms are all skipped', () => {
    const xml = [{ form: 'hello', ref: 'w1' }, { form: 'world', ref: 'w2' }];
    const tsv = [
      'form\tlemma\tPOS',
      'hello\thello\tX',
      '{ghost1}\tg1\tX',
      '{ghost2}\tg2\tX',
      'world\tworld\tX',
    ].join('\n');

    const { tsv: out, method } = alignTsvWithRefs(tsv, xml);
    expect(method).toBe('char');
    const lines = out.split('\n');
    expect(lines[1]).toMatch(/^w1\t/);
    expect(lines[2]).toMatch(/^\t/);
    expect(lines[3]).toMatch(/^\t/);
    expect(lines[4]).toMatch(/^w2\t/);
  });
});

// ── Round-trip integration tests ─────────────────────────────────────────────

describe('round-trip: parseTeiXml → alignTsvWithRefs', () => {
  test('exact alignment with <w> and <pc>, partial lemmatizer response', () => {
    const xml = tei(
      '<w xml:id="w1">De</w>' +
      '<w xml:id="w2">seint</w>' +
      '<pc xml:id="p1">,</pc>' +
      '<w xml:id="w3">Martin</w>'
    );

    const { tokens } = parseTeiXml(xml);
    expect(tokens).toHaveLength(4);
    expect(tokens[2]).toEqual({ form: ',', ref: 'p1' });

    // Mock lemmatizer: returns form+lemma+POS only (no morph column)
    const mockTsv = [
      'form\tlemma\tPOS',
      'De\tde\tPRE',
      'seint\tsaint\tADJqua',
      ',\t,\tPUN',
      'Martin\tmartin\tNOMpro',
    ].join('\n');

    const { tsv, error, method } = alignTsvWithRefs(mockTsv, tokens);
    expect(error).toBeNull();
    expect(method).toBe('exact');

    const lines = tsv.split('\n');
    expect(lines[0]).toBe('token_reference\tform\tlemma\tPOS');
    expect(lines[1]).toBe('w1\tDe\tde\tPRE');
    expect(lines[2]).toBe('w2\tseint\tsaint\tADJqua');
    expect(lines[3]).toBe('p1\t,\t,\tPUN');
    expect(lines[4]).toBe('w3\tMartin\tmartin\tNOMpro');
  });

  test('char alignment: lemmatizer splits <w> on word boundary → _2 suffix, <pc> aligns cleanly', () => {
    // XML has "seintMartin" as one token; lemmatizer splits at the word boundary.
    // Same characters, different cut → clean char alignment, no warning.
    const xml = tei('<w xml:id="w1">seintMartin</w><pc xml:id="p1">.</pc>');
    const { tokens } = parseTeiXml(xml);
    expect(tokens).toHaveLength(2);

    const mockTsv = [
      'form\tlemma\tPOS',
      'seint\tsaint\tADJqua',
      'Martin\tmartin\tNOMpro',
      '.\t.\tPUN',
    ].join('\n');

    const { tsv, method, warning } = alignTsvWithRefs(mockTsv, tokens);
    expect(method).toBe('char');
    expect(warning).toBeNull();

    const lines = tsv.split('\n');
    expect(lines[1]).toMatch(/^w1\t/);   // first split keeps w1
    expect(lines[2]).toMatch(/^w1_2\t/); // second split → w1_2
    expect(lines[3]).toMatch(/^p1\t/);   // pc aligns to p1
  });

  test('extractPlainText output is space-separated', () => {
    const xml = tei('<w xml:id="w1">De</w><pc xml:id="p1">,</pc><w xml:id="w2">Martin</w>');
    const { tokens } = parseTeiXml(xml);
    expect(extractPlainText(tokens)).toBe('De , Martin');
  });
});
