/* Bedford Ave corridor strip map. No build step — plain Leaflet + fetch. */

const SEQ_RAMP = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"];
const STATUS_COLORS = { 1: "#0ca30c", 2: "#fab219", 3: "#ec835a", 4: "#d03b3b" };
const UNKNOWN_COLOR = "#c3c2b7";

let corridorData = null;
let currentView = "raw";
let currentPeriod = "before";
let map, layerGroup;

async function loadData() {
  const resp = await fetch("data/corridor.json");
  if (!resp.ok) throw new Error(`Failed to load corridor.json: ${resp.status}`);
  return resp.json();
}

function seqColor(value, min, max) {
  if (value === null || value === undefined || max === min) return UNKNOWN_COLOR;
  const t = Math.max(0, Math.min(1, (value - min) / (max - min)));
  const idx = Math.min(SEQ_RAMP.length - 1, Math.floor(t * SEQ_RAMP.length));
  return SEQ_RAMP[idx];
}

function blockValue(block, view, period) {
  if (view === "raw") {
    const c = block.raw_counts;
    if (!c || !c.computed) return null;
    return c[period]?.cyclist_injuries ?? null;
  }
  if (view === "rate") {
    const r = block.rate_per_10k_trips;
    if (!r || !r.computed) return null;
    return r[period] ?? null;
  }
  if (view === "lts") {
    return block.lts ?? null;
  }
  return null;
}

function colorFor(block, view, period, domain) {
  const value = blockValue(block, view, period);
  if (value === null) return UNKNOWN_COLOR;
  if (view === "lts") return STATUS_COLORS[value] ?? UNKNOWN_COLOR;
  return seqColor(value, domain.min, domain.max);
}

function computeDomain(blocks, view, period) {
  const values = blocks
    .map((b) => blockValue(b, view, period))
    .filter((v) => v !== null && view !== "lts");
  if (values.length === 0) return { min: 0, max: 1 };
  return { min: Math.min(...values), max: Math.max(...values) };
}

function renderLegend(view) {
  const el = document.getElementById("legend");
  if (view === "lts") {
    el.innerHTML =
      "LTS: " +
      [1, 2, 3, 4]
        .map((n) => `<span class="swatch" style="background:${STATUS_COLORS[n]}"></span>${n}`)
        .join(" &nbsp; ") +
      ` &nbsp; <span class="swatch" style="background:${UNKNOWN_COLOR}"></span>not surveyed`;
  } else {
    const label = view === "raw" ? "cyclist injuries" : "injuries / 10k trips";
    el.innerHTML =
      `Low ${label} <span class="ramp">${SEQ_RAMP.map((c) => `<span style="background:${c}"></span>`).join("")}</span> High` +
      ` &nbsp; <span class="swatch" style="background:${UNKNOWN_COLOR}"></span>not yet computed`;
  }
}

function renderDataStatus(status) {
  const el = document.getElementById("data-status");
  const chip = (label, ok) => `<span class="status-chip ${ok ? "ok" : "pending"}">${ok ? "✓" : "○"} ${label}</span>`;
  el.innerHTML = [
    chip("block geometry", status.segmentation_available),
    chip("crash counts", status.raw_counts_available),
    chip("trip rates", status.rates_available),
    chip("effect estimate", status.did_available),
  ].join("");
}

function fmtNum(n) {
  if (n === null || n === undefined) return "—";
  return typeof n === "number" ? n.toLocaleString(undefined, { maximumFractionDigits: 1 }) : n;
}

function renderPanel(block) {
  const el = document.getElementById("panel");
  const treatedBadge = block.is_treated
    ? `<span class="badge treated-badge">Deprotected block</span>`
    : `<span class="badge control-badge">Still protected</span>`;

  const raw = block.raw_counts;
  const rate = block.rate_per_10k_trips;

  const rawRows = raw && raw.computed
    ? `<dt>Injuries (before)</dt><dd>${fmtNum(raw.before.cyclist_injuries)}</dd>
       <dt>Injuries (after)</dt><dd>${fmtNum(raw.after.cyclist_injuries)}</dd>`
    : `<dt>Injuries</dt><dd class="null-note">not yet computed — needs segmentation.segment_corridor()</dd>`;

  const rateRows = rate && rate.computed
    ? `<dt>Rate (before)</dt><dd>${fmtNum(rate.before)} / 10k trips</dd>
       <dt>Rate (after)</dt><dd>${fmtNum(rate.after)} / 10k trips</dd>
       <dt>After, CI</dt><dd>${rate.after_interval && !rate.after_interval.is_null
         ? `${fmtNum(rate.after_interval.low)}–${fmtNum(rate.after_interval.high)}`
         : `<span class="null-note">null / not enough data</span>`}</dd>`
    : `<dt>Rate</dt><dd class="null-note">not yet computed — needs denominator.py</dd>`;

  const ltsRow = block.lts
    ? `<dt>LTS</dt><dd>${block.lts}${block.lts_notes ? " — " + block.lts_notes : ""}</dd>`
    : `<dt>LTS</dt><dd class="null-note">not yet surveyed (config/lts.yaml)</dd>`;

  el.innerHTML = `
    <h2>${block.from_street} → ${block.to_street}</h2>
    ${treatedBadge}
    <dl>
      ${rawRows}
      ${rateRows}
      ${ltsRow}
    </dl>
  `;
}

function drawBlocks() {
  layerGroup.clearLayers();
  const domain = computeDomain(corridorData.blocks, currentView, currentPeriod);

  for (const block of corridorData.blocks) {
    if (!block.from_coords || !block.to_coords) continue;
    const color = colorFor(block, currentView, currentPeriod, domain);
    const coords = [block.from_coords, block.to_coords];

    // Dark casing first, so a light "not yet computed" gray (or any fill
    // close to the basemap's own palette) still reads clearly on the tiles.
    L.polyline(coords, {
      color: "#0b0b0b",
      weight: 12,
      opacity: 0.35,
      lineCap: "round",
      interactive: false,
    }).addTo(layerGroup);

    const line = L.polyline(coords, {
      color,
      weight: 7,
      opacity: 1,
      dashArray: block.is_treated ? "1, 9" : null,
      lineCap: "round",
    });
    line.on("mouseover click", () => renderPanel(block));
    line.addTo(layerGroup);
  }
}

function wireControls() {
  document.querySelectorAll(".view-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".view-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentView = btn.dataset.view;
      renderLegend(currentView);
      drawBlocks();
    });
  });
  document.querySelectorAll(".period-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".period-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentPeriod = btn.dataset.period;
      drawBlocks();
    });
  });
}

async function init() {
  corridorData = await loadData();

  const coords = corridorData.blocks
    .flatMap((b) => [b.from_coords, b.to_coords])
    .filter(Boolean);

  map = L.map("map");
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 19,
  }).addTo(map);
  layerGroup = L.layerGroup().addTo(map);

  if (coords.length > 0) {
    map.fitBounds(L.latLngBounds(coords), { padding: [30, 30] });
  } else {
    map.setView([40.685, -73.955], 14);
  }

  renderLegend(currentView);
  renderDataStatus(corridorData.data_status);
  drawBlocks();
  wireControls();
}

init().catch((err) => {
  document.getElementById("panel").innerHTML =
    `<div class="panel-empty">Could not load corridor.json: ${err.message}<br><br>Run <code>make build</code> first.</div>`;
  console.error(err);
});
