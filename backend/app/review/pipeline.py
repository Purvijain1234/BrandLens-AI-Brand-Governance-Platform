import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from backend.app.review.rules import run_rule_engine, FindingItem
from backend.app.review.retrieval import segment_text, retrieve_top_k_sources
from backend.app.review.ai_judge import run_ai_judge
from backend.app.review.verify import verify_and_ground_findings, VerifiedFinding
from backend.app.db.database import db

class ReviewOptions(BaseModel):
    rules_only: bool = False
    confidential_mode: bool = False
    has_image: bool = False
    alt_text: str = ""
    fg_color: str = "#9aa6b2"
    bg_color: str = "#ffffff"

class PipelineResult(BaseModel):
    findings: List[Dict[str, Any]]
    ai_used: bool
    ai_calls_count: int
    rule_checks_count: int
    open_count: int
    high_count: int
    summary: str

def run_pipeline(
    text: str,
    options: ReviewOptions,
    org_id: str = "00000000-0000-0000-0000-000000000001",
    content_item_id: Optional[str] = None,
) -> PipelineResult:
    """
    BrandLens End-to-End Review Pipeline:
    L1 (Deterministic Rules) -> L2 (Retrieval) -> L3 (AI Judge) -> L4 (Verification)
    """
    conn = db.get_connection()
    cur = conn.cursor()

    # Fetch Knowledge Base data
    cur.execute("SELECT * FROM terms WHERE org_id = ?", (org_id,))
    terms = cur.fetchall()

    cur.execute("SELECT * FROM facts WHERE org_id = ?", (org_id,))
    facts = cur.fetchall()

    cur.execute("SELECT * FROM clauses")
    clauses = cur.fetchall()

    cur.execute("SELECT * FROM assets WHERE org_id = ? AND type = 'palette'", (org_id,))
    palette_row = cur.fetchone()
    palette = json.loads(palette_row["palette_json"]) if palette_row and palette_row.get("palette_json") else ["#1b2a49", "#0f8b8d", "#ffffff", "#e8a33d"]

    cur.execute("SELECT * FROM redaction_terms WHERE org_id = ?", (org_id,))
    redaction_rows = cur.fetchall()
    redaction_map = {r["term"]: (r.get("replacement") or f"[CONFIDENTIAL_{r['id'][:4]}]") for r in redaction_rows}
    conn.close()

    # Find approved price from facts (F-014)
    price_fact = next((f["value"] for f in facts if f["id"] == "F-014"), "1,199")

    # Step 1: L1 Deterministic Rules Engine
    l1_findings = run_rule_engine(
        text=text,
        terms=terms,
        approved_price=price_fact,
        palette=palette,
        has_image=options.has_image,
        alt_text=options.alt_text,
        fg_color=options.fg_color,
        bg_color=options.bg_color,
    )

    all_findings: List[Dict[str, Any]] = [f.model_dump() for f in l1_findings]
    for f in all_findings:
        f["state"] = "open"

    ai_calls_count = 0
    ai_used = False

    # Step 2 & 3 & 4: Retrieval, AI Judge & Verification (if not rules_only)
    if not options.rules_only:
        try:
            segments = segment_text(text)
            for seg in segments:
                # L2: Retrieval
                top_sources = retrieve_top_k_sources(seg, clauses, facts, k=4)
                if not top_sources:
                    continue

                # L3: AI Judge
                ai_raw = run_ai_judge(
                    segment=seg,
                    retrieved_sources=top_sources,
                    content_item_id=content_item_id,
                    org_id=org_id,
                    confidential_mode=options.confidential_mode,
                    redaction_map=redaction_map,
                )
                if ai_raw:
                    ai_calls_count += 1
                    ai_used = True

                    # L4: Verification & Evidence Grounding
                    verified_ai = verify_and_ground_findings(
                        ai_findings=ai_raw,
                        full_content=text,
                        retrieved_sources=top_sources,
                        approved_facts=facts,
                    )

                    # Deduplicate with L1 findings
                    existing_keys = {(f["source_id"], f["quoted_text"]) for f in all_findings}
                    for v in verified_ai:
                        key = (v.source_id, v.quoted_text)
                        if key not in existing_keys:
                            all_findings.append(v.model_dump())
                            existing_keys.add(key)
        except Exception as e:
            print(f"[Pipeline] AI processing warning: {e}")
            # Resilient fallback: L1 findings are still returned safely!

    # Sort all findings by character span
    all_findings.sort(key=lambda x: (x.get("span_start", 0), x.get("span_end", 0)))

    open_count = sum(1 for f in all_findings if f.get("state") == "open")
    high_count = sum(1 for f in all_findings if f.get("severity") == "high" and f.get("state") == "open")

    summary_text = (
        f"Automated review: {len(all_findings)} findings raised. "
        + ("Rule-based checks only." if not ai_used else f"{ai_calls_count} external AI evaluations grounded in approved guidelines.")
    )

    return PipelineResult(
        findings=all_findings,
        ai_used=ai_used,
        ai_calls_count=ai_calls_count,
        rule_checks_count=len(l1_findings),
        open_count=open_count,
        high_count=high_count,
        summary=summary_text,
    )
