#!/usr/bin/env python3
"""SafeText — train a real SMS spam/scam classifier.

Dataset: UCI SMS Spam Collection v.1 (5,574 messages) + Scam Shield SMS
train+val (Hugging Face, CC-BY-4.0). See BUILD_LOG.md for sources,
licenses, and the honest evaluation numbers.

Models compared on a stratified 80/20 held-out split (random_state=42):
  A) TF-IDF (word 1-2 grams) + Logistic Regression (class_weight=balanced)
  B) TF-IDF (word 1-2 grams) + Multinomial Naive Bayes
Winner is picked by F1 on the held-out set, then exported to JSON so the
exact learned weights run in the browser (no server, no paid API).
"""
import csv, json, re, sys
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, confusion_matrix, classification_report)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

DATA = "data/SMSSpamCollection"
SCAM_SHIELD = ["data/scam-shield-train.csv", "data/scam-shield-val.csv"]
OUT_MODEL = "app/model.json"
OUT_METRICS = "model_metrics.json"

EXAMPLES = [
    ("scam", "URGENT: Your bank account has been locked. Verify your identity now at http://secure-bank-login.net or your funds will be frozen within 24 hours."),
    ("scam", "Congratulations! You've won a $1,000 Amazon gift card. Click here to claim your prize before it expires today: bit.ly/claim-now"),
    ("scam", "Hi Grandma, it's me, I lost my phone and I need $500 for a new one. Please send it by gift card, and don't tell Mom and Dad."),
    ("legit", "Hi, this is Dr. Patel's office reminding you of your appointment tomorrow at 10:30 AM. Reply YES to confirm or call 555-0142 to reschedule."),
    ("legit", "Hi Mom, I'm running late, I'll be home around 7. Can you save me some dinner? Love, Sarah"),
    ("legit", "Your package is out for delivery and will arrive today by 8 PM. Track it here: usps.com/track/940011189"),
]

