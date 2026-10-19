/* Browser port of core/*.py (same rules, same data). Runs fully client-side. */
(function (root) {
  const D = root.CAMPUS_DATA || (typeof require !== "undefined" ? require("./data.js") : null);
  const DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"];
  const WORKDAYS = ["Sunday","Monday","Tuesday","Wednesday","Thursday"];
  const DAY_START = "09:00", DAY_END = "17:30";
  const F_STOP = new Set("sir madam mam maam er ki room number no kothay where is the what of ta teacher faculty now free available kokhon when next will be ache achen office hour hours dr prof mr ms and his her uni ekhon can i meet tell me about please koi ar ke".split(" "));
  const K_STOP = new Set("the a an is are what how do i to of in for my and can ki kivabe kothay er e ta where when".split(" "));

  /* ---------- difflib.SequenceMatcher.ratio() ---------- */
  function longest(a, b, alo, ahi, blo, bhi) {
    let bi = alo, bj = blo, bk = 0;
    for (let i = alo; i < ahi; i++) for (let j = blo; j < bhi; j++) {
      let k = 0; while (i + k < ahi && j + k < bhi && a[i + k] === b[j + k]) k++;
      if (k > bk) { bi = i; bj = j; bk = k; }
    }
    return [bi, bj, bk];
  }
  function blocks(a, b, alo, ahi, blo, bhi, acc) {
    const [i, j, k] = longest(a, b, alo, ahi, blo, bhi);
    if (!k) return;
    if (alo < i && blo < j) blocks(a, b, alo, i, blo, j, acc);
    acc.n += k;
    if (i + k < ahi && j + k < bhi) blocks(a, b, i + k, ahi, j + k, bhi, acc);
  }
  function ratio(a, b) {
    if (!a.length && !b.length) return 1;
    const acc = { n: 0 }; blocks(a, b, 0, a.length, 0, b.length, acc);
    return 2 * acc.n / (a.length + b.length);
  }
  function norm(w) {
    w = w.toLowerCase().replace(/ee/g, "i").replace(/z/g, "j").replace(/ph/g, "f").replace(/w/g, "v");
    return w.replace(/(.)\1+/g, "$1");
  }

  /* ---------- safety ---------- */
  const ORDER = ["crisis", "harassment", "cheating", "toxic", "stress"];
  const RX = {}; ORDER.forEach(l => RX[l] = D.patterns[l].map(p => new RegExp(p)));
  function classify(text) {
    const t = text.toLowerCase();
    for (const l of ORDER) {
      const hits = RX[l].filter(r => r.test(t)).length;
      if (hits) return { label: l, severity: D.severity[l], matches: hits };
    }
    return { label: "safe", severity: "none", matches: 0 };
  }
  function blockingResponse(r) {
    if (r.label === "crisis" || r.label === "harassment") return D.responses[r.label] + D.contacts.join(" | ");
    if (r.label === "cheating" || r.label === "toxic") return D.responses[r.label];
    return null;
  }
  const BAN = D.banned.map(p => new RegExp(p, "i"));
  function outputGuard(a) {
    return BAN.some(r => r.test(a)) ? "Sorry, I can't share personal contact details. I can tell you the faculty member's room and office hours instead." : a;
  }

  /* ---------- time (Asia/Dhaka) ---------- */
  function nowDhaka() {
    const p = new Intl.DateTimeFormat("en-US", { timeZone: "Asia/Dhaka", weekday: "long", hour: "2-digit", minute: "2-digit", hour12: false })
      .formatToParts(new Date()).reduce((o, x) => (o[x.type] = x.value, o), {});
    return { dayIdx: DAYS.indexOf(p.weekday), time: String(+p.hour % 24).padStart(2, "0") + ":" + p.minute };
  }

  /* ---------- faculty ---------- */
  const FAC = D.faculty;
  FAC.forEach(f => f.schedule.sort((a, b) => DAYS.indexOf(a.day) - DAYS.indexOf(b.day) || a.start.localeCompare(b.start)));
  function words(s) { return (s.toLowerCase().match(/[a-z]+/g) || []); }
  function findFaculty(text) {
    const ws = words(text).filter(w => !F_STOP.has(w));
    if (!ws.length) return [null, 0];
    let best = null, bs = 0;
    for (const f of FAC) {
      const toks = new Set([f.name, ...f.aliases].flatMap(words).filter(w => !F_STOP.has(w)));
      for (const w of ws) for (const t of toks) {
        const s = ratio(norm(w), norm(t));
        if (s > bs) { best = f; bs = s; }
      }
    }
    return bs >= 0.75 ? [best, bs] : [null, bs];
  }
  function status(f, now) {
    now = now || nowDhaka(); const day = DAYS[now.dayIdx], t = now.time;
    for (const s of f.schedule) if (s.day === day && s.start <= t && t < s.end)
      return s.type === "office_hour" ? { state: "available", label: "In office hour until " + s.end, until: s.end }
                                      : { state: "busy", label: "In class until " + s.end, until: s.end };
    if (WORKDAYS.includes(day) && DAY_START <= t && t < DAY_END)
      return { state: "free", label: "Not in class right now (may be in office)", until: null };
    return { state: "off", label: "Outside university hours", until: null };
  }
  function nextOfficeHour(f, now) {
    now = now || nowDhaka();
    for (let add = 0; add < 8; add++) {
      const day = DAYS[(now.dayIdx + add) % 7];
      for (const s of f.schedule) if (s.day === day && s.type === "office_hour" && (add > 0 || s.start > now.time))
        return { day, when: add === 0 ? "today" : add === 1 ? "tomorrow" : day, start: s.start, end: s.end };
    }
    return null;
  }
  function pub(f, now) { return Object.assign({}, f, { status: status(f, now), next_office_hour: nextOfficeHour(f, now) }); }
  const faculty = {
    find: findFaculty, status, nextOfficeHour, all: now => FAC.map(f => pub(f, now)),
    answer(text, now) {
      const [f, score] = findFaculty(text);
      if (!f) return { found: false, text: "I couldn't find that faculty member. Could you say the full name?" };
      const st = status(f, now), nxt = nextOfficeHour(f, now);
      let r = `${f.name} (${f.designation}, ${f.department}) sits in room ${f.room_no}, building ${f.building}. ${st.label}.`;
      if (st.state !== "available" && nxt) r += ` Next office hour: ${nxt.when} ${nxt.start} to ${nxt.end}.`;
      return { found: true, text: r, faculty: pub(f, now), match: Math.round(score * 100) / 100 };
    },
  };

  /* ---------- knowledge (TF-IDF) ---------- */
  const tok = s => (s.toLowerCase().match(/[a-z0-9]+/g) || []).filter(w => !K_STOP.has(w));
  const docsTok = D.faq.map(d => tok(d.question + " " + (d.keywords || []).join(" ") + " " + d.answer));
  const df = {}; docsTok.forEach(t => new Set(t).forEach(w => df[w] = (df[w] || 0) + 1));
  const idf = {}; Object.keys(df).forEach(w => idf[w] = Math.log((docsTok.length + 1) / (df[w] + 1)) + 1);
  function vec(tokens) {
    const tf = {}; tokens.forEach(w => tf[w] = (tf[w] || 0) + 1);
    const v = {}; let n = 0;
    for (const w in tf) { v[w] = tf[w] * (idf[w] || 0); n += v[w] * v[w]; }
    n = Math.sqrt(n) || 1; for (const w in v) v[w] /= n; return v;
  }
  const vecs = docsTok.map(vec);
  const THRESH = 0.18;
  function kbAnswer(q) {
    const qv = vec(tok(q));
    let bi = -1, bs = -1;
    vecs.forEach((v, i) => { let s = 0; for (const w in v) s += (qv[w] || 0) * v[w]; if (s > bs) { bs = s; bi = i; } });
    bs = Math.round(bs * 1000) / 1000;
    if (bi < 0 || bs < THRESH) return { found: false, confidence: bs, text: "I'm not sure about that. Please check the AIUB website or ask the relevant office." };
    const d = D.faq[bi];
    return { found: true, confidence: bs, text: d.answer, source: d.source || "campus_faq.json", topic: d.question };
  }

  /* ---------- assistant ---------- */
  const FACULTY_WORDS = /\b(sir|madam|mam|maam|room|office hour|available|free|kothay|faculty|teacher|kokhon)\b/;
  const GREET = /^(hi|hello|hey|salam|assalamu alaikum|kemon acho|hola)\b/;
  const stats = {}, log = [];
  const bump = k => stats[k] = (stats[k] || 0) + 1;
  function handle(text, now) {
    const t0 = performance.now();
    text = (text || "").trim().slice(0, 500);
    if (!text) return { reply: "I didn't catch that. Please try again.", intent: "empty" };
    const safety = classify(text);
    const pipeline = [{ step: "Speech to text", detail: "browser / Whisper" }, { step: "Safety classifier", detail: safety.label }];
    const blocked = blockingResponse(safety);
    let intent, reply, extra = {};
    if (blocked) {
      intent = "safety_escalation"; reply = blocked;
      pipeline.push({ step: "Crisis / policy response", detail: safety.label });
    } else {
      const tl = text.toLowerCase(); const [f] = findFaculty(text);
      intent = GREET.test(tl) ? "greeting" : (f && (FACULTY_WORDS.test(tl) || tl.split(/\s+/).length <= 4) ? "faculty" : "campus_faq");
      pipeline.push({ step: "Intent router", detail: intent });
      if (intent === "greeting") reply = "Hi! I'm your AIUB Campus Companion. Ask me things like \"Nazib sir er room number ki?\" or \"How is CGPA calculated?\"";
      else if (intent === "faculty") {
        const r = faculty.answer(text, now); reply = r.text; extra = { faculty: r.faculty, match: r.match };
        pipeline.push({ step: "Faculty database", detail: "match " + (r.match || 0) });
      } else {
        const r = kbAnswer(text); reply = r.text; extra = { source: r.source, confidence: r.confidence };
        pipeline.push({ step: "Knowledge base (RAG)", detail: "confidence " + r.confidence });
      }
      if (safety.label === "stress") reply += " It sounds like you're under some pressure. Take a short break, breathe slowly, and talk to someone you trust. AIUB counseling is there for you too.";
    }
    reply = outputGuard(reply);
    pipeline.push({ step: "Output guard", detail: "passed" }, { step: "Text to speech", detail: "browser / Parler-TTS" });
    bump(intent); bump("safety_" + safety.label);
    log.unshift({ time: new Date().toTimeString().slice(0, 8), intent, safety: safety.label, severity: safety.severity });
    if (log.length > 50) log.pop();
    return Object.assign({ reply, intent, safety, pipeline, latency_ms: Math.round((performance.now() - t0) * 10) / 10 }, extra);
  }
  const Engine = { handle, faculty, classify, dashboard: () => ({ stats: Object.assign({}, stats), log: log.slice() }) };
  if (typeof module !== "undefined") module.exports = Engine; else root.Engine = Engine;
})(typeof window !== "undefined" ? window : globalThis);
