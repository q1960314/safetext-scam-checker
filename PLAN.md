# SafeText — remaining steps to submission

Deadline: **2026-12-07 17:00 EST = 2026-12-08 06:00 Beijing**. Do NOT submit
to Devpost yet — that needs the user's Devpost account and final approval.

## Done (2026-11-24)
- [x] Trained, evaluated, exported model (logistic regression, F1 0.932 held-out)
- [x] Working static web app in `app/` with 6 built-in examples, 6/6 correct
- [x] JS port verified exact vs Python (306 messages, max diff 2.2e-16)
- [x] End-to-end UI test in jsdom, zero JS errors; wording bug fixed
- [x] Local demo serving at http://localhost:8734/index.html
- [x] README + build log written

## Step 1 — GitHub repo (after local validation: DONE, so this is next)
- Create public repo `safetext` under q1960314 (browser, like the token-radar repo).
- Push the whole `~/workspace/slay-hacks/` tree except `.venv/` (see `.gitignore`).
- README is already written for the repo root.

## Step 2 — Public demo link (preferred: GitHub Pages)
- Enable GitHub Pages on the repo, serving from `app/` (or move `app/`
  contents to repo root / `docs/` if Pages requires it — note `model.json`
  must sit next to `index.html`).
- Why GitHub Pages: free, static, no server to keep alive, matches the
  client-side architecture. Verify the live link by opening it and clicking
  one scam + one safe example.
- Fallback: a Muse artifact space with the same files.

## Step 3 — Screenshots (needs a real browser — headless Chromium in this
## VM cannot launch; see BUILD_LOG.md §6)
- Take in a real browser at desktop width (~1280px) and mobile width (~390px):
  1. Home page, empty checker.
  2. Grandchild scam result (verdict + risk meter + reasons).
  3. Doctor reminder result (safe verdict).
  4. (Optional) the "How it works" section showing honest metrics.
- Save as PNG in `screenshots/` in the repo.

## Step 4 — Demo video (2–4 min, script)
- 0:00–0:20 The problem: older adults lose real money to text scams; show one real-world style scam message.
- 0:20–1:00 Live demo: paste the grandchild scam → 91/100, words highlighted, plain-language reasons.
- 1:00–1:40 Paste a real message (doctor reminder) → 26/100, safe; paste a prize scam → 99/100.
- 1:40–2:30 How it works: real trained model (TF-IDF + logistic regression), 24,161 messages, held-out numbers on screen, privacy (nothing leaves the device).
- 2:30–3:00 Who it is for + what it cannot do (honest limits), closing line.
- Format: screen recording + voiceover (no on-camera presenter). Voiceover
  can be recorded by the user or generated TTS; screen capture needs a real
  browser session.

## Step 5 — Devpost copy (draft outline; final text at submission time)
- **Title:** SafeText — Is this message a scam?
- **Tagline:** A free, private scam checker for older adults. Paste a suspicious text, get a plain-language answer in seconds.
- **Problem:** text-message scams cost older adults billions; existing tools are built for experts, not for grandparents.
- **Solution:** paste → risk score + highlighted words + plain-language reasons + safe next step; runs fully on-device.
- **AI implementation:** TF-IDF + logistic regression, trained on UCI SMS Spam Collection + Scam Shield SMS (24,161 messages); held-out accuracy 93.3%, precision 94.4%, recall 92.2%; independent test accuracy 95.2%. Per-word contribution scores for explainability. No paid API, no server.
- **Responsible AI:** limitations stated in the app (hardest case: scams that read like family messages; English only; never a substitute for calling back on a known number); privacy by design (no data leaves the device).
- **Links:** demo (GitHub Pages), GitHub repo, video, screenshots.

## Step 6 — Submission checklist (day before deadline)
- [ ] Devpost account (user) + project created
- [ ] Demo link opens and works from a clean browser
- [ ] Video uploaded (2–4 min) and plays
- [ ] Screenshots attached
- [ ] GitHub repo public with README + setup instructions
- [ ] AI use disclosed in the submission (required by the rules)
- [ ] Prize payout method / eligibility checked (open question)
