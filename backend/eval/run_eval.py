"""
Eval-Harness: Misst Klassifizierungsqualität gegen eval/gold_set.jsonl.

Führt jeden Gold-Set-Eintrag durch die echte Pipeline:
    pre_filter -> rule_classifier -> classify_batch -> Merge

Gibt Precision/Recall/F1 pro Kategorie und Plattform + Confusion-Matrix aus.
Exit-Code 1 wenn Makro-F1 < FAIL_THRESHOLD.

Verwendung:
    cd backend
    python eval/run_eval.py

Nach einer Prompt-Änderung: PROMPT_VERSION in .env hochzählen, dann erneut ausführen.
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

# Stelle sicher, dass backend/ im Python-Pfad ist
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from services.groq_classifier import classify_batch
from services.pre_filter import pre_filter
from services.rule_classifier import apply_rules

GOLD_FILE               = Path(__file__).parent / "gold_set.jsonl"
FAIL_THRESHOLD          = 0.75   # Gesamt-Makro-F1 (legacy, für CI-Summary)
CRITICALITY_THRESHOLD   = 0.80   # B8: separater Schwellenwert für Kategorie-Accuracy
PLATFORM_THRESHOLD      = 0.70   # B8: separater Schwellenwert für Plattform-Accuracy


# ---------------------------------------------------------------------------
# Pipeline (gleiche Logik wie scheduler._merge_article, aber ohne Cosmos)
# ---------------------------------------------------------------------------

def _run_pipeline_item(item: dict) -> dict:
    title   = item["title"]
    summary = item.get("summary", "")
    source  = item.get("source", "")

    pf = pre_filter(title, summary)
    if pf["off_topic"]:
        return {
            "pred_category": "OFF_TOPIC",
            "pred_platform": "cross",
        }

    rules = apply_rules(title, summary, source)
    if rules["forced_critical"]:
        platform = rules.get("platform_hint") or settings.DEFAULT_PLATFORM
        return {
            "pred_category": "KRITISCH",
            "pred_platform": platform,
        }

    # LLM-Klassifizierung
    results = classify_batch([{"idx": 0, "title": title, "source": source, "summary": summary}])
    llm = results[0]

    forced_critical = rules.get("forced_critical", False)
    category = "KRITISCH" if forced_critical else llm.get("criticality", "NORMAL")
    platform = llm.get("platform") or rules.get("platform_hint") or settings.DEFAULT_PLATFORM

    return {
        "pred_category": category,
        "pred_platform": platform,
    }


# ---------------------------------------------------------------------------
# Metriken
# ---------------------------------------------------------------------------

def _precision_recall_f1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return precision, recall, f1


def _compute_metrics(labels: list[str], preds: list[str]) -> dict:
    classes = sorted(set(labels) | set(preds))
    metrics = {}
    for cls in classes:
        tp = sum(1 for l, p in zip(labels, preds) if l == cls and p == cls)
        fp = sum(1 for l, p in zip(labels, preds) if l != cls and p == cls)
        fn = sum(1 for l, p in zip(labels, preds) if l == cls and p != cls)
        p, r, f = _precision_recall_f1(tp, fp, fn)
        metrics[cls] = {"precision": p, "recall": r, "f1": f, "support": tp + fn}
    macro_f1 = sum(m["f1"] for m in metrics.values()) / len(metrics) if metrics else 0.0
    return {"classes": metrics, "macro_f1": macro_f1}


def _confusion_matrix(labels: list[str], preds: list[str]) -> dict[str, dict[str, int]]:
    classes = sorted(set(labels) | set(preds))
    matrix: dict[str, dict[str, int]] = {c: {p: 0 for p in classes} for c in classes}
    for l, p in zip(labels, preds):
        matrix[l][p] += 1
    return matrix


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    if not GOLD_FILE.exists():
        print(f"[ERROR] Gold-Set nicht gefunden: {GOLD_FILE}", file=sys.stderr)
        return 1

    items = []
    with open(GOLD_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))

    if not items:
        print("[ERROR] Gold-Set ist leer.", file=sys.stderr)
        return 1

    print(f"\n=== Eval-Harness ===  PROMPT_VERSION={settings.PROMPT_VERSION}  Items={len(items)}\n")

    true_cats: list[str] = []
    pred_cats: list[str] = []
    true_plat: list[str] = []
    pred_plat: list[str] = []
    mismatches: list[dict] = []

    for item in items:
        expected_cat  = item["expected_category"]
        expected_plat = item["expected_platform"]

        result = _run_pipeline_item(item)
        pred_cat  = result["pred_category"]
        pred_plat = result["pred_platform"]

        true_cats.append(expected_cat)
        pred_cats.append(pred_cat)
        true_plat.append(expected_plat)
        pred_plat.append(pred_plat)

        if pred_cat != expected_cat or pred_plat != expected_plat:
            mismatches.append({
                "title":         item["title"][:70],
                "expected_cat":  expected_cat,
                "got_cat":       pred_cat,
                "expected_plat": expected_plat,
                "got_plat":      pred_plat,
            })

    # --- Kategorie-Metriken ---
    cat_metrics = _compute_metrics(true_cats, pred_cats)
    print("── Kategorie ──────────────────────────────────────────────")
    print(f"{'Klasse':<12} {'Precision':>9} {'Recall':>8} {'F1':>6} {'Support':>8}")
    print("-" * 50)
    for cls, m in cat_metrics["classes"].items():
        print(f"{cls:<12} {m['precision']:>9.2f} {m['recall']:>8.2f} {m['f1']:>6.2f} {m['support']:>8}")
    print(f"\n  Makro-F1 (Kategorie): {cat_metrics['macro_f1']:.3f}")

    # --- Plattform-Metriken ---
    plat_metrics = _compute_metrics(true_plat, pred_plat)
    print("\n── Plattform ──────────────────────────────────────────────")
    print(f"{'Klasse':<12} {'Precision':>9} {'Recall':>8} {'F1':>6} {'Support':>8}")
    print("-" * 50)
    for cls, m in plat_metrics["classes"].items():
        print(f"{cls:<12} {m['precision']:>9.2f} {m['recall']:>8.2f} {m['f1']:>6.2f} {m['support']:>8}")
    print(f"\n  Makro-F1 (Plattform): {plat_metrics['macro_f1']:.3f}")

    # --- Confusion-Matrix ---
    cm = _confusion_matrix(true_cats, pred_cats)
    classes = sorted(cm.keys())
    print("\n── Confusion-Matrix (Kategorie, Zeile=erwartet, Spalte=erhalten) ──")
    header = f"{'':>12}" + "".join(f"{c:>10}" for c in classes)
    print(header)
    for row in classes:
        line = f"{row:>12}" + "".join(f"{cm[row].get(c, 0):>10}" for c in classes)
        print(line)

    # --- Fehlklassifikationen ---
    if mismatches:
        print(f"\n── Fehlklassifikationen ({len(mismatches)}) ──────────────────────────")
        for m in mismatches:
            print(
                f"  [{m['expected_cat']:>9}/{m['expected_plat']:>7}] "
                f"→ [{m['got_cat']:>9}/{m['got_plat']:>7}]  "
                f"{m['title']}"
            )
    else:
        print("\n  Keine Fehlklassifikationen!")

    # --- Accuracy pro Dimension ---
    criticality_acc = sum(1 for l, p in zip(true_cats, pred_cats) if l == p) / len(true_cats)
    platform_acc    = sum(1 for l, p in zip(true_plat, pred_plat) if l == p) / len(true_plat)

    # --- Schwellenwert ---
    overall_f1 = (cat_metrics["macro_f1"] + plat_metrics["macro_f1"]) / 2
    print(f"\n  Gesamt-F1 (Kat+Plat Ø): {overall_f1:.3f}  |  Schwelle: {FAIL_THRESHOLD}")
    print(f"  Criticality Accuracy:    {criticality_acc:.3f}  |  Schwelle: {CRITICALITY_THRESHOLD}")
    print(f"  Platform Accuracy:       {platform_acc:.3f}  |  Schwelle: {PLATFORM_THRESHOLD}")

    failed = False
    if criticality_acc < CRITICALITY_THRESHOLD:
        print(f"\n[FAIL] Criticality Accuracy {criticality_acc:.3f} < {CRITICALITY_THRESHOLD}  → Exit 1")
        failed = True
    if platform_acc < PLATFORM_THRESHOLD:
        print(f"\n[FAIL] Platform Accuracy {platform_acc:.3f} < {PLATFORM_THRESHOLD}  → Exit 1")
        failed = True

    if failed:
        return 1

    print(f"\n[PASS] Criticality={criticality_acc:.3f} >= {CRITICALITY_THRESHOLD}  |  Platform={platform_acc:.3f} >= {PLATFORM_THRESHOLD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
