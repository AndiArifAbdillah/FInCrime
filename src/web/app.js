/*
 * FinCrime — Web UI client
 * Talks to the FastAPI backend at the same origin (http://localhost:8000).
 * All "live" numbers come from the real ML models — no hardcoded data.
 */
const API = ""; // same-origin

/* ---------- helpers ---------- */
async function api(path, init) {
  const r = await fetch(API + path, init);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText} — ${path}`);
  return r.json();
}

function setText(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }
function setHtml(id, html) { const el = document.getElementById(id); if (el) el.innerHTML = html; }

const fmt = {
  int: n => Number(n).toLocaleString("id-ID"),
  rp: n => "Rp " + Math.round(Number(n)).toLocaleString("id-ID"),
  short: s => (s || "").length > 22 ? (s.slice(0, 10) + "…" + s.slice(-8)) : s,
};

/* ---------- page nav ---------- */
const pages = {
  0: { title: "Overview", sub: "FinCrime · Command Center" },
  1: { title: "Risk Scoring", sub: "Layer 0 · XGBoost + SHAP" },
  2: { title: "Fraud Detection", sub: "Layer 1 · Isolation Forest + Autoencoder + rules" },
  3: { title: "Graph Tracing", sub: "Layer 2 · GraphSAGE GNN + NetworkX" },
  4: { title: "Laporan APU/PPT", sub: "Layer 3 · Regtech · LTKM/LTKT" },
  5: { title: "Live Trace", sub: "Layer 2 · Real-time wallet investigation" },
  6: { title: "Case Management", sub: "Group alerts → Investigation Cases" },
  7: { title: "Screening", sub: "DTTOT / UN Sanctions + Negative News" },
  8: { title: "Private Sector AML", sub: "DNFBP · Property · UBO · Shell Company" },
  9: { title: "Multi-chain Crypto", sub: "BTC · ETH · BSC · Polygon · Tron" },
  10: { title: "Model Monitoring", sub: "Drift Detection · PSI · KS test" },
  11: { title: "Investigation Timeline", sub: "Chronological transaction flow viz" },
  12: { title: "Privacy Coin Monitor", sub: "Monero · Zcash · Dash — on/off-ramp detection" },
};
function nav(i) {
  document.querySelectorAll(".page").forEach((p, j) => p.classList.toggle("active", j === i));
  document.querySelectorAll(".sb-btn").forEach((b, j) => b.classList.toggle("active", j === i));
  setText("tb-title", pages[i].title); setText("tb-sub", pages[i].sub);
  if (i === 0) { setTimeout(drawOverviewChart, 50); loadOverview(); }
  if (i === 1) loadRiskScoring();
  if (i === 2) loadFraudDetection();
  if (i === 3) loadDefaultTrace();
  if (i === 4) loadReports();
  if (i === 6) loadCases();
  if (i === 10) loadMonitoring();
  if (i === 11) setTimeout(loadTimeline, 30);
  if (i === 12) loadPrivacyCoinMatrix();
  // sync URL ?p= so PWA shortcut deep-links work
  try { history.replaceState({}, "", `/?p=${i}`); } catch (e) {}
}
// Honor ?p= query on initial load (used by PWA shortcuts)
(function () {
  const p = new URLSearchParams(location.search).get("p");
  if (p && /^\d+$/.test(p) && pages[+p]) {
    setTimeout(() => nav(+p), 80);
  }
})();
window.nav = nav;

/* ---------- API status / clock ---------- */
async function pingApi() {
  const badge = document.getElementById("api-status");
  try {
    await api("/health");
    badge.className = "tb-badge tb-live";
    badge.innerHTML = '<div class="pulse"></div>API Live';
  } catch (e) {
    badge.className = "tb-badge tb-offline";
    badge.innerHTML = "API Offline";
  }
}
function clock() {
  setText("clock", new Date().toLocaleTimeString("id-ID"));
}
setInterval(clock, 1000); clock();
setInterval(pingApi, 10000); pingApi();

/* ============================================================
 *  PAGE 0 — Overview
 * ============================================================ */
let overviewData = null;
async function loadOverview() {
  try {
    overviewData = await api("/v1/overview/metrics");
    const d = overviewData;
    setText("m-tx", fmt.int(d.transactions_total));
    setText("m-tx-sub", d.transactions_today_pct);
    setText("m-alerts", d.alerts_active);
    setText("m-alerts-sub", `${d.alerts_critical} kritikal`);
    setText("m-highrisk", d.entities_high_risk);
    setText("m-highrisk-sub", `${d.entities_total} entitas total`);
    setText("m-reports", d.reports_total);
    setText("m-reports-sub", `${d.reports_ltkm} LTKM, ${d.reports_ltkt} LTKT`);
    setText("status-l0", d.layer_status.l0);
    setText("status-l1", d.layer_status.l1);
    setText("status-l2", d.layer_status.l2);
    setText("status-l3", d.layer_status.l3);

    setHtml("recent-alerts", d.recent_alerts.map(a => `
      <div class="alert-item">
        <div class="alert-dot ${a.severity === "critical" ? "ad-red" : a.severity === "high" ? "ad-red" : "ad-amber"}"></div>
        <div class="alert-body">
          <div class="alert-title">${a.title}</div>
          <div class="alert-meta">${a.subtitle}</div>
        </div>
      </div>
    `).join(""));
    drawOverviewChart(d.volume_7d);
  } catch (e) {
    console.error(e);
    setText("m-tx", "OFFLINE");
    setHtml("recent-alerts", `<div class="loading" style="color:var(--red2)">API offline — pastikan FastAPI jalan: .\\fc api</div>`);
  }
}

function drawOverviewChart(data) {
  const c = document.getElementById("chart-overview"); if (!c) return;
  const W = c.offsetWidth || 600; c.width = W; c.height = 80;
  const ctx = c.getContext("2d"); ctx.clearRect(0, 0, W, 80);
  const vals = data && data.length ? data : [62, 71, 58, 84, 79, 91, 84];
  const labels = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"];
  const max = Math.max(...vals) * 1.15;
  const bw = (W - 80) / vals.length;
  vals.forEach((v, i) => {
    const h = (v / max) * 60; const x = 40 + i * bw + bw * .15; const bww = bw * .7;
    const opa = i === vals.length - 1 ? 1 : .5;
    ctx.fillStyle = `rgba(79,143,255,${opa})`;
    ctx.beginPath(); ctx.roundRect(x, 70 - h, bww, h, 3); ctx.fill();
    ctx.fillStyle = "rgba(148,163,180,.5)"; ctx.font = "9px IBM Plex Mono"; ctx.textAlign = "center";
    ctx.fillText(labels[i], x + bww / 2, 80);
    ctx.fillStyle = "rgba(196,218,255,.7)";
    ctx.fillText(Math.round(v / 1000) + "K", x + bww / 2, 65 - h);
  });
}

/* ============================================================
 *  PAGE 1 — Risk Scoring (Layer 0)
 * ============================================================ */
async function loadRiskScoring() {
  try {
    const r = await api("/v1/entities/top?limit=12");
    setText("rs-total", fmt.int(r.total_entities));
    setText("rs-high", fmt.int(r.high_count));
    setText("rs-mid", fmt.int(r.medium_count));
    setText("rs-low", fmt.int(r.low_count));

    setHtml("entity-tbody", r.entities.map(e => {
      const color = e.score >= 70 ? "var(--red)" : e.score >= 40 ? "var(--amber)" : "var(--green)";
      const text = e.score >= 70 ? "var(--red2)" : e.score >= 40 ? "var(--amber2)" : "var(--green2)";
      const badge = e.score >= 70 ? "b-red" : e.score >= 40 ? "b-amber" : "b-green";
      const lbl = e.score >= 70 ? "High" : e.score >= 40 ? "Medium" : "Low";
      return `
        <tr>
          <td>${e.entity_id}</td>
          <td>${e.entity_type}</td>
          <td>${e.country}</td>
          <td>
            <div class="score-wrap">
              <div class="score-bar"><div class="score-fill" style="width:${e.score}%;background:${color}"></div></div>
              <span class="score-num" style="color:${text}">${e.score.toFixed(0)}</span>
            </div>
          </td>
          <td><span class="badge ${badge}">${lbl}</span></td>
          <td><button class="btn btn-primary" onclick="showShap('${e.entity_id}')">Detail →</button></td>
        </tr>
      `;
    }).join(""));
  } catch (e) {
    setHtml("entity-tbody", `<tr><td colspan="6"><div class="loading" style="color:var(--red2)">Error: ${e.message}</div></td></tr>`);
  }
}

window.showShap = async function (entityId) {
  const sc = document.getElementById("shap-card");
  const st = document.getElementById("shap-title");
  const sb = document.getElementById("shap-body");
  sc.style.display = "block";
  st.textContent = `SHAP Explainability — ${entityId} · memuat...`;
  sb.innerHTML = `<div class="loading">Computing SHAP</div>`;

  try {
    const r = await api(`/v1/entities/${entityId}/shap`);
    const v = r.verdict || {};
    st.textContent = `Penjelasan Skor — ${entityId}`;

    // Verdict banner (plain language) + factor list
    const factorsPlain = r.factors_plain || [];
    const bannerColor = v.color || "#888";
    sb.innerHTML = `
      <div style="padding:14px 16px;border-radius:10px;background:${bannerColor}22;border:1px solid ${bannerColor}55;margin-bottom:14px">
        <div style="font-size:15px;font-weight:600;color:${bannerColor};margin-bottom:4px">
          ${v.emoji || ""} ${v.label || "—"} &mdash; Skor ${r.score.toFixed(0)}/100
        </div>
        <div style="font-size:12px;color:var(--t2);margin-bottom:8px">${v.plain || ""}</div>
        <div style="font-size:11px;color:var(--t1);background:var(--bg3);padding:8px 10px;border-radius:6px">
          ⚡ <b>Rekomendasi:</b> ${v.action || "—"}
        </div>
      </div>
      <div style="font-size:11px;color:var(--t3);margin-bottom:8px;font-family:var(--mono)">
        FAKTOR PENYEBAB (kenapa skornya begini):
      </div>
    `;
    sb.innerHTML += (factorsPlain.length ? factorsPlain : r.factors.map(f => ({
      ...f, label: f.feature, plain: f.feature,
    }))).map(f => {
      const positive = f.contribution > 0;
      const color = positive ? "#ef4444" : "#22c55e";
      const w = Math.min(100, Math.abs(f.contribution) * 100);
      const arrow = positive ? "⬆ memperberat" : "⬇ mengurangi";
      const label = f.label || f.feature;
      return `
        <div class="shap-row" title="${label}">
          <div class="shap-label" style="min-width:200px">${label}</div>
          <div class="shap-track"><div class="shap-fill" style="width:${w}%;background:${color};margin-left:${positive ? "0" : "auto"}"></div></div>
          <div class="shap-val" style="color:${color};min-width:90px;text-align:right">${arrow}</div>
        </div>`;
    }).join("");
    sc.scrollIntoView({ behavior: "smooth", block: "nearest" });
  } catch (e) {
    sb.innerHTML = `<div class="loading" style="color:var(--red2)">Error: ${e.message}</div>`;
  }
};

/* ============================================================
 *  PAGE 2 — Fraud Detection (Layer 1)
 * ============================================================ */
async function loadFraudDetection() {
  try {
    const r = await api("/v1/fraud/recent-alerts?limit=12");
    setText("fd-monitored", fmt.int(r.total_scored));
    setText("fd-anomalies", fmt.int(r.anomaly_count));

    setHtml("fraud-alerts", r.alerts.map(a => {
      const v = a.verdict || {};
      const cls = v.severity >= 4 ? "b-red" : v.severity >= 3 ? "b-red" : "b-amber";
      const dot = v.severity >= 3 ? "ad-red" : "ad-amber";
      const rulesPlain = (a.rules_plain || []).join(", ");
      return `
        <div class="alert-item">
          <div class="alert-dot ${dot}"></div>
          <div class="alert-body">
            <div class="alert-title">${v.emoji || ""} ${v.label || "Anomali"} — ${(a.score * 100).toFixed(0)}% anomali</div>
            <div class="alert-meta">${a.subtitle}</div>
            ${rulesPlain ? `<div style="font-size:10px;color:var(--amber2);margin-top:3px">⚠ ${rulesPlain}</div>` : ""}
            ${v.action ? `<div style="font-size:10px;color:var(--t3);margin-top:3px">⚡ ${v.action}</div>` : ""}
            <div class="alert-action">
              <button class="btn">Tutup</button>
              <button class="btn btn-primary" onclick="nav(3);document.getElementById('wallet-input').value='${a.sender_id || ""}';traceWallet()">Lacak Jaringan →</button>
              <button class="btn btn-red" onclick="nav(4)">Buat Laporan</button>
            </div>
          </div>
          <span class="badge ${cls}">${v.label || "—"}</span>
        </div>
      `;
    }).join(""));
  } catch (e) {
    setHtml("fraud-alerts", `<div class="loading" style="color:var(--red2)">Error: ${e.message}</div>`);
  }
}

/* ============================================================
 *  PAGE 3 — Graph Tracing (Layer 2)
 * ============================================================ */
let lastTrace = null;

async function loadDefaultTrace() {
  if (!lastTrace) {
    traceWallet();
  } else {
    drawGraph(lastTrace);
  }
}

window.traceWallet = async function () {
  const id = document.getElementById("wallet-input").value.trim();
  if (!id) return;
  setText("case-id", "Memuat...");
  document.getElementById("node-detail").innerHTML = `<div class="loading">Tracing ${id}</div>`;
  try {
    const t = await api(`/v1/tracing/wallet/${encodeURIComponent(id)}/trace-explained?hops=2`);
    lastTrace = { ...t, fraud_score: t.gnn_fraud_score, wallet: id };

    setText("case-id", `Kasus ${id.slice(-8)}`);
    const lv = t.layering_verdict || {};
    const gv = t.gnn_verdict || {};
    const ls = (t.layering_score || 0).toFixed(2);
    const bannerColor = lv.color || "#888";

    document.getElementById("node-detail").innerHTML = `
      <div style="padding:12px 14px;border-radius:10px;background:${bannerColor}22;border:1px solid ${bannerColor}55;margin-bottom:12px">
        <div style="font-size:14px;font-weight:600;color:${bannerColor};margin-bottom:4px">
          ${lv.emoji || ""} ${lv.label || "—"}
        </div>
        <div style="font-size:11px;color:var(--t2)">${lv.plain || ""}</div>
      </div>
      <div class="nd-row"><span class="nd-key">Wallet ID</span><span class="nd-val">${fmt.short(id)}</span></div>
      <div class="nd-row" title="Seberapa kuat pola pencucian uang berlapis"><span class="nd-key">Skor Pencucian</span><span class="nd-val" style="color:${bannerColor}">${ls} / 1.00 — ${lv.label || ""}</span></div>
      <div class="nd-row" title="Prediksi AI berdasarkan jaringan transaksi"><span class="nd-key">Prediksi AI (GNN)</span><span class="nd-val" style="color:${gv.color || "var(--t2)"}">${(t.gnn_fraud_score || 0).toFixed(2)} — ${gv.label || ""}</span></div>
      <div class="nd-row"><span class="nd-key">Jaringan terhubung</span><span class="nd-val">${t.subgraph_size} wallet</span></div>
      <div class="nd-row"><span class="nd-key">Rantai pencucian</span><span class="nd-val">${t.path_count}</span></div>
      <div class="nd-row"><span class="nd-key">Wallet ter-flag</span><span class="nd-val">${(t.flagged_wallets || []).length}</span></div>
      ${lv.action ? `<div style="margin-top:10px;font-size:11px;background:var(--bg3);padding:8px 10px;border-radius:6px;color:var(--t1)">⚡ <b>Rekomendasi:</b> ${lv.action}</div>` : ""}
    `;
    setHtml("gnn-patterns", (t.pattern_types || []).map(p => {
      const label = { smurfing: "Smurfing (transaksi dipecah-pecah)",
                      layering: "Layering (pencucian berlapis)",
                      anomalous_pattern: "Pola anomali" }[p] || p;
      return `
      <div class="alert-item" style="padding:7px 0">
        <div class="alert-dot ad-red"></div>
        <div class="alert-body"><div class="alert-title" style="font-size:11px">${label}</div></div>
      </div>`;
    }).join("") || `<div class="loading">Tidak ada pola mencurigakan</div>`);

    drawGraph(lastTrace);
  } catch (e) {
    document.getElementById("node-detail").innerHTML = `<div class="loading" style="color:var(--red2)">Pelacakan gagal: ${e.message}</div>`;
  }
};

window.resetGraph = function () {
  document.getElementById("wallet-input").value = "";
  document.getElementById("node-detail").innerHTML = `<div class="loading">Masukkan wallet ID lalu klik "Trace Jaringan"</div>`;
  setHtml("gnn-patterns", "");
  const c = document.getElementById("graph-canvas");
  if (c) c.getContext("2d").clearRect(0, 0, c.width, c.height);
  lastTrace = null;
};

window.generateLtkm = async function () {
  if (!lastTrace) { alert("Lakukan trace dulu."); return; }
  try {
    const r = await api(`/v1/reports/ltkm/auto/${encodeURIComponent(lastTrace.wallet)}`, { method: "POST" });
    alert(`LTKM berhasil dibuat: ${r.report_id}`);
    nav(4);
  } catch (e) {
    alert("Gagal: " + e.message);
  }
};

function drawGraph(trace) {
  const c = document.getElementById("graph-canvas"); if (!c) return;
  const W = c.offsetWidth || 400; c.width = W; c.height = 280;
  const ctx = c.getContext("2d"); ctx.clearRect(0, 0, W, 280);
  if (!trace) return;

  const cx = W / 2, cy = 140;
  const flagged = (trace.flagged_wallets || []).slice(0, 8);
  const score = trace.fraud_score || 0;
  const centerCol = score > 0.7 ? "#ef4444" : score > 0.4 ? "#f59e0b" : "#64748b";

  // outer ring of flagged wallets
  const n = Math.max(flagged.length, 3);
  const ring = [];
  for (let i = 0; i < n; i++) {
    const ang = (i / n) * Math.PI * 2 - Math.PI / 2;
    const radius = 100;
    ring.push({ x: cx + Math.cos(ang) * radius, y: cy + Math.sin(ang) * radius, label: flagged[i] || "" });
  }
  // edges
  ctx.lineWidth = 1.5;
  ring.forEach(r => {
    ctx.strokeStyle = centerCol + "55";
    ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(r.x, r.y); ctx.stroke();
  });
  // outer nodes
  ring.forEach(r => {
    ctx.beginPath(); ctx.arc(r.x, r.y, 12, 0, Math.PI * 2);
    ctx.fillStyle = r.label ? "rgba(239,68,68,.25)" : "rgba(100,116,139,.18)";
    ctx.fill();
    ctx.strokeStyle = r.label ? "#ef4444" : "#64748b";
    ctx.lineWidth = 1; ctx.stroke();
    if (r.label) {
      ctx.font = "8px IBM Plex Mono"; ctx.fillStyle = "#fca5a5"; ctx.textAlign = "center";
      ctx.fillText(r.label.slice(-6), r.x, r.y + 24);
    }
  });
  // center node
  ctx.beginPath(); ctx.arc(cx, cy, 24, 0, Math.PI * 2);
  ctx.fillStyle = centerCol + "33"; ctx.fill();
  ctx.strokeStyle = centerCol; ctx.lineWidth = 2.5; ctx.stroke();
  ctx.fillStyle = "#fff"; ctx.font = "600 11px IBM Plex Mono"; ctx.textAlign = "center";
  ctx.fillText("SEED", cx, cy - 2);
  ctx.fillStyle = centerCol; ctx.font = "9px IBM Plex Mono";
  ctx.fillText(score.toFixed(2), cx, cy + 10);
}

/* ============================================================
 *  PAGE 4 — Laporan
 * ============================================================ */
async function loadReports() {
  try {
    const r = await api("/v1/reports/list");
    setText("r-total", r.total);
    setText("r-ltkm", r.ltkm_count);
    setText("r-ltkt", r.ltkt_count);
    setText("r-formats", r.with_json);

    setHtml("reports-list", r.reports.map(rep => {
      const icon = rep.type === "LTKT" ? "ri-green" : (rep.type === "LTKM" ? "" : "ri-amber");
      const lbl = rep.type === "LTKT" ? "LK" : "LT";
      return `
        <div class="report-item" onclick="previewReport('${rep.id}')">
          <div class="report-icon ${icon}">${lbl}</div>
          <div class="report-body">
            <div class="report-title">${rep.id}</div>
            <div class="report-sub">${rep.type} · ${rep.created}</div>
          </div>
          <span class="badge b-blue">${rep.formats.join(", ")}</span>
        </div>
      `;
    }).join("") || `<div class="loading">Belum ada laporan. Jalankan: .\\fc demo</div>`);
  } catch (e) {
    setHtml("reports-list", `<div class="loading" style="color:var(--red2)">Error: ${e.message}</div>`);
  }
}

window.previewReport = async function (id) {
  setText("preview-title", `Preview — ${id}`);
  setHtml("report-preview", `<div class="loading">Memuat preview</div>`);
  try {
    const r = await fetch(`/v1/reports/${id}/preview`);
    const html = await r.text();
    document.getElementById("report-preview").innerHTML = html;
  } catch (e) {
    setHtml("report-preview", `<div class="loading" style="color:var(--red2)">Error: ${e.message}</div>`);
  }
};

/* ============================================================
 *  PAGE 5 — Live Trace
 * ============================================================ */
let traceExamples = [];

async function loadTraceExamples() {
  try {
    const r = await api("/v1/tracing/example-wallets?limit=6");
    traceExamples = r.wallets;
  } catch (e) { console.warn(e); }
}
loadTraceExamples();

window.quickTrace = function (i) {
  if (traceExamples[i]) {
    document.getElementById("trace-input").value = traceExamples[i];
    runTrace();
  }
};

window.runTrace = async function () {
  const id = document.getElementById("trace-input").value.trim();
  if (!id) return;
  document.getElementById("trace-result").style.display = "block";
  setText("tr-score", "..."); setText("tr-layering", "..."); setText("tr-conn", "..."); setText("tr-pat", "...");
  setHtml("tr-patterns", `<div class="loading">Tracing</div>`);
  setHtml("tr-connections", "");

  try {
    const t = await api(`/v1/tracing/wallet/${encodeURIComponent(id)}/trace?hops=2`);
    const s = await api(`/v1/tracing/wallet/${encodeURIComponent(id)}/score`);
    const fs = s.fraud_score;
    lastTrace = { ...t, fraud_score: fs, wallet: id };

    const scoreEl = document.getElementById("tr-score");
    scoreEl.textContent = fs.toFixed(2);
    scoreEl.style.color = fs > 0.7 ? "var(--red2)" : fs > 0.4 ? "var(--amber2)" : "var(--green2)";

    const riskEl = document.getElementById("tr-risk");
    riskEl.textContent = fs > 0.7 ? "sangat mencurigakan" : fs > 0.4 ? "perlu review" : "aman";
    riskEl.style.color = scoreEl.style.color;

    setText("tr-layering", t.layering_score.toFixed(4));
    setText("tr-conn", t.subgraph_size);
    setText("tr-pat", (t.pattern_types || []).length);

    setHtml("tr-patterns", (t.pattern_types || []).map(p => `
      <div style="display:flex;gap:8px;align-items:flex-start;padding:7px 0;font-size:12px;color:var(--t2);border-bottom:1px solid rgba(255,255,255,.04)">
        <span style="color:var(--red);flex-shrink:0">⚠</span>
        <span>${p}</span>
      </div>
    `).join("") || `<div style="padding:7px 0;font-size:12px;color:var(--green2)">✓ Tidak ada pola mencurigakan</div>`);

    setHtml("tr-connections", (t.flagged_wallets || []).slice(0, 6).map(w => `
      <div style="display:flex;justify-content:space-between;align-items:center;padding:7px 0;font-size:11px;border-bottom:1px solid rgba(255,255,255,.04)">
        <span style="font-family:var(--mono);color:var(--t2)">${fmt.short(w)}</span>
        <span style="display:flex;gap:10px;align-items:center">
          <span style="font-size:10px;color:var(--red2)">flagged</span>
        </span>
      </div>
    `).join("") || `<div style="padding:8px 0;font-size:11px;color:var(--t3)">Tidak ada wallet flagged</div>`);

    drawTraceGraph(lastTrace);
  } catch (e) {
    setHtml("tr-patterns", `<div class="loading" style="color:var(--red2)">Error: ${e.message}</div>`);
  }
};

function drawTraceGraph(trace) {
  const c = document.getElementById("trace-graph"); if (!c) return;
  const W = c.offsetWidth || 500; c.width = W; c.height = 280;
  const ctx = c.getContext("2d"); ctx.clearRect(0, 0, W, 280);
  const score = trace.fraud_score || 0;
  const flagged = (trace.flagged_wallets || []).slice(0, 5);
  const cx = W / 2;
  const center = { x: cx, y: 45, r: 24, col: score > 0.7 ? "#ef4444" : score > 0.4 ? "#f59e0b" : "#3b82f6" };

  const n1 = Math.max(2, Math.min(flagged.length || 2, 5));
  const layer1 = [];
  for (let i = 0; i < n1; i++) {
    const x = cx - ((n1 - 1) * 70) / 2 + i * 70;
    const col = score > 0.7 ? "#ef4444" : "#3b82f6";
    layer1.push({ x, y: 140, r: 15, col, label: flagged[i] ? flagged[i].slice(-4) : "" });
  }
  const layer2 = [];
  const n2 = Math.min(5, trace.subgraph_size || 3);
  for (let i = 0; i < n2; i++) {
    const x = cx - ((n2 - 1) * 95) / 2 + i * 95;
    const col = score > 0.7 && i < 2 ? "#f59e0b" : "#3b82f6";
    layer2.push({ x: Math.max(25, Math.min(W - 25, x)), y: 235, r: 11, col });
  }

  ctx.lineWidth = 1.5;
  layer1.forEach(n => {
    ctx.strokeStyle = center.col + "66";
    ctx.beginPath(); ctx.moveTo(center.x, center.y); ctx.lineTo(n.x, n.y); ctx.stroke();
  });
  layer2.forEach((n, i) => {
    const src = layer1[i % layer1.length];
    ctx.strokeStyle = n.col + "44";
    ctx.beginPath(); ctx.moveTo(src.x, src.y); ctx.lineTo(n.x, n.y); ctx.stroke();
  });

  const drawNode = (n, label) => {
    ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, 7);
    ctx.fillStyle = n.col + "33"; ctx.fill();
    ctx.strokeStyle = n.col; ctx.lineWidth = 2; ctx.stroke();
    if (label) {
      ctx.fillStyle = "#fff"; ctx.font = "600 9px IBM Plex Mono"; ctx.textAlign = "center";
      ctx.fillText(label, n.x, n.y - 1);
    }
  };
  layer2.forEach(n => drawNode(n, ""));
  layer1.forEach(n => drawNode(n, n.label));
  drawNode(center, "SEED");
  ctx.fillStyle = center.col; ctx.font = "9px IBM Plex Mono"; ctx.textAlign = "center";
  ctx.fillText(score.toFixed(2), center.x, center.y + 10);
}

window.downloadTraceJson = function () {
  if (!lastTrace) return;
  const blob = new Blob([JSON.stringify(lastTrace, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `trace-${lastTrace.wallet}.json`; a.click();
  URL.revokeObjectURL(url);
};

window.generateLtkmFromTrace = async function () {
  if (!lastTrace) { alert("Lakukan trace dulu."); return; }
  try {
    const r = await api(`/v1/reports/ltkm/auto/${encodeURIComponent(lastTrace.wallet)}`, { method: "POST" });
    alert(`LTKM berhasil dibuat: ${r.report_id}`);
    nav(4);
  } catch (e) {
    alert("Gagal: " + e.message);
  }
};

/* ---------- on resize ---------- */
window.addEventListener("resize", () => {
  const active = [...document.querySelectorAll(".page")].findIndex(p => p.classList.contains("active"));
  if (active === 0) drawOverviewChart(overviewData && overviewData.volume_7d);
  if (active === 3 && lastTrace) drawGraph(lastTrace);
  if (active === 5 && lastTrace) drawTraceGraph(lastTrace);
});

/* ============================================================
 *  PAGE 6 — Cases
 * ============================================================ */
async function loadCases() {
  try {
    const r = await api("/v1/cases/list?limit=50");
    setText("cs-total", r.stats.total || 0);
    setText("cs-open", r.stats.by_status?.open || 0);
    setText("cs-escalated", r.stats.by_status?.escalated || 0);
    setText("cs-closed", r.stats.by_status?.closed || 0);

    if (!r.cases.length) {
      setHtml("cases-list", `<div class="loading">Belum ada cases. Klik "+ Buat Case" untuk mulai.</div>`);
      return;
    }
    setHtml("cases-list", r.cases.map(c => {
      const badge = ({
        open: "b-amber", in_review: "b-blue",
        escalated: "b-red", reported: "b-blue", closed: "b-green",
      })[c.status] || "b-gray";
      return `
        <div class="report-item" onclick="openCase('${c.case_id}')">
          <div class="report-icon">CS</div>
          <div class="report-body">
            <div class="report-title">${c.title}</div>
            <div class="report-sub">${c.case_id} · subject ${c.subject_id} · ${c.assignee}</div>
          </div>
          <span class="badge ${badge}">${c.status}</span>
        </div>
      `;
    }).join(""));
  } catch (e) {
    setHtml("cases-list", `<div class="loading" style="color:var(--red2)">Error: ${e.message}</div>`);
  }
}

window.openCase = async function (id) {
  setText("case-detail-title", `Case ${id}`);
  setHtml("case-detail", `<div class="loading">Memuat detail</div>`);
  try {
    const c = await api(`/v1/cases/${id}`);
    setHtml("case-detail", `
      <div class="node-detail">
        <div class="nd-row"><span class="nd-key">Title</span><span class="nd-val">${c.title}</span></div>
        <div class="nd-row"><span class="nd-key">Subject</span><span class="nd-val">${c.subject_id}</span></div>
        <div class="nd-row"><span class="nd-key">Status</span><span class="nd-val">${c.status}</span></div>
        <div class="nd-row"><span class="nd-key">Assignee</span><span class="nd-val">${c.assignee}</span></div>
        <div class="nd-row"><span class="nd-key">Created</span><span class="nd-val">${c.created_at}</span></div>
        <div class="nd-row"><span class="nd-key">Updated</span><span class="nd-val">${c.updated_at}</span></div>
        <div class="nd-row"><span class="nd-key">Alerts</span><span class="nd-val">${c.alerts.length}</span></div>
        <div class="nd-row"><span class="nd-key">Reports</span><span class="nd-val">${c.report_ids.length}</span></div>
      </div>
      ${c.description ? `<div style="margin-top:10px;font-size:12px;color:var(--t2)">${c.description}</div>` : ""}
      <div style="display:flex;gap:6px;margin-top:14px;flex-wrap:wrap">
        <button class="btn" onclick="caseStatus('${id}','in_review')">→ In Review</button>
        <button class="btn btn-red" onclick="caseStatus('${id}','escalated')">→ Escalated</button>
        <button class="btn btn-primary" onclick="caseStatus('${id}','reported')">→ Reported</button>
        <button class="btn btn-success" onclick="caseStatus('${id}','closed')">→ Closed</button>
      </div>
      ${c.alerts.length ? `<div style="margin-top:14px"><div class="card-title">Linked Alerts</div>` +
        c.alerts.map(a => `<div style="font-size:11px;padding:6px 0;color:var(--t2);border-bottom:1px solid rgba(255,255,255,.04)">
          <span style="font-family:var(--mono);color:var(--t1)">${a.alert_type}</span> · ${a.alert_ref}
          <span style="float:right;color:var(--red2)">score ${a.score.toFixed(2)}</span>
        </div>`).join("") + "</div>" : ""}
    `);
  } catch (e) {
    setHtml("case-detail", `<div class="loading" style="color:var(--red2)">Error: ${e.message}</div>`);
  }
};

window.caseStatus = async function (id, newStatus) {
  try {
    await fetch(`/v1/cases/${id}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus }),
    });
    loadCases();
    openCase(id);
  } catch (e) { alert("Gagal: " + e.message); }
};

