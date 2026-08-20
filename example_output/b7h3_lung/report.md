# Clinical-trial assessment: B7-H3 in lung cancer

**Question:** Assess B7-H3 potential as a therapeutic target in lung cancer  
**Assessment:** **Clinically advanced hypothesis**  
**Interpretation:** Late-stage testing is present, but trial phase or existence is not evidence of efficacy.

## Executive answer

ClinicalTrials.gov contains **13 direct-intervention record(s)** matching B7-H3, CD276 in lung cancer; **10** are active and **1** have registry-posted results. This supports the conclusion that the target is clinically actionable enough to test in humans, but trial registration alone does **not** establish target validation, efficacy, or a favorable therapeutic index.

The most decision-relevant next step is to inspect arm-level efficacy, safety, dose/exposure, target-expression enrichment, and monotherapy versus combination results in the results-bearing studies and linked publications. A target should not receive a positive efficacy verdict merely because several early-phase trials exist.

## Landscape

- Phase distribution: `{"PHASE1": 8, "PHASE2": 6, "PHASE3": 2}`
- Status distribution: `{"ACTIVE_NOT_RECRUITING": 1, "NOT_YET_RECRUITING": 2, "RECRUITING": 7, "TERMINATED": 2, "WITHDRAWN": 1}`
- Results posted: **1**
- Discontinued/withdrawn/suspended: **3**
- Apparent monotherapy records: **0** (heuristic; arm-level review required)
- Leading sponsors: `{"BioNTech SE": 1, "Daiichi Sankyo": 3, "GlaxoSmithKline": 1, "Hansoh BioMedical R&D Company": 1, "MacroGenics": 2, "National Cancer Institute (NCI)": 1, "Radiopharm Theranostics, Ltd": 1, "SUNHO\uff08China\uff09BioPharmaceutical CO., Ltd.": 1, "Second Affiliated Hospital of Guangzhou Medical University": 2}`

| NCT | Phase | Status | Targeted intervention(s) | Enrollment | Results posted |
|---|---|---|---|---:|---|
| [NCT03729596](https://clinicaltrials.gov/study/NCT03729596) | PHASE1, PHASE2 | TERMINATED | vobramitamab duocarmazine | 143 | Yes |
| [NCT05280470](https://clinicaltrials.gov/study/NCT05280470) | PHASE2 | ACTIVE_NOT_RECRUITING | Ifinatamab Deruxtecan (I-DXd) | 187 | No |
| [NCT07076095](https://clinicaltrials.gov/study/NCT07076095) | PHASE2 | NOT_YET_RECRUITING | IBB0979; topotecan hydrochloride for injection | 200 | No |
| [NCT07509034](https://clinicaltrials.gov/study/NCT07509034) | PHASE1 | NOT_YET_RECRUITING | Autologous B7-H3 CAR T; Cyclophosphamide; Fludarabine | 40 | No |
| [NCT03198052](https://clinicaltrials.gov/study/NCT03198052) | PHASE1 | RECRUITING | CAR-T cells targeting GPC3, Mesothelin, Claudin18.2, GUCY2C, B7-H3, PSCA, PSMA, MUC1, TGFβ, HER2, Lewis-Y, AXL, or EGFR | 30 | No |
| [NCT04842812](https://clinicaltrials.gov/study/NCT04842812) | PHASE1 | RECRUITING | TILs and CAR-TILs targeting HER2, Mesothelin, PSCA, MUC1, Lewis-Y, GPC3, AXL, EGFR, Claudin18.2/6, ROR1, GD1, or B7-H3 | 40 | No |
| [NCT05142189](https://clinicaltrials.gov/study/NCT05142189) | PHASE1 | RECRUITING | BNT116; Cemiplimab; Docetaxel; Carboplatin; Paclitaxel; BNT316; anti-B7-H3 antibody conjugated to topoisomerase I inhibitor; anti-HER3 antibody conjugated to topoisomerase I inhibitor; Bispecific antibody for PD-L1 and VEGF-A; Osimertinib; ALK-inhibitor or RET-inhibitor | 320 | No |
| [NCT06203210](https://clinicaltrials.gov/study/NCT06203210) | PHASE3 | RECRUITING | Ifinatamab deruxtecan; Topotecan; Amrubicin; Lurbinectedin | 540 | No |
| [NCT06362252](https://clinicaltrials.gov/study/NCT06362252) | PHASE1, PHASE2 | RECRUITING | Ifinatamab deruxtecan; Atezolizumab; Carboplatin | 123 | No |
| [NCT07099898](https://clinicaltrials.gov/study/NCT07099898) | PHASE3 | RECRUITING | Ris-Rez; Topotecan | 420 | No |
| [NCT07189871](https://clinicaltrials.gov/study/NCT07189871) | PHASE1, PHASE2 | RECRUITING | 177Lu-BetaBart | 61 | No |
| [NCT02628535](https://clinicaltrials.gov/study/NCT02628535) | PHASE1 | TERMINATED | MGD009 | 67 | No |
| [NCT06052423](https://clinicaltrials.gov/study/NCT06052423) | PHASE2 | WITHDRAWN | HS-20093 | NA | No |

## What the evidence does—and does not—show

**Supported:** direct human perturbation, modality/sponsor activity, development maturity, current status, and whether structured registry results exist.

**Not established by registry records alone:** biological causality, response magnitude, durability, target dependence, superiority to standard of care, normal-tissue toxicity, or commercial differentiation. Combination studies are especially weak evidence for target-specific efficacy unless the design contains an informative control or monotherapy arm.

## Method and limitations

The agent searched ClinicalTrials.gov API v2 by condition plus each target alias, deduplicated by NCT ID, and required a target alias in intervention/arm/title fields for the core evidence set. Free-text registration is heterogeneous, aliases can be missing, `hasResults` does not guarantee clinically meaningful benefit, and publication/regulatory data outside ClinicalTrials.gov are not reviewed here.
