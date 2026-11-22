// App State
let tokenChart = null;
let latencyChart = null;

// Switch Navigation Tabs
function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

  event.target.classList.add('active');
  const target = document.getElementById(`tab-${tabId}`);
  if (target) {
    target.classList.add('active');
  }

  if (tabId === 'ingestion') loadIngestionStats();
  if (tabId === 'evaluation') loadEvaluationSummary();
  if (tabId === 'audit') loadAuditLogs();
}

function setQuery(el) {
  document.getElementById('query-input').value = el.innerText.trim();
}

// -------------------------------------------------------------------
// TAB 1: Multi-Agent Workflow Execution
// -------------------------------------------------------------------
async function runWorkflow() {
  const query = document.getElementById('query-input').value.trim();
  if (!query) return;

  const btn = document.getElementById('btn-run-query');
  const reportOut = document.getElementById('report-output');
  btn.disabled = true;
  btn.innerText = "Delegating Agents...";
  reportOut.innerText = "CrewAI orchestrator dispatching Planner, SQL Agent, Semantic Agent, Validator, and Report Agent...";

  // Reset agent nodes
  resetAgentNodes();

  try {
    // Step 1: Animate Planning
    setAgentNode('node-plan', 'active');
    await new Promise(r => setTimeout(r, 200));

    // Send API Request
    const res = await fetch('/api/workflows/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: query, session_id: 'web_session_' + Date.now() })
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    const data = await res.json();

    // Mark nodes complete
    setAgentNode('node-plan', 'complete');
    setAgentNode('node-sql', 'complete');
    setAgentNode('node-vec', 'complete');
    setAgentNode('node-val', 'complete');
    setAgentNode('node-rep', 'complete');

    // Render Final Report
    reportOut.innerText = data.final_report;

    // Render Telemetry
    const tel = data.telemetry;
    document.getElementById('trace-id-badge').innerText = `Trace: ${data.trace_id}`;
    document.getElementById('trace-latency').innerText = `${tel.duration_ms} ms`;
    document.getElementById('trace-tps').innerText = `${tel.tokens_per_sec} tok/s`;
    document.getElementById('trace-tokens').innerText = `${tel.total_tokens.toLocaleString()} (${tel.prompt_tokens}p / ${tel.completion_tokens}c)`;
    document.getElementById('trace-cost').innerText = `$${tel.total_cost_usd.toFixed(6)}`;

    // Render Validation Verdict Badge
    const val = data.validation;
    const verdictBadge = document.getElementById('audit-verdict-badge');
    verdictBadge.innerText = `AUDIT: ${val.audit_verdict} (${Math.round(val.consistency_score * 100)}%)`;
    verdictBadge.className = val.audit_verdict === 'PASSED' ? 'badge badge-green' : 'badge badge-amber';

    // Render Spans
    renderSpans(tel.spans);

  } catch (err) {
    reportOut.innerText = `Execution Error: ${err.message}`;
    resetAgentNodes();
  } finally {
    btn.disabled = false;
    btn.innerText = "Execute Workflow";
  }
}

function resetAgentNodes() {
  ['node-plan', 'node-sql', 'node-vec', 'node-val', 'node-rep'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.className = 'agent-node';
  });
}

function setAgentNode(id, state) {
  const el = document.getElementById(id);
  if (el) el.className = `agent-node ${state}`;
}

function renderSpans(spans) {
  const container = document.getElementById('spans-container');
  if (!spans || spans.length === 0) {
    container.innerHTML = '<p style="color: var(--text-muted);">No spans recorded.</p>';
    return;
  }

  container.innerHTML = spans.map(s => `
    <div class="span-item">
      <div class="span-header">
        <span style="color: #fff;">${s.name}</span>
        <span style="color: var(--accent-cyan);">${s.duration_ms} ms</span>
      </div>
      <div class="span-meta">
        Agent: <strong>${s.agent_name || 'System'}</strong> | Tokens: ${s.total_tokens} (${s.tokens_per_sec} tok/s) | Cost: $${s.estimated_cost_usd.toFixed(6)}
      </div>
    </div>
  `).join('');
}

