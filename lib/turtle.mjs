// A small Turtle reader for the benchmark question files.
//
// data.world's and dbt Labs' question files use a plain subset of Turtle:
// @prefix lines, prefixed names and <IRIs>, "strings" (and """long strings"""),
// the keyword `a`, and the `;` `,` `.` separators. That subset is read here so
// the harness needs no RDF library. Anything outside it (blank nodes, typed or
// language-tagged literals, collections) is refused rather than guessed at.

const ESCAPES = { t: '\t', b: '\b', n: '\n', r: '\r', f: '\f', '"': '"', "'": "'", '\\': '\\' };

function tokenize(text) {
  const tokens = [];
  let i = 0;
  const fail = (message) => {
    const line = text.slice(0, i).split('\n').length;
    throw new Error(`Turtle line ${line}: ${message}`);
  };
  while (i < text.length) {
    const ch = text[i];
    if (/\s/.test(ch)) { i += 1; continue; }
    if (ch === '#') { while (i < text.length && text[i] !== '\n') i += 1; continue; }
    if (ch === ';' || ch === ',' || ch === '.') { tokens.push({ kind: 'punct', value: ch }); i += 1; continue; }
    if (ch === '<') {
      const end = text.indexOf('>', i);
      if (end === -1) fail('unterminated IRI');
      tokens.push({ kind: 'iri', value: text.slice(i + 1, end) });
      i = end + 1;
      continue;
    }
    if (ch === '"' || ch === "'") {
      const long = text.startsWith(ch.repeat(3), i);
      const quote = long ? ch.repeat(3) : ch;
      i += quote.length;
      let value = '';
      for (;;) {
        if (i >= text.length) fail('unterminated string');
        if (text.startsWith(quote, i)) { i += quote.length; break; }
        const c = text[i];
        if (c === '\\') {
          const next = text[i + 1];
          if (next === 'u' || next === 'U') {
            const width = next === 'u' ? 4 : 8;
            value += String.fromCodePoint(parseInt(text.slice(i + 2, i + 2 + width), 16));
            i += 2 + width;
            continue;
          }
          if (!(next in ESCAPES)) fail(`unknown escape \\${next}`);
          value += ESCAPES[next];
          i += 2;
          continue;
        }
        if (!long && c === '\n') fail('newline inside a short string');
        value += c;
        i += 1;
      }
      if (text[i] === '@' || text.startsWith('^^', i)) fail('typed or language-tagged literals are not supported');
      tokens.push({ kind: 'literal', value });
      continue;
    }
    if (ch === '[' || ch === '(') fail('blank nodes and collections are not supported');
    const match = /^[^\s;,<>"']+/.exec(text.slice(i));
    if (!match) fail(`unexpected character ${JSON.stringify(ch)}`);
    let word = match[0];
    // A name never ends with '.', so a trailing '.' is the statement terminator.
    if (word.endsWith('.') && word !== '.') word = word.slice(0, -1);
    tokens.push({ kind: 'word', value: word });
    i += word.length;
  }
  return tokens;
}

/** Parse Turtle text into triples of full IRIs and literal values. */
export function parseTurtle(text) {
  const tokens = tokenize(text);
  const prefixes = new Map();
  const triples = [];
  let position = 0;
  const next = () => tokens[position++];
  const peek = () => tokens[position];
  const expectPunct = (value) => {
    const token = next();
    if (!token || token.kind !== 'punct' || token.value !== value) {
      throw new Error(`Turtle: expected "${value}", found ${token ? JSON.stringify(token.value) : 'end of file'}`);
    }
  };
  const resolve = (token, { allowLiteral }) => {
    if (!token) throw new Error('Turtle: unexpected end of file');
    if (token.kind === 'iri') return { type: 'iri', value: token.value };
    if (token.kind === 'literal') {
      if (!allowLiteral) throw new Error(`Turtle: a literal cannot be a subject or predicate (${token.value.slice(0, 40)})`);
      return { type: 'literal', value: token.value };
    }
    if (token.kind === 'word') {
      if (token.value === 'a') return { type: 'iri', value: 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type' };
      const colon = token.value.indexOf(':');
      if (colon === -1) throw new Error(`Turtle: ${token.value} is not a prefixed name`);
      const prefix = token.value.slice(0, colon);
      if (!prefixes.has(prefix)) throw new Error(`Turtle: undeclared prefix "${prefix}:"`);
      return { type: 'iri', value: prefixes.get(prefix) + token.value.slice(colon + 1) };
    }
    throw new Error(`Turtle: unexpected "${token.value}"`);
  };

  while (position < tokens.length) {
    const token = peek();
    if (token.kind === 'word' && (token.value === '@prefix' || token.value.toUpperCase() === 'PREFIX')) {
      const sparqlStyle = token.value !== '@prefix';
      next();
      const name = next();
      const iri = next();
      if (name?.kind !== 'word' || !name.value.endsWith(':') || iri?.kind !== 'iri') {
        throw new Error('Turtle: malformed prefix declaration');
      }
      prefixes.set(name.value.slice(0, -1), iri.value);
      if (!sparqlStyle) expectPunct('.');
      continue;
    }
    const subject = resolve(next(), { allowLiteral: false });
    for (;;) {
      const predicate = resolve(next(), { allowLiteral: false });
      for (;;) {
        const object = resolve(next(), { allowLiteral: true });
        triples.push({ subject: subject.value, predicate: predicate.value, object });
        if (peek()?.kind === 'punct' && peek().value === ',') { next(); continue; }
        break;
      }
      const separator = next();
      if (separator?.kind !== 'punct') throw new Error('Turtle: expected ";" or "."');
      if (separator.value === '.') break;
      if (separator.value !== ';') throw new Error(`Turtle: unexpected "${separator.value}"`);
      // A trailing ';' before '.' is allowed.
      if (peek()?.kind === 'punct' && peek().value === '.') { next(); break; }
    }
  }
  return { prefixes: Object.fromEntries(prefixes), triples };
}

/** Group triples by subject: { subject: { predicate: [objects] } }. */
export function subjects(triples) {
  const out = new Map();
  for (const { subject, predicate, object } of triples) {
    if (!out.has(subject)) out.set(subject, new Map());
    const predicates = out.get(subject);
    if (!predicates.has(predicate)) predicates.set(predicate, []);
    predicates.get(predicate).push(object);
  }
  return out;
}
