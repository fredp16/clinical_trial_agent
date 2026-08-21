from __future__ import annotations

import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .clinicaltrials import Trial, fetch_studies, normalize

TARGET_ALIASES = {
    "b7-h3": ["B7-H3", "CD276"],
    "cd276": ["B7-H3", "CD276"],
}
CONDITION_ALIASES = {
    "lung cancer": "lung cancer",
    "nsclc": "non-small cell lung cancer",
    "sclc": "small cell lung cancer",
}


def parse_question(question: str) -> tuple[str, str]:
    match = re.search(r"assess\s+(.+?)\s+potential\s+as\s+a\s+therapeutic\s+target\s+in\s+(.+?)\s*[?.]*$", question, re.I)
    if not match:
        raise ValueError("Use: Assess <target> potential as a therapeutic target in <indication>")
    return match.group(1).strip(), match.group(2).strip()


def aliases_for(target: str) -> list[str]:
    return TARGET_ALIASES.get(target.lower(), [target])


def deepseek_plan(question: str, target: str, condition: str, model: str) -> tuple[list[str], str]:
    """Use DeepSeek V4 only to expand query vocabulary, never to invent trials."""
    client = _deepseek_client()
    instructions = (
        "Return JSON only. You plan a ClinicalTrials.gov search. Provide canonical human gene/target aliases "
        "and one registry-friendly disease term. Do not provide drug names, trial IDs, or commentary."
    )
    prompt = (
            f'Question: {question}\nTarget: {target}\nDisease: {condition}\n'
            'JSON schema: {"target_aliases":["string"],"condition_query":"string"}. '
            "Include the user's target verbatim; at most 6 aliases."
    )
    try:
        text = _deepseek_text(client, model, instructions, prompt, max_output_tokens=400, reasoning_effort="low")
    except Exception:
        return aliases_for(target), condition
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    try:
        data = json.loads(text)
        proposed = [str(x).strip() for x in data.get("target_aliases", []) if str(x).strip()]
        aliases = list(dict.fromkeys([target, *proposed]))[:6]
        condition_query = str(data.get("condition_query") or condition).strip()
        return aliases, condition_query
    except (json.JSONDecodeError, AttributeError, TypeError):
        return aliases_for(target), condition


def summarize(trials: list[Trial]) -> dict[str, Any]:
    direct = [t for t in trials if t.target_role == "direct_intervention"]
    active_statuses = {"RECRUITING", "NOT_YET_RECRUITING", "ACTIVE_NOT_RECRUITING", "ENROLLING_BY_INVITATION"}
    terminated = {"TERMINATED", "WITHDRAWN", "SUSPENDED"}
    return {
        "retrieved": len(trials),
        "direct_intervention": len(direct),
        "excluded_or_uncertain": len(trials) - len(direct),
        "active": sum(t.status in active_statuses for t in direct),
        "discontinued": sum(t.status in terminated for t in direct),
        "results_posted": sum(t.has_results for t in direct),
        "monotherapy_signal": sum(t.monotherapy_signal for t in direct),
        "phases": dict(Counter(p for t in direct for p in (t.phases or ["NA"]))),
        "statuses": dict(Counter(t.status for t in direct)),
        "sponsors": dict(Counter(t.sponsor for t in direct).most_common(10)),
        "intervention_types": dict(Counter(x for t in direct for x in t.intervention_types)),
    }


def evidence_grade(stats: dict[str, Any], trials: list[Trial] | None = None) -> tuple[str, str]:
    if stats["direct_intervention"] == 0:
        return "Insufficient", "No direct target-intervention trial was identified."
    direct = [t for t in (trials or []) if t.target_role == "direct_intervention"]
    late_with_results = any(t.has_results and ({"PHASE3", "PHASE4"} & set(t.phases)) for t in direct)
    if late_with_results:
        return "Late-stage clinical evidence available", "At least one late-stage record has posted results; effect sizes, controls, and safety still require direct review."
    if stats["phases"].get("PHASE3", 0) or stats["phases"].get("PHASE4", 0):
        return "Clinically advanced hypothesis", "Late-stage testing is present, but trial phase or existence is not evidence of efficacy."
    if stats["results_posted"]:
        return "Early clinical signal", "Human interventional evidence exists, but maturity and efficacy interpretation remain limited."
    return "Clinical hypothesis under active test", "The registry shows development activity, not demonstrated efficacy."


