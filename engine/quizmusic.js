/* QuizMusic v2 — clean rewrite after "raspy, doesn't flow".
   Rules for this version: no noise-based percussion, no FM (it aliased on high notes), no clipping.
   Every sound is a small stack of pure sine partials kept under 7 kHz. Flow comes from a continuous
   eighth-note ostinato, a sustained pad that crossfades chord to chord, and a stepwise legato melody.
   120 BPM, one bar = 2 s, arranged backwards from the end so the last chord lands at zero. */
(function (root) {
  'use strict';
  var TWO_PI = Math.PI * 2, BAR = 2.0, BEAT = 0.5, FMAX = 7000;

  function rng(seed) { var s = seed >>> 0; return function () { s = (s + 0x6D2B79F5) >>> 0; var t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  function mtof(m) { return 440 * Math.pow(2, (m - 69) / 12); }
  function makeCtx(seconds, sr, seed) { var n = Math.ceil(seconds * sr); return { sr: sr, n: n, L: new Float32Array(n), R: new Float32Array(n), S: new Float32Array(n), gains: { lead: 1, ost: 1, pad: 1, bass: 1, fx: 1 }, rand: rng(seed || 7) }; }

  /* One voice = a few sine partials. o.partials: [ratio, amp, decayPerSecond]. o.sustain: hold level while the note is down. */
  function voice(ctx, group, t, midi, dur, vel, pan, send, o) {
    var sr = ctx.sr, g = ctx.gains[group] * vel * o.gain, a = (pan + 1) * Math.PI / 4, gl = Math.cos(a) * g, gr = Math.sin(a) * g;
    var f = mtof(midi), i0 = Math.floor(t * sr), durS = dur * sr, relS = o.rel * sr, attS = Math.max(8, o.att * sr);
    var N = Math.floor(Math.min(dur + o.rel * 7, o.maxLen || 6) * sr);
    var det = o.detune || [0], j, d, np = 0, cap = det.length * o.partials.length;
    var pw = new Float64Array(cap), pa = new Float64Array(cap), pk = new Float64Array(cap), pp = new Float64Array(cap);
    for (d = 0; d < det.length; d++) for (j = 0; j < o.partials.length; j++) {
      var pf = f * o.partials[j][0] * Math.pow(2, det[d] / 1200); if (pf > FMAX) continue;
      pw[np] = TWO_PI * pf / sr; pa[np] = o.partials[j][1] / det.length; pk[np] = Math.exp(-o.partials[j][2] / sr); pp[np] = ctx.rand() * (det.length > 1 ? TWO_PI : 0); np++;
    }
    var kRel = Math.exp(-1 / relS), rCur = 1, vibW = TWO_PI * 5 / sr, vib = o.vib || 0, vibIn = 0.35 * sr;
    var fade = Math.floor(0.02 * sr);
    for (var i = 0; i < N; i++) {
      var k = i0 + i; if (k >= ctx.n) break;
      var e = i < attS ? 0.5 - 0.5 * Math.cos(Math.PI * i / attS) : 1;        // raised-cosine attack: no click
      if (i > durS) { rCur *= kRel; e *= rCur; if (rCur < 3e-3) break; }
      if (i > N - fade) e *= (N - i) / fade;
      var vm = vib ? 1 + vib * Math.min(1, i / vibIn) * Math.sin(vibW * i) : 1, s = 0;
      for (j = 0; j < np; j++) { pa[j] *= pk[j]; pp[j] += pw[j] * vm; s += pa[j] * Math.sin(pp[j]); }
      if ((i & 511) === 0) { while (np > 1 && pa[np - 1] < 2e-4) np--; if (pa[0] < 2e-4) break; }
      if (k < 0) continue;
      s *= e;
      ctx.L[k] += s * gl; ctx.R[k] += s * gr; ctx.S[k] += s * g * send;
    }
  }
  var INS = {
    chime:  { gain: 0.30, att: 0.002, rel: 0.2, maxLen: 1.6, partials: [[1, 1, 2.2], [2, 0.3, 4], [3, 0.1, 6]] },
    bell:   { gain: 0.30, att: 0.002, rel: 0.5, maxLen: 3.5, partials: [[1, 1, 1.4], [2, 0.3, 2.5], [3, 0.1, 4], [4.2, 0.05, 7]] },
    mallet: { gain: 0.34, att: 0.003, rel: 0.35, maxLen: 3.5, partials: [[1, 1, 1.1], [4, 0.16, 5], [10, 0.025, 12]] },
    wood:   { gain: 0.36, att: 0.002, rel: 0.12, maxLen: 1.2, partials: [[1, 1, 5], [4, 0.2, 14], [9.2, 0.04, 30]] },
    pluck:  { gain: 0.30, att: 0.002, rel: 0.1, maxLen: 1.0, partials: [[1, 1, 6], [2, 0.4, 9], [3, 0.2, 12], [4, 0.1, 16], [5, 0.05, 20]] },
    keys:   { gain: 0.30, att: 0.004, rel: 0.18, maxLen: 3.0, partials: [[1, 1, 1.6], [2, 0.32, 2.6], [3, 0.1, 4], [7, 0.03, 9]] },
    flute:  { gain: 0.27, att: 0.06, rel: 0.16, maxLen: 6, vib: 0.004, partials: [[1, 1, 0.15], [2, 0.22, 0.3], [3, 0.07, 0.5]] },
    pad:    { gain: 0.11, att: 0.35, rel: 0.45, maxLen: 8, detune: [-5, 5], partials: [[1, 1, 0.05], [2, 0.35, 0.1], [3, 0.15, 0.15]] },
    bass:   { gain: 0.42, att: 0.012, rel: 0.12, maxLen: 3, partials: [[1, 1, 1.0], [2, 0.5, 1.6], [3, 0.2, 2.4], [4, 0.07, 3.5]] }
  };
  function play(ctx, ins, group, t, midi, dur, vel, pan, send) { voice(ctx, group, t, midi, dur, vel, pan, send, INS[ins]); }

  function tick(ctx, t, vel, hi) {   // soft wooden clock tick: two short sines, nothing noisy
    voice(ctx, 'fx', t, hi ? 86 : 81, 0.02, vel, -0.05, 0.25, { gain: 0.2, att: 0.001, rel: 0.02, maxLen: 0.2, partials: [[1, 1, 40], [1.51, 0.4, 70]] });
  }
  function thump(ctx, t, midi, vel) { // timpani-like: a low sine with a fast pitch settle
    voice(ctx, 'fx', t, midi, 0.05, vel, 0, 0.3, { gain: 0.5, att: 0.004, rel: 0.5, maxLen: 3, partials: [[1, 1, 0.5], [1.5, 0.3, 3], [2, 0.18, 4]] });
  }

  /* ---------- reverb + master (no clipper: levels are set so peaks stay under full scale) ---------- */
  function reverb(ctx, wet) {
    var sr = ctx.sr, sc = sr / 44100, n = ctx.n, combL = [1116, 1188, 1277, 1356, 1422, 1491, 1557, 1617], apL = [556, 441, 341, 225], fb = 0.84, damp = 0.45, out = [new Float32Array(n), new Float32Array(n)];
    for (var ch = 0; ch < 2; ch++) {
      var o = out[ch], j, i;
      for (j = 0; j < 8; j++) { var len = Math.floor((combL[j] + ch * 23) * sc), buf = new Float32Array(len), idx = 0, st = 0; for (i = 0; i < n; i++) { var y = buf[idx]; st = y * (1 - damp) + st * damp; buf[idx] = ctx.S[i] * 0.015 + st * fb; o[i] += y; if (++idx >= len) idx = 0; } }
      for (j = 0; j < 4; j++) { var al = Math.floor((apL[j] + ch * 23) * sc), ab = new Float32Array(al), ai = 0; for (i = 0; i < n; i++) { var bo = ab[ai], x = o[i]; o[i] = bo - x; ab[ai] = x + bo * 0.5; if (++ai >= al) ai = 0; } }
    }
    for (var k = 0; k < n; k++) { ctx.L[k] += out[0][k] * wet; ctx.R[k] += out[1][k] * wet; }
  }
  function master(ctx, gain, wet) {
    reverb(ctx, wet);
    var n = ctx.n, fade = Math.floor(0.5 * ctx.sr), pk = 0, i;
    for (i = 0; i < n; i++) { var f = i > n - fade ? (n - i) / fade : 1; ctx.L[i] *= gain * f; ctx.R[i] *= gain * f; var a = Math.abs(ctx.L[i]), b = Math.abs(ctx.R[i]); if (a > pk) pk = a; if (b > pk) pk = b; }
    if (pk > 0.95) { var sc = 0.95 / pk; for (i = 0; i < n; i++) { ctx.L[i] *= sc; ctx.R[i] *= sc; } }   // safety net: turn down, never distort
    return { left: ctx.L, right: ctx.R, sampleRate: ctx.sr, seconds: n / ctx.sr, rawPeak: pk };
  }

  /* ---------- composition ---------- */
  var CH = {            // pitch classes from the tonic: [root, third, fifth, colour]
    I: [0, 4, 7, 2], vi: [9, 0, 4, 7], IV: [5, 9, 0, 7], V: [7, 11, 2, 5], ii: [2, 5, 9, 0], iii: [4, 7, 11, 2], sivo: [6, 9, 0, 3]
  };
  var SEC = {
    A: { ch: [['I'], ['vi'], ['IV'], ['V'], ['I'], ['vi'], ['ii', 'V'], ['I']],
      mel: [[[0, 1.5, 76], [1.5, .5, 79], [2, 1, 81], [3, 1, 79]], [[0, 2, 76], [2, 1, 72], [3, 1, 74]], [[0, 1.5, 81], [1.5, .5, 79], [2, 1, 77], [3, 1, 81]], [[0, 3, 79], [3, 1, 74]],
            [[0, 1.5, 76], [1.5, .5, 79], [2, 1, 84], [3, 1, 83]], [[0, 2, 81], [2, 1, 76], [3, 1, 81]], [[0, 1, 77], [1, 1, 81], [2, 1, 79], [3, 1, 77]], [[0, 1, 76], [1, 3, 72]]] },
    B: { ch: [['IV'], ['V'], ['iii'], ['vi'], ['ii'], ['V'], ['I'], ['V']],
      mel: [[[0, 1, 81], [1, 1, 84], [2, 1, 81], [3, 1, 77]], [[0, 1, 79], [1, 1, 83], [2, 1, 79], [3, 1, 74]], [[0, 1, 79], [1, 1, 76], [2, 1, 79], [3, 1, 83]], [[0, 3, 81], [3, 1, 76]],
            [[0, 1, 77], [1, 1, 81], [2, 1.5, 86], [3.5, .5, 84]], [[0, 1, 83], [1, 1, 79], [2, 1, 74], [3, 1, 79]], [[0, 1, 76], [1, 1, 79], [2, 2, 84]], [[0, 1, 83], [1, 1, 81], [2, 1, 79], [3, 1, 74]]] },
    BUILD: { ch: [['ii'], ['V'], ['IV'], ['sivo'], ['V']],
      mel: [[[0, 1, 74], [1, 1, 77], [2, 1, 81], [3, 1, 86]], [[0, 1, 74], [1, 1, 79], [2, 1, 83], [3, 1, 86]],
            [[0, .5, 77], [.5, .5, 81], [1, .5, 84], [1.5, .5, 81], [2, .5, 77], [2.5, .5, 81], [3, .5, 84], [3.5, .5, 89]],
            [[0, .5, 78], [.5, .5, 81], [1, .5, 84], [1.5, .5, 81], [2, .5, 78], [2.5, .5, 81], [3, .5, 84], [3.5, .5, 87]],
            [[0, .5, 79], [.5, .5, 81], [1, .5, 83], [1.5, .5, 84], [2, .5, 86], [2.5, .5, 88], [3, .5, 89], [3.5, .5, 91]]] },
    SOFTEND: { ch: [['ii'], ['V']], mel: [[[0, 2, 77], [2, 2, 81]], [[0, 2, 79], [2, 2, 74]]] }
  };
  /* Three sketches of the same tune, so the ear can pick a direction. */
  var SKETCH = {
    1: { name: 'Music box', key: 0, lead: 'mallet', leadUp: 'bell', ost: 'chime', ostOct: 0 },
    2: { name: 'Tiptoe', key: -7, lead: 'flute', leadUp: null, ost: 'pluck', ostOct: 0 },
    3: { name: 'Lounge', key: -2, lead: 'mallet', leadUp: null, ost: 'keys', ostOct: 0 },
    final: { name: 'Final', key: -4, lead: 'flute', leadUp: 'bell', ost: 'keys', ostOct: 0 }
  };
  function buildPlan(nBars, ending) {
    var endSec = ending === 'soft' ? 'SOFTEND' : 'BUILD', endLen = Math.min(SEC[endSec].ch.length, nBars), body = nBars - endLen, r = body % 8, plan = [], i;
    for (i = 0; i < r; i++) plan.push({ sec: 'A', bar: 8 - r + i, melody: r >= 4 && i >= r - 4 });
    for (var s = 0; s < (body - r) / 8; s++) for (i = 0; i < 8; i++) plan.push({ sec: s % 2 ? 'B' : 'A', bar: i, melody: true, rep: s });
    for (i = 0; i < endLen; i++) plan.push({ sec: endSec, bar: SEC[endSec].ch.length - endLen + i, melody: true, ending: true, fromEnd: endLen - i });
    return plan;
  }
  function inRange(pc, key, lo) { return lo + ((pc + key - lo) % 12 + 12) % 12; }

  function renderThink(opt) {
    var sr = opt.sampleRate || 44100, T = opt.seconds, style = opt.style || 'huddle';
    var K = SKETCH[style === 'final' ? 'final' : (opt.variation || 1)], key = K.key, full = style !== 'solo';
    var ending = opt.ending || (style === 'solo' ? 'soft' : 'big');
    var nBars = Math.floor(T / BAR + 1e-9), lead = T - nBars * BAR, ctx = makeCtx(T + 4.0, sr, 500 + Math.round(T));
    var MIX = full ? { lead: 1, ost: 0.8, pad: 1, bass: 1, fx: 1 } : { lead: 0.85, ost: 0.55, pad: 1, bass: 0.8, fx: 0.7 };
    for (var gk in MIX) ctx.gains[gk] = MIX[gk] * (opt.gains && opt.gains[gk] !== undefined ? opt.gains[gk] : 1);
    var plan = buildPlan(nBars, ending), rand = ctx.rand, n;
    function hum(t) { return t + (rand() - 0.5) * 0.005; }

    for (var i = 0; i < plan.length; i++) {
      var p = plan[i], t0 = lead + i * BAR, sec = SEC[p.sec], chs = sec.ch[p.bar], big = !!p.ending && ending === 'big';
      var cres = big ? 0.9 + 0.3 * (1 - (p.fromEnd - 1) / 5) : 1, lastBar = i === plan.length - 1, secsLeft = T - t0;

      /* pad: one sustained chord per harmony, long attack and release so chords melt into each other */
      for (var c = 0; c < chs.length; c++) {
        var tones = CH[chs[c]], ct = t0 + c * (BAR / chs.length), cd = BAR / chs.length;
        for (n = 0; n < 3; n++) play(ctx, 'pad', 'pad', ct - 0.12, inRange(tones[n], key, 55), cd + 0.1, (full ? 0.9 : 1) * cres, n === 1 ? 0.4 : -0.3 + n * 0.1, 0.6);
        play(ctx, 'pad', 'pad', ct - 0.12, inRange(tones[0], key, 43), cd + 0.1, 0.45 * cres, 0, 0.5);
      }

      /* ostinato: unbroken eighth notes, root-fifth-third-fifth, the thing that makes it flow */
      for (n = 0; n < 8; n++) {
        var oc = CH[chs[chs.length === 2 && n >= 4 ? 1 : 0]], r0 = inRange(oc[0], key, 48);
        var third = r0 + ((oc[1] - oc[0] + 12) % 12), fifth = r0 + ((oc[2] - oc[0] + 12) % 12);
        var patt = [r0, fifth, third + 12, fifth, r0 + 12, fifth, third + 12, fifth][n];
        if (K.ost === 'pluck') patt = [r0, third, fifth, third, r0 + 12, third, fifth, third][n];
        var ov = (n % 2 ? 0.5 : n % 4 === 0 ? 0.8 : 0.65) * cres;
        play(ctx, K.ost, 'ost', hum(t0 + n * 0.25), patt, 0.24, ov, 0.3, 0.5);
        if (big && p.fromEnd <= 2) play(ctx, K.ost, 'ost', t0 + n * 0.25 + 0.125, patt + 12, 0.12, ov * 0.6, 0.45, 0.5);   // sixteenths in the last 4 s
      }

      /* melody: legato, notes ring into each other; doubled an octave up in the full version */
      if (p.melody) {
        var mel = sec.mel[p.bar];
        for (n = 0; n < mel.length; n++) {
          var nb = mel[n], shape = 0.82 + 0.18 * Math.sin(Math.PI * (p.bar % 4 + nb[0] / 4) / 4), mv = shape * cres * (nb[1] >= 1 ? 1 : 0.85);
          var mt = hum(t0 + nb[0] * BEAT), md = nb[1] * BEAT * (K.lead === 'flute' ? 0.97 : 1.05);
          play(ctx, K.lead, 'lead', mt, nb[2] + key, md, mv, -0.12, 0.6);
          if (K.leadUp && (full || p.rep)) play(ctx, K.leadUp, 'lead', mt, nb[2] + key + 12, md, mv * 0.5, 0.25, 0.7);
        }
      }

      /* bass: round and simple. root, then fifth; walks up into the next chord at phrase ends */
      var b0 = inRange(CH[chs[0]][0], key, 36);
      if (big && lastBar) { for (n = 0; n < 8; n++) play(ctx, 'bass', 'bass', t0 + n * 0.25, inRange(7, key, 36) + (n % 2 ? 12 : 0), 0.22, 0.9 * cres, 0, 0.1); }
      else if (chs.length === 2) { play(ctx, 'bass', 'bass', t0, b0, 0.9, 0.9 * cres, 0, 0.1); play(ctx, 'bass', 'bass', t0 + 1, inRange(CH[chs[1]][0], key, 36), 0.9, 0.85 * cres, 0, 0.1); }
      else {
        play(ctx, 'bass', 'bass', t0, b0, full ? 0.7 : 0.95, 0.9 * cres, 0, 0.1);
        if (full) play(ctx, 'bass', 'bass', t0 + 0.75, b0, 0.2, 0.55 * cres, 0, 0.1);
        play(ctx, 'bass', 'bass', t0 + 1, b0 + ((CH[chs[0]][2] - CH[chs[0]][0] + 12) % 12) - (b0 > 41 ? 12 : 0), 0.9, 0.75 * cres, 0, 0.1);
      }

      /* clock through the last ten seconds */
      if (secsLeft <= 10.001 && opt.ticks !== false) {
        var tv = full ? 1 : 0.6;
        tick(ctx, t0, tv, true); tick(ctx, t0 + 1, tv, false);
        if (secsLeft <= 4.001) { tick(ctx, t0 + 0.5, tv * 0.7, false); tick(ctx, t0 + 1.5, tv * 0.7, false); }
      }
    }

    /* landing at exactly T */
    var rootB = inRange(0, key, 36);
    if (ending === 'big') {
      var sp = [48, 55, 60, 64, 67, 72, 76];
      for (n = 0; n < sp.length; n++) { play(ctx, 'pad', 'pad', T - 0.02, sp[n] + key, 1.6, 1.0, (n - 3) * 0.2, 0.7); play(ctx, 'mallet', 'lead', T, sp[n] + key + 12, 1.5, 0.45, (n - 3) * 0.15, 0.7); }
      play(ctx, 'bass', 'bass', T, rootB, 1.6, 0.9, 0, 0.15); thump(ctx, T, rootB, 0.6);
      for (n = 0; n < 6; n++) play(ctx, 'bell', 'fx', T + 0.06 + n * 0.06, 84 + key + [0, 4, 7, 12, 16, 19][n], 1.0, 0.7, 0.4 - n * 0.1, 0.8);
    } else {
      [0, 4, 7, 14].forEach(function (iv, j) { play(ctx, 'mallet', 'lead', T + j * 0.03, 72 + key + iv, 2.0, 0.7, -0.2 + j * 0.12, 0.7); });
      play(ctx, 'pad', 'pad', T - 0.1, 60 + key, 1.5, 1, 0, 0.6); play(ctx, 'pad', 'pad', T - 0.1, 67 + key, 1.5, 1, 0.2, 0.6);
      play(ctx, 'bass', 'bass', T, rootB, 1.6, 0.9, 0, 0.1);
      play(ctx, 'bell', 'fx', T, 96 + key, 1.5, 0.8, 0.3, 0.8);
    }
    return master(ctx, full ? 0.62 : 0.56, 1.6);
  }

  /* ---------- stings: same clean palette ---------- */
  function renderSting(name, sr) {
    sr = sr || 44100; var ctx, n;
    function arp(ins, t, notes, step, dur, vel) { for (var j = 0; j < notes.length; j++) play(ctx, ins, 'fx', t + j * step, notes[j], dur, vel, -0.3 + 0.6 * j / notes.length, 0.7); }
    function chord(ins, t, notes, dur, vel) { for (var j = 0; j < notes.length; j++) play(ctx, ins, 'fx', t, notes[j], dur, vel, -0.4 + 0.8 * j / notes.length, 0.7); }
    if (name === 'pick') { ctx = makeCtx(2.2, sr, 1); arp('mallet', 0.02, [72, 76, 79, 84], 0.07, 0.6, 0.8); play(ctx, 'bell', 'fx', 0.3, 96, 0.8, 0.8, 0.3, 0.8); }
    else if (name === 'double') { ctx = makeCtx(4.5, sr, 2); arp('mallet', 0.02, [67, 67, 67], 0.16, 0.12, 0.9); chord('pad', 0.5, [48, 60, 64, 67, 72], 0.5, 1.6); chord('mallet', 0.52, [72, 76, 79], 0.5, 0.8); chord('pad', 1.02, [46, 58, 62, 65, 70], 0.4, 1.6); chord('mallet', 1.04, [70, 74, 77], 0.4, 0.8); chord('pad', 1.52, [48, 60, 64, 67, 72, 76], 1.5, 1.8); chord('mallet', 1.54, [72, 76, 79, 84], 1.5, 0.9); thump(ctx, 0.52, 36, 0.8); thump(ctx, 1.54, 36, 1); arp('bell', 1.6, [84, 86, 88, 91, 93, 96, 98, 100], 0.055, 0.9, 0.6); }
    else if (name === 'huddle') { ctx = makeCtx(2.2, sr, 3); arp('wood', 0.02, [79, 79, 84], 0.17, 0.2, 0.9); arp('pluck', 0.02, [67, 67, 72], 0.17, 0.2, 0.9); play(ctx, 'bass', 'fx', 0.36, 48, 0.4, 0.8, 0, 0.1); }
    else if (name === 'boards') { ctx = makeCtx(2.8, sr, 4); play(ctx, 'bell', 'fx', 0.02, 84, 0.5, 0.9, -0.2, 0.8); play(ctx, 'mallet', 'fx', 0.02, 72, 0.5, 0.9, -0.2, 0.6); play(ctx, 'bell', 'fx', 0.34, 91, 1.4, 1.0, 0.2, 0.8); play(ctx, 'mallet', 'fx', 0.34, 79, 1.4, 1.0, 0.2, 0.6); thump(ctx, 0.34, 43, 0.6); }
    else if (name === 'correct') { ctx = makeCtx(3.0, sr, 5); arp('bell', 0.02, [84, 88, 91, 96, 100], 0.07, 0.8, 0.8); arp('pluck', 0.02, [72, 76, 79, 84, 88], 0.07, 0.3, 0.8); chord('pad', 0.4, [60, 64, 67, 72], 0.9, 1.6); chord('mallet', 0.42, [72, 76, 79, 84], 1.0, 0.75); thump(ctx, 0.42, 36, 0.7); }
    else if (name === 'notyet') { ctx = makeCtx(2.2, sr, 6); play(ctx, 'wood', 'fx', 0.02, 67, 0.3, 1, -0.1, 0.5); play(ctx, 'wood', 'fx', 0.02, 55, 0.3, 0.8, -0.1, 0.5); play(ctx, 'wood', 'fx', 0.32, 64, 0.5, 0.95, 0.1, 0.5); play(ctx, 'wood', 'fx', 0.32, 52, 0.5, 0.8, 0.1, 0.5); play(ctx, 'bass', 'fx', 0.32, 40, 0.5, 0.7, 0, 0.1); }
    else if (name === 'winner') { ctx = makeCtx(8.5, sr, 7);
      [[0.1, 0.42, [48, 60, 64, 67, 72]], [0.6, 0.42, [53, 60, 65, 69, 72]], [1.1, 0.42, [48, 60, 64, 67, 76]], [1.6, 0.9, [55, 59, 62, 67, 74]], [2.6, 0.35, [55, 62, 65, 71, 77]], [3.1, 2.6, [48, 60, 64, 67, 72, 79, 84]]].forEach(function (ev) { chord('pad', ev[0] - 0.02, ev[2], ev[1], 1.7); chord('mallet', ev[0], ev[2].slice(1).map(function (m) { return m + 12; }), ev[1], 0.8); thump(ctx, ev[0], ev[2][0] - 12, 0.8); });
      arp('bell', 3.15, [84, 86, 88, 91, 93, 96, 98, 100, 103], 0.06, 0.9, 0.6);
      for (n = 0; n < 3; n++) arp('mallet', 4.0 + n * 0.5, [72, 76, 79, 84].map(function (m) { return m + (n === 2 ? 12 : 0); }), 0.11, 0.6, 0.6); }
    else throw new Error('unknown sting ' + name);
    return master(ctx, 0.8, 1.6);
  }

  var api = { renderThink: renderThink, renderSting: renderSting, STINGS: ['pick', 'double', 'huddle', 'boards', 'correct', 'notyet', 'winner'], SKETCHES: { 1: 'Music box', 2: 'Tiptoe', 3: 'Lounge' }, VERSION: '0.2' };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.QuizMusic = api;
})(typeof self !== 'undefined' ? self : this);
