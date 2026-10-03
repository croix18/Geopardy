/* Review game — trivia night on a quiz-show board. Every team answers every question; scores only go up. */
(function () {
'use strict';
var UNIT = JSON.parse(document.getElementById('unit').textContent);
var SCHED = null; try { SCHED = JSON.parse(document.getElementById('schedule').textContent); } catch (e) {}
var SAVE_KEY = 'reviewgame.v1.' + String(UNIT.title).toLowerCase().replace(/[^a-z0-9]+/g, '-') + '.' + UNIT.categories.length + 'x' + UNIT.tiers.length, PREF_KEY = 'reviewgame.prefs.v1';
var app = document.getElementById('app');
var S = null;                                   // game state (saved)
var undoStack = [];                             // snapshots (not saved)
var ui = { overlay: null, reopen: false, correct: {}, podiumShown: 0 };
var prefs = load(PREF_KEY) || { title: 'GEOPARDY!', vol: 80, tickVol: 60, music: true, teams: 6, teamSize: 4, mult: 1, huddle: 20, bonus: 50, startTier: 0, dark: true, names: [] };
if (prefs.title === 'BOARDS UP!') prefs.title = 'GEOPARDY!';   // the game was Boards Up! until 3 Oct 2026; a saved default follows the rename

function load(k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } }
function store(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
function save() { if (S) store(SAVE_KEY, S); store(PREF_KEY, prefs); }
function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }

/* ---------- text with math: $...$ inline, $$...$$ display, \$ for a literal dollar sign ---------- */
function rich(text, strict) {
  var parts = String(text).replace(/\\\$/g, '\u0001').split(/(\$\$[^$]+\$\$|\$[^$]+\$)/), out = '';
  for (var i = 0; i < parts.length; i++) {
    var p = parts[i];
    if (/^\$\$/.test(p)) out += katex.renderToString(p.slice(2, -2), { displayMode: true, throwOnError: !!strict });
    else if (/^\$/.test(p)) {   // keep punctuation that follows math on the same line as the math
      var m = katex.renderToString(p.slice(1, -1), { throwOnError: !!strict }), nx = parts[i + 1] || '', pm = /^[?.,;:!)]+/.exec(nx);
      if (pm) { parts[i + 1] = nx.slice(pm[0].length); m = '<span style="white-space:nowrap">' + m + esc(pm[0]) + '</span>'; }
      out += m;
    }
    else out += esc(p).replace(/\n/g, '<br>');
  }
  return out.replace(/\u0001/g, '$');
}
function validateUnit() {
  var bad = [];
  function chk(where, o) { ['q', 'a', 'work'].forEach(function (k) { if (!o[k] && k !== 'work') bad.push(where + ': missing ' + k); try { rich(o[k] || '', true); } catch (e) { bad.push(where + ' (' + k + '): ' + e.message.slice(0, 80)); } }); }
  UNIT.categories.forEach(function (c) { if (c.questions.length !== UNIT.tiers.length) bad.push(c.name + ': has ' + c.questions.length + ' questions, needs ' + UNIT.tiers.length); c.questions.forEach(function (q, r) { chk(c.name + ' ' + UNIT.tiers[r], q); }); });
  chk('Final', UNIT.final);
  return bad;
}