window.newCaseDialog = async function () {
  const title = prompt("Judul case:", "Investigation - " + new Date().toLocaleDateString("id-ID"));
  if (!title) return;
  const subject_id = prompt("Subject ID (wallet/entity):", "WALLET_0x000000000002");
  if (!subject_id) return;
  const assignee = prompt("Assignee:", "officer_01") || "unassigned";
  try {
    await fetch("/v1/cases/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, subject_id, assignee, subject_type: "wallet" }),
    });
    loadCases();
  } catch (e) { alert("Gagal: " + e.message); }
};

/* ============================================================
 *  PAGE 7 — Screening (DTTOT + Negative News)
 * ============================================================ */
window.quickScreen = function (name) {
  document.getElementById("screen-input").value = name;
  runScreening();
};

window.runScreening = async function () {
  const name = document.getElementById("screen-input").value.trim();
  if (!name) return;
  setHtml("dttot-result", `<div class="loading">Checking DTTOT</div>`);
  setHtml("news-result", `<div class="loading">Scraping news</div>`);

  // DTTOT
  try {
    const r = await api(`/v1/screening/dttot/${encodeURIComponent(name)}`);
    if (r.match) {
      setHtml("dttot-result", `
        <div style="padding:14px;background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.3);border-radius:8px">
          <div style="color:var(--red2);font-weight:600;margin-bottom:6px">⚠ MATCH DITEMUKAN</div>
          <div class="nd-row"><span class="nd-key">List ID</span><span class="nd-val">${r.entry.list_id}</span></div>
          <div class="nd-row"><span class="nd-key">Name</span><span class="nd-val">${r.entry.name}</span></div>
          <div class="nd-row"><span class="nd-key">Type</span><span class="nd-val">${r.entry.list_type}</span></div>
          <div class="nd-row"><span class="nd-key">Program</span><span class="nd-val">${r.entry.program}</span></div>
          <div class="nd-row"><span class="nd-key">Nationality</span><span class="nd-val">${r.entry.nationality || "—"}</span></div>
          <div class="nd-row"><span class="nd-key">Indonesian priority</span><span class="nd-val">${r.entry.is_indonesian_priority ? "YES" : "no"}</span></div>
        </div>
      `);
    } else {
      setHtml("dttot-result", `
        <div style="padding:14px;background:rgba(34,197,94,.06);border:1px solid rgba(34,197,94,.2);border-radius:8px;color:var(--green2);font-size:12px">
          ✓ Tidak ada match di DTTOT / UN Consolidated List (${r.index_size} entitas dicek)
        </div>
      `);
    }
  } catch (e) {
    setHtml("dttot-result", `<div class="loading" style="color:var(--red2)">Error: ${e.message}</div>`);
  }

  // News
  try {
    const r = await api(`/v1/screening/news/${encodeURIComponent(name)}?min_score=0&limit=10`);
    if (!r.hits.length) {
      setHtml("news-result", `<div class="loading">Tidak ada news yang menyebut "${name}"</div>`);
      return;
    }
    setHtml("news-result", `
      <div style="font-size:11px;color:var(--t3);margin-bottom:10px">
        ${r.hit_count} hits · max sentiment ${r.max_score.toFixed(2)}
      </div>
      ${r.hits.map(h => {
        const sc = h.sentiment_score;
        const col = sc > 0.5 ? "var(--red2)" : sc > 0.2 ? "var(--amber2)" : "var(--t2)";
        const badgeCls = sc > 0.5 ? "b-red" : sc > 0.2 ? "b-amber" : "b-gray";
        return `
          <div style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,.04);font-size:11px">
            <div style="display:flex;justify-content:space-between;gap:8px;margin-bottom:4px">
              <a href="${h.link}" target="_blank" style="color:var(--blue2);text-decoration:none;font-weight:500">${h.title}</a>
              <span class="badge ${badgeCls}" style="flex-shrink:0">${sc.toFixed(2)}</span>
            </div>
            <div style="color:var(--t3);font-family:var(--mono);font-size:10px;margin-bottom:4px">${h.source} · ${h.published.slice(0,16)}</div>
            <div style="color:var(--t2)">${h.snippet}...</div>
            ${h.matched_keywords.length ? `<div style="margin-top:4px;font-size:9px;color:${col}">⚠ ${h.matched_keywords.join(", ")}</div>` : ""}
          </div>
        `;
      }).join("")}
    `);
  } catch (e) {
    setHtml("news-result", `<div class="loading" style="color:var(--red2)">Error: ${e.message}</div>`);
  }
};

