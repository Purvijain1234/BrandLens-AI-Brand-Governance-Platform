import json
import os
import sys
from typing import List, Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.app.review.pipeline import run_pipeline, ReviewOptions

def run_evaluation() -> Dict[str, Any]:
    dataset_path = os.path.join(os.path.dirname(__file__), "dataset.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    total_samples = len(samples)
    tp = 0
    fp = 0
    fn = 0

    print("=" * 80)
    print(" BRANDLENS (TEAM DOUBLE TROUBLE) - L5 EVALUATION BENCHMARK ")
    print("=" * 80)
    print(f"{'ID':<4} | {'Sample Snippet':<36} | {'Expected':<12} | {'Predicted':<12} | {'Match'}")
    print("-" * 80)

    for s in samples:
        opts = ReviewOptions(
            rules_only=False,
            has_image=s.get("has_image", False),
            alt_text=s.get("alt_text", ""),
            fg_color=s.get("fg_color", "#9aa6b2"),
            bg_color=s.get("bg_color", "#ffffff"),
        )
        res = run_pipeline(s["text"], opts)
        predicted_sources = sorted(list(set(f["source_id"] for f in res.findings)))
        expected_sources = sorted(list(set(s.get("expected_sources", []))))

        # Calculate TP, FP, FN for this sample
        sample_tp = len(set(predicted_sources).intersection(set(expected_sources)))
        sample_fp = len(set(predicted_sources) - set(expected_sources))
        sample_fn = len(set(expected_sources) - set(predicted_sources))

        tp += sample_tp
        fp += sample_fp
        fn += sample_fn

        snippet = (s["text"][:33] + "...") if len(s["text"]) > 36 else s["text"]
        match_str = "PASS" if sample_fp == 0 and sample_fn == 0 else "PARTIAL"
        print(f"{s['id']:<4} | {snippet:<36} | {','.join(expected_sources) or 'None':<12} | {','.join(predicted_sources) or 'None':<12} | {match_str}")

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    print("=" * 80)
    print(" EVALUATION SUMMARY METRICS ")
    print("=" * 80)
    print(f" Total Labelled Samples Evaluated: {total_samples}")
    print(f" Ground Truth Violations:           {tp + fn}")
    print(f" System Raised Violations:          {tp + fp}")
    print(f" True Positives (TP):               {tp}")
    print(f" False Positives (FP):              {fp}")
    print(f" False Negatives (FN):              {fn}")
    print(f" Precision:                         {precision:.2%}")
    print(f" Recall:                            {recall:.2%}")
    print(f" F1-Score:                          {f1:.2%}")
    print("=" * 80)

    return {
        "total_samples": total_samples,
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": round(precision * 100, 2),
        "recall": round(recall * 100, 2),
        "f1_score": round(f1 * 100, 2),
    }

if __name__ == "__main__":
    run_evaluation()