def render_report(question: str, target: str, condition: str, aliases: list[str], trials: list[Trial], stats: dict[str, Any]) -> str:
    grade, interpretation = evidence_grade(stats, trials)
    direct = [t for t in trials if t.target_role == "direct_intervention"]
    rows = []
    for t in sorted(direct, key=lambda x: (not x.has_results, x.status, x.nct_id)):
        rows.append(
            f"| [{t.nct_id}]({t.url}) | {', '.join(t.phases) or 'NA'} | {t.status} | "
            f"{'; '.join(t.interventions) or 'Not stated'} | {t.enrollment or 'NA'} | {'Yes' if t.has_results else 'No'} |"
        )
    table = "\n".join(rows) if rows else "| — | — | — | No direct intervention trials identified | — | — |"
    return f"""# Clinical-trial assessment: {target} in {condition}

**Question:** {question}  
**Assessment:** **{grade}**  
**Interpretation:** {interpretation}

## Executive answer

ClinicalTrials.gov contains **{stats['direct_intervention']} direct-intervention record(s)** matching {', '.join(aliases)} in {condition}; **{stats['active']}** are active and **{stats['results_posted']}** have registry-posted results. This supports the conclusion that the target is clinically actionable enough to test in humans, but trial registration alone does **not** establish target validation, efficacy, or a favorable therapeutic index.

The most decision-relevant next step is to inspect arm-level efficacy, safety, dose/exposure, target-expression enrichment, and monotherapy versus combination results in the results-bearing studies and linked publications. A target should not receive a positive efficacy verdict merely because several early-phase trials exist.

## Landscape

- Phase distribution: `{json.dumps(stats['phases'], sort_keys=True)}`
- Status distribution: `{json.dumps(stats['statuses'], sort_keys=True)}`
- Results posted: **{stats['results_posted']}**
- Discontinued/withdrawn/suspended: **{stats['discontinued']}**
- Apparent monotherapy records: **{stats['monotherapy_signal']}** (heuristic; arm-level review required)
- Leading sponsors: `{json.dumps(stats['sponsors'], sort_keys=True)}`

| NCT | Phase | Status | Targeted intervention(s) | Enrollment | Results posted |
|---|---|---|---|---:|---|
{table}

## What the evidence does—and does not—show

**Supported:** direct human perturbation, modality/sponsor activity, development maturity, current status, and whether structured registry results exist.

**Not established by registry records alone:** biological causality, response magnitude, durability, target dependence, superiority to standard of care, normal-tissue toxicity, or commercial differentiation. Combination studies are especially weak evidence for target-specific efficacy unless the design contains an informative control or monotherapy arm.

## Method and limitations

The agent searched ClinicalTrials.gov API v2 by condition plus each target alias, deduplicated by NCT ID, and required a target alias in intervention/arm/title fields for the core evidence set. Free-text registration is heterogeneous, aliases can be missing, `hasResults` does not guarantee clinically meaningful benefit, and publication/regulatory data outside ClinicalTrials.gov are not reviewed here.
"""


def _deepseek_client():
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install dependencies with: pip install -e .") from exc
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is required (or run the CLI with --no-llm for deterministic mode)")
    return OpenAI(api_key=api_key, base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))


