/**
 * TEI XML ingestion helpers for the Pyrrha corpus creation form.
 *
 * All functions are pure (no DOM side-effects beyond DOMParser) so they can
 * be imported by Jest as well as loaded as a plain browser <script>.
 */

/**
 * Parse a TEI XML string and extract every <w> and <pc> element in document
 * order, collecting their text content (form) and xml:id (ref).
 *
 * @param {string} xmlString
 * @returns {{ tokens: Array<{form: string, ref: string|null}>, warnings: string[] }}
 */
function parseTeiXml(xmlString) {
  const parser = new DOMParser();
  const doc = parser.parseFromString(xmlString, 'text/xml');

  const tokens = [];
  const warnings = [];
  const ANNOTATION_ATTRS = ['lemma', 'pos', 'msd', 'ana'];
  const XML_NS = 'http://www.w3.org/XML/1998/namespace';

  const elements = doc.querySelectorAll('body w, body pc');
  elements.forEach(el => {
    // Prefer namespace-aware lookup; fall back for parsers that flatten xml:id
    const ref =
      el.getAttributeNS(XML_NS, 'id') ||
      el.getAttribute('xml:id') ||
      null;

    const form = el.textContent.trim();

    ANNOTATION_ATTRS.forEach(attr => {
      if (el.hasAttribute(attr)) {
        warnings.push(
          `<${el.tagName}> carries a "${attr}" attribute — annotation values should not be present in the input XML`
        );
      }
    });

    tokens.push({ form, ref });
  });

  return { tokens, warnings };
}

/**
 * Build the plain-text string sent to the lemmatizer: token forms joined by a
 * single space.
 *
 * @param {Array<{form: string, ref: string|null}>} tokens
 * @returns {string}
 */
function extractPlainText(tokens) {
  return tokens.map(t => t.form).join(' ');
}

/**
 * Returns true for lemmatizer phantom tokens — forms wrapped in curly braces,
 * e.g. "{saisine}".  These are injected by some lemmatizers for disambiguation
 * and have no corresponding XML element; they must be excluded from alignment.
 *
 * @param {string|undefined} form
 * @returns {boolean}
 */
function _isPhantom(form) {
  return typeof form === 'string' && /^\{.*\}$/.test(form);
}

/**
 * Derive a token_reference for a split sub-token.
 * splitIndex 0 → original id unchanged
 * splitIndex 1 → id_2, splitIndex 2 → id_3, …
 *
 * @param {string|null} base
 * @param {number} splitIndex
 * @returns {string}
 */
function _derivedRef(base, splitIndex) {
  if (!base) return '';
  if (splitIndex === 0) return base;
  return `${base}_${splitIndex + 1}`;
}

/**
 * Align a lemmatizer TSV response with the original XML token list, adding a
 * token_reference column sourced from xml:id attributes.
 *
 * Two strategies are tried in order:
 *   1. Exact (positional): used when row count matches token count.
 *   2. Character-level: used otherwise — concatenated forms are walked
 *      char-by-char to map TSV rows onto XML tokens even when tokenisation
 *      boundaries differ.  When character strings diverge the alignment
 *      continues best-effort; unmatched rows receive an empty ref and a
 *      warning is set on the result.
 *
 * @param {string} tsvText   — raw text from the lemmatizer (header + data rows)
 * @param {Array<{form: string, ref: string|null}>} xmlTokens
 * @returns {{ tsv: string, error: string|null, method: 'exact'|'char', warning: string|null }}
 */