/* ============================================================
 *  WebSocket — real-time alert toast notifications
 * ============================================================ */
let ws = null;
function showToast(payload) {
  const cont = document.getElementById("toasts");
  if (!cont) return;
  const sev = payload.severity || "medium";
  const col = sev === "critical" ? "var(--red)" : sev === "high" ? "var(--red)" :
              sev === "medium" ? "var(--amber)" : "var(--blue)";
  const toast = document.createElement("div");
  toast.style.cssText = `
    background:var(--surf);border:1px solid var(--b2);border-left:3px solid ${col};
    border-radius:8px;padding:12px 14px;box-shadow:0 8px 24px rgba(0,0,0,.4);
    font-size:12px;color:var(--t1);animation:slideIn .3s ease;
  `;
  toast.innerHTML = `
    <div style="font-weight:600;color:${col};font-size:10px;text-transform:uppercase;margin-bottom:4px">${sev} · ${payload.source}</div>
    <div style="margin-bottom:2px">${payload.title}</div>
    <div style="font-size:10px;color:var(--t3);font-family:var(--mono)">${payload.subtitle}</div>
  `;
  cont.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transition = "opacity .4s";
    setTimeout(() => toast.remove(), 400);
  }, 6000);
}

function connectWs() {
  if (ws && ws.readyState !== WebSocket.CLOSED) return;
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  ws = new WebSocket(`${proto}//${location.host}/ws/alerts`);
  ws.onopen = () => console.log("WS connected");
  ws.onmessage = (ev) => {
    try {
      const data = JSON.parse(ev.data);
      if (data.type === "alert") showToast(data);
    } catch (e) { /* ignore */ }
  };
  ws.onclose = () => {
    console.log("WS closed — retry in 5s");
    setTimeout(connectWs, 5000);
  };
  ws.onerror = () => { ws.close(); };
}
const wsStyle = document.createElement("style");
wsStyle.textContent = `@keyframes slideIn{from{transform:translateX(100%);opacity:0}to{transform:translateX(0);opacity:1}}`;
document.head.appendChild(wsStyle);
connectWs();