def main():
    rows, skipped = [], 0
    with open(DATA, newline="", encoding="utf-8") as f:
        for parts in csv.reader(f, delimiter="\t"):
            if len(parts) != 2:
                skipped += 1
                continue
            label, text = parts
            rows.append((1 if label == "spam" else 0, text, "uci"))
    if skipped:
        print(f"note: skipped {skipped} malformed line(s) in UCI file")
    # Second public dataset: Scam Shield SMS (Hugging Face, CC-BY-4.0).
    # Mixes real messages with clearly-labelled synthetic examples, including
    # modern family-impersonation / gift-card scams the 2011 UCI corpus
    # predates. Train+val only; its own test.csv is kept untouched as an
    # extra out-of-sample check.
    ss_rows = 0
    for path in SCAM_SHIELD:
        with open(path, newline="", encoding="utf-8") as f:
            for rec in csv.DictReader(f):
                text = (rec.get("text") or "").strip()
                label = (rec.get("label") or "").strip()
                if not text or label not in ("scam", "safe"):
                    continue
                rows.append((1 if label == "scam" else 0, text,
                             "scamshield:" + (rec.get("source") or "?")))
                ss_rows += 1
    print(f"scam-shield train+val rows added: {ss_rows}")
    # exact-text dedupe (keep first occurrence, UCI first)
    seen, deduped, dups = set(), [], 0
    for label, text, src in rows:
        key = text.strip()
        if key in seen:
            dups += 1
            continue
        seen.add(key)
        deduped.append((label, text, src))
    rows = deduped
    print(f"after exact dedupe: {len(rows)} rows ({dups} duplicates removed)")
    labels = np.array([r[0] for r in rows])
    texts_all = [r[1] for r in rows]
    print(f"dataset: {len(rows)} messages, spam={labels.sum()} ({labels.mean():.1%})")
    # sanity: none of the demo examples may be in the training data verbatim
    texts = set(t.strip() for t in texts_all)
    for kind, ex in EXAMPLES:
        assert ex not in texts, f"demo example overlaps training data: {ex[:40]}"
    print("demo examples: no verbatim overlap with training data")

    X_train, X_test, y_train, y_test = train_test_split(
        texts_all, labels, test_size=0.20, random_state=42, stratify=labels)

    vec = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=2,
                          max_features=8000, sublinear_tf=True)
    models = {
        "logreg": LogisticRegression(C=1.0, class_weight="balanced", max_iter=1000),
        "nb": MultinomialNB(alpha=0.1),
    }
    results = {}
    for name, clf in models.items():
        pipe = Pipeline([("tfidf", vec), ("clf", clf)])
        pipe.fit(X_train, y_train)
        pred = pipe.predict(X_test)
        proba = pipe.predict_proba(X_test)[:, 1]
        results[name] = {
            "accuracy": float(accuracy_score(y_test, pred)),
            "precision": float(precision_score(y_test, pred, zero_division=0)),
            "recall": float(recall_score(y_test, pred, zero_division=0)),
            "f1": float(f1_score(y_test, pred, zero_division=0)),
            "confusion": [[int(c) for c in row] for row in confusion_matrix(y_test, pred).tolist()],
            "pipe": pipe,
        }
        print(f"\n{name}: acc={results[name]['accuracy']:.4f} "
              f"prec={results[name]['precision']:.4f} rec={results[name]['recall']:.4f} "
              f"f1={results[name]['f1']:.4f} conf={results[name]['confusion']}")

    best_name = max(results, key=lambda k: results[k]["f1"])
    best = results[best_name]
    print(f"\nwinner by F1: {best_name} (f1={best['f1']:.4f})")
    print(classification_report(y_test, best["pipe"].predict(X_test),
                                target_names=["ham", "spam"]))

    # ---- export the winner's exact learned weights for the browser ----
    pipe = best["pipe"]
    tfidf = pipe.named_steps["tfidf"]
    clf = pipe.named_steps["clf"]
    vocab = {term: int(idx) for term, idx in tfidf.vocabulary_.items()}
    idf = tfidf.idf_.tolist()
    if hasattr(clf, "coef_"):
        coef = clf.coef_[0].tolist()
        intercept = float(clf.intercept_[0])
        kind = "logistic_regression"
    else:
        # MultinomialNB: log-prob difference is the linear score
        coef = (clf.feature_log_prob_[1] - clf.feature_log_prob_[0]).tolist()
        intercept = float(clf.class_log_prior_[1] - clf.class_log_prior_[0])
        kind = "multinomial_nb_logodds"
    model = {
        "model": kind,
        "vocab": vocab,
        "idf": idf,
        "coef": coef,
        "intercept": intercept,
        "token_pattern": "lowercase, word tokens of 2+ chars, 1-2 grams",
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "metrics": {k: v for k, v in best.items() if k != "pipe"},
        "all_models": {k: {kk: vv for kk, vv in v.items() if kk != "pipe"}
                       for k, v in results.items()},
        "dataset": "UCI SMS Spam Collection v.1 (Almeida et al. 2011), 5572 msgs + "
                   "Scam Shield SMS train+val (Hugging Face rasheq/scam-shield-sms, "
                   "CC-BY-4.0), exact-deduped",
        "threshold": 0.5,
    }
    with open(OUT_MODEL, "w") as f:
        json.dump(model, f)
    with open(OUT_METRICS, "w") as f:
        json.dump(model["all_models"], f, indent=2)
    print(f"\nexported {OUT_MODEL} ({len(vocab)} features, {kind})")

    # ---- score the demo examples with the exported (Python) pipeline ----
    print("\ndemo examples (held-out from training, scored by the model):")
    demo = []
    for kind, ex in EXAMPLES:
        p = float(pipe.predict_proba([ex])[0, 1])
        verdict = "SCAM" if p >= 0.5 else "SAFE"
        ok = (verdict == "SCAM") == (kind == "scam")
        demo.append({"expected": kind, "score": round(p, 4), "verdict": verdict,
                     "correct": ok, "text": ex})
        print(f"  [{'OK ' if ok else 'MISS'}] expected={kind:5s} p(spam)={p:.3f} -> {verdict}: {ex[:70]}...")
    print(f"demo accuracy: {sum(d['correct'] for d in demo)}/{len(demo)}")
    with open("demo_scores.json", "w") as f:
        json.dump(demo, f, indent=2)

    # ---- extra out-of-sample check: scam-shield test.csv was never trained on ----
    ss_test = []
    with open("data/scam-shield-test.csv", newline="", encoding="utf-8") as f:
        for rec in csv.DictReader(f):
            text = (rec.get("text") or "").strip()
            label = (rec.get("label") or "").strip()
            if text and label in ("scam", "safe"):
                ss_test.append((1 if label == "scam" else 0, text))
    y_ss = np.array([r[0] for r in ss_test])
    pred_ss = pipe.predict([r[1] for r in ss_test])
    print(f"\nscam-shield test.csv (never trained on, n={len(ss_test)}): "
          f"acc={accuracy_score(y_ss, pred_ss):.4f} "
          f"prec={precision_score(y_ss, pred_ss, zero_division=0):.4f} "
          f"rec={recall_score(y_ss, pred_ss, zero_division=0):.4f} "
          f"f1={f1_score(y_ss, pred_ss, zero_division=0):.4f} "
          f"conf={confusion_matrix(y_ss, pred_ss).tolist()}")

if __name__ == "__main__":
    main()