function alignTsvWithRefs(tsvText, xmlTokens) {
  const lines = tsvText.trimEnd().split('\n');
  if (lines.length < 1 || !lines[0].trim()) {
    return { tsv: null, error: 'TSV is empty', method: null, warning: null };
  }

  const headers = lines[0].split('\t');
  const dataRows = lines.slice(1).filter(l => l.trim()).map(line => {
    const cols = line.split('\t');
    const obj = {};
    headers.forEach((h, i) => { obj[h] = cols[i] !== undefined ? cols[i] : ''; });
    return obj;
  });

  if (dataRows.length === 0) {
    return { tsv: null, error: 'TSV has no data rows', method: null, warning: null };
  }

  const hasAnyRef = xmlTokens.some(t => t.ref);
  const formCol = headers[0];

  // Phantom rows ({form}) are injected by some lemmatizers for disambiguation.
  // They have no XML counterpart and must be excluded from alignment entirely.
  const phantomRows = new Set();
  dataRows.forEach((row, i) => { if (_isPhantom(row[formCol])) phantomRows.add(i); });

  // ── EXACT (positional) alignment ────────────────────────────────────────────
  // Only safe when no phantom rows are present (phantoms would shift refs).
  if (dataRows.length === xmlTokens.length && phantomRows.size === 0) {
    if (!hasAnyRef) {
      return { tsv: tsvText, error: null, method: 'exact', warning: null };
    }
    const newHeaders = ['token_reference', ...headers].join('\t');
    const newDataLines = dataRows.map((row, i) => {
      const ref = xmlTokens[i].ref || '';
      return [ref, ...headers.map(h => row[h])].join('\t');
    });
    return {
      tsv: [newHeaders, ...newDataLines].join('\n'),
      error: null,
      method: 'exact',
      warning: null,
    };
  }

  // ── CHARACTER-LEVEL alignment ────────────────────────────────────────────────
  // Build char runs (ignoring spaces); phantom rows are skipped in tsvRun so
  // they don't shift the alignment — they will receive an empty ref naturally.
  const xmlRun = []; // { char, tokenIdx }
  const tsvRun = []; // { char, rowIdx }

  xmlTokens.forEach((tok, idx) => {
    for (const c of tok.form.replace(/\s/g, '')) {
      xmlRun.push({ char: c, tokenIdx: idx });
    }
  });

  dataRows.forEach((row, idx) => {
    if (phantomRows.has(idx)) return;
    for (const c of (row[formCol] || '').replace(/\s/g, '')) {
      tsvRun.push({ char: c, rowIdx: idx });
    }
  });

  const len = Math.min(xmlRun.length, tsvRun.length);
  const mismatches = [];

  // rowToFirstXmlToken[rowIdx] = the first XML token index that row touches
  // xmlTokenToRows[tokenIdx]   = ordered list of TSV row indices touching that token
  const rowToFirstXmlToken = new Map();
  const xmlTokenToRows = new Map();

  for (let i = 0; i < len; i++) {
    const { char: xc, tokenIdx } = xmlRun[i];
    const { char: tc, rowIdx } = tsvRun[i];

    if (xc !== tc) {
      mismatches.push(`pos ${i}: XML '${xc}' vs TSV '${tc}'`);
    }

    // Record first xml token seen for this row
    if (!rowToFirstXmlToken.has(rowIdx)) {
      rowToFirstXmlToken.set(rowIdx, tokenIdx);
    }

    // Record rows that touch this xml token
    if (!xmlTokenToRows.has(tokenIdx)) xmlTokenToRows.set(tokenIdx, []);
    const rows = xmlTokenToRows.get(tokenIdx);
    if (!rows.includes(rowIdx)) rows.push(rowIdx);
  }

  // Assign a ref to every TSV row
  const rowRefs = new Array(dataRows.length).fill('');
  const unmatched = [];

  for (let rowIdx = 0; rowIdx < dataRows.length; rowIdx++) {
    if (!rowToFirstXmlToken.has(rowIdx)) {
      unmatched.push(rowIdx);
      continue;
    }
    const firstTokenIdx = rowToFirstXmlToken.get(rowIdx);
    const base = xmlTokens[firstTokenIdx].ref || '';
    // splitIndex = position of this row within the list of rows for that token
    const rowsForToken = xmlTokenToRows.get(firstTokenIdx) || [];
    const splitIndex = rowsForToken.indexOf(rowIdx);
    rowRefs[rowIdx] = _derivedRef(base, splitIndex);
  }

  // Rebuild TSV
  const newHeaders = hasAnyRef ? ['token_reference', ...headers] : headers;
  const newDataLines = dataRows.map((row, i) => {
    const cols = headers.map(h => row[h]);
    if (hasAnyRef) cols.unshift(rowRefs[i]);
    return cols.join('\t');
  });

  const warningParts = [];
  if (mismatches.length) warningParts.push(`Character mismatches: ${mismatches.join(', ')}`);
  if (unmatched.length) warningParts.push(`Unaligned TSV rows: ${unmatched.join(', ')}`);

  return {
    tsv: [newHeaders.join('\t'), ...newDataLines].join('\n'),
    error: null,
    method: 'char',
    warning: warningParts.length ? warningParts.join('; ') : null,
  };
}

/**
 * Validate a TSV string for structural consistency.
 *
 * Checks:
 *   - A header row is present.
 *   - Every data row has exactly the same number of columns as the header.
 *   - The first column is named "form" (warning if not).
 *
 * At most MAX_SHOWN individual bad-row messages are returned; beyond that a
 * summary line is appended instead.
 *
 * @param {string} tsvText
 * @returns {{ errors: string[], warnings: string[] }}
 */
function validateTsv(tsvText) {
  const errors   = [];
  const warnings = [];
  const MAX_SHOWN = 5;

  if (!tsvText || !tsvText.trim()) return { errors, warnings };

  const lines = tsvText.trimEnd().split('\n');
  if (!lines[0] || !lines[0].trim()) {
    errors.push('No header row found.');
    return { errors, warnings };
  }

  const headers     = lines[0].split('\t');
  const expectedCols = headers.length;

  if (headers[0] !== 'form') {
    warnings.push(
      `First column is "${headers[0]}", expected "form". ` +
      'Make sure your TSV has at least: form, lemma, POS, morph.'
    );
  }

  const badRows = [];
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];
    if (!line.trim()) continue;
    const cols = line.split('\t');
    if (cols.length !== expectedCols) {
      badRows.push(`line ${i + 1}: expected ${expectedCols} columns, got ${cols.length}`);
    }
  }

  if (badRows.length > 0) {
    const shown = badRows.slice(0, MAX_SHOWN);
    shown.forEach(msg => errors.push(msg));
    if (badRows.length > MAX_SHOWN) {
      errors.push(`… and ${badRows.length - MAX_SHOWN} more rows with inconsistent column count.`);
    }
  }

  return { errors, warnings };
}

// Dual export: CommonJS (Jest/Node) + browser global
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { parseTeiXml, extractPlainText, alignTsvWithRefs, _isPhantom, validateTsv };
}