/* ---------- audio: Mozart cues that land on zero, synthesized stings, clock ticks ---------- */
var A = (function () {
  var ac = null, master = null, decoded = {}, stings = {}, live = [], LAND = 93.0;
  var TRACK = { solo: { id: 'k545', gain: 0.8, tick: 0.6 }, huddle: { id: 'finale', gain: 1.0, tick: 1.0 }, final: { id: 'menuetto', gain: 1.0, tick: 1.0 } };
  function ensure() {
    if (!ac) { var AC = window.AudioContext || window.webkitAudioContext; if (!AC) return false; ac = new AC(); master = ac.createGain(); master.connect(ac.destination); setVol(); preload(); }
    return true;
  }
  function setVol() { if (master) master.gain.value = Math.pow(prefs.vol / 100, 2); }
  function b64(id) { var s = atob(document.getElementById('au_' + id).textContent.trim()), n = s.length, u = new Uint8Array(n); for (var i = 0; i < n; i++) u[i] = s.charCodeAt(i); return u.buffer; }
  function track(id) { if (decoded[id]) return Promise.resolve(decoded[id]); return new Promise(function (res, rej) { ac.decodeAudioData(b64(id), res, rej); }).then(function (b) { decoded[id] = b; return b; }); }
  function preload() {
    ['k545', 'finale', 'menuetto'].forEach(function (id) { track(id).catch(function () {}); });
    try {   // stings are rendered once, off the main thread
      var src = document.getElementById('engine').textContent + '\nself.onmessage=function(e){var r=QuizMusic.renderSting(e.data);self.postMessage({name:e.data,left:r.left,right:r.right,sr:r.sampleRate},[r.left.buffer,r.right.buffer])};';
      var w = new Worker(URL.createObjectURL(new Blob([src], { type: 'text/javascript' })));
      w.onmessage = function (e) { var d = e.data, b = ac.createBuffer(2, d.left.length, d.sr); b.getChannelData(0).set(d.left); b.getChannelData(1).set(d.right); stings[d.name] = b; };
      ['pick', 'huddle', 'boards', 'correct', 'notyet', 'double', 'winner'].forEach(function (n) { w.postMessage(n); });
    } catch (e) {}
  }
  function now() { return ac ? ac.currentTime : performance.now() / 1000; }
  function sting(name) { if (!ac || !stings[name]) return; var s = ac.createBufferSource(), g = ac.createGain(); g.gain.value = 0.9; s.buffer = stings[name]; s.connect(g); g.connect(master); s.start(); }
  function tickAt(t, hi, v) {
    var o = ac.createOscillator(), o2 = ac.createOscillator(), g = ac.createGain(), f = hi ? 1175 : 880, lvl = 0.6 * v * Math.pow(prefs.tickVol / 100, 2);
    if (lvl <= 0) return;
    o.frequency.value = f; o2.frequency.value = f * 1.51; o.connect(g); o2.connect(g); g.connect(master);
    g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(lvl, t + 0.002); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.09);
    o.start(t); o2.start(t); o.stop(t + 0.12); o2.stop(t + 0.12); live.push(o, o2);
  }
  /* Start a cue whose final chord lands `seconds` from `at`. Music longer than the recording waits, then joins. */
  function cue(style, seconds, at) {
    stopMusic(0.12);
    if (!ac) return;
    var tr = TRACK[style], k;
    for (k = 10; k >= 1; k--) if (k <= seconds) { tickAt(at + seconds - k, k % 2 === 0, tr.tick); if (k <= 4) tickAt(at + seconds - k + 0.5, false, tr.tick * 0.7); }
    if (!prefs.music || !decoded[tr.id]) return;
    var play = Math.min(seconds, 90), startAt = at + (seconds - play), s = ac.createBufferSource(), g = ac.createGain();
    s.buffer = decoded[tr.id]; s.connect(g); g.connect(master);
    g.gain.setValueAtTime(0, startAt); g.gain.linearRampToValueAtTime(tr.gain, startAt + 1.5);
    s.start(startAt, LAND - play); s._g = g; live.push(s);
  }
  function stopMusic(fade) {
    if (!ac) return;
    var t = ac.currentTime, old = live; live = [];
    old.forEach(function (n) { try { if (n._g) { n._g.gain.cancelScheduledValues(t); n._g.gain.setValueAtTime(n._g.gain.value, t); n._g.gain.linearRampToValueAtTime(0, t + fade); n.stop(t + fade + 0.02); } else n.stop(t); } catch (e) {} });
  }
  function pause() { if (ac) ac.suspend(); }
  function resume() { if (ac) ac.resume(); }
  return { ensure: ensure, now: now, sting: sting, cue: cue, stopMusic: stopMusic, pause: pause, resume: resume, setVol: setVol, has: function () { return !!ac; } };
})();

/* ---------- countdown tied to the audio clock, so music and numbers can never drift ---------- */
var T = { endAt: 0, total: 0, running: false, paused: false, pausedLeft: 0, onDone: null, style: null, iv: null };
function timerStart(style, seconds, onDone) {
  timerStop();
  var at = A.now() + 0.15;
  T.endAt = at + seconds; T.total = seconds; T.running = true; T.paused = false; T.onDone = onDone; T.style = style;
  A.cue(style, seconds, at);
  T.iv = setInterval(timerTick, 100); timerTick();
}
function timerLeft() { return T.paused ? T.pausedLeft : Math.max(0, T.endAt - A.now()); }
function timerTick() {
  var el = document.getElementById('clock'); if (!T.running) return;
  var left = timerLeft(), s = Math.ceil(left - 0.001);
  if (el) { el.textContent = Math.floor(s / 60) + ':' + ('0' + s % 60).slice(-2); el.className = 'clock' + (left <= 10 ? ' last' : '') + (T.paused ? ' paused' : ''); }
  if (left <= 0 && !T.paused) { var cb = T.onDone; timerStop(true); if (cb) cb(); }
}
function timerStop(keepMusic) { clearInterval(T.iv); T.running = false; T.onDone = null; if (!keepMusic) A.stopMusic(0.4); }
function timerPause() {
  if (!T.running) return;
  if (!T.paused) { T.pausedLeft = timerLeft(); T.paused = true; if (A.has()) A.pause(); }
  else { T.paused = false; if (A.has()) A.resume(); else T.endAt = A.now() + T.pausedLeft; }
  timerTick(); render();
}
function timerAdd(sec) {
  if (!T.running) return;
  if (T.paused) timerPause();
  var left = timerLeft() + sec, at = A.now() + 0.05;
  T.endAt = at + left; T.total += sec; A.cue(T.style, left, at); timerTick();
}

