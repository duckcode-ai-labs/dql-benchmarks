// Render the W2 project's modeling (entities, keys, certified relationships) and metric definitions
// as compact text: the same knowledge DQL's W2 level has, given to the agent baseline as context.
// node insurance/contexts/render-modeling.cjs <W2 project dir> > insurance/contexts/w2-modeling.txt
// (needs js-yaml on NODE_PATH)
const fs = require('fs'); const path = require('path'); const yaml = require('js-yaml');
const dir = process.argv[2];
const walk = (d) => fs.readdirSync(d, { withFileTypes: true }).flatMap((e) => e.isDirectory() ? walk(path.join(d, e.name)) : [path.join(d, e.name)]);
const out = [];
out.push('# Business model of this warehouse (entities, keys, relationships) and the approved metric definitions');
for (const f of walk(path.join(dir, 'domains')).filter((f) => f.endsWith('.dql.yaml')).sort()) {
  const d = yaml.load(fs.readFileSync(f, 'utf8'));
  if (!d?.entities && !d?.relationships) continue;
  out.push(`\n## Area: ${d.area?.name ?? path.basename(f)}${d.area?.description ? `\n${d.area.description}` : ''}`);
  for (const e of d.entities ?? []) out.push(`- entity ${e.id} = ${e.relation}; grain ${e.grain}; keys ${(e.keys ?? []).join(', ')}${e.business_context ? `\n  ${String(e.business_context).replace(/\s+/g, ' ')}` : ''}`);
  for (const r of d.relationships ?? []) out.push(`- relationship ${r.from} → ${r.to} (${r.cardinality}${r.status ? `, ${r.status}` : ''}): ${(r.keys ?? []).map((k) => `${r.from}.${k.from} = ${r.to}.${k.to}`).join(' AND ')}${r.description ? ` — ${r.description}` : ''}`);
}
const sl = path.join(dir, 'semantic-layer');
const list = (sub) => fs.existsSync(path.join(sl, sub)) ? walk(path.join(sl, sub)).filter((f) => f.endsWith('.yaml')).sort().map((f) => yaml.load(fs.readFileSync(f, 'utf8'))) : [];
out.push('\n## Approved measures');
for (const m of list('measures')) out.push(`- ${m.name}: ${m.agg}(${m.expr}) over ${m.table}${m.description ? ` — ${m.description}` : ''}`);
out.push('\n## Approved dimensions (computed ones, as used by metric filters)');
for (const d of list('dimensions').filter((d) => d.expr && !/^[A-Za-z_][A-Za-z0-9_]*$/.test(String(d.expr).trim()))) out.push(`- ${d.cube ?? ''}__${d.name}: ${String(d.expr).replace(/\s+/g, ' ')}${d.table ? ` over ${d.table}` : ''}`);
out.push('\n## Approved metrics');
for (const m of list('metrics')) {
  const tp = m.typeParams ?? {};
  const how = m.sql ? m.sql : tp.numerator ? `${JSON.stringify(tp.numerator)} / ${JSON.stringify(tp.denominator)}` : tp.expr ?? '';
  const wf = [...(m.filter?.where_filters ?? []), ...(tp.measure?.filter?.where_filters ?? [])].map((w) => String(w.where_sql_template).trim());
  const filter = wf.length ? ` where ${wf.join(' AND ')}` : '';
  out.push(`- ${m.name} (${m.metricType ?? m.type}): ${how}${filter}${m.table ? ` over ${m.table}` : ''}${m.description ? ` — ${m.description}` : ''}`);
}
process.stdout.write(out.join('\n') + '\n');
