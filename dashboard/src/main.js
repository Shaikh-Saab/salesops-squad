import Chart from 'chart.js/auto';
import QRCode from 'qrcode';
import './style.css';
import { config, riskScore, riskLevel } from './config.js';
import { loadAll } from './data.js';

const AGENTS = ['SalesOps Lead', 'Lead Research Agent', 'Quote Agent', 'Follow-up Agent'];
const OUTCOMES = ['success', 'escalated', 'failed'];
const OUTCOME_VAR = { success: '--good', escalated: '--warning', failed: '--critical' };
const OUTCOME_ICON = { success: '✓', escalated: '!', failed: '✕' };

const $ = (id) => document.getElementById(id);
const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const usd = (n, d = 4) => `$${n.toFixed(d)}`;
const fmtTime = (iso) => new Date(iso).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

const badge = (o) => `<span class="badge ${o}"><span aria-hidden="true">${OUTCOME_ICON[o] || ''}</span> ${esc(o)}</span>`;
const riskBadge = (lvl) => `<span class="risk ${lvl}">${lvl}</span>`;

function table(headers, rows) {
  return `<table><thead><tr>${headers.map((h) => `<th>${h}</th>`).join('')}</tr></thead><tbody>${
    rows.length ? rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join('')}</tr>`).join('') : `<tr><td colspan="${headers.length}" class="empty">Nothing here</td></tr>`
  }</tbody></table>`;
}

// ---- local demo approvals (per-browser only; never sent anywhere)
const STORE_KEY = 'act-demo-approvals';
function readOverrides() {
  try { return JSON.parse(localStorage.getItem(STORE_KEY) || '{}'); } catch { return {}; }
}
function writeOverrides(o) {
  try { localStorage.setItem(STORE_KEY, JSON.stringify(o)); } catch { /* storage blocked: state lives in memory only */ }
}

let state = { runs: [], drafts: [], overrides: readOverrides() };
let charts = [];

function renderTiles(runs) {
  const total = runs.length;
  const ok = runs.filter((r) => r.outcome === 'success').length;
  const avgLat = total ? runs.reduce((s, r) => s + r.latency_ms, 0) / total : 0;
  const cost = runs.reduce((s, r) => s + r.est_cost_usd, 0);
  const tiles = [
    ['Total runs', total.toLocaleString(), 'agent calls logged'],
    ['Success rate', total ? `${Math.round((ok / total) * 100)}%` : '–', `${ok} of ${total} runs`],
    ['Avg latency', `${(avgLat / 1000).toFixed(1)} s`, 'estimate'],
    ['Total est. cost', usd(cost, 2), 'simulated'],
  ];
  $('tiles').innerHTML = tiles.map(([k, v, s]) => `<div class="tile"><div class="k">${k}</div><div class="v">${v}</div><div class="s">${s}</div></div>`).join('');
}

function chartDefaults() {
  Chart.defaults.font.family = css('--font');
  Chart.defaults.color = css('--text-2');
  Chart.defaults.borderColor = css('--grid');
}

function tooltipStyle() {
  return {
    backgroundColor: css('--surface-raised'), titleColor: css('--text-1'), bodyColor: css('--text-2'),
    borderColor: css('--line'), borderWidth: 1, padding: 10, boxPadding: 4,
  };
}

function renderRunsChart(runs) {
  const data = OUTCOMES.map((o) => ({
    label: o,
    data: AGENTS.map((a) => runs.filter((r) => r.agent_name === a && r.outcome === o).length),
    backgroundColor: css(OUTCOME_VAR[o]),
    borderColor: css('--surface'),
    borderWidth: { right: 2 },
    borderSkipped: false,
    borderRadius: 4,
    barThickness: 18,
  }));
  $('legend-runs').innerHTML = OUTCOMES.map((o) => `<span class="key"><i style="background:var(${OUTCOME_VAR[o]})"></i>${OUTCOME_ICON[o]} ${o}</span>`).join('');
  charts.push(new Chart($('chart-runs'), {
    type: 'bar',
    data: { labels: AGENTS, datasets: data },
    options: {
      indexAxis: 'y', responsive: true, maintainAspectRatio: false,
      interaction: { mode: 'index', axis: 'y', intersect: false },
      plugins: { legend: { display: false }, tooltip: tooltipStyle() },
      scales: {
        x: { stacked: true, grid: { color: css('--grid') }, ticks: { precision: 0 }, title: { display: true, text: 'Runs' } },
        y: { stacked: true, grid: { display: false } },
      },
    },
  }));
  $('table-runs').innerHTML = table(['Agent', ...OUTCOMES, 'Total'], AGENTS.map((a, i) => {
    const counts = data.map((d) => d.data[i]);
    return [esc(a), ...counts, counts.reduce((x, y) => x + y, 0)];
  }));
}

function renderCostChart(runs) {
  const rows = AGENTS.map((a) => {
    const ok = runs.filter((r) => r.agent_name === a && r.outcome === 'success');
    const sum = ok.reduce((s, r) => s + r.est_cost_usd, 0);
    return { agent: a, n: ok.length, per: ok.length ? sum / ok.length : 0 };
  });
  charts.push(new Chart($('chart-cost'), {
    type: 'bar',
    data: { labels: AGENTS, datasets: [{ label: 'Est. cost per successful run (USD, simulated)', data: rows.map((r) => r.per), backgroundColor: css('--accent'), borderRadius: 4, barThickness: 18 }] },
    options: {
      indexAxis: 'y', responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { ...tooltipStyle(), callbacks: { label: (c) => ` ${usd(c.parsed.x)} per run (simulated, ${rows[c.dataIndex].n} runs)` } },
      },
      scales: {
        x: { grid: { color: css('--grid') }, ticks: { callback: (v) => `$${Number(v).toFixed(3)}` }, title: { display: true, text: 'USD per successful run (estimate)' } },
        y: { grid: { display: false } },
      },
    },
  }));
  $('table-cost').innerHTML = table(['Agent', 'Successful runs', 'Est. cost / run'], rows.map((r) => [esc(r.agent), r.n, usd(r.per)]));
}

function renderQueue() {
  const drafts = state.drafts.map((d) => ({ ...d, status: state.overrides[d.draft_id] || d.status }));
  const pending = drafts.filter((d) => d.status === 'pending');
  const decided = drafts.filter((d) => state.overrides[d.draft_id]);
  $('queue-count').textContent = pending.length;
  $('queue').innerHTML = (pending.length ? pending.map((d) => `
    <article class="draft">
      <div class="draft-head"><strong>${esc(d.subject)}</strong><span class="mono">${esc(d.draft_id)} · ${esc(d.account_id)}</span></div>
      <p>${esc(d.body)}</p>
      <div class="actions">
        <button class="btn primary" data-act="approved" data-id="${esc(d.draft_id)}">Approve (demo)</button>
        <button class="btn" data-act="rejected" data-id="${esc(d.draft_id)}">Reject (demo)</button>
      </div>
    </article>`).join('') : '<p class="empty">No drafts waiting. Every customer email has a human decision.</p>')
    + (decided.length ? `<p class="hint">Decided in this browser: ${decided.map((d) => `${esc(d.draft_id)} → ${esc(d.status)}`).join(', ')} · <button class="link" id="reset-demo">reset demo</button></p>` : '');
}

function renderRisk(runs) {
  const flagged = runs
    .filter((r) => (r.touched_customer_data === 'yes' && r.approved_by_human === 'no') || r.outcome === 'escalated' || r.outcome === 'failed')
    .map((r) => ({ ...r, score: riskScore(r) }))
    .sort((a, b) => b.score - a.score || b.timestamp.localeCompare(a.timestamp));
  $('risk-count').textContent = flagged.length;
  $('risk').innerHTML = table(['Risk', 'Agent', 'Request', 'Outcome', 'Approved'], flagged.map((r) => [
    `${riskBadge(riskLevel(r.score))} <span class="mono">${r.score}</span>`, esc(r.agent_name), `<span class="req">${esc(r.user_request)}</span>`, badge(r.outcome), esc(r.approved_by_human),
  ]));
}

function renderRecent(runs) {
  const last = [...runs].sort((a, b) => b.timestamp.localeCompare(a.timestamp)).slice(0, 20);
  $('recent').innerHTML = table(['Time', 'Request', 'Agent', 'Tools called', 'Outcome', 'Est. cost', 'Latency', 'Risk'], last.map((r) => {
    const s = riskScore(r);
    return [
      `<span class="mono nowrap">${esc(fmtTime(r.timestamp))}</span>`, `<span class="req">${esc(r.user_request)}</span>`, esc(r.agent_name),
      `<span class="mono small">${esc(r.tools_called)}</span>`, badge(r.outcome), `<span class="mono">${usd(r.est_cost_usd)}</span>`,
      `<span class="mono">${(r.latency_ms / 1000).toFixed(1)} s</span>`, riskBadge(riskLevel(s)),
    ];
  }));
}

async function renderShare() {
  const url = window.location.href.split('#')[0];
  $('share-url').textContent = url;
  try {
    await QRCode.toCanvas($('share-qr'), url, { width: 160, margin: 1, color: { dark: '#0b0b0b', light: '#ffffff' } });
  } catch { $('share-qr').remove(); }
}

function renderAll() {
  charts.forEach((c) => c.destroy());
  charts = [];
  chartDefaults();
  renderTiles(state.runs);
  renderRunsChart(state.runs);
  renderCostChart(state.runs);
  renderQueue();
  renderRisk(state.runs);
  renderRecent(state.runs);
}

document.addEventListener('click', (e) => {
  const b = e.target.closest('[data-act]');
  if (b) {
    state.overrides[b.dataset.id] = b.dataset.act;
    writeOverrides(state.overrides);
    renderQueue();
  }
  if (e.target.id === 'reset-demo') {
    state.overrides = {};
    writeOverrides({});
    renderQueue();
  }
});

window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => state.runs.length && renderAll());

async function start() {
  $('source').textContent = `Data source: ${config.dataSource}`;
  renderShare();
  try {
    const { runs, drafts } = await loadAll();
    state.runs = runs;
    state.drafts = drafts;
    renderAll();
  } catch (err) {
    $('app').insertAdjacentHTML('afterbegin', `<div class="error" role="alert"><strong>Could not load data.</strong> ${esc(err.message)}</div>`);
  }
}

start();