/* ---------- game rules ---------- */
function nCats() { return UNIT.categories.length; }
function nTiers() { return UNIT.tiers.length; }
function soloSeconds(r) { var base = [30, 45, 60, 75, 90][Math.min(4, r)]; return Math.round(base * prefs.mult / 5) * 5; }
function perQuestionSeconds(r) { return soloSeconds(r) + prefs.huddle + 50; }
function estimate(minutes) {
  var budget = minutes * 60 - 6 * 60, used = 0, fit = 0, total = 0;
  for (var r = prefs.startTier; r < nTiers(); r++) for (var c = 0; c < nCats(); c++) { total++; if (used + perQuestionSeconds(r) <= budget) { used += perQuestionSeconds(r); fit++; } }
  return { fit: Math.max(0, fit), total: total };
}
function newGame() {
  var teams = [];
  for (var i = 0; i < prefs.teams; i++) teams.push({ name: (prefs.names[i] || '').trim() || 'Team ' + (i + 1), score: 0 });
  var played = [], c, r;
  for (c = 0; c < nCats(); c++) { played.push([]); for (r = 0; r < nTiers(); r++) played[c].push(r < prefs.startTier); }
  var pool = [];
  for (c = 0; c < nCats(); c++) for (r = Math.max(1, prefs.startTier); r < nTiers(); r++) pool.push([c, r]);
  var dbl = pool.length ? pool[Math.floor(Math.random() * pool.length)] : null;
  S = { screen: 'board', teams: teams, played: played, picker: 0, double: dbl, cur: null, lastSeat: 0, endTime: ui.endTime || null, finalDone: false, guardSnoozeUntil: 0, count: 0 };
  undoStack = []; save(); render();
}
function snapshot() { undoStack.push(JSON.stringify(S)); if (undoStack.length > 40) undoStack.shift(); }
function undo() { if (!undoStack.length) return; timerStop(); S = JSON.parse(undoStack.pop()); S.screen = S.finalDone ? 'podium' : 'board'; S.cur = null; ui.overlay = null; save(); render(); }
function nextTier(c) { for (var r = 0; r < nTiers(); r++) if (!S.played[c][r]) return r; return -1; }
function tilesLeft() { var n = 0; for (var c = 0; c < nCats(); c++) for (var r = 0; r < nTiers(); r++) if (!S.played[c][r]) n++; return n; }
function totalTiles() { return nCats() * (nTiers() - prefs.startTier); }
function scoresDark() { return prefs.dark && !S.finalDone && (S.count >= Math.ceil(totalTiles() * 2 / 3) || (S.cur && S.cur.final)); }
function guardSecondsLeft() {   // seconds until the Final Question must start (5 min for the final, 1 for the podium)
  if (!S || !S.endTime) return null;
  var p = S.endTime.split(':'), d = new Date(); d.setHours(+p[0], +p[1], 0, 0);
  return Math.round((d.getTime() - Date.now()) / 1000) - 360;
}
function finalSolo() { return +UNIT.final.solo || 60; }
function curQ() { return S.cur.final ? UNIT.final : UNIT.categories[S.cur.c].questions[S.cur.r]; }
function curValue() { if (S.cur.final) return UNIT.tiers[nTiers() - 1] * 2; return UNIT.tiers[S.cur.r] * (S.cur.double ? 2 : 1); }

function openTile(c) {
  var r = nextTier(c); if (r < 0) return;
  snapshot();
  var isD = !!(S.double && S.double[0] === c && S.double[1] === r);
  S.cur = { c: c, r: r, phase: 'read', double: isD, seat: 0 }; S.screen = 'question'; ui.correct = {};
  if (isD) { ui.overlay = 'double'; A.sting('double'); setTimeout(function () { if (ui.overlay === 'double') { ui.overlay = null; render(); } }, 3200); } else A.sting('pick');
  render();
}
function startFinal() { snapshot(); timerStop(); S.cur = { final: true, phase: 'read', seat: 0 }; S.screen = 'question'; ui.correct = {}; ui.overlay = null; A.sting('double'); render(); }
function startSolo() { S.cur.phase = 'solo'; render(); timerStart('solo', S.cur.final ? finalSolo() : soloSeconds(S.cur.r), toHuddle); }
function toHuddle() {
  timerStop(true);
  var seat; do { seat = 1 + Math.floor(Math.random() * prefs.teamSize); } while (prefs.teamSize > 1 && seat === S.lastSeat);
  S.cur.seat = seat; S.lastSeat = seat; S.cur.phase = 'huddle'; render();
  setTimeout(function () { A.stopMusic(0.5); A.sting('huddle'); }, T.total && timerLeft() <= 0 ? 1200 : 0);
  setTimeout(function () { if (S.cur && S.cur.phase === 'huddle') timerStart(S.cur.final ? 'final' : 'huddle', S.cur.final ? 30 : prefs.huddle, toBoards); }, 2300);
}
function skipSolo() { timerStop(); T.total = 0; toHuddle(); }
function toBoards() { timerStop(true); S.cur.phase = 'boards'; setTimeout(function () { A.sting('boards'); }, 1500); render(); }
function reveal() { S.cur.phase = 'answer'; A.stopMusic(0.6); render(); }
function award() {
  var v = curValue(), any = false;
  S.teams.forEach(function (t, i) { if (ui.correct[i]) { any = true; t.score += v + (!S.cur.final && i === S.picker ? prefs.bonus : 0); } });
  A.sting(any ? 'correct' : 'notyet');
  if (S.cur.final) { S.finalDone = true; S.screen = 'podium'; ui.podiumShown = 0; }
  else { S.played[S.cur.c][S.cur.r] = true; S.count++; S.picker = (S.picker + 1) % S.teams.length; S.screen = 'board'; }
  S.cur = null; save(); render();
  if (S.screen === 'podium') runPodium();
}
function runPodium() {
  var n = S.teams.length;
  (function step() { if (S.screen !== 'podium') return; ui.podiumShown++; render(); if (ui.podiumShown === n) A.sting('winner'); else setTimeout(step, 1400); })();
}

