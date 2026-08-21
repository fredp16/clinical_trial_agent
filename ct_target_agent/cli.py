from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

from .agent import assess


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Assess a therapeutic target from ClinicalTrials.gov records.")
    parser.add_argument("question", help='e.g. "Assess B7-H3 potential as a therapeutic target in lung cancer"')
    parser.add_argument("--out", default="output/assessment", help="output directory")
    parser.add_argument("--max-studies", type=int, default=250)
    parser.add_argument("--no-llm", action="store_true", help="skip DeepSeek and emit the deterministic report")
    parser.add_argument("--model", default=None, help="DeepSeek model; defaults to DEEPSEEK_MODEL or deepseek-v4-pro")
    args = parser.parse_args()
    try:
        report = assess(args.question, args.out, args.max_studies, not args.no_llm, args.model)
    except (ValueError, RuntimeError) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(report)


if __name__ == "__main__":
    main()
