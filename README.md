# SafeText — Is this message a scam?

An AI scam-message checker for older adults. Paste a suspicious SMS /
WhatsApp message, get a risk score, the words that raised it, a
plain-language explanation, and a safe next step. Built for
**SLAY HACKS 2026** (Devpost, deadline 2026-12-07 17:00 EST).

## What it is

- **Real, trained model — no paid API, no server.** A TF-IDF +
  logistic-regression classifier, trained on 24,161 labelled messages and
  evaluated on held-out data. The learned weights ship with the page as
  `app/model.json` and run entirely in the browser. Nothing you paste
  leaves your device.
- **Explainable.** Every score shows the words/phrases that pushed it up
  or down, with their exact contribution. The plain-language "why" notes
  are only wording for words that actually raised the score — they never
  change the score.
- **Built for older adults.** Large text, high contrast, no account, no
  jargon, one clear action per screen.

## Run it locally

```sh
cd app
python3 -m http.server 8734
# open http://localhost:8734/index.html
```

Or open `app/index.html` directly — but note `fetch("model.json")` needs
http(s); `file://` may block it in some browsers. The `http.server`
command above is the reliable way.

To retrain:

```sh
python3 -m venv .venv && .venv/bin/pip install scikit-learn
.venv/bin/python train.py   # rebuilds app/model.json + model_metrics.json
```

## Model results (honest numbers)

Training data: UCI SMS Spam Collection v.1 (Almeida et al., 2011) +
Scam Shield SMS train+val (Hugging Face, CC-BY-4.0), exact-deduped to
24,161 messages (50.1% scam). Stratified 80/20 split, random_state=42.

| Model | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| **Logistic regression (shipped)** | **0.933** | **0.944** | **0.922** | **0.932** |
| Multinomial Naive Bayes | 0.916 | 0.930 | 0.900 | 0.915 |

Independent check on Scam Shield `test.csv` (1,510 messages the model
was **never trained on**): accuracy **0.952**, precision **0.992**,
recall **0.939**, F1 **0.965**.

Demo examples (all written by us, none in the training data): **6/6
correct** — bank lockout 96, prize scam 99, grandchild scam 91, doctor
reminder 26, family message 6, parcel update 31 (risk scores out of 100).

## Known limitations (stated on the page too)

- English SMS-style text only.
- Scams that read like an ordinary family message are the hardest case;
  the 2011-only model missed the grandchild example — adding the modern
  Scam Shield data fixed it, but a brand-new scam wording can still slip
  through. See `BUILD_LOG.md` for that story.
- Never a substitute for calling the person or company directly on a
  number you already know.

## Datasets & citations

- UCI Machine Learning Repository, “SMS Spam Collection”
  (DOI 10.24432/C5CC84). Almeida, T.A., Gómez Hidalgo, J.M., Yamakami, A.
  (2011), *Contributions to the study of SMS Spam Filtering*, ACM DocEng'11.
  Free for research/educational use.
- Hugging Face, “rasheq/scam-shield-sms”, version 1.1.0, **CC-BY-4.0**.
  Mixes real messages with clearly-labelled synthetic examples, including
  family-impersonation scams. Used to train rasheq/scam-shield-distilbert.

## Files

- `app/` — the demo: `index.html`, `app.js`, `style.css`, `model.json`
- `train.py` — training + evaluation + model export (reproducible)
- `model_metrics.json`, `demo_scores.json` — the numbers behind the claims
- `data/` — the two public datasets as downloaded
- `BUILD_LOG.md` — decisions, dead ends, and validation evidence
- `PLAN.md` — what is left before the Devpost submission
- `LICENSE` — MIT
- `.github/workflows/pages.yml` — deploys `app/` to GitHub Pages on every push to `main`