/* ---------- rendering ---------- */
function render() {
  var h = '';
  if (!S || S.screen === 'setup') h = viewSetup();
  else if (S.screen === 'board') h = viewBar() + viewBoard() + viewScores();
  else if (S.screen === 'question') h = viewBar() + viewQuestion();
  else if (S.screen === 'podium') h = viewBar() + viewPodium();
  app.innerHTML = h + viewOverlay();
  fitQuestion();
  if (T.running) timerTick();
}
function figHtml(q, answer) { var f = (answer && q.afig) || q.fig; return f ? '<div class="fig">' + f + '</div>' : ''; }
function fitQuestion() {   // if the question + answer block is taller than its area, scale it down to fit
  var b = app.querySelector('.qbody'), t = app.querySelector('.qtext'); if (!b || !t) return;
  t.style.zoom = '';
  var cs = getComputedStyle(b), avail = b.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom), side = b.querySelector('.side');
  if (side && cs.flexDirection === 'column') avail -= side.offsetHeight + (parseFloat(cs.rowGap) || 0);
  if (avail > 40 && t.offsetHeight > avail) t.style.zoom = Math.max(0.5, avail / t.offsetHeight).toFixed(3);
}
window.addEventListener('resize', fitQuestion);
if (document.fonts && document.fonts.ready) document.fonts.ready.then(fitQuestion);
function viewBar() {
  var g = guardSecondsLeft(), gs = '';
  if (g !== null && !S.finalDone) { var m = Math.max(0, g); gs = '<div class="guard' + (g < 180 ? ' warn' : '') + '" id="guard">FINAL IN <b>' + Math.floor(m / 60) + ':' + ('0' + m % 60).slice(-2) + '</b></div>'; }
  return '<div class="bar"><div class="title">' + esc(prefs.title) + '</div><div class="unit">' + esc(UNIT.title) + '</div>' + gs + '<button class="btn small ghost" data-act="menu">Menu</button></div>';
}
function viewBoard() {
  var cols = nCats(), longest = Math.max.apply(null, UNIT.categories.map(function (c) { return Math.max.apply(null, c.name.split(/\s+/).map(function (w) { return w.length; })); }));
  var h = '<div class="board" style="grid-template-columns:repeat(' + cols + ',minmax(0,1fr));grid-template-rows:auto repeat(' + (nTiers() - prefs.startTier) + ',minmax(0,1fr));--tf:' + Math.min(5, 21 / (nTiers() - prefs.startTier)).toFixed(2) + ';--cfp:' + Math.min(1.75, (50 / cols - 1.6) / (longest * 0.62)).toFixed(2) + '">';
  UNIT.categories.forEach(function (c) { h += '<div class="cat">' + esc(c.name) + '</div>'; });
  for (var r = prefs.startTier; r < nTiers(); r++) for (var c = 0; c < cols; c++) {
    var played = S.played[c][r], next = nextTier(c) === r, cls = played ? 'played' : next ? 'next' : 'locked';
    if (ui.reopen && played) cls += ' reopen';
    h += '<button class="tile ' + cls + '" ' + (ui.reopen ? (played ? 'data-act="reopen" data-c="' + c + '" data-r="' + r + '"' : 'disabled') : (next ? 'data-act="tile" data-c="' + c + '"' : 'disabled')) + '>' + UNIT.tiers[r] + '<small>' + esc((UNIT.tierNotes || [])[r] || '') + '</small></button>';
  }
  return h + '</div>';
}
function viewScores() {
  var dark = scoresDark();
  return '<div class="scores">' + S.teams.map(function (t, i) {
    return '<button class="team' + (i === S.picker && S.screen === 'board' ? ' pick' : '') + '" data-act="adjust" data-i="' + i + '">' + (i === S.picker && S.screen === 'board' ? '<span class="tag">PICKS</span>' : '') + '<div class="nm">' + esc(t.name) + '</div><div class="sc">' + (dark ? '?' : t.score) + '</div></button>';
  }).join('') + '</div>';
}
function viewQuestion() {
  var q = curQ(), c = S.cur, ph = c.phase, long = q.q.length > 150;
  var head = '<div class="qhead"><div class="qcat">' + esc(c.final ? 'Final Question · ' + UNIT.final.category : UNIT.categories[c.c].name) + '</div><div class="qpts">' + (c.double ? 'DOUBLE UP · ' : '') + curValue() + '</div></div>';
  var fig = figHtml(q, ph === 'answer'), ans = ph === 'answer' ? '<div class="answer"><div class="a">' + rich(q.a) + '</div>' + (q.work ? '<div class="w">' + rich(q.work) + '</div>' : '') + '</div>' : '';
  var text = '<div class="qtext' + (ph === 'answer' ? ' shrunk' : '') + (long ? ' long' : '') + (fig ? ' hasfig' : '') + '">' + rich(q.q) + (fig ? '<div class="figrow">' + fig + ans + '</div>' : ans) + '</div>';
  var side = '';
  if (ph === 'solo') side = '<div class="side"><div class="phase">Solo · silent</div><div class="clock" id="clock">0:00</div></div>';
  if (ph === 'huddle') side = '<div class="side"><div class="phase">Huddle · agree</div><div class="clock" id="clock">' + (T.running ? '' : '0:' + ('0' + (c.final ? 30 : prefs.huddle)).slice(-2)) + '</div><div class="seat">Player<b>' + c.seat + '</b>writes the board' + (c.seat > 1 ? '<i>No Player ' + c.seat + ' on your team? Player 1 writes.</i>' : '') + '</div></div>';
  if (ph === 'boards') side = '<div class="side"><div class="splash" style="font-size:calc(var(--u)*6.5)">BOARDS<br>UP!</div><div class="seat" style="margin-top:calc(var(--u)*1.5)">Player<b>' + c.seat + '</b>holds it up</div></div>';
  var foot = '';
  if (ph === 'read') foot = '<button class="btn ghost" data-act="back">Back to board</button><button class="btn go big" data-act="solo">Start solo timer · ' + fmt(c.final ? finalSolo() : soloSeconds(c.r)) + '</button>';
  if (ph === 'solo') foot = '<button class="btn ghost" data-act="pause">' + (T.paused ? 'Resume' : 'Pause') + '</button><button class="btn ghost" data-act="add">+15 sec</button><button class="btn gold" data-act="skipsolo">Everyone\'s done → Huddle</button>';
  if (ph === 'huddle') foot = '<button class="btn ghost" data-act="pause">' + (T.paused ? 'Resume' : 'Pause') + '</button><button class="btn ghost" data-act="add">+15 sec</button><button class="btn gold" data-act="skiphuddle">Boards up now</button>';
  if (ph === 'boards') foot = '<button class="btn gold big" data-act="reveal">Reveal answer</button>';
  var awardRow = '';
  if (ph === 'answer') {
    var v = curValue();
    awardRow = '<div class="award"><div class="lab">Tap every team that got it right</div><div class="row">' + S.teams.map(function (t, i) {
      var pts = v + (!c.final && i === S.picker ? prefs.bonus : 0);
      return '<button class="tog' + (ui.correct[i] ? ' on' : '') + '" data-act="tog" data-i="' + i + '">' + esc(t.name) + '<span class="plus">+' + pts + (!c.final && i === S.picker && prefs.bonus ? ' ★' : '') + '</span></button>';
    }).join('') + '</div></div>';
    foot = '<button class="btn ghost" data-act="all">All correct</button><button class="btn ghost" data-act="none">Clear</button><button class="btn go big" data-act="award">Award points</button>';
  }
  return '<div class="q">' + head + '<div class="qbody">' + text + side + '</div>' + awardRow + '<div class="qfoot">' + foot + '</div></div>';
}
function fmt(s) { return Math.floor(s / 60) + ':' + ('0' + s % 60).slice(-2); }
function viewPodium() {
  var order = S.teams.map(function (t, i) { return { t: t, i: i }; }).sort(function (a, b) { return b.t.score - a.t.score; }), n = order.length, top = order[0].t.score;
  var h = '<div class="podium"><h1>Final standings</h1>';
  order.forEach(function (o, k) {
    var place = 1 + order.filter(function (x) { return x.t.score > o.t.score; }).length, show = (n - k) <= ui.podiumShown;
    h += '<div class="rank' + (o.t.score === top ? ' first' : '') + (show ? ' show' : '') + '"><span class="pl">' + place + '</span><span class="nm">' + esc(o.t.name) + '</span><span class="sc">' + o.t.score + '</span></div>';
  });
  return h + '<div style="margin-top:calc(var(--u)*1.5)"><button class="btn ghost" data-act="newgame">New game</button></div></div>';
}
function viewOverlay() {
  var o = ui.overlay; if (!o) return '';
  if (o === 'double') return '<div class="overlay" data-act="closeov"><div class="splash">DOUBLE UP!<small>THIS TILE IS WORTH DOUBLE FOR EVERYONE</small></div></div>';
  if (o === 'menu') return '<div class="overlay"><div class="panel"><h2>Menu</h2><div class="menu">' +
    '<button class="btn" data-act="undo"' + (undoStack.length ? '' : ' disabled') + '>Undo last action</button>' +
    '<button class="btn" data-act="reopenmode"' + (S.screen !== 'board' ? ' disabled' : '') + '>Reopen a played tile</button>' +
    '<button class="btn gold" data-act="final"' + (S.finalDone || S.screen !== 'board' ? ' disabled' : '') + '>Go to Final Question</button>' +
    '<button class="btn" data-act="fullscreen">Full screen</button>' +
    '<button class="btn" data-act="printsheet">Print recording sheet</button>' +
    '<button class="btn" data-act="printkey">Print answer key</button>' +
    '<button class="btn ghost" data-act="quit">End game · back to setup</button>' +
    '<button class="btn go" data-act="closeov">Close</button></div>' +
    '<div class="field" style="margin-top:calc(var(--u)*1.2)"><label>Volume</label><input type="range" min="0" max="100" value="' + prefs.vol + '" data-pref="vol"></div>' +
    '<div class="field"><label>Clock tick</label><input type="range" min="0" max="100" value="' + prefs.tickVol + '" data-pref="tickVol"></div>' +
    '<div class="field"><label>Music</label><div class="segs"><button class="btn small' + (prefs.music ? ' gold' : '') + '" data-act="music" data-v="1">On</button><button class="btn small' + (!prefs.music ? ' gold' : '') + '" data-act="music" data-v="0">Off</button></div></div>' +
    '<p>Mozart recordings via Musopen (public domain): Piano Sonata K. 545; Symphony No. 40, Czech National Symphony Orchestra.</p></div></div>';
  if (o === 'guard') return '<div class="overlay"><div class="panel" style="text-align:center"><h2>Time for the Final Question</h2><p>The period ends at ' + esc(fmt12(S.endTime)) + '. Starting now leaves room for the final and the standings.</p><div style="display:flex;gap:calc(var(--u)*1);justify-content:center;margin-top:calc(var(--u)*1.2);flex-wrap:wrap"><button class="btn ghost" data-act="snooze">One more tile</button><button class="btn gold big" data-act="final">Go to Final</button></div></div></div>';
  if (o === 'resume') return '<div class="overlay"><div class="panel" style="text-align:center"><h2>Game in progress</h2><p>A saved game was found (' + ui.saved.count + ' questions played). Pick up where it left off?</p><div style="display:flex;gap:calc(var(--u)*1);justify-content:center;margin-top:calc(var(--u)*1.2)"><button class="btn ghost" data-act="discard">New game</button><button class="btn go big" data-act="resume">Resume</button></div></div></div>';
  if (o && o.adjust !== undefined) { var t = S.teams[o.adjust]; return '<div class="overlay"><div class="panel" style="text-align:center"><h2>' + esc(t.name) + ' · ' + t.score + '</h2><p>Fix a scoring mistake. (Game rules never subtract; this is only for corrections.)</p><div style="display:flex;gap:calc(var(--u)*.8);justify-content:center;flex-wrap:wrap">' + [-100, -50, 50, 100].map(function (d) { return '<button class="btn" data-act="adj" data-d="' + d + '">' + (d > 0 ? '+' : '') + d + '</button>'; }).join('') + '</div><div style="margin-top:calc(var(--u)*1.2)"><button class="btn go" data-act="closeov">Done</button></div></div></div>'; }
  return '';
}
function fmt12(hm) { if (!hm) return ''; var p = hm.split(':'), h = +p[0]; return ((h + 11) % 12 + 1) + ':' + p[1] + (h < 12 ? ' AM' : ' PM'); }

