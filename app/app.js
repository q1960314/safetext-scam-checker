/* SafeText — the trained model runs entirely in this file + model.json.
   It replicates scikit-learn's TfidfVectorizer (lowercase, word tokens of
   2+ characters, 1-2 grams, sublinear tf, L2 norm) + logistic regression
   exactly, using the weights learned in train.py. Nothing is sent anywhere.
   The plain-language "why" notes below are only wording: they are shown
   when a word that actually pushed the score up is present. They never
   change the score. */

let MODEL = null;

const EXAMPLES = [
  { label: "Bank lockout scam", expected: "scam",
    text: "URGENT: Your bank account has been locked. Verify your identity now at http://secure-bank-login.net or your funds will be frozen within 24 hours." },
  { label: "Prize scam", expected: "scam",
    text: "Congratulations! You've won a $1,000 Amazon gift card. Click here to claim your prize before it expires today: bit.ly/claim-now" },
  { label: "Grandchild scam", expected: "scam",
    text: "Hi Grandma, it's me, I lost my phone and I need $500 for a new one. Please send it by gift card, and don't tell Mom and Dad." },
  { label: "Doctor reminder (real)", expected: "safe",
    text: "Hi, this is Dr. Patel's office reminding you of your appointment tomorrow at 10:30 AM. Reply YES to confirm or call 555-0142 to reschedule." },
  { label: "Message from Sarah (real)", expected: "safe",
    text: "Hi Mom, I'm running late, I'll be home around 7. Can you save me some dinner? Love, Sarah" },
  { label: "Parcel update (real)", expected: "safe",
    text: "Your package is out for delivery and will arrive today by 8 PM. Track it here: usps.com/track/940011189" },
];

/* Word -> plain-language note. Shown ONLY when that word actually raised
   this message's score. The score itself comes only from the model. */
const EXPLAIN = [
  { words: ["urgent", "immediately", "now", "today", "expires", "expire", "hurry", "limited", "act", "within", "hours"], note: "It pressures you to act fast — real banks and companies do not rush you like this." },
  { words: ["won", "win", "prize", "congratulations", "winner", "claim", "reward", "free"], note: "It promises free money or a prize you never entered to win." },
  { words: ["click", "link", "verify", "confirm", "update", "login", "account", "locked", "suspended", "blocked", "security"], note: "It asks you to click a link or log in — the link usually goes to a fake copy of a real website." },
  { words: ["card", "gift", "send", "money", "payment", "wire", "bitcoin", "paypal"], note: "It asks for money or gift cards. No real company or family member asks to be paid in gift cards." },
  { words: ["secret", "tell", "mom", "dad", "parents", "anyone"], note: "It asks you to keep it secret from family — scammers say this so nobody can warn you." },
  { words: ["bank", "amazon", "apple", "paypal", "usps", "fedex", "irs", "police"], note: "It pretends to be a company, bank, or government office you know." },
  { words: ["grandma", "grandpa", "mum", "mom", "son", "daughter", "grandson", "granddaughter", "phone", "lost"], note: "It pretends to be a family member in trouble — a very common scam aimed at grandparents." },
];

function tokenize(text) {
  // sklearn default token pattern (?u)\b\w\w+\b, lowercased
  return (text.toLowerCase().match(/[\p{L}\p{N}_]{2,}/gu) || []);
}

function scoreMessage(text) {
  const tokens = tokenize(text);
  const grams = [];
  for (let i = 0; i < tokens.length; i++) {
    grams.push(tokens[i]);
    if (i + 1 < tokens.length) grams.push(tokens[i] + " " + tokens[i + 1]);
  }
  const counts = new Map();
  for (const g of grams) counts.set(g, (counts.get(g) || 0) + 1);
  // sublinear tf: 1 + ln(count), times idf, then L2-normalize
  const vec = [];
  let normSq = 0;
  for (const [term, c] of counts) {
    const idx = MODEL.vocab[term];
    if (idx === undefined) continue;
    const v = (1 + Math.log(c)) * MODEL.idf[idx];
    vec.push([term, idx, v]);
    normSq += v * v;
  }
  const norm = Math.sqrt(normSq) || 1;
  let score = MODEL.intercept;
  const contrib = [];
  for (const [term, idx, v] of vec) {
    const tfidf = v / norm;
    const c = tfidf * MODEL.coef[idx];
    score += c;
    contrib.push({ term, c });
  }
  const p = 1 / (1 + Math.exp(-score));
  contrib.sort((a, b) => b.c - a.c);
  return { p, contrib, tokens };
}

