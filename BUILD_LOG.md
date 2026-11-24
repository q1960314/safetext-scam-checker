# SafeText — build log

## 2026-11-24 — first working build (this round)

### Decisions
- **Project:** SafeText, an AI scam-message checker for older adults.
  Decided by the parent agent; not re-picked. Rationale: real problem
  (elder scam losses), demoable in 30 seconds, strong responsible-AI angle.
- **Architecture: fully static, client-side model.** The trained weights
  are exported to `app/model.json` and the TF-IDF + logistic-regression
  scoring is re-implemented in `app/app.js`. No backend, no paid API key,
  nothing leaves the user's device. This makes the public demo a free
  static host (GitHub Pages) instead of a server we have to keep alive.
  Trade-off accepted: the model file is 462 KB and the model is small by
  design (TF-IDF + linear model, 8,000 features).
- **Language:** everything in English (app, docs, code comments).

### Datasets (sources + licenses)
1. **UCI SMS Spam Collection v.1** — 5,574 messages (4,827 ham / 747 spam).
   Downloaded from the UCI ML Repository
   (archive.ics.uci.edu, dataset 228). Almeida, T.A., Gómez Hidalgo, J.M.,
   Yamakami, A. (2011), ACM DocEng'11. Free for research/educational use.
   DOI 10.24432/C5CC84. Two lines in the file were malformed and skipped;
   5,572 rows used.
2. **Scam Shield SMS** (Hugging Face `rasheq/scam-shield-sms`, v1.1.0,
   **CC-BY-4.0**) — train 21,054 + val 1,508 rows used for training;
   test 1,510 rows kept untouched as an extra out-of-sample check. Mixes
   real messages with clearly-labelled synthetic examples, including
   family-impersonation / gift-card scams. Used to train the published
   rasheq/scam-shield-distilbert model.
3. After exact-text dedupe: **24,161 rows, 50.1% scam** (3,973 duplicates
   removed, mostly UCI/NUS messages also present in Scam Shield).

### The honest miss, and the fix
- First model (UCI only, Naive Bayes won on F1 0.9395): demo **5/6**.
  It missed the **grandchild impersonation scam** ("Hi Grandma, it's me,
  I lost my phone and I need $500… send it by gift card, don't tell Mom
  and Dad") at p=0.018 — it reads like a normal family message, and a
  2011 corpus predates gift-card scams. Logistic regression on UCI-only
  was worse on the demo (4/6, and it false-alarmed a doctor reminder).
- Fix, done legitimately: added the second public dataset above, which
  contains modern family-impersonation scams. **No demo example was added
  to training data** — all 6 demo messages were verified to have no
  verbatim overlap with either dataset, before and after the change.
- Second model (combined data, logistic regression won on F1 0.9324):
  demo **6/6** — bank lockout 0.962, prize 0.989, grandchild 0.907,
  doctor reminder 0.265, family message 0.061, parcel update 0.309.

### Evaluation (held-out, stratified 80/20, random_state=42, n=4,833)
| Model | Acc | Prec | Rec | F1 |
|---|---|---|---|---|
| Logistic regression (shipped) | 0.9332 | 0.9437 | 0.9215 | 0.9324 |
| Multinomial Naive Bayes | 0.9162 | 0.9303 | 0.9000 | 0.9149 |

Independent check — Scam Shield test.csv, never trained on (n=1,510):
acc 0.9523, precision 0.9919, recall 0.9388, F1 0.9646.

Note the held-out F1 fell slightly vs UCI-only (0.94 → 0.93) because the
combined task is harder (modern + synthetic variety), but the model now
generalises to modern scams, which is the point of the product. Full
numbers in `model_metrics.json`; demo scores in `demo_scores.json`.

### Validation done this round
1. **Model:** `train.py` exit 0; metrics reproduced on re-run.
2. **JS port exactness:** the real `app.js` was executed in Node (vm
   sandbox) and compared with Python probabilities on **306 messages**
   (300 random held-out + 6 demo): max |JS − Python| = **2.2e-16**,
   0 rows differing by >1e-6. The browser model is the trained model,
   not a re-implementation that drifts.
3. **Local demo serving:** `python3 -m http.server 8734` in `app/` —
   index.html, model.json, app.js, style.css all HTTP 200. Server left
   running (PID in `/tmp/safetext_server.log`); demo URL
   http://localhost:8734/index.html.
4. **End-to-end UI test (jsdom, real app.js + real DOM):** all 6 example
   buttons clicked, verdicts and scores correct (scams 96/99/91, legit
   26/6/31); an unseen custom message (customs-fee scam) scored 94 →
   SCAM; Clear button works; **zero JS errors**.
5. **Bug found and fixed in UI testing:** the "why" notes were showing
   scam-pattern wording under SAFE verdicts (e.g. "asks you to click a
   link" on a doctor reminder). Fixed: notes only appear for scores
   ≥ 0.35; safe messages now get "No pressure tactics…" wording. Also
   removed "gift" from the prize group so the grandchild scam's reasons
   read correctly (gift cards / secrecy / family impersonation).
6. **NOT validated:** visual rendering in a real browser. Headless
   Chromium in this VM refuses to launch ("Hatch WebGL domain policy is
   required for browser startup", both /opt/meta-chromium/chrome and the
   hatch-chromium-sandbox wrapper; the system Google Chrome from Nov 23
   is no longer installed). Screenshots must be taken in a real browser
   — see PLAN.md. The layout is plain semantic HTML + CSS and the JS
   runs error-free, but no screenshot exists yet.

### Open items / risks
- Visual check + screenshots outstanding (needs a real browser).
- Prize payout eligibility / KYC for the Devpost prize (China) not
  verified — same open question as the other money routes.
- "Best Beginner" $500 requires first-time hackathon participants; the
  user may qualify, but I built the entry as an agent — do not claim it
  without checking the rules.
