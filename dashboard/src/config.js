// The ONE place that decides where data comes from and how simulated metrics are computed.
// Switching data source is a settings change (VITE_DATA_SOURCE in the root .env), not a rewrite.

const env = import.meta.env;

export const config = {
  // csv | supabase | dataverse
  dataSource: (env.VITE_DATA_SOURCE || 'csv').toLowerCase(),

  csv: {
    // Files live in dashboard/public/data (written by seed/generate_data.py, or a Dataverse CSV export).
    agentRuns: `${env.BASE_URL}data/agent_runs.csv`,
    emailDrafts: `${env.BASE_URL}data/email_drafts.csv`,
  },

  supabase: {
    url: env.VITE_SUPABASE_URL || '',
    anonKey: env.VITE_SUPABASE_ANON_KEY || '', // public anon key only; protect tables with RLS
  },

  // Cost model ASSUMPTIONS (USD per 1,000 tokens). Not Microsoft billing.
  prices: { inputPer1k: 0.003, outputPer1k: 0.015 },

  // Agents whose actions reach a customer (used by the risk rule).
  customerFacingAgents: ['Follow-up Agent'],
};

// Risk score: simple and explainable. Shown on the page as well.
export function riskScore(run) {
  let s = 0;
  if (run.touched_customer_data === 'yes') s += 2;
  if (run.approved_by_human === 'no' && config.customerFacingAgents.includes(run.agent_name)) s += 3;
  if (run.outcome === 'failed' || run.outcome === 'escalated') s += 1;
  return s;
}

export function riskLevel(score) {
  if (score >= 4) return 'high';
  if (score >= 2) return 'medium';
  return 'low';
}