function viewSetup() {
  autoEndTime();
  var bad = validateUnit(), mins = minutesFromEnd(), est = mins ? estimate(mins) : null, names = '';
  for (var i = 0; i < prefs.teams; i++) names += '<input type="text" maxlength="14" placeholder="Team ' + (i + 1) + '" value="' + esc(prefs.names[i] || '') + '" data-name="' + i + '">';
  function stepper(k, lo, hi) { return '<div class="step"><button class="btn" data-act="step" data-k="' + k + '" data-d="-1" data-lo="' + lo + '" data-hi="' + hi + '">−</button><b>' + prefs[k] + '</b><button class="btn" data-act="step" data-k="' + k + '" data-d="1" data-lo="' + lo + '" data-hi="' + hi + '">+</button></div>'; }
  function segs(k, opts) { return '<div class="segs">' + opts.map(function (o) { return '<button class="btn small' + (prefs[k] === o[0] ? ' gold' : '') + '" data-act="seg" data-k="' + k + '" data-v="' + o[0] + '">' + o[1] + '</button>'; }).join('') + '</div>'; }
  var estHtml = '';
  if (est) estHtml = '<div class="est' + (est.fit < 6 ? ' bad' : '') + '">' + (mins < 8 ? 'That end time is less than 8 minutes away.' : '<b>' + mins + ' minutes</b> until the bell. About <b>' + est.fit + ' of ' + est.total + '</b> board questions will fit, plus the Final Question. The game will call the final with 6 minutes left.') + '</div>';
  else estHtml = '<div class="est">No end time set: the game will not watch the clock. You can start the Final Question from the menu whenever you like.</div>';
  return '<div class="setup"><div class="sethead"><div><h1>' + esc(prefs.title) + '</h1><p class="sub">' + esc(UNIT.course || '') + ' · ' + esc(UNIT.title) + '</p></div><button class="btn go big" data-act="start"' + (bad.length ? ' disabled' : '') + '>Tap to start · sound on</button></div><div class="cols">' +
    '<div class="box"><h3>Teams</h3>' +
      '<div class="field"><label>Number of teams</label>' + stepper('teams', 2, 8) + '</div>' +
      '<div class="field"><label>Players per team<span class="hint">Sets the random "Player N writes" call</span></label>' + stepper('teamSize', 2, 6) + '</div>' +
      '<div class="names">' + names + '</div></div>' +
    '<div class="box"><h3>Time</h3>' +
      schedLine() + '<div class="field"><label>Class ends at<span class="hint">Bell guard saves 6 minutes for the final</span></label><input type="time" id="endtime" value="' + esc(ui.endTime || '') + '"></div>' +
      '<div class="field"><label>Solo time<span class="hint">' + UNIT.tiers.map(function (t, r) { return t + ': ' + fmt(soloSeconds(r)); }).join(' · ') + '</span></label>' + segs('mult', [[1, 'Standard'], [1.25, '+25%'], [1.5, '+50%']]) + '</div>' +
      '<div class="field"><label>Huddle time</label>' + segs('huddle', [[20, '20 s'], [30, '30 s']]) + '</div>' +
      estHtml + '</div>' +
    '<div class="box"><h3>Rules</h3>' +
      '<div class="field"><label>Start the ladder at</label>' + segs('startTier', UNIT.tiers.slice(0, 2).map(function (t, r) { return [r, String(t)]; })) + '</div>' +
      '<div class="field"><label>Picker\'s bonus<span class="hint">Extra points when the picking team is right</span></label>' + segs('bonus', [[0, 'Off'], [50, '+50']]) + '</div>' +
      '<div class="field"><label>Scores go dark<span class="hint">Hidden for the last third of the game</span></label>' + segs('dark', [[true, 'On'], [false, 'Off']]) + '</div></div>' +
    '<div class="box"><h3>This game</h3>' +
      '<div class="field"><label>Title</label><input type="text" id="title" maxlength="22" value="' + esc(prefs.title) + '"></div>' +
      '<div class="field"><label>Print before class</label><div class="segs"><button class="btn small" data-act="printsheet">Recording sheet</button><button class="btn small" data-act="printkey">Answer key</button></div></div>' +
      (bad.length ? '<div class="warnlist"><b>Fix before class:</b><br>' + bad.map(esc).join('<br>') + '</div>' : '<div class="est">Unit check passed: ' + (nCats() * nTiers() + 1) + ' questions, all math renders.</div>') + '</div>' +
    '</div></div>';
}
function schedLine() {
  var b = currentBlock(); if (!b) return '';
  var txt = b.label ? '<b>' + esc(b.week) + '</b> · ' + esc(b.label) + (/^\d/.test(b.label) ? ' period' : '') + (b.wed ? ' · Wednesday bells' : '') : '<b>' + esc(b.week) + '</b> · no class in session right now';
  return '<div class="field"><label>' + txt + '<span class="hint">From your Deckhand bell schedule' + (ui.endTouched ? ' · end time set by hand' : '') + '</span></label><div class="segs"><button class="btn small" data-act="flipweek">Switch week</button>' + (ui.endTouched ? '<button class="btn small" data-act="autoend">Use schedule</button>' : '') + '</div></div>';
}
function minutesFromEnd() { if (!ui.endTime) return null; var p = ui.endTime.split(':'), d = new Date(); d.setHours(+p[0], +p[1], 0, 0); var m = Math.round((d - Date.now()) / 60000); return m > 0 ? m : null; }

