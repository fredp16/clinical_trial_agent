# Clinical Trial Target Assessment Agent

A small, auditable agent that answers questions such as:

```text
Assess B7-H3 potential as a therapeutic target in lung cancer
```

It uses **DeepSeek V4** to plan target/disease synonyms, queries the ClinicalTrials.gov API v2, removes records in which the target is
only a biomarker or background mention, summarizes the clinical development
landscape, and produces an evidence-calibrated assessment. The registry data and
the generated report are saved together so every conclusion can be traced back
to an NCT record.

## Quick start

Requires Python 3.11+ and a DeepSeek API key.

```bash
pip install -e .
export DEEPSEEK_API_KEY=...
python -m ct_target_agent "Assess B7-H3 potential as a therapeutic target in lung cancer" \
  --out output/b7h3_lung
```

Keep the key in an environment variable or a local `.env` file that is not
committed. The program never writes the key into its output artifacts.

The default model is `deepseek-v4-pro`. Use the faster model when latency matters:

```bash
python -m ct_target_agent "Assess B7-H3 potential as a therapeutic target in lung cancer" \
  --model deepseek-v4-flash --out output/b7h3_lung
```

Outputs:

- `report.md`: final assessment with NCT links and limitations
- `trials.json`: normalized trial-level evidence
- `retrieval.json`: exact query, retrieval date, aliases, and counts

Useful options:

```bash
python -m ct_target_agent --help
python -m ct_target_agent "Assess CD276 potential as a therapeutic target in NSCLC" --max-studies 300
python -m ct_target_agent "Assess PCSK9 potential as a therapeutic target in atherosclerosis" --no-llm
```

## Assessment logic

The agent deliberately separates four questions:

1. **Does the query cover the target?** DeepSeek V4 returns a small set of gene/target aliases and a registry-friendly disease term. It never supplies trial records.
2. **Is the target actually being perturbed?** Intervention names, descriptions,
   arm labels, and study titles must contain a target alias. Biomarker-only
   records are excluded from the core evidence set.
3. **How mature is the program?** Phase, status, enrollment, sponsor diversity,
   modality, monotherapy arms, posted results, and discontinuation are counted.
4. **Is there clinical efficacy evidence?** A registered trial is treated as
   development activity, not efficacy validation. Results-posted studies are
   called out separately; response claims are not inferred from endpoints.
5. **What can the registry not answer?** Target biology, normal-tissue safety,
   expression prevalence, exposure, competitor publications, and regulatory
   status require external evidence modules.

This makes the tool suitable as the ClinicalTrials.gov module inside a larger
AIBERT target-assessment workflow, but not as a stand-alone target-validation
oracle.

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests use a local fixture and never call external services.

## Colab troubleshooting

Always install or upgrade the SDK before importing the package:

```python
!pip install -U "openai>=1.0"
```

If DeepSeek's Responses endpoint returns reasoning tokens but no final text, the
agent automatically retries through Chat Completions with thinking disabled.
If both calls fail or remain empty, it keeps the deterministic report instead
of overwriting `report.md`. Inspect `llm_refinement_status` and `llm_warning` in
`retrieval.json` for the exact fallback status.