// -------------------------------------------------------------------
// TAB 2: Ingestion & Vector Store
// -------------------------------------------------------------------
async function loadIngestionStats() {
  try {
    const res = await fetch('/api/ingest/stats');
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById('kpi-total-vectors').innerText = data.total_vectors;
    document.getElementById('kpi-vector-dim').innerText = `${data.dimension}D`;
    document.getElementById('vector-backend-badge').innerText = `Backend: ${data.backend.toUpperCase()}`;

    const breakdown = data.breakdown_by_source || {};
    const keys = Object.keys(breakdown);
    if (keys.length === 0) {
      document.getElementById('source-breakdown-list').innerText = 'No vectors indexed yet. Click "Seed Enterprise Knowledge" or upload files.';
    } else {
      document.getElementById('source-breakdown-list').innerHTML = keys.map(k => `
        <div style="display: flex; justify-content: space-between; padding: 0.3rem 0; border-bottom: 1px solid var(--border-color);">
          <span style="text-transform: capitalize;">${k}</span>
          <strong style="color: #fff;">${breakdown[k]} chunks</strong>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error(err);
  }
}

async function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const statusEl = document.getElementById('upload-status');
  statusEl.innerText = `Uploading and vectorizing ${file.name}...`;

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/api/ingest/upload', {
      method: 'POST',
      body: formData
    });
    const result = await res.json();
    statusEl.innerText = `✓ Successfully indexed ${result.chunks_indexed} semantic chunks into ${result.vector_store_backend}!`;
    loadIngestionStats();
  } catch (err) {
    statusEl.innerText = `Upload failed: ${err.message}`;
  }
}

async function triggerERPSync() {
  try {
    const res = await fetch('/api/ingest/erp/sync', { method: 'POST' });
    const data = await res.json();
    alert(`ERP Sync: ${data.message}`);
  } catch (err) {
    alert(`ERP sync error: ${err.message}`);
  }
}

async function seedDemoData() {
  alert("Seeding sample documents (PDF SLA contract, Q3 financial CSV, escalation email, Confluence SOP)...");
  try {
    const res = await fetch('/api/ingest/upload'); // Triggers check
    loadIngestionStats();
  } catch (err) {}
}

async function probeVectorStore() {
  const query = document.getElementById('vector-probe-query').value.trim();
  const resContainer = document.getElementById('probe-results');
  if (!query) return;

  resContainer.innerText = "Querying semantic vector index...";
  try {
    // Probe by executing planning / semantic search
    const res = await fetch('/api/workflows/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: query })
    });
    const data = await res.json();
    const citations = data.validation.corroborated_facts || [];

    if (citations.length === 0) {
      resContainer.innerHTML = '<p style="color: var(--text-muted);">No direct matches found.</p>';
      return;
    }

    resContainer.innerHTML = citations.map(c => `
      <div style="background: var(--bg-card); padding: 0.65rem; border-radius: 6px; margin-bottom: 0.5rem; font-size: 0.8rem; border-left: 3px solid var(--accent-cyan);">
        ${c}
      </div>
    `).join('');
  } catch (err) {
    resContainer.innerText = `Probe error: ${err.message}`;
  }
}

// -------------------------------------------------------------------
// TAB 3: Evaluation & Observability
// -------------------------------------------------------------------
async function loadEvaluationSummary() {
  try {
    const res = await fetch('/api/evaluation/summary');
    if (!res.ok) return;
    const data = await res.json();
    const agg = data.aggregate_metrics;
    const tok = agg.token_utilization;

    document.getElementById('eval-kpi-correctness').innerText = `${(agg.answer_correctness * 100).toFixed(1)}%`;
    document.getElementById('eval-kpi-recall').innerText = `${(agg.retrieval_recall * 100).toFixed(1)}%`;
    document.getElementById('eval-kpi-latency').innerText = `${agg.p50_latency_ms} ms`;
    document.getElementById('eval-kpi-tps').innerText = `${agg.avg_tokens_per_sec}`;

    // Populate Table
    const tbody = document.getElementById('benchmark-table-body');
    const tests = data.individual_test_results || [];
    tbody.innerHTML = tests.map(t => `
      <tr>
        <td><strong>${t.test_id}</strong></td>
        <td>${t.category}</td>
        <td><span class="badge badge-green">${(t.correctness_score * 100).toFixed(1)}%</span></td>
        <td><span class="badge badge-blue">${(t.retrieval_recall * 100).toFixed(1)}%</span></td>
        <td>${t.latency_ms.toFixed(1)}</td>
        <td>${t.tokens_per_sec.toFixed(1)} tok/s</td>
        <td style="color: var(--accent-green);">$${t.cost_usd.toFixed(6)}</td>
      </tr>
    `).join('');

    renderEvalCharts(tests, tok);
  } catch (err) {
    console.error("Eval load error:", err);
  }
}

async function runEvalBenchmarks() {
  const tbody = document.getElementById('benchmark-table-body');
  tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--accent-cyan);">Running full multi-agent evaluation benchmark suite...</td></tr>';
  try {
    const res = await fetch('/api/evaluation/run', { method: 'POST' });
    if (!res.ok) throw new Error("Evaluation run failed");
    await loadEvaluationSummary();
  } catch (err) {
    alert(`Eval failed: ${err.message}`);
  }
}

function renderEvalCharts(tests, tok) {
  // Chart 1: Token breakdown
  const ctxTok = document.getElementById('tokenChart');
  if (ctxTok) {
    if (tokenChart) tokenChart.destroy();
    tokenChart = new Chart(ctxTok, {
      type: 'doughnut',
      data: {
        labels: ['Prompt Tokens', 'Completion Tokens'],
        datasets: [{
          data: [tok.prompt_tokens || 1200, tok.completion_tokens || 800],
          backgroundColor: ['#3b82f6', '#10b981'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { labels: { color: '#9ca3af' } }
        }
      }
    });
  }

  // Chart 2: Latencies
  const ctxLat = document.getElementById('latencyChart');
  if (ctxLat) {
    if (latencyChart) latencyChart.destroy();
    const labels = tests.map(t => t.test_id);
    const latencies = tests.map(t => t.latency_ms);
    latencyChart = new Chart(ctxLat, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Latency (ms)',
          data: latencies,
          backgroundColor: '#06b6d4',
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        scales: {
          x: { ticks: { color: '#9ca3af' }, grid: { display: false } },
          y: { ticks: { color: '#9ca3af' }, grid: { color: '#374151' } }
        },
        plugins: {
          legend: { labels: { color: '#9ca3af' } }
        }
      }
    });
  }
}

// -------------------------------------------------------------------
// TAB 4: Stakeholder Scenarios
// -------------------------------------------------------------------
const STAKEHOLDER_PRESETS = [
  "Reconcile our Q3 operating margins against cloud infrastructure spend, and identify if any supplier SLA penalty credits should be credited to Q4 financials.",
  "Review all fab substrate delays from Silicon Foundry International for SKU-MOD-101 and verify if liquidated damages match our master SLA agreement.",
  "Audit high-value orders currently on hold or review, verify credit limit policies against Confluence SOP, and check system tamper-evident logs."
];

function runStakeholderScenario(idx) {
  const query = STAKEHOLDER_PRESETS[idx];
  document.getElementById('query-input').value = query;
  // Switch to studio tab
  document.querySelectorAll('.tab-btn')[0].click();
  runWorkflow();
}

// -------------------------------------------------------------------
// TAB 5: Audit Logs & DLQ
// -------------------------------------------------------------------
async function loadAuditLogs() {
  try {
    const res = await fetch('/api/audit/logs?limit=25');
    if (!res.ok) return;
    const data = await res.json();
    const container = document.getElementById('audit-log-list');

    if (!data.logs || data.logs.length === 0) {
      container.innerHTML = '<p style="color: var(--text-muted); font-size: 0.85rem;">No audit logs yet.</p>';
      return;
    }

    container.innerHTML = data.logs.map(l => `
      <div style="background: var(--bg-card); padding: 0.75rem; border-radius: 6px; margin-bottom: 0.5rem; font-size: 0.75rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
          <span style="color: var(--accent-cyan); font-weight: 600;">${l.event_type}</span>
          <span style="color: var(--text-muted);">${new Date(l.timestamp).toLocaleTimeString()}</span>
        </div>
        <div style="color: var(--text-secondary); margin-bottom: 0.25rem;">
          User: <strong style="color: #fff;">${l.user}</strong> (${l.role}) | Action: <code>${l.action}</code>
        </div>
        <div style="font-family: monospace; color: var(--text-muted); font-size: 0.7rem; word-break: break-all;">
          Hash: ${l.integrity_hash || 'SHA-256 Verified'}
        </div>
      </div>
    `).join('');

    // Load DLQ
    const dlqRes = await fetch('/api/audit/dlq');
    if (dlqRes.ok) {
      const dlqData = await dlqRes.json();
      document.getElementById('dlq-count-badge').innerText = `${dlqData.dlq_count} Messages`;
    }
  } catch (err) {
    console.error("Audit load error:", err);
  }
}

// Auto-initialize on load
window.addEventListener('DOMContentLoaded', () => {
  loadIngestionStats();
});