/* ---------- bell schedule (copied from Deckhand): which period is it, and when does it end? ---------- */
function schoolMins(hm) { var p = hm.split(':'), h = +p[0]; if (h < 6) h += 12; return h * 60 + (+p[1]); }
function autoWeekIndex(d) {
  var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(SCHED.anchorMonday); if (!m || SCHED.groups.length < 2) return 0;
  var anchorIdx = SCHED.groups[1].name === SCHED.anchorWeekName ? 1 : 0;
  function mondayOf(x) { var y = new Date(x.getFullYear(), x.getMonth(), x.getDate()); y.setDate(y.getDate() - ((y.getDay() + 6) % 7)); return y; }
  var diff = Math.round((mondayOf(d) - mondayOf(new Date(+m[1], +m[2] - 1, +m[3]))) / 604800000);
  return (((diff % 2) + 2) % 2 === 0) ? anchorIdx : (anchorIdx === 0 ? 1 : 0);
}
function currentBlock() {   // the block happening now, or starting within 5 minutes
  if (!SCHED || !SCHED.groups || !SCHED.groups.length) return null;
  var d = new Date(), day = d.getDay(); if (day === 0 || day === 6) return null;
  var gi = ui.weekFlip ? 1 - autoWeekIndex(d) : autoWeekIndex(d), g = SCHED.groups[gi] || SCHED.groups[0];
  var list = (day === 3 && g.wednesday) ? g.wednesday : g.regular, now = d.getHours() * 60 + d.getMinutes() + d.getSeconds() / 60;
  for (var i = 0; i < list.length; i++) { var st = schoolMins(list[i].start), en = schoolMins(list[i].end); if (now >= st - 5 && now < en) return { week: g.name, label: list[i].label, end: en, wed: day === 3 && !!g.wednesday }; }
  return { week: g.name, label: null };
}
function autoEndTime() {
  if (ui.endTouched) return; var b = currentBlock();
  ui.endTime = b && b.label ? ('0' + Math.floor(b.end / 60)).slice(-2) + ':' + ('0' + b.end % 60).slice(-2) : null;
}

