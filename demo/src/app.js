(async () => {
  "use strict";
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const status = $("#status");
  const META = JSON.parse($("#meta").textContent);
  const F = Math.fround;
  const N = META.n;
  const SESS = META.sessions;
  const INPUTS = META.inputs;
  const FEATURES = META.features;
  const NF = FEATURES.length;
  const SIGMA = META.safety.sigma;
  const THOT = META.safety.tHot;
  const PER_MIN = 120;
  const MINUS = "−";

  const num = (v, d = 1) => {
    const s = Math.abs(v).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
    return (v < 0 && Number(s.replace(/,/g, "")) !== 0 ? MINUS : "") + s;
  };
  const signed = (v, d = 1) => (v > 0 ? "+" : "") + num(v, d);
  const deg = (v, d = 1) => `${num(v, d)} °C`;
  const paren = (v, d = 1) => (v < 0 ? `(${num(v, d)})` : num(v, d));
  const clock = (samples) => {
    const total = Math.round(samples / PER_MIN), h = Math.floor(total / 60), m = total % 60;
    return h ? `${h} h ${m} min` : `${m} min`;
  };
  const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const C = {
    est: cssVar("--est"), ridge: cssVar("--ridge"), real: cssVar("--real"), cool: cssVar("--cool"),
    hot: cssVar("--hot"), navy: cssVar("--navy"), muted: cssVar("--muted"), line: cssVar("--line"),
    soft: cssVar("--line-soft"), ink: cssVar("--ink"), ink2: cssVar("--ink-2"), lgbm: cssVar("--lgbm"),
  };
  const POS = "#e0662e", NEG = "#2a78d6", OFF = "#e6e8ee";
  const SPAN_BLUES = ["#a9c9ee", "#6ea4e4", "#2a78d6", "#163f7a"];

  const SIGNALS = {
    ambient: { name: "Ambient temperature", unit: "°C", d: 1 },
    coolant: { name: "Coolant temperature", unit: "°C", d: 1 },
    u_d: { name: "Voltage, d axis", unit: "V", d: 1 },
    u_q: { name: "Voltage, q axis", unit: "V", d: 1 },
    i_d: { name: "Current, d axis", unit: "A", d: 1 },
    i_q: { name: "Current, q axis", unit: "A", d: 1 },
    motor_speed: { name: "Motor speed", unit: "rpm", d: 0 },
    torque: { name: "Torque", unit: "N·m", d: 1 },
    i_s: { name: "Current magnitude", unit: "A", d: 1 },
    u_s: { name: "Voltage magnitude", unit: "V", d: 1 },
    i_s_sq: { name: "Current squared", unit: "A²", d: 0 },
    p_el: { name: "Electrical power", unit: "W", d: 0 },
    p_mech: { name: "Mechanical power", unit: "W", d: 0 },
  };
  const SPANS = { 120: "1 min", 600: "5 min", 1800: "15 min", 5400: "45 min" };
  const featInfo = (f) => {
    const k = f.lastIndexOf("_ewma_");
    if (k < 0) return { ...SIGNALS[f], label: SIGNALS[f].name };
    const base = SIGNALS[f.slice(0, k)];
    return { ...base, label: `${base.name}, ${SPANS[f.slice(k + 6)]} average` };
  };

  // ---------- data
  async function decode() {
    const b64 = $("#blob").textContent.trim();
    const bin = atob(b64);
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
    const buf = new Uint8Array(await new Response(stream).arrayBuffer());
    const out = {};
    for (const L of META.layout) {
      if (L.kind === "f32shuf") {
        const raw = new Uint8Array(N * 4);
        for (let b = 0; b < 4; b++) {
          const base = L.offset + b * N;
          for (let i = 0; i < N; i++) raw[i * 4 + b] = buf[base + i];
        }
        out[L.name] = new Float32Array(raw.buffer);
      } else {
        const dv = new DataView(buf.buffer, buf.byteOffset + L.offset, N * 4);
        const col = new Float64Array(N);
        let acc = 0;
        for (let i = 0; i < N; i++) { acc += dv.getInt32(i * 4, true); col[i] = acc / 1000; }
        out[L.name] = col;
      }
    }
    return out;
  }
  if (typeof DecompressionStream === "undefined") {
    status.textContent = "This browser cannot unpack the data. Please use a current Chrome, Edge, Firefox or Safari.";
    return;
  }
  const D = await decode();
  const TARGET = META.layout[INPUTS.length].name;
  const REAL = D[TARGET];
  const INCOLS = INPUTS.map((c) => D[c]);

  // ---------- the model in JavaScript: same maths as our Python features and the scikit-learn pipeline
  const FI = Object.fromEntries(FEATURES.map((f, i) => [f, i]));
  const IN_IDX = INPUTS.map((c) => FI[c]);
  const EW = [];
  FEATURES.forEach((f, j) => {
    const k = f.lastIndexOf("_ewma_");
    if (k > 0) EW.push({ j, base: FI[f.slice(0, k)], w: 1 - 2 / (Number(f.slice(k + 6)) + 1) });
  });
  const EW_J = Int32Array.from(EW, (e) => e.j), EW_B = Int32Array.from(EW, (e) => e.base), EW_W = Float64Array.from(EW, (e) => e.w);
  const SI = (n) => INPUTS.indexOf(n);
  const iD = SI("i_d"), iQ = SI("i_q"), uD = SI("u_d"), uQ = SI("u_q"), SP = SI("motor_speed"), TQ = SI("torque"), CO = SI("coolant");

  function prep(m) {
    m.meanF = Float64Array.from(m.mean);
    m.scaleF = Float64Array.from(m.scale);
    if (m.layers) for (const L of m.layers) { L.Wf = Float64Array.from(L.W, F); L.bf = Float64Array.from(L.b, F); }
    if (m.coef) { m.coefF = Float64Array.from(m.coef, F); m.b0 = F(m.intercept); }
  }
  const MLP = META.mlp, RIDGE = META.ridge;
  prep(MLP); prep(RIDGE);
  const [L1, L2, L3] = MLP.layers;
  const H1 = L1.out, H2 = L2.out;

  class Engine {
    constructor() {
      this.x = new Float64Array(NF); this.num = new Float64Array(NF); this.den = new Float64Array(NF);
      this.z = new Float64Array(NF); this.h1 = new Float64Array(H1); this.h2 = new Float64Array(H2);
      this.mlp = NaN; this.ridge = NaN;
    }
    reset() { this.num.fill(0); this.den.fill(0); this.mlp = NaN; this.ridge = NaN; }
    step(s) {
      const x = this.x;
      for (let k = 0; k < IN_IDX.length; k++) x[IN_IDX[k]] = s[k];
      const id = s[iD], iq = s[iQ], ud = s[uD], uq = s[uQ];
      const is64 = Math.sqrt(id * id + iq * iq);
      x[FI.i_s] = F(is64);
      x[FI.u_s] = F(Math.sqrt(ud * ud + uq * uq));
      x[FI.i_s_sq] = F(is64 * is64);
      x[FI.p_el] = F(1.5 * (ud * id + uq * iq));
      x[FI.p_mech] = F(s[TQ] * s[SP] * 2 * Math.PI / 60);
      for (let e = 0; e < EW_J.length; e++) {
        const j = EW_J[e], w = EW_W[e];
        this.num[j] = x[EW_B[e]] + w * this.num[j];
        this.den[j] = 1 + w * this.den[j];
        x[j] = F(this.num[j] / this.den[j]);
      }
      const z = this.z, h1 = this.h1, h2 = this.h2;
      for (let j = 0; j < NF; j++) z[j] = (x[j] - MLP.meanF[j]) / MLP.scaleF[j];
      h1.set(L1.bf);
      for (let i = 0; i < NF; i++) {
        const zi = z[i], o0 = i * H1, W = L1.Wf;
        for (let o = 0; o < H1; o++) h1[o] += zi * W[o0 + o];
      }
      for (let o = 0; o < H1; o++) if (h1[o] < 0) h1[o] = 0;
      h2.set(L2.bf);
      for (let i = 0; i < H1; i++) {
        const a = h1[i];
        if (a === 0) continue;
        const o0 = i * H2, W = L2.Wf;
        for (let o = 0; o < H2; o++) h2[o] += a * W[o0 + o];
      }
      for (let o = 0; o < H2; o++) if (h2[o] < 0) h2[o] = 0;
      let y = L3.bf[0];
      for (let i = 0; i < H2; i++) y += h2[i] * L3.Wf[i];
      this.mlp = y;
      let r = RIDGE.b0;
      for (let j = 0; j < NF; j++) r += ((x[j] - RIDGE.meanF[j]) / RIDGE.scaleF[j]) * RIDGE.coefF[j];
      this.ridge = r;
    }
  }

  // ---------- run the whole test set (start-up self-check and the "run the test set" button)
  const LIVE = { mlp: new Float32Array(N), ridge: new Float32Array(N), ready: false };
  async function runAll(onProgress) {
    const eng = new Engine(), sig = new Float64Array(INPUTS.length);
    const t0 = performance.now();
    let done = 0;
    for (const s of SESS) {
      eng.reset();
      for (let g = s.start; g < s.start + s.rows; g++) {
        for (let k = 0; k < sig.length; k++) sig[k] = INCOLS[k][g];
        eng.step(sig);
        LIVE.mlp[g] = eng.mlp;
        LIVE.ridge[g] = eng.ridge;
        if (++done % 6000 === 0) { onProgress(done / N); await new Promise((r) => setTimeout(r, 0)); }
      }
    }
    onProgress(1);
    const ms = performance.now() - t0;
    let dM = 0, dR = 0, seM = 0, seR = 0;
    for (let g = 0; g < N; g++) {
      dM = Math.max(dM, Math.abs(LIVE.mlp[g] - D.m6[g]));
      dR = Math.max(dR, Math.abs(LIVE.ridge[g] - D.m3[g]));
      seM += (LIVE.mlp[g] - REAL[g]) ** 2;
      seR += (LIVE.ridge[g] - REAL[g]) ** 2;
    }
    LIVE.ready = true;
    return { ms, dM, dR, rmseM: Math.sqrt(seM / N), rmseR: Math.sqrt(seR / N) };
  }

  const check = await runAll((p) => { status.textContent = `Checking the model on all ${N.toLocaleString("en-US")} test rows: ${Math.round(p * 100)} %`; });
  const statusText = () => `Running in this browser. Self-check: on all ${N.toLocaleString("en-US")} test rows our MLP gives the same estimates as the Python model, to within ${num(Math.max(check.dM, 0.001), 3)} °C.`;
  status.textContent = statusText();

  // ---------- canvas helpers
  function canvasCtx(cv) {
    const w = cv.clientWidth, h = cv.clientHeight;
    if (!w || !h) return null;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const W = Math.round(w * dpr), H = Math.round(h * dpr);
    if (cv.width !== W || cv.height !== H) { cv.width = W; cv.height = H; }
    const ctx = cv.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    return { ctx, w, h };
  }
  const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const mix = (a, b, t) => {
    const A = hex(a), B = hex(b);
    return `rgb(${A.map((v, i) => Math.round(v + (B[i] - v) * t)).join(",")})`;
  };
  const act = (t) => (t <= 0 ? OFF : t < 0.5 ? mix("#f9dccb", POS, t * 2) : mix(POS, "#7c2a0b", (t - 0.5) * 2));
  const div = (v, scale) => {
    const t = Math.max(-1, Math.min(1, v / scale));
    return t >= 0 ? mix("#eef0f4", POS, t) : mix("#eef0f4", NEG, -t);
  };
  function niceStep(span, target) {
    const raw = span / target, p = 10 ** Math.floor(Math.log10(raw)), m = raw / p;
    return (m < 1.5 ? 1 : m < 3.5 ? 2 : m < 7.5 ? 5 : 10) * p;
  }
  function minuteTicks(minutes) {
    for (const s of [5, 10, 15, 30, 60, 120]) if (minutes / s <= 8) return s;
    return 240;
  }
  function envelopePath(ctx, arr, offset, count, x0, xScale, yOf) {
    // one vertical stroke per pixel column: keeps 40,000 samples cheap to draw and still honest
    let col = -1, lo = 0, hi = 0, started = false;
    const flush = () => {
      const x = x0 + col + 0.5;
      if (!started) { ctx.moveTo(x, yOf(lo)); started = true; } else ctx.lineTo(x, yOf(lo));
      if (hi !== lo) ctx.lineTo(x, yOf(hi));
    };
    for (let i = 0; i < count; i++) {
      const v = arr[offset + i];
      if (!Number.isFinite(v)) continue;
      const c = Math.floor(i * xScale);
      if (c !== col) { if (col >= 0) flush(); col = c; lo = hi = v; } else { if (v < lo) lo = v; if (v > hi) hi = v; }
    }
    if (col >= 0) flush();
  }

  // ---------- replay state
  const rep = {
    si: Math.max(0, SESS.findIndex((s) => s.id === 66)), model: "mlp", speed: 5, playing: false,
    i: 0, acc: 0, eng: new Engine(), sig: new Float64Array(INPUTS.length),
    estM: null, estR: null, feats: null, h1: null, isRaw: null, seM: 0, seR: 0, usPerStep: 0, steps: 0,
  };
  const kRange = $("#k-range");
  const kVal = () => Number(kRange.value);

  function selectSession(si) {
    const s = SESS[si];
    rep.si = si; rep.i = 0; rep.acc = 0; rep.seM = 0; rep.seR = 0; rep.steps = 0;
    rep.estM = new Float32Array(s.rows).fill(NaN);
    rep.estR = new Float32Array(s.rows).fill(NaN);
    rep.feats = new Float32Array(s.rows * NF);
    rep.isRaw = new Float32Array(s.rows);
    for (let i = 0; i < s.rows; i++) {
      const g = s.start + i, id = D.i_d[g], iq = D.i_q[g];
      rep.isRaw[i] = Math.sqrt(id * id + iq * iq);
    }
    rep.eng.reset();
    stepReplay(1);
    $$("#sess-list button").forEach((b) => b.setAttribute("aria-pressed", String(Number(b.dataset.si) === si)));
    $("#sess-title").textContent = `Session ${s.id}`;
    dirty.all = true;
  }

  function stepReplay(count) {
    const s = SESS[rep.si], eng = rep.eng, sig = rep.sig;
    const t0 = performance.now();
    let done = 0;
    while (done < count && rep.i < s.rows) {
      const g = s.start + rep.i;
      for (let k = 0; k < sig.length; k++) sig[k] = INCOLS[k][g];
      eng.step(sig);
      rep.estM[rep.i] = eng.mlp;
      rep.estR[rep.i] = eng.ridge;
      rep.feats.set(eng.x, rep.i * NF);
      rep.seM += (eng.mlp - REAL[g]) ** 2;
      rep.seR += (eng.ridge - REAL[g]) ** 2;
      rep.i++; done++;
    }
    rep.steps += done;
    if (done) {
      const us = (performance.now() - t0) * 1000 / done;
      rep.usPerStep = rep.usPerStep ? rep.usPerStep * 0.9 + us * 0.1 : us;
    }
  }

  // ---------- live chart
  function drawLive() {
    const c = canvasCtx($("#live"));
    if (!c) return;
    const { ctx, w, h } = c, s = SESS[rep.si];
    const L = 42, R = 14, T = 10, B = 54;
    const pw = w - L - R, ph = h - T - B;
    const yMin = 10, yMax = 150;
    const yOf = (v) => T + ph - ((Math.max(yMin, Math.min(yMax, v)) - yMin) / (yMax - yMin)) * ph;
    const xScale = pw / s.rows;
    const nowX = L + rep.i * xScale;
    ctx.font = "12px Segoe UI, system-ui, sans-serif";
    ctx.textBaseline = "middle";
    // future area: the model has not reached it yet
    ctx.fillStyle = "#f4f5f8";
    ctx.fillRect(nowX, T, L + pw - nowX, ph);
    if (L + pw - nowX > 150) {
      ctx.fillStyle = C.muted; ctx.textAlign = "center";
      ctx.fillText("not computed yet", (nowX + L + pw) / 2, T + ph / 2);
    }
    // grid and axes
    ctx.strokeStyle = C.soft; ctx.lineWidth = 1; ctx.fillStyle = C.muted; ctx.textAlign = "right";
    for (let v = 20; v <= 140; v += 20) {
      const y = Math.round(yOf(v)) + 0.5;
      ctx.beginPath(); ctx.moveTo(L, y); ctx.lineTo(L + pw, y); ctx.stroke();
      ctx.fillText(String(v), L - 6, y);
    }
    ctx.save(); ctx.translate(11, T + ph / 2); ctx.rotate(-Math.PI / 2); ctx.textAlign = "center"; ctx.fillText("°C", 0, 0); ctx.restore();
    const minutes = s.rows / PER_MIN, tick = minuteTicks(minutes);
    ctx.textAlign = "center";
    for (let m = 0; m <= minutes + 0.01; m += tick) {
      const x = L + m * PER_MIN * xScale;
      ctx.fillText(m >= 60 && m % 60 === 0 ? `${m / 60} h` : `${m} min`, x, h - 8);
    }
    // hot level and alarm trigger lines; their labels go on top of the curves further down
    const k = kVal(), yHot = Math.round(yOf(THOT)) + 0.5, yTrig = Math.round(yOf(THOT - k * SIGMA)) + 0.5;
    ctx.setLineDash([6, 4]); ctx.strokeStyle = C.hot; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(L, yHot); ctx.lineTo(L + pw, yHot); ctx.stroke();
    if (k > 0) {
      ctx.setLineDash([2, 3]); ctx.globalAlpha = 0.7;
      ctx.beginPath(); ctx.moveTo(L, yTrig); ctx.lineTo(L + pw, yTrig); ctx.stroke();
      ctx.globalAlpha = 1;
    }
    ctx.setLineDash([]);
    // the real sensor and the estimate, up to now
    ctx.lineJoin = "round";
    ctx.beginPath(); envelopePath(ctx, REAL, s.start, rep.i, L, xScale, yOf);
    ctx.strokeStyle = C.real; ctx.lineWidth = 1.4; ctx.stroke();
    const est = rep.model === "mlp" ? rep.estM : rep.estR;
    ctx.beginPath(); envelopePath(ctx, est, 0, rep.i, L, xScale, yOf);
    ctx.strokeStyle = rep.model === "mlp" ? C.est : C.ridge; ctx.lineWidth = 2; ctx.stroke();
    const halo = (text, x, y, base) => {
      ctx.textBaseline = base; ctx.textAlign = "right";
      ctx.lineWidth = 4; ctx.strokeStyle = "rgba(255,255,255,.92)"; ctx.strokeText(text, x, y);
      ctx.fillStyle = C.hot; ctx.fillText(text, x, y);
    };
    halo(`Hot level ${num(THOT)} °C`, L + pw - 6, yHot - 3, "bottom");
    if (k > 0) halo(`Alarm when the estimate reaches ${num(THOT - k * SIGMA)} °C`, L + pw - 6, yTrig + 3, "top");
    ctx.textBaseline = "middle";
    // hot and alarm strips
    const sy = T + ph + 6, sh = 8;
    ctx.fillStyle = C.muted; ctx.textAlign = "right"; ctx.font = "11px Segoe UI, system-ui, sans-serif";
    ctx.fillText("hot", L - 6, sy + sh / 2); ctx.fillText("alarm", L - 6, sy + sh + 5 + sh / 2);
    ctx.fillStyle = "#f0f1f5"; ctx.fillRect(L, sy, pw, sh); ctx.fillRect(L, sy + sh + 5, pw, sh);
    const trig = THOT - k * SIGMA;
    let hotStart = -1, alStart = -1;
    for (let i = 0; i <= rep.i; i++) {
      const isHot = i < rep.i && REAL[s.start + i] >= THOT, isAl = i < rep.i && est[i] >= trig;
      if (isHot && hotStart < 0) hotStart = i;
      if (!isHot && hotStart >= 0) { ctx.fillStyle = C.real; ctx.fillRect(L + hotStart * xScale, sy, Math.max(1, (i - hotStart) * xScale), sh); hotStart = -1; }
      if (isAl && alStart < 0) alStart = i;
      if (!isAl && alStart >= 0) { ctx.fillStyle = C.hot; ctx.fillRect(L + alStart * xScale, sy + sh + 5, Math.max(1, (i - alStart) * xScale), sh); alStart = -1; }
    }
    // now marker
    if (rep.i > 0) {
      ctx.strokeStyle = C.ink; ctx.lineWidth = 1; ctx.globalAlpha = 0.5;
      ctx.beginPath(); ctx.moveTo(Math.round(nowX) + 0.5, T); ctx.lineTo(Math.round(nowX) + 0.5, T + ph); ctx.stroke();
      ctx.globalAlpha = 1;
      const last = rep.i - 1;
      for (const [v, col] of [[REAL[s.start + last], C.real], [est[last], rep.model === "mlp" ? C.est : C.ridge]]) {
        ctx.beginPath(); ctx.arc(nowX, yOf(v), 4.5, 0, Math.PI * 2);
        ctx.fillStyle = col; ctx.fill(); ctx.strokeStyle = "#fff"; ctx.lineWidth = 2; ctx.stroke();
      }
    }
  }

  function drawSignals() {
    const c = canvasCtx($("#signals"));
    if (!c) return;
    const { ctx, w, h } = c, s = SESS[rep.si];
    const L = 42, R = 14, pw = w - L - R, gap = 8, sh = (h - gap * 2) / 3;
    const xScale = pw / s.rows;
    const rows = [
      { label: "Current", unit: "A", arr: rep.isRaw, off: 0, col: C.navy },
      { label: "Speed", unit: "rpm", arr: D.motor_speed, off: s.start, col: C.navy },
      { label: "Coolant", unit: "°C", arr: D.coolant, off: s.start, col: C.cool },
    ];
    ctx.font = "11px Segoe UI, system-ui, sans-serif"; ctx.textBaseline = "top";
    rows.forEach((r, k) => {
      const top = k * (sh + gap);
      let lo = Infinity, hi = -Infinity;
      for (let i = 0; i < s.rows; i++) { const v = r.arr[r.off + i]; if (v < lo) lo = v; if (v > hi) hi = v; }
      if (hi - lo < 1e-6) { hi = lo + 1; }
      const yOf = (v) => top + sh - 3 - ((v - lo) / (hi - lo)) * (sh - 21);
      ctx.fillStyle = "#f6f7fa"; ctx.fillRect(L, top, pw, sh);
      ctx.fillStyle = C.ink2; ctx.textAlign = "left";
      const nowV = rep.i ? r.arr[r.off + rep.i - 1] : NaN;
      ctx.fillText(`${r.label}${Number.isFinite(nowV) ? `: ${num(nowV, r.unit === "rpm" ? 0 : 1)} ${r.unit}` : ""}`, L + 6, top + 2);
      ctx.beginPath(); envelopePath(ctx, r.arr, r.off, rep.i, L, xScale, yOf);
      ctx.strokeStyle = r.col; ctx.lineWidth = 1.2; ctx.stroke();
    });
  }

  // ---------- readout, lamp and the small network view
  function lampText(alarm, hot) {
    if (alarm && hot) return "Correct: the winding really is hot.";
    if (alarm) return "False alarm: the real winding is below the hot level.";
    if (hot) return "Missed: the winding is hot, the estimate plus margin is not.";
    return "The winding is below the hot level.";
  }
  function renderReadout() {
    const s = SESS[rep.si], last = rep.i - 1;
    const est = rep.model === "mlp" ? rep.estM[last] : rep.estR[last];
    const real = REAL[s.start + last];
    $("#ro-model").textContent = rep.model === "mlp" ? "Estimate, MLP" : "Estimate, Ridge";
    $("#ro-est").textContent = deg(est);
    $("#ro-est").style.color = rep.model === "mlp" ? C.est : C.ridge;
    $("#ro-real").textContent = deg(real);
    $("#ro-err").textContent = `${signed(est - real)} °C`;
    $("#ro-rmse").textContent = deg(Math.sqrt((rep.model === "mlp" ? rep.seM : rep.seR) / rep.i), 2);
    $("#clock").textContent = `${clock(rep.i)} of ${clock(s.rows)}`;
    const k = kVal(), alarm = est + k * SIGMA >= THOT, hot = real >= THOT;
    $("#lamp").classList.toggle("on", alarm);
    $("#lamp-state").textContent = alarm ? "Alarm on" : "No alarm";
    $("#lamp-verdict").textContent = lampText(alarm, hot);
    $("#engine-note").textContent = `${rep.steps.toLocaleString("en-US")} ${rep.steps === 1 ? "estimate" : "estimates"} computed so far in this session, about ${num(Math.max(rep.usPerStep, 0.1), 1)} µs each. Each one turns the 8 signals into 45 inputs and runs them through 64 and 32 neurons.`;
  }

  function drawMiniNet() {
    const c = canvasCtx($("#mini-net"));
    if (!c) return;
    const { ctx, w } = c, e = rep.eng;
    const layers = [
      { label: "45 inputs after scaling", vals: e.z, perRow: 23, color: (v) => div(v, 3) },
      { label: "First layer, 64 neurons", vals: e.h1, perRow: 32, color: null },
      { label: "Second layer, 32 neurons", vals: e.h2, perRow: 32, color: null },
    ];
    let y = 0;
    ctx.font = "11.5px Segoe UI, system-ui, sans-serif"; ctx.textBaseline = "top";
    for (const ly of layers) {
      const n = ly.vals.length, rows = Math.ceil(n / ly.perRow), cw = w / ly.perRow, chh = Math.min(10, cw);
      let mx = 0, active = 0;
      for (const v of ly.vals) { if (v > mx) mx = v; if (v > 0) active++; }
      ctx.fillStyle = C.ink2; ctx.textAlign = "left";
      ctx.fillText(ly.label, 0, y);
      if (!ly.color) { ctx.fillStyle = C.muted; ctx.textAlign = "right"; ctx.fillText(`${active} active`, w, y); }
      y += 16;
      for (let i = 0; i < n; i++) {
        const r = Math.floor(i / ly.perRow), col = i % ly.perRow;
        ctx.fillStyle = ly.color ? ly.color(ly.vals[i]) : act(mx ? ly.vals[i] / mx : 0);
        ctx.fillRect(col * cw + 0.5, y + r * (chh + 2), cw - 1.5, chh);
      }
      y += rows * (chh + 2) + 10;
    }
    ctx.fillStyle = C.ink2; ctx.textAlign = "left"; ctx.textBaseline = "middle";
    ctx.fillText("Output, the estimate", 0, y + 9);
    ctx.fillStyle = C.est; ctx.font = "bold 16px Segoe UI, system-ui, sans-serif"; ctx.textAlign = "right";
    ctx.fillText(Number.isFinite(e.mlp) ? deg(e.mlp) : "–", w, y + 9);
  }

  // ---------- inside the model
  let step = 0, memBase = "i_s_sq";
  const xNow = () => rep.eng.x;
  function renderSignals() {
    const x = xNow(), tr = META.trainRange;
    $("#sig-table").innerHTML = `<thead><tr><th>Signal</th><th>Symbol</th><th>Value now</th><th>Within the training range</th></tr></thead><tbody>` +
      INPUTS.map((c) => {
        const info = SIGNALS[c], v = x[FI[c]], [lo, hi] = tr[c];
        const p = Math.max(0, Math.min(100, ((v - lo) / (hi - lo)) * 100));
        return `<tr><td>${info.name}</td><td class="sym">${c}</td><td class="val">${num(v, info.d)} ${info.unit}</td>` +
          `<td><span class="range-bar" title="${num(lo, info.d)} to ${num(hi, info.d)} ${info.unit}"><i style="left:${p}%"></i></span></td></tr>`;
      }).join("") + "</tbody>";
  }
  function renderPhysics() {
    const x = xNow(), g = (n) => x[FI[n]];
    const id = g("i_d"), iq = g("i_q"), ud = g("u_d"), uq = g("u_q");
    const rows = [
      ["Current magnitude", `i<sub>s</sub> = &radic;(i<sub>d</sub>&sup2; + i<sub>q</sub>&sup2;) = &radic;(${paren(id)}&sup2; + ${paren(iq)}&sup2;) = <b>${num(g("i_s"))} A</b>`, "How much current flows in total, whatever its direction."],
      ["Current squared", `i<sub>s</sub>&sup2; = ${num(g("i_s"))}&sup2; = <b>${num(g("i_s_sq"), 0)} A&sup2;</b>`, "Copper loss is I&sup2;R, so this is the heat being made in the winding, up to a constant."],
      ["Voltage magnitude", `u<sub>s</sub> = &radic;(u<sub>d</sub>&sup2; + u<sub>q</sub>&sup2;) = &radic;(${paren(ud)}&sup2; + ${paren(uq)}&sup2;) = <b>${num(g("u_s"))} V</b>`, "The size of the voltage the controller applies."],
      ["Electrical power", `p<sub>el</sub> = 1.5 &times; (u<sub>d</sub>i<sub>d</sub> + u<sub>q</sub>i<sub>q</sub>) = 1.5 &times; (${paren(ud)} &times; ${paren(id)} + ${paren(uq)} &times; ${paren(iq)}) = <b>${num(g("p_el"), 0)} W</b>`, "Power going into the motor."],
      ["Mechanical power", `p<sub>mech</sub> = torque &times; speed &times; 2&pi; &divide; 60 = ${paren(g("torque"))} &times; ${num(g("motor_speed"), 0)} &times; 2&pi; &divide; 60 = <b>${num(g("p_mech"), 0)} W</b>`, "Power coming out at the shaft."],
    ];
    $("#phys").innerHTML = rows.map(([h, eq, why]) => `<div class="phys-row"><h4>${h}</h4><div class="eq">${eq}</div><div class="why">${why}</div></div>`).join("");
  }
  const MEM_BASES = ["i_s_sq", "i_s", "p_el", "u_s", "motor_speed", "torque", "coolant", "ambient"];
  const MEM_SHORT = { i_s_sq: "Current²", i_s: "Current", p_el: "Electrical power", u_s: "Voltage", motor_speed: "Speed", torque: "Torque", coolant: "Coolant", ambient: "Ambient" };
  $("#mem-sig").innerHTML = MEM_BASES.map((b) => `<button type="button" data-base="${b}" aria-pressed="${b === memBase}">${MEM_SHORT[b]}</button>`).join("");
  $("#mem-sig").addEventListener("click", (ev) => {
    const b = ev.target.closest("button[data-base]");
    if (!b) return;
    memBase = b.dataset.base;
    $$("#mem-sig button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    renderMemory();
  });
  function renderMemory() {
    const c = canvasCtx($("#mem-canvas"));
    const info = SIGNALS[memBase], spans = Object.keys(SPANS);
    const idx = [FI[memBase], ...spans.map((s) => FI[`${memBase}_ewma_${s}`])];
    const end = rep.i, start = Math.max(0, end - 60 * PER_MIN);
    if (c) {
      const { ctx, w, h } = c, L = 60, R = 12, T = 10, B = 26, pw = w - L - R, ph = h - T - B;
      let lo = Infinity, hi = -Infinity;
      for (let i = start; i < end; i++) for (const j of idx) { const v = rep.feats[i * NF + j]; if (v < lo) lo = v; if (v > hi) hi = v; }
      if (!(hi > lo)) { hi = lo + 1; lo -= 1; }
      const pad = (hi - lo) * 0.08; lo -= pad; hi += pad;
      const yOf = (v) => T + ph - ((v - lo) / (hi - lo)) * ph;
      const xOf = (i) => L + pw - ((end - 1 - i) / (60 * PER_MIN)) * pw;
      ctx.font = "12px Segoe UI, system-ui, sans-serif"; ctx.fillStyle = C.muted; ctx.textBaseline = "middle"; ctx.textAlign = "right";
      const stepV = niceStep(hi - lo, 4);
      ctx.strokeStyle = C.soft;
      for (let v = Math.ceil(lo / stepV) * stepV; v <= hi; v += stepV) {
        const y = Math.round(yOf(v)) + 0.5;
        ctx.beginPath(); ctx.moveTo(L, y); ctx.lineTo(L + pw, y); ctx.stroke();
        ctx.fillText(num(v, Math.abs(stepV) < 1 ? 1 : 0), L - 6, y);
      }
      ctx.textAlign = "center";
      for (let m = 60; m >= 0; m -= 15) ctx.fillText(m ? `${m} min ago` : "now", L + pw - (m / 60) * pw, h - 9);
      const series = [{ j: idx[0], col: "#b9bccb", w: 1 }, ...idx.slice(1).map((j, k) => ({ j, col: SPAN_BLUES[k], w: 2 }))];
      for (const sr of series) {
        ctx.beginPath();
        const stride = Math.max(1, Math.floor((end - start) / (pw * 2)));
        for (let i = start; i < end; i += stride) {
          const x = xOf(i), y = yOf(rep.feats[i * NF + sr.j]);
          if (i === start) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.strokeStyle = sr.col; ctx.lineWidth = sr.w; ctx.stroke();
      }
    }
    const x = xNow();
    $("#mem-legend").innerHTML = `<span><i class="sw" style="background:#b9bccb"></i>${info.name} now: ${num(x[idx[0]], info.d)} ${info.unit}</span>` +
      spans.map((s, k) => `<span><i class="sw" style="background:${SPAN_BLUES[k]}"></i>${SPANS[s]}: ${num(x[idx[k + 1]], info.d)}</span>`).join("");
    $("#mem-table").innerHTML = `<thead><tr><th>Signal</th><th>Now</th>${spans.map((s) => `<th>${SPANS[s]} average</th>`).join("")}</tr></thead><tbody>` +
      MEM_BASES.map((b) => {
        const inf = SIGNALS[b];
        return `<tr><td>${inf.name} (${inf.unit})</td><td>${num(x[FI[b]], inf.d)}</td>${spans.map((s) => `<td class="cellv">${num(x[FI[`${b}_ewma_${s}`]], inf.d)}</td>`).join("")}</tr>`;
      }).join("") + "</tbody>";
  }
  const zBars = [];
  function renderZ() {
    const c = canvasCtx($("#z-canvas"));
    if (!c) return;
    const { ctx, w, h } = c, z = rep.eng.z;
    const L = 34, R = 8, T = 10, B = 40, pw = w - L - R, ph = h - T - B, zMax = 4;
    const yOf = (v) => T + ph / 2 - (Math.max(-zMax, Math.min(zMax, v)) / zMax) * (ph / 2);
    ctx.font = "12px Segoe UI, system-ui, sans-serif"; ctx.fillStyle = C.muted; ctx.textAlign = "right"; ctx.textBaseline = "middle";
    for (const v of [-4, -2, 0, 2, 4]) {
      const y = Math.round(yOf(v)) + 0.5;
      ctx.strokeStyle = v === 0 ? C.line : C.soft;
      ctx.beginPath(); ctx.moveTo(L, y); ctx.lineTo(L + pw, y); ctx.stroke();
      ctx.fillText(v > 0 ? `+${v}` : v < 0 ? `${MINUS}${-v}` : "0", L - 6, y);
    }
    const groups = [[0, 8, "8 signals"], [8, 13, "5 physics features"], [13, NF, "32 running averages"]];
    const gapPx = 14, bw = (pw - gapPx * 2) / NF;
    zBars.length = 0;
    let xPos = L;
    groups.forEach(([a, b, label], gi) => {
      const x0 = xPos;
      for (let j = a; j < b; j++) {
        const v = z[j], y0 = yOf(0), y1 = yOf(v);
        ctx.fillStyle = v >= 0 ? POS : NEG;
        ctx.fillRect(xPos + 1, Math.min(y0, y1), Math.max(1, bw - 2), Math.max(1, Math.abs(y1 - y0)));
        if (Math.abs(v) > zMax) { ctx.fillStyle = C.ink; ctx.textAlign = "center"; ctx.fillText(v > 0 ? "▲" : "▼", xPos + bw / 2, y1 + (v > 0 ? -7 : 7)); }
        zBars.push({ x: xPos, w: bw, j });
        xPos += bw;
      }
      ctx.fillStyle = C.ink2; ctx.textAlign = "center";
      ctx.fillText(label, (x0 + xPos) / 2, h - 14);
      ctx.strokeStyle = C.line; ctx.beginPath(); ctx.moveTo(x0 + 1, h - 26.5); ctx.lineTo(xPos - 1, h - 26.5); ctx.stroke();
      if (gi < 2) xPos += gapPx;
    });
  }
  const tip = $("#tip");
  $("#z-canvas").addEventListener("mousemove", (ev) => {
    const r = ev.currentTarget.getBoundingClientRect(), mx = ev.clientX - r.left;
    const bar = zBars.find((b) => mx >= b.x && mx < b.x + b.w);
    if (!bar) { tip.hidden = true; return; }
    const f = FEATURES[bar.j], info = featInfo(f), x = rep.eng.x[bar.j];
    tip.innerHTML = `<b>${info.label}</b><br>value ${num(x, info.d)} ${info.unit}<br>training mean ${num(MLP.meanF[bar.j], info.d)}, spread ${num(MLP.scaleF[bar.j], info.d)}<br>scaled: ${signed(rep.eng.z[bar.j], 2)}`;
    tip.hidden = false;
    tip.style.left = `${Math.min(ev.clientX + 14, window.innerWidth - 290)}px`;
    tip.style.top = `${ev.clientY + 14}px`;
  });
  $("#z-canvas").addEventListener("mouseleave", () => { tip.hidden = true; });

  function renderNet() {
    const c = canvasCtx($("#net-canvas"));
    const e = rep.eng;
    if (c) {
      const { ctx, w, h } = c, T = 26, B = 12;
      const cols = [
        { n: NF, x: 40, r: 3.4, vals: e.z },
        { n: H1, x: w * 0.36, r: 3.2, vals: e.h1 },
        { n: H2, x: w * 0.66, r: 5, vals: e.h2 },
        { n: 1, x: w - 90, r: 16, vals: [e.mlp] },
      ];
      const yOf = (col, i) => (col.n === 1 ? T + (h - T - B) / 2 : T + (i + 0.5) * ((h - T - B) / col.n));
      const top = (pairs, n) => pairs.sort((a, b) => Math.abs(b[2]) - Math.abs(a[2])).slice(0, n);
      const edges = [];
      const p1 = [];
      for (let o = 0; o < H1; o++) if (e.h1[o] > 0) for (let i = 0; i < NF; i++) p1.push([i, o, e.z[i] * L1.Wf[i * H1 + o]]);
      top(p1, 90).forEach(([i, o, v]) => edges.push([cols[0], i, cols[1], o, v]));
      const p2 = [];
      for (let o = 0; o < H2; o++) if (e.h2[o] > 0) for (let i = 0; i < H1; i++) if (e.h1[i] > 0) p2.push([i, o, e.h1[i] * L2.Wf[i * H2 + o]]);
      top(p2, 70).forEach(([i, o, v]) => edges.push([cols[1], i, cols[2], o, v]));
      for (let i = 0; i < H2; i++) if (e.h2[i] > 0) edges.push([cols[2], i, cols[3], 0, e.h2[i] * L3.Wf[i]]);
      const mag = Math.max(1e-9, ...edges.map((d) => Math.abs(d[4])));
      for (const [ca, ia, cb, ib, v] of edges) {
        const t = Math.abs(v) / mag;
        ctx.strokeStyle = v >= 0 ? POS : NEG; ctx.globalAlpha = 0.12 + 0.6 * t; ctx.lineWidth = 0.5 + 2.5 * t;
        ctx.beginPath(); ctx.moveTo(ca.x, yOf(ca, ia)); ctx.lineTo(cb.x, yOf(cb, ib)); ctx.stroke();
      }
      ctx.globalAlpha = 1;
      cols.forEach((col, ci) => {
        let mx = 0;
        if (ci === 1 || ci === 2) for (const v of col.vals) mx = Math.max(mx, v);
        for (let i = 0; i < col.n; i++) {
          const v = col.vals[i];
          ctx.beginPath(); ctx.arc(col.x, yOf(col, i), col.r, 0, Math.PI * 2);
          ctx.fillStyle = ci === 0 ? div(v, 3) : ci === 3 ? C.est : act(mx ? v / mx : 0);
          ctx.fill();
          ctx.strokeStyle = ci === 3 ? C.est : "rgba(20,22,43,.25)"; ctx.lineWidth = 0.8; ctx.stroke();
        }
      });
      ctx.font = "12px Segoe UI, system-ui, sans-serif"; ctx.fillStyle = C.ink2; ctx.textAlign = "center"; ctx.textBaseline = "alphabetic";
      ["45 inputs", "64 neurons", "32 neurons", "estimate"].forEach((t, i) => ctx.fillText(t, cols[i].x, 14));
      ctx.font = "bold 16px Segoe UI, system-ui, sans-serif"; ctx.fillStyle = C.ink; ctx.textAlign = "left"; ctx.textBaseline = "middle";
      ctx.fillText(deg(e.mlp), cols[3].x + 22, yOf(cols[3], 0));
    }
    const a1 = e.h1.reduce((n, v) => n + (v > 0), 0), a2 = e.h2.reduce((n, v) => n + (v > 0), 0);
    const parts = [];
    for (let i = 0; i < H2; i++) if (e.h2[i] > 0) parts.push({ i, w: L3.Wf[i], h: e.h2[i], v: L3.Wf[i] * e.h2[i] });
    parts.sort((a, b) => Math.abs(b.v) - Math.abs(a.v));
    const shown = parts.slice(0, 5), rest = parts.slice(5).reduce((s, p) => s + p.v, 0);
    $("#net-explain").innerHTML =
      `<p>Each neuron multiplies all its inputs by its own <strong>learned weights</strong>, adds them up with a bias and keeps the result only if it is positive. That last step is called <strong>ReLU</strong>: max(0, value).</p>` +
      `<p>Right now <strong>${a1} of 64</strong> neurons in the first layer and <strong>${a2} of 32</strong> in the second are active. The lines show the strongest contributions: orange pushes the temperature up, blue pulls it down.</p>` +
      `<p>The estimate is one last weighted sum of the second layer:</p>` +
      `<table class="contrib"><tbody>` +
      shown.map((p) => `<tr><td>Neuron ${p.i + 1}: weight ${num(p.w, 2)} &times; activity ${num(p.h, 2)}</td><td class="${p.v >= 0 ? "pos" : "neg"}">${signed(p.v, 1)}</td></tr>`).join("") +
      `<tr><td>The other ${Math.max(0, parts.length - shown.length)} active neurons</td><td class="${rest >= 0 ? "pos" : "neg"}">${signed(rest, 1)}</td></tr>` +
      `<tr><td>Bias</td><td>${signed(L3.bf[0], 1)}</td></tr>` +
      `<tr class="total"><td>Estimate</td><td>${deg(e.mlp)}</td></tr></tbody></table>` +
      `<p class="note">5,057 learned numbers in all. Training set them by showing the network 1.19 million training rows with the real winding temperature.</p>`;
  }
  const STEP_RENDER = [renderSignals, renderPhysics, renderMemory, renderZ, renderNet];
  function renderStep() { if (rep.i > 0) STEP_RENDER[step](); }
  function setStep(k) {
    step = k;
    $$("#step-tabs button").forEach((b, i) => { b.setAttribute("aria-selected", String(i === k)); b.tabIndex = i === k ? 0 : -1; });
    $$(".step-panel").forEach((p) => { p.hidden = Number(p.dataset.panel) !== k; });
    renderStep();
  }
  $("#step-tabs").addEventListener("click", (ev) => { const b = ev.target.closest("button[data-step]"); if (b) setStep(Number(b.dataset.step)); });
  $("#step-tabs").addEventListener("keydown", (ev) => {
    if (ev.key !== "ArrowRight" && ev.key !== "ArrowLeft") return;
    const k = (step + (ev.key === "ArrowRight" ? 1 : 4)) % 5;
    setStep(k); $$("#step-tabs button")[k].focus();
  });

  // ---------- drive the motor yourself
  const PRESETS = META.presets;
  const PRESET_NAMES = Object.keys(PRESETS);
  const CAP = 6 * 60 * PER_MIN, WARM = 30 * PER_MIN;
  const drv = {
    eng: new Engine(), sig: new Float64Array(INPUTS.length), est: new Float32Array(CAP), cool: new Float32Array(CAP),
    t: 0, playing: false, acc: 0, speed: 5, preset: PRESET_NAMES.find((n) => n.startsWith("Heavy")) || PRESET_NAMES[0],
    coolant: 40, ambient: 24, marks: [],
  };
  function driveStep(name) {
    const p = PRESETS[name], sig = drv.sig;
    INPUTS.forEach((c, k) => {
      sig[k] = F(c === "coolant" ? drv.coolant : c === "ambient" ? drv.ambient : p[c]);
    });
    drv.eng.step(sig);
    drv.est[drv.t] = drv.eng.mlp;
    drv.cool[drv.t] = drv.coolant;
    drv.t++;
  }
  function driveReset() {
    drv.eng.reset(); drv.t = 0; drv.acc = 0; drv.playing = false;
    const idle = PRESET_NAMES.find((n) => n.startsWith("Idle")) || PRESET_NAMES[0];
    drv.marks = [{ t: 0, label: "Idle" }];
    for (let i = 0; i < WARM; i++) driveStep(idle);
    drv.marks.push({ t: drv.t, label: shortPreset(drv.preset) });
    $("#drive-play").textContent = "Run";
    dirty.drive = true;
  }
  const shortPreset = (n) => n.replace(/\s*\(.*\)/, "");
  $("#preset-list").innerHTML = PRESET_NAMES.map((n) => `<button type="button" data-preset="${n}" aria-pressed="${n === drv.preset}">${n}</button>`).join("");
  $("#preset-list").addEventListener("click", (ev) => {
    const b = ev.target.closest("button[data-preset]");
    if (!b) return;
    drv.preset = b.dataset.preset;
    $$("#preset-list button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    const lastMark = drv.marks[drv.marks.length - 1];
    if (lastMark.t === drv.t) lastMark.label = shortPreset(drv.preset); else drv.marks.push({ t: drv.t, label: shortPreset(drv.preset) });
    dirty.drive = true;
  });
  const coolR = $("#cool-range"), ambR = $("#amb-range");
  const syncDriveInputs = () => {
    drv.coolant = Number(coolR.value); drv.ambient = Number(ambR.value);
    $("#cool-out").textContent = `${drv.coolant} °C`; $("#amb-out").textContent = `${drv.ambient} °C`;
  };
  coolR.addEventListener("input", () => { syncDriveInputs(); dirty.drive = true; });
  ambR.addEventListener("input", () => { syncDriveInputs(); dirty.drive = true; });
  syncDriveInputs();
  $("#drive-play").addEventListener("click", () => {
    if (drv.t >= CAP) driveReset();
    drv.playing = !drv.playing;
    $("#drive-play").textContent = drv.playing ? "Pause" : "Run";
  });
  $("#drive-reset").addEventListener("click", () => { driveReset(); });
  $("#drive-speed").addEventListener("click", (ev) => {
    const b = ev.target.closest("button[data-speed]");
    if (!b) return;
    drv.speed = Number(b.dataset.speed);
    $$("#drive-speed button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
  });

  function drawDrive() {
    const c = canvasCtx($("#drive-canvas"));
    if (c) {
      const { ctx, w, h } = c, L = 42, R = 14, T = 12, B = 30, pw = w - L - R, ph = h - T - B;
      const win = 120 * PER_MIN, x0 = Math.max(0, drv.t - win * 0.85), x1 = x0 + win;
      const xOf = (t) => L + ((t - x0) / (x1 - x0)) * pw;
      const yMin = 10, yMax = 150, yOf = (v) => T + ph - ((Math.max(yMin, Math.min(yMax, v)) - yMin) / (yMax - yMin)) * ph;
      ctx.font = "12px Segoe UI, system-ui, sans-serif"; ctx.textBaseline = "middle"; ctx.fillStyle = C.muted; ctx.textAlign = "right";
      ctx.strokeStyle = C.soft; ctx.lineWidth = 1;
      for (let v = 20; v <= 140; v += 20) {
        const y = Math.round(yOf(v)) + 0.5;
        ctx.beginPath(); ctx.moveTo(L, y); ctx.lineTo(L + pw, y); ctx.stroke();
        ctx.fillText(String(v), L - 6, y);
      }
      ctx.textAlign = "center";
      for (let m = Math.ceil(x0 / PER_MIN / 15) * 15; m * PER_MIN <= x1; m += 15) ctx.fillText(`${m} min`, xOf(m * PER_MIN), h - 10);
      ctx.setLineDash([6, 4]); ctx.strokeStyle = C.hot; ctx.lineWidth = 1.5;
      const yh = Math.round(yOf(THOT)) + 0.5;
      ctx.beginPath(); ctx.moveTo(L, yh); ctx.lineTo(L + pw, yh); ctx.stroke(); ctx.setLineDash([]);
      ctx.fillStyle = C.hot; ctx.textAlign = "right"; ctx.textBaseline = "bottom"; ctx.fillText(`Hot level ${num(THOT)} °C`, L + pw - 4, yh - 3);
      ctx.textBaseline = "top"; ctx.textAlign = "left";
      for (const m of drv.marks) {
        if (m.t < x0) continue;
        const x = Math.round(xOf(m.t)) + 0.5;
        ctx.strokeStyle = C.line; ctx.beginPath(); ctx.moveTo(x, T); ctx.lineTo(x, T + ph); ctx.stroke();
        ctx.fillStyle = C.ink2; ctx.fillText(m.label, x + 4, T + 2);
      }
      const from = Math.max(0, Math.floor(x0));
      for (const [arr, col, lw] of [[drv.cool, C.cool, 1.5], [drv.est, C.est, 2.2]]) {
        ctx.beginPath();
        const stride = Math.max(1, Math.floor((drv.t - from) / (pw * 2)));
        for (let t = from; t < drv.t; t += stride) { const x = xOf(t), y = yOf(arr[t]); if (t === from) ctx.moveTo(x, y); else ctx.lineTo(x, y); }
        ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.stroke();
      }
      if (drv.t > 0) {
        ctx.beginPath(); ctx.arc(xOf(drv.t - 1), yOf(drv.est[drv.t - 1]), 4.5, 0, Math.PI * 2);
        ctx.fillStyle = C.est; ctx.fill(); ctx.strokeStyle = "#fff"; ctx.lineWidth = 2; ctx.stroke();
      }
    }
    const est = drv.est[drv.t - 1], p = PRESETS[drv.preset];
    $("#dr-est").textContent = deg(est); $("#dr-est").style.color = C.est;
    $("#dr-rise").textContent = `${signed(est - drv.coolant)} °C`;
    const since = drv.t - drv.marks[drv.marks.length - 1].t;
    $("#dr-time").textContent = clock(since);
    $("#dr-cur").textContent = `${num(Math.hypot(p.i_d, p.i_q))} A at ${num(p.motor_speed, 0)} rpm`;
    const alarm = est + kVal() * SIGMA >= THOT;
    $("#dr-lamp").classList.toggle("on", alarm);
    $("#dr-lamp-state").textContent = alarm ? "Alarm on" : "No alarm";
    $("#dr-lamp-note").textContent = alarm ? `Estimate plus the safety margin is at or above ${num(THOT)} °C.` : `Alarm when the estimate reaches ${num(THOT - kVal() * SIGMA)} °C.`;
  }

  // ---------- results
  const OPENED = (() => {
    const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(META.facts.testOpened);
    const months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    return m ? `${Number(m[3])} ${months[Number(m[2]) - 1]} ${m[1]}` : META.facts.testOpened;
  })();
  const TEST_NAMES = { "M3 Ridge": ["Ridge", C.ridge], "M5 LightGBM": ["LightGBM", C.lgbm], "M6 MLP (64-32)": ["MLP, final model", C.est], "B1 coolant + offset": ["Coolant + offset", "#9aa0b4"], "B0 mean": ["Always the average", "#9aa0b4"] };
  function renderAccuracy() {
    const max = 28, target = META.targets.test_rmse_max;
    const rows = META.test.map((r) => ({ ...r, name: TEST_NAMES[r.model][0], col: TEST_NAMES[r.model][1] }));
    $("#acc-chart").innerHTML = rows.map((r) => {
      const p = (r.rmse / max) * 100;
      return `<div class="acc-row"><div class="who"><i class="sw" style="background:${r.col}"></i>${r.name}</div>` +
        `<div class="track"><div class="fill" style="width:${p}%;background:${r.col}"></div><div class="target" style="left:${(target / max) * 100}%"></div></div>` +
        `<span class="num">${num(r.rmse, 2)} °C</span></div>`;
    }).join("") + `<div class="acc-axis"><span></span><div><span>0</span><span>${max / 2} °C</span><span>${max} °C</span></div><span></span></div>`;
    $("#acc-note").textContent = `Root mean square error on the 6 test sessions, opened once on ${OPENED}. Lower is better. The dashed line is our target of ${num(target, 1)} °C, set before testing. We chose the MLP by cross-validation before the test; on the test, Ridge did best.`;
  }
  function renderMemoryChart() {
    const labels = ["No memory", "1 min", "1 and 5 min", "1, 5 and 15 min", "1, 5, 15 and 45 min"];
    const max = 14;
    $("#mem-chart").innerHTML = META.memory.map((r, i) => {
      const p = (r.cv_rmse / max) * 100;
      return `<div class="acc-row"><div class="who">${labels[i] || r.memory}</div><div class="track"><div class="fill" style="width:${p}%;background:${C.navy}"></div></div>` +
        `<span class="num">${num(r.cv_rmse, 2)} °C</span></div>`;
    }).join("");
  }
  let safeCurve = [];
  function computeSafety() {
    safeCurve = [];
    let hot = 0;
    for (let g = 0; g < N; g++) if (REAL[g] >= THOT) hot++;
    for (let k = 0; k <= 3.0001; k += 0.1) {
      const trig = THOT - k * SIGMA;
      let caught = 0, fa = 0;
      for (let g = 0; g < N; g++) {
        if (LIVE.mlp[g] >= trig) { if (REAL[g] >= THOT) caught++; else fa++; }
      }
      safeCurve.push({ k: Math.round(k * 10) / 10, caught: (100 * caught) / hot, fa: (100 * fa) / (N - hot) });
    }
  }
  function renderSafety() {
    const k = kVal(), W = 560, H = 250, L = 70, R = 34, T = 12, B = 40, pw = W - L - R, ph = H - T - B;
    const faMax = Math.ceil(Math.max(...safeCurve.map((p) => p.fa)) / 5) * 5;
    const cMin = Math.floor(Math.min(...safeCurve.map((p) => p.caught)) / 10) * 10, cMax = 100;
    const xOf = (v) => L + (v / faMax) * pw, yOf = (v) => T + ph - ((v - cMin) / (cMax - cMin)) * ph;
    let svg = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Share of hot moments caught against false alarms for each safety margin">`;
    svg += `<g class="grid">`;
    for (let v = cMin; v <= cMax; v += 10) svg += `<line x1="${L}" x2="${L + pw}" y1="${yOf(v)}" y2="${yOf(v)}"/><text x="${L - 6}" y="${yOf(v) + 4}" text-anchor="end">${v} %</text>`;
    for (let v = 0; v <= faMax; v += 5) svg += `<text x="${xOf(v)}" y="${H - 22}" text-anchor="middle">${v} %</text>`;
    svg += `</g><text x="${L + pw / 2}" y="${H - 4}" text-anchor="middle">False alarms (share of normal moments)</text>`;
    svg += `<text x="12" y="${T + ph / 2}" text-anchor="middle" transform="rotate(-90 12 ${T + ph / 2})">Hot moments caught</text>`;
    svg += `<polyline fill="none" stroke="${C.navy}" stroke-width="2" points="${safeCurve.map((p) => `${xOf(p.fa)},${yOf(p.caught)}`).join(" ")}"/>`;
    for (const p of safeCurve) if (Number.isInteger(p.k)) svg += `<circle cx="${xOf(p.fa)}" cy="${yOf(p.caught)}" r="3.5" fill="${C.navy}"/><text x="${xOf(p.fa) + 7}" y="${yOf(p.caught) + 14}">k = ${p.k}</text>`;
    const cur = safeCurve.reduce((a, b) => (Math.abs(b.k - k) < Math.abs(a.k - k) ? b : a));
    svg += `<circle cx="${xOf(cur.fa)}" cy="${yOf(cur.caught)}" r="8" fill="${C.hot}" stroke="#fff" stroke-width="2.5"/>`;
    svg += `</svg>`;
    $("#safe-chart").innerHTML = `<div class="chart">${svg}</div>`;
    const saved = META.safety.table.find((r) => Math.abs(r.k - cur.k) < 1e-9);
    $("#safe-note").textContent = `Move the safety margin slider at the top. With k = ${num(cur.k, 1)} (a margin of ${num(cur.k * SIGMA, 1)} °C) the alarm catches ${num(cur.caught, 1)} % of hot moments and goes off in ${num(cur.fa, 2)} % of normal moments.` +
      (saved ? ` Our saved table for k = ${saved.k}: ${num(saved.caught_pct, 1)} % and ${num(saved.false_alarm_pct, 2)} %.` : "") + " Computed from this page's own estimates on all test rows.";
  }
  $("#run-btn").addEventListener("click", async () => {
    const btn = $("#run-btn"), bar = $("#run-bar"), out = $("#run-out");
    btn.disabled = true; out.textContent = "Running both models on every test row…";
    const res = await runAll((p) => { bar.style.width = `${p * 100}%`; });
    const rowsHtml = SESS.map((s) => {
      let se = 0, seR = 0;
      for (let g = s.start; g < s.start + s.rows; g++) { se += (LIVE.mlp[g] - REAL[g]) ** 2; seR += (LIVE.ridge[g] - REAL[g]) ** 2; }
      return `<tr><td>Session ${s.id}</td><td>${num(s.hours, 1)} h</td><td>${num(Math.sqrt(se / s.rows), 2)}</td><td>${num(s.rmse.m6, 2)}</td><td>${num(Math.sqrt(seR / s.rows), 2)}</td></tr>`;
    }).join("");
    out.innerHTML = `<table class="run-table"><thead><tr><th>Test session</th><th>Length</th><th>MLP here (°C)</th><th>MLP in Python (°C)</th><th>Ridge here (°C)</th></tr></thead><tbody>${rowsHtml}` +
      `<tr class="total"><td>All ${N.toLocaleString("en-US")} rows</td><td></td><td>${num(res.rmseM, 2)}</td><td>${num(META.test.find((r) => r.model.startsWith("M6")).rmse, 2)}</td><td>${num(res.rmseR, 2)}</td></tr></tbody></table>` +
      `<p class="note">RMSE per session. ${(2 * N).toLocaleString("en-US")} estimates in ${num(res.ms / 1000, 1)} s. Largest difference from our saved Python estimates: MLP ${num(Math.max(res.dM, 0.001), 3)} °C, Ridge ${num(Math.max(res.dR, 0.001), 3)} °C.</p>`;
    btn.disabled = false;
  });

  // ---------- static text
  const fx = META.facts;
  $("#results-lead").textContent = `Measured once on the six test sessions, ${fx.testRows.toLocaleString("en-US")} rows, after the final model had been chosen. The test set was opened on ${OPENED} and never used for any decision.`;
  $("#about-data").innerHTML = `The public Paderborn University test-bench dataset on Kaggle: one 50 kW permanent-magnet synchronous motor, <strong>${fx.rows.toLocaleString("en-US")} rows</strong> recorded twice a second in ${fx.sessions} sessions, ${num(fx.hours, 2)} hours in all. We split by whole session: ${fx.trainSessions} sessions for training with 5-fold cross-validation, and 6 sessions (${num(fx.testShare * (fx.testShare < 1 ? 100 : 1), 1)} % of the rows) locked away for one final test.`;
  $("#lag-min").textContent = num(fx.lagMin, 1);
  $("#signal-list").innerHTML = INPUTS.map((c) => `<li><b>${SIGNALS[c].name}</b> (${SIGNALS[c].unit})</li>`).join("");
  $("#sess-list").innerHTML = SESS.map((s, i) =>
    `<button type="button" data-si="${i}" aria-pressed="false"><b>Session ${s.id}</b><span>${num(s.hours, 1)} h</span>` +
    `<span class="${s.peak >= THOT ? "hotspot" : ""}">peak ${num(s.peak, 0)} °C</span><span>MLP error ${num(s.rmse.m6, 2)} °C</span></button>`).join("");

  // ---------- controls
  const playBtn = $("#play-btn");
  const setPlaying = (on) => { rep.playing = on; playBtn.textContent = on ? "Pause" : "Play"; };
  playBtn.addEventListener("click", () => {
    if (!rep.playing && rep.i >= SESS[rep.si].rows) selectSession(rep.si);
    setPlaying(!rep.playing);
  });
  $("#restart-btn").addEventListener("click", () => { selectSession(rep.si); setPlaying(true); });
  $("#sess-list").addEventListener("click", (ev) => {
    const b = ev.target.closest("button[data-si]");
    if (!b) return;
    selectSession(Number(b.dataset.si));
    setPlaying(true);
  });
  $("#model-seg").addEventListener("click", (ev) => {
    const b = ev.target.closest("button[data-model]");
    if (!b) return;
    rep.model = b.dataset.model;
    $$("#model-seg button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    $("#est-sw").style.background = rep.model === "mlp" ? C.est : C.ridge;
    $("#est-legend").textContent = rep.model === "mlp" ? "MLP estimate, computed live" : "Ridge estimate, computed live";
    dirty.all = true;
  });
  $("#speed-seg").addEventListener("click", (ev) => {
    const b = ev.target.closest("button[data-speed]");
    if (!b) return;
    rep.speed = Number(b.dataset.speed);
    $$("#speed-seg button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
  });
  const syncK = () => { $("#k-out").textContent = `k = ${num(kVal(), 1)}, ${num(kVal() * SIGMA, 1)} °C`; };
  kRange.addEventListener("input", () => { syncK(); dirty.all = true; dirty.drive = true; dirty.safety = true; });
  window.addEventListener("resize", () => { dirty.all = true; dirty.drive = true; });

  // ---------- main loop
  const dirty = { all: true, drive: true, safety: true };
  let lastT = performance.now(), lastStepDraw = 0;
  function frame(t) {
    const dt = Math.min(0.1, (t - lastT) / 1000);
    lastT = t;
    if (rep.playing) {
      rep.acc += dt * rep.speed * PER_MIN;
      const n = Math.floor(rep.acc);
      rep.acc -= n;
      if (n) { stepReplay(n); dirty.all = true; }
      if (rep.i >= SESS[rep.si].rows) setPlaying(false);
    }
    if (drv.playing) {
      drv.acc += dt * drv.speed * PER_MIN;
      const n = Math.min(Math.floor(drv.acc), CAP - drv.t);
      drv.acc -= Math.floor(drv.acc);
      for (let i = 0; i < n; i++) driveStep(drv.preset);
      if (n) dirty.drive = true;
      if (drv.t >= CAP) { drv.playing = false; $("#drive-play").textContent = "Run"; }
    }
    if (dirty.all) {
      drawLive(); drawSignals(); renderReadout(); drawMiniNet();
      if (!rep.playing || t - lastStepDraw > 150) { renderStep(); lastStepDraw = t; }
      dirty.all = false;
    }
    if (dirty.drive) { drawDrive(); dirty.drive = false; }
    if (dirty.safety && LIVE.ready) { renderSafety(); dirty.safety = false; }
    requestAnimationFrame(frame);
  }

  computeSafety();
  renderAccuracy();
  renderMemoryChart();
  syncK();
  selectSession(rep.si);
  setStep(0);
  driveReset();
  requestAnimationFrame(frame);
})().catch((err) => {
  const s = document.getElementById("status");
  if (s) s.textContent = `Something went wrong while starting the page: ${err.message}`;
  console.error(err);
});
