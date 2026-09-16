import { resolveDqlCli, dqlVersion } from '../lib/dql.mjs';

const cli = resolveDqlCli();
console.log(`DQL ${dqlVersion(cli)} (${cli.source}: ${cli.entry})`);