/* ---------- printing ---------- */
function printWhenReady() {
  var go = function () { window.print(); };
  try { Promise.all(Array.from(document.fonts).map(function (f) { return f.load(); })).then(go, go); } catch (e) { go(); }
}
function printSheet() {
  var P = document.getElementById('print'), cats = UNIT.categories, pages = [], perPage = 2, h = '';
  for (var i = 0; i < cats.length; i += perPage) pages.push(cats.slice(i, i + perPage));
  pages.forEach(function (pc, pi) {
    var last = pi === pages.length - 1;
    h += '<div class="pg"><div class="ph"><h1>' + esc(prefs.title) + ' · Recording Sheet</h1><div>Name<span class="ln"></span>Team<span class="ln s"></span>Player #<span class="ln s"></span></div></div><div class="sheet" style="grid-template-rows:repeat(' + nTiers() + ',1fr)' + (last ? ' .8fr' : '') + (pc.length === 1 ? ';grid-template-columns:1fr' : '') + '">';
    for (var r = 0; r < nTiers(); r++) pc.forEach(function (c) { h += '<div class="cell"><div class="hd"><span>' + esc(c.name) + '</span><span>' + UNIT.tiers[r] + '</span></div><div class="ans">Answer<span></span></div></div>'; });
    if (pc.length < perPage) for (r = 0; r < 0; r++) {}
    if (last) h += '<div class="cell final" style="grid-column:1/-1"><div class="hd"><span>Final Question · ' + esc(UNIT.final.category) + '</span><span>' + UNIT.tiers[nTiers() - 1] * 2 + '</span></div><div class="ans">Answer<span></span></div></div>';
    h += '</div></div>';
  });
  P.innerHTML = h; printWhenReady();
}
function printKey() {
  var P = document.getElementById('print'), h = '<div class="ph"><h1>' + esc(prefs.title) + ' · Answer Key</h1><div>' + esc(UNIT.title) + '</div></div><table class="key"><tr><th>Tile</th><th>Question</th><th>Answer</th><th>Work</th></tr>';
  UNIT.categories.forEach(function (c) { c.questions.forEach(function (q, r) { h += '<tr><td class="pt">' + esc(c.name) + '<br>' + UNIT.tiers[r] + '</td><td>' + rich(q.q) + figHtml(q, true) + '</td><td><b>' + rich(q.a) + '</b></td><td>' + rich(q.work || '') + '</td></tr>'; }); });
  h += '<tr><td class="pt">FINAL<br>' + UNIT.tiers[nTiers() - 1] * 2 + '</td><td>' + rich(UNIT.final.q) + figHtml(UNIT.final, true) + '</td><td><b>' + rich(UNIT.final.a) + '</b></td><td>' + rich(UNIT.final.work || '') + '</td></tr></table>';
  P.innerHTML = h; printWhenReady();
}

