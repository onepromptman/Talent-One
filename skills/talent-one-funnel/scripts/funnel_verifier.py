"""Verify one cumulative recruiting cohort. Standard library only; no ATS writes."""

import argparse
import csv
import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path


def analyze(rows):
    if len(rows) < 2:
        raise ValueError("At least two ordered stages are required")
    cohort = {(r.get("role", "").strip(), r.get("quarter", "").strip()) for r in rows}
    if len(cohort) != 1 or any(not x for x in next(iter(cohort))):
        raise ValueError("Provide one explicit role and quarter per report")
    seen, result, findings = set(), [], []
    previous = None
    for i, row in enumerate(rows):
        stage = row.get("stage", "").strip()
        if not stage or stage.casefold() in seen:
            raise ValueError("Stage names must be nonempty and unique")
        seen.add(stage.casefold())
        raw = row.get("count", "").strip()
        if not raw.isascii() or not raw.isdigit():
            raise ValueError(f"{stage}: count must be a nonnegative integer")
        count = int(raw)
        if previous is not None and count > previous:
            raise ValueError(
                f"{stage}: counts increase; this is not a cumulative cohort"
            )
        rate = (
            None if previous in (None, 0) else Decimal(count) * 100 / Decimal(previous)
        )
        supplied = row.get("pass_pct_of_prior", "").strip()
        if supplied:
            try:
                reported = Decimal(supplied.removesuffix("%").strip())
            except InvalidOperation as exc:
                raise ValueError(f"{stage}: invalid reported percentage") from exc
            if not reported.is_finite() or not 0 <= reported <= 100:
                raise ValueError(
                    f"{stage}: percentage must be finite and between 0 and 100"
                )
            if rate is None:
                findings.append(
                    f"{stage}: supplied percentage has no defined denominator"
                )
            elif abs(reported - rate) > Decimal("0.5"):
                findings.append(f"{stage}: reported {reported}%; computed {rate:.1f}%")
        result.append(
            {
                "stage": stage,
                "count": count,
                "prior_count": previous,
                "pass_pct": None if rate is None else float(rate),
            }
        )
        previous = count
    role, quarter = next(iter(cohort))
    return {
        "role": role,
        "quarter": quarter,
        "stages": result,
        "findings": findings,
        "scope": "Ordered cumulative cohort; counts are supplied, not independently verified.",
        "interpretation": "Stage conversion is descriptive. No causal diagnosis, candidate ranking, or inferred acceptances.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("Output must differ from input")
    try:
        with args.input.open(encoding="utf-8-sig", newline="") as stream:
            report = analyze(list(csv.DictReader(stream)))
        report["source_sha256"] = hashlib.sha256(args.input.read_bytes()).hexdigest()
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Validation failed: {exc}\n")
    print(
        f"Verified {len(report['stages'])} stages; {len(report['findings'])} discrepancy(s)."
    )
    return 1 if report["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