def _extract_response_text(response: Any) -> str:
    """Extract final text across OpenAI-SDK and DeepSeek Responses variants."""
    direct = getattr(response, "output_text", None)
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    output = getattr(response, "output", None)
    if output is None and hasattr(response, "model_dump"):
        output = response.model_dump().get("output", [])
    chunks: list[str] = []
    for item in output or []:
        item_type = item.get("type") if isinstance(item, dict) else getattr(item, "type", None)
        if item_type != "message":
            continue
        content = item.get("content", []) if isinstance(item, dict) else getattr(item, "content", [])
        for part in content or []:
            part_type = part.get("type") if isinstance(part, dict) else getattr(part, "type", None)
            if part_type not in {"output_text", "text"}:
                continue
            value = part.get("text", "") if isinstance(part, dict) else getattr(part, "text", "")
            if isinstance(value, str) and value.strip():
                chunks.append(value.strip())
    return "\n".join(chunks).strip()


def _deepseek_text(client: Any, model: str, instructions: str, prompt: str, max_output_tokens: int, reasoning_effort: str) -> str:
    """Call Responses first; retry without thinking through Chat Completions if final text is empty."""
    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=prompt,
        max_output_tokens=max_output_tokens,
        reasoning={"effort": reasoning_effort},
    )
    text = _extract_response_text(response)
    if text:
        return text

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_output_tokens,
        stream=False,
        extra_body={"thinking": {"type": "disabled"}},
    )
    content = completion.choices[0].message.content
    return content.strip() if isinstance(content, str) else ""


def llm_refine(report: str, trials: list[Trial], model: str) -> str:
    client = _deepseek_client()
    evidence = json.dumps([t.to_dict() for t in trials if t.target_role == "direct_intervention"], ensure_ascii=False)
    prompt = f"""Rewrite the draft as a concise decision memo. Use only the supplied registry evidence.
Never infer efficacy from trial existence, phase, enrollment, planned endpoints, or results-posted status.
Preserve every NCT citation and explicitly separate facts, inferences, and unknowns.

DRAFT:\n{report}\n\nTRIAL EVIDENCE:\n{evidence}"""
    text = _deepseek_text(
        client,
        model,
        (
            "You are a skeptical clinical-development analyst. Do not add facts not present in the evidence. "
            "Answer in the language used by the user's question."
        ),
        prompt,
        max_output_tokens=5000,
        reasoning_effort="high",
    )
    if not text:
        raise RuntimeError("DeepSeek returned no final answer text")
    return text


def assess(question: str, out_dir: str | Path, max_studies: int = 250, use_llm: bool = True, model: str | None = None, raw_studies: list[dict[str, Any]] | None = None) -> Path:
    target, condition_input = parse_question(question)
    condition = CONDITION_ALIASES.get(condition_input.lower(), condition_input)
    selected_model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")
    aliases, condition = deepseek_plan(question, target, condition, selected_model) if use_llm else (aliases_for(target), condition)
    raw = raw_studies if raw_studies is not None else fetch_studies(condition, aliases, max_studies)
    trials = [normalize(x, aliases) for x in raw]
    stats = summarize(trials)
    report = render_report(question, target, condition, aliases, trials, stats)
    llm_status = "not_requested"
    llm_warning = None
    if use_llm:
        deterministic_report = report
        try:
            refined = llm_refine(deterministic_report, trials, selected_model).strip()
            if not refined:
                raise RuntimeError("DeepSeek returned an empty report")
            report = refined
            llm_status = "succeeded"
        except Exception as exc:
            llm_status = "fallback_to_deterministic"
            llm_warning = f"{type(exc).__name__}: {exc}"
            report = (
                "> **Generation note:** DeepSeek refinement did not return usable final text; "
                "the deterministic evidence report is retained. See `retrieval.json` for diagnostics.\n\n"
                + deterministic_report
            )

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text(report, encoding="utf-8")
    (out / "trials.json").write_text(json.dumps([t.to_dict() for t in trials], indent=2, ensure_ascii=False), encoding="utf-8")
    metadata = {
        "question": question,
        "target": target,
        "target_aliases": aliases,
        "condition": condition,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source": "ClinicalTrials.gov API v2",
        "llm_provider": "DeepSeek" if use_llm else None,
        "llm_model": selected_model if use_llm else None,
        "llm_refinement_status": llm_status,
        "llm_warning": llm_warning,
        "max_studies": max_studies,
        "summary": stats,
    }
    (out / "retrieval.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return out / "report.md"