/* ---------- input ---------- */
function act(a, d, el) {
  switch (a) {
    case 'start': readSetup(); A.ensure(); A.resume(); newGame(); break;
    case 'step': prefs[d.k] = Math.max(+d.lo, Math.min(+d.hi, prefs[d.k] + (+d.d))); readSetup(); save(); render(); break;
    case 'seg': var v = d.v; prefs[d.k] = v === 'true' ? true : v === 'false' ? false : +v; readSetup(); save(); render(); break;
    case 'flipweek': readSetup(); ui.weekFlip = !ui.weekFlip; ui.endTouched = false; render(); break;
    case 'autoend': readSetup(); ui.endTouched = false; render(); break;
    case 'tile': openTile(+d.c); break;
    case 'back': undo(); break;
    case 'solo': startSolo(); break;
    case 'pause': timerPause(); break;
    case 'add': timerAdd(15); break;
    case 'skipsolo': skipSolo(); break;
    case 'skiphuddle': timerStop(); toBoards(); break;
    case 'reveal': reveal(); break;
    case 'tog': ui.correct[d.i] = !ui.correct[d.i]; render(); break;
    case 'all': S.teams.forEach(function (t, i) { ui.correct[i] = true; }); render(); break;
    case 'none': ui.correct = {}; render(); break;
    case 'award': snapshotAward(); break;
    case 'menu': ui.overlay = 'menu'; render(); break;
    case 'closeov': ui.overlay = null; render(); break;
    case 'undo': undo(); break;
    case 'reopenmode': if (S.screen !== 'board') break; ui.reopen = true; ui.overlay = null; S.screen = 'board'; render(); break;
    case 'reopen': snapshot(); S.played[+d.c][+d.r] = false; S.count = Math.max(0, S.count - 1); ui.reopen = false; save(); render(); break;
    case 'final': startFinal(); break;
    case 'snooze': S.guardSnoozeUntil = Date.now() + 4 * 60000; ui.overlay = null; save(); render(); break;
    case 'fullscreen': var de = document.documentElement; if (document.fullscreenElement) document.exitFullscreen(); else if (de.requestFullscreen) de.requestFullscreen().catch(function () {}); ui.overlay = null; render(); break;
    case 'printsheet': printSheet(); break;
    case 'printkey': printKey(); break;
    case 'music': prefs.music = d.v === '1'; if (!prefs.music) A.stopMusic(0.3); save(); render(); break;
    case 'quit': timerStop(); S = null; ui.overlay = null; try { localStorage.removeItem(SAVE_KEY); } catch (e) {} render(); break;
    case 'newgame': S = null; try { localStorage.removeItem(SAVE_KEY); } catch (e) {} render(); break;
    case 'adjust': if (S.screen === 'board' && !ui.reopen) { ui.overlay = { adjust: +d.i }; render(); } break;
    case 'adj': snapshot(); var t = S.teams[ui.overlay.adjust]; t.score = Math.max(0, t.score + (+d.d)); save(); render(); break;
    case 'resume': S = ui.saved; S.cur = null; if (S.screen === 'question') S.screen = 'board'; ui.endTime = S.endTime; ui.overlay = null; A.ensure(); A.resume(); ui.podiumShown = S.teams.length; render(); break;
    case 'discard': ui.overlay = null; try { localStorage.removeItem(SAVE_KEY); } catch (e) {} render(); break;
  }
}
function snapshotAward() { award(); }
function readSetup() {
  var t = document.getElementById('title'), e = document.getElementById('endtime');
  if (t) prefs.title = t.value.trim() || 'GEOPARDY!';
  if (e) ui.endTime = e.value || null;
  Array.prototype.forEach.call(document.querySelectorAll('[data-name]'), function (inp) { prefs.names[+inp.dataset.name] = inp.value; });
}
app.addEventListener('click', function (e) {
  var el = e.target.closest('[data-act]'); if (!el || el.disabled) return;
  if (el.classList.contains('overlay') && e.target !== el) return;
  act(el.dataset.act, el.dataset, el);
});
app.addEventListener('change', function (e) {
  if (e.target.id === 'endtime') ui.endTouched = true;
  if (e.target.id === 'endtime' || e.target.id === 'title' || e.target.dataset.name !== undefined) { readSetup(); save(); if (e.target.id !== 'title' && e.target.dataset.name === undefined) render(); }
});
app.addEventListener('input', function (e) { var k = e.target.dataset && e.target.dataset.pref; if (k) { prefs[k] = +e.target.value; A.setVol(); save(); } });
document.addEventListener('keydown', function (e) {
  if (/INPUT/.test(e.target.tagName) || !S) return;
  if (e.key === ' ') { e.preventDefault(); var b = app.querySelector('.qfoot .btn.go, .qfoot .btn.gold.big'); if (b) b.click(); }
  if (e.key === 'u' || e.key === 'U') undo();
  if (e.key === 'p' || e.key === 'P') timerPause();
});
setInterval(function () {   // bell guard
  if (!S || S.finalDone) return;
  var g = guardSecondsLeft(), el = document.getElementById('guard');
  if (g === null) return;
  if (el) { var m = Math.max(0, g); el.className = 'guard' + (g < 180 ? ' warn' : ''); el.innerHTML = 'FINAL IN <b>' + Math.floor(m / 60) + ':' + ('0' + m % 60).slice(-2) + '</b>'; }
  if (g <= 0 && S.screen === 'board' && !ui.overlay && Date.now() > (S.guardSnoozeUntil || 0)) { ui.overlay = 'guard'; render(); }
}, 1000);

/* ---------- boot ---------- */
var saved = load(SAVE_KEY);
if (saved && saved.teams && (saved.count > 0 || saved.finalDone)) { ui.saved = saved; ui.overlay = 'resume'; }
render();
window.__game = { state: function () { return S; }, prefs: prefs };
})();