function explain(tokens, contrib) {
  const raised = new Set(contrib.filter(x => x.c > 0.03).map(x => x.term));
  const present = new Set(tokens);
  const notes = [];
  for (const group of EXPLAIN) {
    const hit = group.words.some(w =>
      present.has(w) && [...raised].some(t => t === w || t.startsWith(w + " ") || t.endsWith(" " + w)));
    if (hit) notes.push(group.note);
  }
  return notes;
}

function verdictFor(p) {
  if (p >= 0.65) return { cls: "scam", title: "⚠️ Likely a scam — do not reply or click anything.",
    advice: "Do not reply. Do not click any link. Do not send money or gift cards. If it says it is family, call them on the number you already have — not a number in this message. Report it as spam in your messaging app, then delete it." };
  if (p >= 0.35) return { cls: "unsure", title: "❓ Not sure — be careful with this one.",
    advice: "Do not click or reply yet. Call the company or person using a number you already know — not a number from this message. If you cannot reach them, ask a family member to look at it with you." };
  return { cls: "safe", title: "✅ Looks like an ordinary message.",
    advice: "This looks fine. Still, never share passwords, PINs, or one-time codes by text — no real company asks for those." };
}

function runCheck() {
  const text = document.getElementById("msg").value.trim();
  if (!text) { alert("Please paste a message first."); return; }
  const { p, contrib, tokens } = scoreMessage(text);
  const v = verdictFor(p);
  const result = document.getElementById("result");
  result.classList.remove("hidden");
  const verdictEl = document.getElementById("verdict");
  verdictEl.textContent = v.title;
  verdictEl.className = "verdict " + v.cls;
  const fill = document.getElementById("meterfill");
  fill.style.width = Math.round(p * 100) + "%";
  fill.style.background = v.cls === "scam" ? "#b91c1c" : v.cls === "unsure" ? "#b45309" : "#166534";
  document.getElementById("score").textContent =
    "Risk score: " + Math.round(p * 100) + " out of 100. (The model calls it a scam at 50 or higher.)";
  const notes = p >= 0.35 ? explain(tokens, contrib) : [];
  document.getElementById("reasons").innerHTML = notes.length
    ? notes.map(n => "<li>" + n + "</li>").join("")
    : "<li>No pressure tactics, no prize promises, and no requests for money or secret-keeping in this message.</li>";
  const top = contrib.filter(x => x.c > 0.02).slice(0, 5);
  const bottom = contrib.filter(x => x.c < -0.02).slice(-2).reverse();
  let feats = top.map(x => "<li><code>" + escapeHtml(x.term) + "</code> pushed the score up by " + x.c.toFixed(2) + "</li>");
  feats = feats.concat(bottom.map(x => "<li><code>" + escapeHtml(x.term) + "</code> pushed the score down by " + Math.abs(x.c).toFixed(2) + "</li>"));
  document.getElementById("features").innerHTML = feats.length
    ? feats.join("")
    : "<li>No single word mattered much — the judgement came from the whole message.</li>";
  document.getElementById("advice").textContent = v.advice;
  result.scrollIntoView({ behavior: "smooth", block: "start" });
}

function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function init() {
  const box = document.getElementById("examples");
  EXAMPLES.forEach((ex, i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = ex.label;
    b.onclick = () => {
      document.getElementById("msg").value = ex.text;
      runCheck();
    };
    box.appendChild(b);
  });
  document.getElementById("check").onclick = runCheck;
  document.getElementById("clear").onclick = () => {
    document.getElementById("msg").value = "";
    document.getElementById("result").classList.add("hidden");
    document.getElementById("msg").focus();
  };
}

fetch("model.json")
  .then(r => r.json())
  .then(m => { MODEL = m; init(); })
  .catch(() => {
    document.getElementById("msg").placeholder =
      "Could not load the checker model (model.json). Please open this page from the app folder.";
  });
