from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Iterable

API_URL = "https://clinicaltrials.gov/api/v2/studies"


@dataclass
class Trial:
    nct_id: str
    title: str
    status: str
    phases: list[str]
    study_type: str
    enrollment: int | None
    sponsor: str
    interventions: list[str]
    intervention_types: list[str]
    conditions: list[str]
    has_results: bool
    start_date: str | None
    completion_date: str | None
    last_update: str | None
    target_role: str
    matched_aliases: list[str]
    monotherapy_signal: bool
    summary: str
    why_stopped: str | None
    url: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _get(obj: dict[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = obj
    for key in path.split("."):
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def fetch_studies(condition: str, aliases: Iterable[str], max_studies: int = 250) -> list[dict[str, Any]]:
    """Retrieve union of intervention-specific searches with cursor pagination."""
    seen: dict[str, dict[str, Any]] = {}
    for alias in aliases:
        page_token: str | None = None
        while len(seen) < max_studies:
            params = {
                "query.cond": condition,
                "query.intr": alias,
                "pageSize": str(min(100, max_studies - len(seen))),
                "format": "json",
                "countTotal": "true",
            }
            if page_token:
                params["pageToken"] = page_token
            url = API_URL + "?" + urllib.parse.urlencode(params)
            payload = _request_json(url)
            for study in payload.get("studies", []):
                nct = _get(study, "protocolSection.identificationModule.nctId")
                if nct:
                    seen[nct] = study
            page_token = payload.get("nextPageToken")
            if not page_token:
                break
        if len(seen) >= max_studies:
            break
    return list(seen.values())


def _request_json(url: str, retries: int = 3) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "ct-target-agent/0.1"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == retries - 1:
                raise RuntimeError(f"ClinicalTrials.gov returned HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == retries - 1:
                raise RuntimeError(f"ClinicalTrials.gov request failed: {exc}") from exc
        time.sleep(2**attempt)
    raise AssertionError("unreachable")


def normalize(study: dict[str, Any], aliases: Iterable[str]) -> Trial:
    protocol = study.get("protocolSection", {})
    ident = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    design = protocol.get("designModule", {})
    sponsor = protocol.get("sponsorCollaboratorsModule", {})
    arms = protocol.get("armsInterventionsModule", {})
    desc = protocol.get("descriptionModule", {})
    conditions = protocol.get("conditionsModule", {}).get("conditions", [])

    interventions = arms.get("interventions", [])
    intervention_names = [x.get("name", "") for x in interventions if x.get("name")]
    intervention_types = sorted({x.get("type", "UNKNOWN") for x in interventions})
    arm_labels = [x.get("label", "") for x in arms.get("armGroups", [])]
    target_text = " ".join(
        intervention_names
        + [x.get("description", "") for x in interventions]
        + arm_labels
        + [ident.get("briefTitle", ""), ident.get("officialTitle", "")]
    ).lower()
    background_text = " ".join(
        [desc.get("briefSummary", ""), desc.get("detailedDescription", "")]
    ).lower()
    matched = sorted({a for a in aliases if a.lower() in target_text})
    background_matches = sorted({a for a in aliases if a.lower() in background_text})
    role = "direct_intervention" if matched else ("background_or_biomarker" if background_matches else "unconfirmed")

    target_arm_count = sum(any(a.lower() in label.lower() for a in aliases) for label in arm_labels)
    all_names = " ".join(intervention_names).lower()
    combo_markers = ("pembrolizumab", "nivolumab", "chemotherapy", "radiotherapy", "carboplatin", "etoposide")
    monotherapy = bool(matched) and target_arm_count > 0 and not any(x in all_names for x in combo_markers)

    enrollment = design.get("enrollmentInfo", {}).get("count")
    return Trial(
        nct_id=ident.get("nctId", "UNKNOWN"),
        title=ident.get("briefTitle", "Untitled study"),
        status=status.get("overallStatus", "UNKNOWN"),
        phases=design.get("phases", []),
        study_type=design.get("studyType", "UNKNOWN"),
        enrollment=enrollment if isinstance(enrollment, int) else None,
        sponsor=_get(sponsor, "leadSponsor.name", "Unknown"),
        interventions=intervention_names,
        intervention_types=intervention_types,
        conditions=conditions,
        has_results=bool(study.get("hasResults")),
        start_date=_get(status, "startDateStruct.date"),
        completion_date=_get(status, "completionDateStruct.date"),
        last_update=_get(status, "lastUpdatePostDateStruct.date"),
        target_role=role,
        matched_aliases=matched or background_matches,
        monotherapy_signal=monotherapy,
        summary=desc.get("briefSummary", ""),
        why_stopped=status.get("whyStopped"),
        url=f"https://clinicaltrials.gov/study/{ident.get('nctId', '')}",
    )
