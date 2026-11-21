// All table access goes through here. Nothing else in the app knows the data source.
import Papa from 'papaparse';
import { config } from './config.js';

const NUMERIC = ['tokens_in', 'tokens_out', 'est_cost_usd', 'latency_ms'];

function normaliseRuns(rows) {
  return rows.map((r) => {
    const out = { ...r };
    for (const k of NUMERIC) out[k] = Number(r[k]) || 0;
    return out;
  });
}

async function fromCsv(url) {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error(`Could not load ${url} (${res.status})`);
  const text = await res.text();
  return Papa.parse(text, { header: true, skipEmptyLines: true }).data;
}

async function fromSupabase(table) {
  const { url, anonKey } = config.supabase;
  if (!url || !anonKey) throw new Error('Supabase selected but VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY are not set.');
  const res = await fetch(`${url}/rest/v1/${table}?select=*`, {
    headers: { apikey: anonKey, Authorization: `Bearer ${anonKey}` },
  });
  if (!res.ok) throw new Error(`Supabase ${table}: ${res.status}`);
  return res.json();
}

async function loadTable(table) {
  switch (config.dataSource) {
    case 'supabase':
      return fromSupabase(table);
    case 'dataverse':
      // Direct Dataverse access from a public browser page needs OAuth and would expose your tenant.
      // Export the tables to CSV instead and use DATA_SOURCE=csv.
      throw new Error('Dataverse: export agent_runs and email_drafts to CSV, drop them in dashboard/public/data, and set VITE_DATA_SOURCE=csv.');
    case 'csv':
    default:
      return fromCsv(table === 'agent_runs' ? config.csv.agentRuns : config.csv.emailDrafts);
  }
}

export async function loadAll() {
  const [runs, drafts] = await Promise.all([loadTable('agent_runs'), loadTable('email_drafts')]);
  return { runs: normaliseRuns(runs), drafts };
}