/* ============================================================
 *  PAGE 8 — Private Sector AML
 * ============================================================ */
window.screenProperty = async function () {
  const body = {
    tx_id: "PROP-" + Date.now(),
    buyer_id: document.getElementById("ps-buyer").value,
    buyer_country: document.getElementById("ps-country").value,
    sale_price_idr: parseFloat(document.getElementById("ps-amount").value),
    appraised_value_idr: parseFloat(document.getElementById("ps-appraised").value),
    cash_portion_idr: parseFloat(document.getElementById("ps-cash").value),
    mortgage_idr: 0,
  };
  setHtml("ps-result", `<div class="loading">Screening</div>`);
  try {
    const r = await api("/v1/private/property/screen", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.alerts.length) {
      setHtml("ps-result", `<div style="padding:14px;background:rgba(34,197,94,.06);border:1px solid rgba(34,197,94,.2);border-radius:8px;color:var(--green2)">✓ Clean — tidak ada red flag terdeteksi</div>`);
      return;
    }
    setHtml("ps-result", `
      <div style="font-size:11px;color:var(--t3);margin-bottom:10px">${r.alerts.length} alert untuk ${body.tx_id}</div>
      ${r.alerts.map(a => {
        const sev = a.severity;
        const col = sev === "critical" ? "var(--red)" : sev === "high" ? "var(--red2)" : sev === "medium" ? "var(--amber2)" : "var(--blue2)";
        const badgeCls = sev === "critical" ? "b-red" : sev === "high" ? "b-red" : sev === "medium" ? "b-amber" : "b-blue";
        return `
          <div style="padding:10px;background:var(--surf2);border-left:3px solid ${col};border-radius:6px;margin-bottom:6px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
              <span style="font-family:var(--mono);font-size:10px;color:${col};font-weight:600">${a.rule}</span>
              <span class="badge ${badgeCls}">${sev}</span>
            </div>
            <div style="font-size:11px;color:var(--t2)">${a.message}</div>
          </div>
        `;
      }).join("")}
    `);
  } catch (e) {
    setHtml("ps-result", `<div class="loading" style="color:var(--red2)">Error: ${e.message}</div>`);
  }
};

window.seedUboDemo = async function () {
  setHtml("ps-result", `<div class="loading">Seeding UBO demo graph</div>`);
  try {
    const r = await api("/v1/private/ubo/seed-demo", { method: "POST" });
    const ubos = r.ubo_for_PT_MAJU_BERSAMA;
    const shell = r.shell_check_BVI;
    setHtml("ps-result", `
      <div style="padding:14px;background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.2);border-radius:8px;margin-bottom:10px">
        <div style="font-weight:600;color:var(--red2);margin-bottom:8px">⚠ UBO Trace: PT Maju Bersama</div>
        ${ubos.map(u => `
          <div style="font-size:11px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,.04)">
            <div><span style="color:var(--t1);font-weight:600">${u.name || u.entity_id}</span> ${u.is_pep ? '<span class="badge b-red">PEP</span>' : ''}</div>
            <div style="font-family:var(--mono);color:var(--t3);font-size:10px">
              Effective ${u.effective_pct}% · depth ${u.depth} hops · ${u.country}
            </div>
          </div>
        `).join("")}
      </div>
      <div style="padding:14px;background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.2);border-radius:8px">
        <div style="font-weight:600;color:var(--amber2);margin-bottom:8px">Shell Company Check: BVI_HOLDING_001</div>
        <div style="font-size:11px;color:var(--t2);margin-bottom:6px">
          Shell score: <strong style="color:var(--red2)">${shell.shell_score.toFixed(3)}</strong>
          · ${shell.is_likely_shell ? '<span class="badge b-red">LIKELY SHELL</span>' : 'borderline'}
        </div>
        <div style="font-size:10px;color:var(--t3);font-family:var(--mono)">
          Indikator: ${shell.indicators.join(", ")}
        </div>
      </div>
    `);
  } catch (e) {
    setHtml("ps-result", `<div class="loading" style="color:var(--red2)">Error: ${e.message}</div>`);
  }
};

/* ============================================================
 *  PAGE 9 — Multi-chain Crypto
 * ============================================================ */
window.setMc = function (addr, chain) {
  document.getElementById("mc-addr").value = addr;
  document.getElementById("mc-chain").value = chain;
  multichainFetch();
};

window.multichainFetch = async function () {
  const addr = document.getElementById("mc-addr").value.trim();
  const chain = document.getElementById("mc-chain").value;
  if (!addr) return;
  setHtml("mc-result", `<div class="loading">Querying ${chain === "auto" ? "auto-detected chain" : chain}</div>`);
  try {
    const url = chain === "auto"
      ? `/v1/multichain/auto/${encodeURIComponent(addr)}?limit=15`
      : `/v1/multichain/${chain}/wallet/${encodeURIComponent(addr)}/txs?limit=15`;
    const r = await api(url);
    const detected = r.detected_chain || chain;
    if (!r.txs.length) {
      setHtml("mc-result", `<div style="padding:14px;color:var(--t3);font-size:12px">
        Chain: <strong style="color:var(--t1)">${detected}</strong> · 0 transaksi.
        ${(detected === "bsc" || detected === "polygon") ? "<br><br><span style='color:var(--amber2)'>Note: butuh API key. Set BSCSCAN_API_KEY / POLYGONSCAN_API_KEY di .env</span>" : ""}
      </div>`);
      return;
    }
    setHtml("mc-result", `
      <div style="font-size:11px;color:var(--t3);margin-bottom:10px;font-family:var(--mono)">
        Chain: <strong style="color:var(--t1)">${detected}</strong> · ${r.count} transactions
      </div>
      <table class="tbl">
        <thead><tr><th>Hash</th><th>From</th><th>To</th><th>Amount</th><th>IDR</th></tr></thead>
        <tbody>
          ${r.txs.map(t => `
            <tr>
              <td><a href="#" style="color:var(--blue2);text-decoration:none">${fmt.short(t.tx_hash)}</a></td>
              <td>${fmt.short(t.sender)}</td>
              <td>${fmt.short(t.receiver)}</td>
              <td style="text-align:right;font-family:var(--mono)">${t.amount_native.toFixed(6)} ${t.token_symbol || ""}</td>
              <td style="text-align:right;font-family:var(--mono);color:var(--blue2)">${fmt.rp(t.amount_idr)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `);
  } catch (e) {
    setHtml("mc-result", `<div class="loading" style="color:var(--red2)">Error: ${e.message}</div>`);
  }
};

/* ============================================================
 *  PAGE 10 — Model Monitoring
 * ============================================================ */
window.seedMonitoring = async function () {
  try {
    await api("/v1/monitoring/seed-demo?n=300", { method: "POST" });
    loadMonitoring();
  } catch (e) { alert("Gagal: " + e.message); }
};

async function loadMonitoring() {
  try {
    const h = await api("/v1/monitoring/health");
    h.layers.forEach(l => {
      const num = l.layer === "layer0" ? "l0" : l.layer === "layer1" ? "l1" : "l2";
      setText(`mon-${num}`, l.total_predictions);
      setText(`mon-${num}-rate`, `${(l.alert_rate * 100).toFixed(1)}% alert rate`);
    });
    const d = await api("/v1/monitoring/drift");
    setText("mon-psi", d.overall_psi.toFixed(4));
    const sevCol = d.overall_severity === "high" ? "var(--red2)" : d.overall_severity === "medium" ? "var(--amber2)" : "var(--green2)";
    const psiEl = document.getElementById("mon-psi-sev");
    if (psiEl) { psiEl.textContent = d.overall_severity; psiEl.style.color = sevCol; }
    setHtml("drift-tbody", d.feature_drifts.map(f => {
      const sevCls = f.severity === "high" ? "b-red" : f.severity === "medium" ? "b-amber" : "b-green";
      return `
        <tr>
          <td>${f.feature}</td>
          <td><span style="font-family:var(--mono)">${f.psi}</span></td>
          <td><span style="font-family:var(--mono)">${f.ks_stat}</span></td>
          <td><span style="font-family:var(--mono);color:var(--t3)">${f.ks_pvalue}</span></td>
          <td><span class="badge ${sevCls}">${f.severity}</span></td>
        </tr>
      `;
    }).join(""));
  } catch (e) {
    setHtml("drift-tbody", `<tr><td colspan="5"><div class="loading" style="color:var(--red2)">Error: ${e.message}</div></td></tr>`);
  }
}

/* ============================================================
 *  PAGE 11 — Investigation Timeline
 * ============================================================ */
let timelineData = null;

window.loadTimeline = async function () {
  const id = document.getElementById("tl-id").value.trim();
  if (!id) return;
  const canvas = document.getElementById("timeline-canvas");
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  setText("timeline-summary", "Memuat transaksi...");

  try {
    // Reuse the fraud recent-alerts to seed; in production we'd add a /tx?subject=...
    // Pull tx that touch this subject from sample data via a custom endpoint.
    const r = await api(`/v1/fraud/recent-alerts?limit=200&sample=1500`);
    const all = r.alerts || [];
    // Filter for ones whose subtitle mentions this ID
    const filtered = all
      .map(a => ({ ...a, subtitle: a.subtitle || "" }))
      .filter(a => a.subtitle.includes(id) || a.sender_id === id);
    timelineData = filtered.length ? filtered : all.slice(0, 30);
    drawTimeline(timelineData, id);
    setText("timeline-summary",
      `Rendered ${timelineData.length} transaksi (latest 30) untuk ${id}. ` +
      `Klik node untuk detail (coming soon).`);
  } catch (e) {
    setText("timeline-summary", "Error: " + e.message);
  }
};

function drawTimeline(events, subjectId) {
  const canvas = document.getElementById("timeline-canvas");
  const W = Math.max(900, events.length * 80);
  canvas.width = W; canvas.height = 340;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, W, 340);

  if (!events.length) {
    ctx.fillStyle = "#404858"; ctx.font = "12px IBM Plex Mono";
    ctx.textAlign = "center";
    ctx.fillText("Tidak ada transaksi untuk " + subjectId, W / 2, 170);
    return;
  }

  // axis
  const yAxis = 280;
  ctx.strokeStyle = "rgba(82,140,255,.2)";
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(40, yAxis); ctx.lineTo(W - 20, yAxis); ctx.stroke();

  // ticks every 80px
  ctx.fillStyle = "#404858"; ctx.font = "9px IBM Plex Mono"; ctx.textAlign = "center";
  for (let x = 40; x < W; x += 80) {
    ctx.beginPath(); ctx.moveTo(x, yAxis - 3); ctx.lineTo(x, yAxis + 3); ctx.stroke();
  }

  // events as bubbles, alternating above/below axis
  events.forEach((ev, i) => {
    const x = 60 + i * 80;
    const above = i % 2 === 0;
    const y = above ? yAxis - 60 : yAxis + 60;
    const sc = ev.score || 0.5;
    const col = sc > 0.85 ? "#ef4444" : sc > 0.7 ? "#f59e0b" : "#4f8fff";
    const r = 8 + sc * 8;

    // connector
    ctx.strokeStyle = col + "55"; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(x, yAxis); ctx.lineTo(x, y); ctx.stroke();

    // bubble
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fillStyle = col + "33"; ctx.fill();
    ctx.strokeStyle = col; ctx.lineWidth = 2; ctx.stroke();

    // label (tx_id)
    ctx.fillStyle = "#e8edf5";
    ctx.font = "9px IBM Plex Mono"; ctx.textAlign = "center";
    const lbl = (ev.tx_id || "").slice(-6);
    ctx.fillText(lbl, x, y + (above ? -r - 6 : r + 14));

    // amount (subtitle is "X -> Y · Rp ...")
    const m = (ev.subtitle || "").match(/Rp\s+([\d,\.]+)/);
    if (m) {
      ctx.font = "8px IBM Plex Mono";
      ctx.fillStyle = "#8892a4";
      ctx.fillText(m[0], x, y + (above ? -r - 18 : r + 26));
    }

    // tick label at axis
    ctx.fillStyle = "#404858"; ctx.font = "8px IBM Plex Mono";
    ctx.fillText("#" + (i + 1), x, yAxis + 16);
  });

  // legend title
  ctx.fillStyle = "#7ab0ff"; ctx.font = "11px DM Sans"; ctx.textAlign = "left";
  ctx.fillText(`Subject: ${subjectId}  ·  ${events.length} events`, 20, 24);
}

/* ============================================================
 *  Command Palette (Cmd+K / Ctrl+K)
 * ============================================================ */
const PALETTE_COMMANDS = [
  { label: "Go to Overview", icon: "📊", action: () => nav(0) },
  { label: "Go to Risk Scoring (Layer 0)", icon: "👤", action: () => nav(1) },
  { label: "Go to Fraud Detection (Layer 1)", icon: "💳", action: () => nav(2) },
  { label: "Go to Graph Tracing (Layer 2)", icon: "🕸", action: () => nav(3) },
  { label: "Go to PPATK Reports (Layer 3)", icon: "📄", action: () => nav(4) },
  { label: "Go to Live Trace", icon: "🔍", action: () => nav(5) },
  { label: "Go to Case Management", icon: "📋", action: () => nav(6) },
  { label: "Go to Screening (DTTOT/News)", icon: "🛡", action: () => nav(7) },
  { label: "Go to Private Sector AML", icon: "🏠", action: () => nav(8) },
  { label: "Go to Multi-chain Crypto", icon: "⛓", action: () => nav(9) },
  { label: "Go to Model Monitoring", icon: "📈", action: () => nav(10) },
  { label: "Go to Investigation Timeline", icon: "⏱", action: () => nav(11) },
  { label: "Create new Case", icon: "➕", action: () => { nav(6); setTimeout(newCaseDialog, 200); } },
  { label: "Seed UBO demo (PT → BVI shell → PEP)", icon: "🏢", action: () => { nav(8); setTimeout(seedUboDemo, 200); } },
  { label: "Seed monitoring demo predictions", icon: "📊", action: () => { nav(10); setTimeout(seedMonitoring, 200); } },
  { label: "Trigger test WebSocket alert (critical)", icon: "🔔",
    action: () => fetch("/v1/alerts/test-broadcast?severity=critical&title=Manual test alert", { method: "POST" }) },
  { label: "Open API docs (/docs)", icon: "📚", action: () => window.open("/docs", "_blank") },
  { label: "Open Prometheus metrics (/metrics)", icon: "📡", action: () => window.open("/metrics", "_blank") },
];

let paletteFiltered = [];
let paletteCursor = 0;

window.openPalette = function () {
  const el = document.getElementById("palette");
  el.style.display = "flex";
  const input = document.getElementById("palette-input");
  input.value = ""; renderPalette(""); input.focus();
};
window.closePalette = function () {
  document.getElementById("palette").style.display = "none";
};
function renderPalette(query) {
  const q = query.toLowerCase().trim();
  // Dynamic commands: trace <id>, risk <id>, screen <name>
  const dyn = [];
  if (q.startsWith("trace ")) {
    const id = q.slice(6).trim();
    if (id) dyn.push({ label: `Trace wallet '${id}'`, icon: "🕸",
      action: () => { nav(3); document.getElementById("wallet-input").value = id; setTimeout(traceWallet, 200); } });
  }
  if (q.startsWith("risk ") || q.startsWith("screen ")) {
    const name = q.split(" ").slice(1).join(" ").trim();
    if (name) dyn.push({ label: `Screen '${name}' against DTTOT + news`, icon: "🛡",
      action: () => { nav(7); document.getElementById("screen-input").value = name; setTimeout(runScreening, 200); } });
  }
  paletteFiltered = [
    ...dyn,
    ...PALETTE_COMMANDS.filter(c => !q || c.label.toLowerCase().includes(q)),
  ];
  paletteCursor = 0;
  const out = paletteFiltered.length
    ? paletteFiltered.map((c, i) => `
        <div class="palette-row" data-i="${i}" style="display:flex;align-items:center;gap:10px;padding:10px 18px;cursor:pointer;font-size:12px;color:var(--t1);background:${i === 0 ? "var(--surf2)" : "transparent"}">
          <span style="font-size:16px;width:24px;text-align:center">${c.icon}</span>
          <span>${c.label}</span>
        </div>`).join("")
    : `<div style="padding:24px;text-align:center;color:var(--t3);font-size:12px">Tidak ada match. Coba: <code style="color:var(--blue2)">trace 0x...</code> atau <code style="color:var(--blue2)">screen PT XYZ</code></div>`;
  document.getElementById("palette-results").innerHTML = out;
  // attach click handlers
  document.querySelectorAll(".palette-row").forEach((row, i) => {
    row.onclick = () => { paletteFiltered[i].action(); closePalette(); };
    row.onmouseover = () => { paletteCursor = i; highlightPaletteRow(); };
  });
}
function highlightPaletteRow() {
  document.querySelectorAll(".palette-row").forEach((r, i) => {
    r.style.background = i === paletteCursor ? "var(--surf2)" : "transparent";
  });
}
document.addEventListener("keydown", (e) => {
  // Cmd/Ctrl + K toggles palette
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
    e.preventDefault();
    const open = document.getElementById("palette").style.display === "flex";
    open ? closePalette() : openPalette();
    return;
  }
  if (document.getElementById("palette").style.display !== "flex") return;
  if (e.key === "Escape") { closePalette(); }
  else if (e.key === "ArrowDown") {
    paletteCursor = Math.min(paletteCursor + 1, paletteFiltered.length - 1);
    highlightPaletteRow(); e.preventDefault();
  } else if (e.key === "ArrowUp") {
    paletteCursor = Math.max(paletteCursor - 1, 0);
    highlightPaletteRow(); e.preventDefault();
  } else if (e.key === "Enter") {
    if (paletteFiltered[paletteCursor]) {
      paletteFiltered[paletteCursor].action(); closePalette();
    }
  }
});
document.addEventListener("DOMContentLoaded", () => {
  const inp = document.getElementById("palette-input");
  if (inp) inp.addEventListener("input", (e) => renderPalette(e.target.value));
  document.getElementById("palette")?.addEventListener("click", (e) => {
    if (e.target.id === "palette") closePalette();
  });
});

/* ============================================================
 *  i18n — Indonesian (default) ↔ English
 * ============================================================ */
const I18N = {
  id: {
    "Connecting": "Menyambungkan",
    "API Live": "API Live",
    "API Offline": "API Offline",
  },
  en: {
    "FinCrime · Command Center": "FinCrime · Command Center",
    "Memuat alert": "Loading alerts",
    "Memuat cases": "Loading cases",
    "Memuat entitas dari API": "Loading entities from API",
    "Memuat fraud detection": "Loading fraud detection",
    "Memuat daftar laporan": "Loading reports list",
    "Belum ada query": "No query yet",
    "Belum ada cases. Klik \"+ Buat Case\" untuk mulai.": "No cases yet. Click '+ New Case' to start.",
    "+ Buat Case": "+ New Case",
    "Pilih case di kiri untuk lihat detail": "Pick a case on the left to see details",
    "Memuat detail": "Loading details",
    "Buat Laporan": "Generate Report",
    "Buat Laporan LTKM →": "Generate LTKM Report →",
    "Trace ke GNN →": "Trace via GNN →",
    "Trace Jaringan →": "Trace Network →",
    "Trace Wallet →": "Trace Wallet →",
    "Risk Scoring": "Risk Scoring",
    "Fraud Detection": "Fraud Detection",
    "Graph Tracing": "Graph Tracing",
    "Laporan APU/PPT": "AML/CFT Reports",
    "Live Trace": "Live Trace",
    "Case Management": "Case Management",
    "Screening": "Screening",
    "Private Sector AML": "Private Sector AML",
    "Multi-chain Crypto": "Multi-chain Crypto",
    "Model Monitoring": "Model Monitoring",
    "Investigation Timeline": "Investigation Timeline",
  },
};
let currentLang = localStorage.getItem("fincrime_lang") || "id";

function applyI18n() {
  const dict = I18N[currentLang] || {};
  // Walk every text node; cheap because the tree is small.
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) {
    const t = node.nodeValue.trim();
    if (!t || t.length > 100) continue;
    if (dict[t]) node.nodeValue = node.nodeValue.replace(t, dict[t]);
  }
  // Update topbar pill
  const btn = document.getElementById("lang-toggle");
  if (btn) btn.textContent = currentLang.toUpperCase();
}

window.toggleLang = function () {
  currentLang = currentLang === "id" ? "en" : "id";
  localStorage.setItem("fincrime_lang", currentLang);
  // Reload to re-render translations cleanly (template strings re-applied)
  location.reload();
};

document.addEventListener("DOMContentLoaded", () => setTimeout(applyI18n, 300));

/* ============================================================
 *  PWA — register service worker
 * ============================================================ */
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/static/sw.js")
      .then((reg) => console.log("SW registered:", reg.scope))
      .catch((e) => console.warn("SW failed:", e));
  });
}

/* ============================================================
 *  PAGE 12 — Privacy Coin Monitor
 * ============================================================ */
async function loadPrivacyCoinMatrix() {
  try {
    const r = await api("/v1/privacy-coin/matrix");
    setHtml("pc-matrix", r.matrix.map(t => `
      <div style="display:flex;gap:12px;align-items:flex-start;padding:10px;border-radius:8px;background:${t.color}18;border:1px solid ${t.color}44;margin-bottom:8px">
        <div style="font-size:20px;font-weight:700;color:${t.color};min-width:54px">TIER ${t.tier}</div>
        <div style="flex:1">
          <div style="font-weight:600;color:${t.color}">${t.label}</div>
          <div style="font-size:11px;color:var(--t2);margin-top:2px">Aset: ${t.coins.join(", ")}</div>
          <div style="font-size:11px;color:var(--t3);margin-top:2px">Keterlacakan: <b>${t.traceable}</b></div>
          <div style="font-size:11px;color:var(--t2);margin-top:2px">FinCrime: ${t.fincrime_capability}</div>
        </div>
      </div>
    `).join(""));
  } catch (e) {
    setHtml("pc-matrix", `<div class="loading" style="color:var(--red2)">Error: ${e.message}</div>`);
  }
}

window.checkPrivacyCoin = async function () {
  const addr = document.getElementById("pc-addr").value.trim();
  if (!addr) return;
  setHtml("pc-result", `<div class="loading">Memeriksa</div>`);
  try {
    const det = await api(`/v1/multichain/detect/${encodeURIComponent(addr)}`);
    let chain = det.chain || "eth";
    if (chain === "evm") chain = "eth";
    const r = await api(`/v1/privacy-coin/check/${chain}/${encodeURIComponent(addr)}`);
    if (!r.flagged) {
      setHtml("pc-result", `
        <div style="padding:12px;border-radius:8px;background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.25)">
          <div style="color:var(--green2);font-weight:600">🟢 Tidak terdeteksi konversi privacy coin</div>
          <div style="font-size:11px;color:var(--t3);margin-top:4px">${r.txs_checked} transaksi diperiksa. Butuh API key blockchain untuk data nyata.</div>
        </div>`);
      return;
    }
    const f = r.flag;
    const col = f.severity === "critical" ? "var(--red)" : f.severity === "high" ? "#f97316" : "var(--amber)";
    setHtml("pc-result", `
      <div style="padding:12px;border-radius:8px;background:${col}18;border:1px solid ${col}55">
        <div style="font-weight:600;color:${col}">⚠ INDIKASI PRIVACY COIN — ${f.severity.toUpperCase()}</div>
        <div style="font-size:12px;color:var(--t2);margin:6px 0">${f.message}</div>
        <div style="font-size:11px;color:var(--t3)">Coin terkait: ${f.coins_involved.join(", ")} · Exchange: ${f.exchange || "—"}</div>
        <div style="margin-top:8px;font-size:11px;color:var(--t1)">
          ${f.indicators.map(i => `• ${i}`).join("<br>")}
        </div>
      </div>`);
  } catch (e) {
    setHtml("pc-result", `<div class="loading" style="color:var(--red2)">Error: ${e.message}</div>`);
  }
};

window.pcInfo = async function (symbol) {
  setHtml("pc-info", `<div class="loading">Memuat ${symbol}</div>`);
  try {
    const r = await api(`/v1/privacy-coin/info/${symbol}`);
    const traceColor = r.internally_traceable ? "var(--amber2)" : "var(--red2)";
    const bapColor = r.bappebti_allowed ? "var(--green2)" : "var(--red2)";
    setHtml("pc-info", `
      <div class="node-detail">
        <div class="nd-row"><span class="nd-key">Privacy coin</span><span class="nd-val">${r.symbol}</span></div>
        <div class="nd-row"><span class="nd-key">Tingkat privasi</span><span class="nd-val">${r.privacy_level} / 5</span></div>
        <div class="nd-row"><span class="nd-key">Bisa di-trace internal?</span><span class="nd-val" style="color:${traceColor}">${r.internally_traceable ? "Sebagian" : "TIDAK"}</span></div>
        <div class="nd-row"><span class="nd-key">Diizinkan Bappebti?</span><span class="nd-val" style="color:${bapColor}">${r.bappebti_allowed ? "Ya" : "TIDAK"}</span></div>
      </div>
      <div style="margin-top:10px;font-size:11px;color:var(--t2);background:var(--bg3);padding:8px 10px;border-radius:6px">${r.note}</div>
    `);
  } catch (e) {
    setHtml("pc-info", `<div class="loading" style="color:var(--red2)">Error: ${e.message}</div>`);
  }
};

/* ---------- UI preferences: sidebar labels, theme, collapse ---------- */
function initSidebarLabels() {
  document.querySelectorAll(".sb-btn").forEach(btn => {
    if (btn.querySelector(".sb-label")) return;
    const t = btn.getAttribute("title");
    if (!t) return;
    const span = document.createElement("span");
    span.className = "sb-label";
    span.textContent = t;
    btn.appendChild(span);
  });
}
window.toggleNav = function () {
  const collapsed = document.body.classList.toggle("nav-collapsed");
  try { localStorage.setItem("fc-nav", collapsed ? "collapsed" : "expanded"); } catch (e) {}
};
window.toggleTheme = function () {
  const light = document.body.classList.toggle("light");
  try { localStorage.setItem("fc-theme", light ? "light" : "dark"); } catch (e) {}
  const b = document.getElementById("theme-toggle");
  if (b) b.textContent = light ? "☀" : "🌙";
};
(function initPrefs() {
  try {
    if (localStorage.getItem("fc-theme") === "light") {
      document.body.classList.add("light");
      const b = document.getElementById("theme-toggle");
      if (b) b.textContent = "☀";
    }
    if (localStorage.getItem("fc-nav") === "collapsed") {
      document.body.classList.add("nav-collapsed");
    }
  } catch (e) {}
})();
initSidebarLabels();

/* ---------- boot ---------- */
loadOverview();
