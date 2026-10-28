"""Tests for ats_fetch.py and the runner kb_root wiring.

Stdlib unittest only, so the runner keeps its zero-dependency posture; pytest collects
these too when the module's evals run. From the runner dir:
python3 -m unittest discover -s tests -p "test_*.py"

The load-bearing test is test_pii_never_written: the committed fixtures under
fixtures/greenhouse/ deliberately carry candidate names/emails, and the tool must
never let any of them reach a KB file.
"""
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER_DIR = HERE.parent
FIX = HERE / "fixtures" / "greenhouse"
CROSSWALK = FIX / "crosswalk.csv"

sys.path.insert(0, str(RUNNER_DIR))
import ats_fetch          # noqa: E402
import talent_kit         # noqa: E402

# Candidate PII strings that appear in the fixtures and must never reach output.
PII_SENTINELS = [
    "Jane Q. Applicant", "jane.applicant@example.com",
    "Carol Screening", "carol.screening@example.com",
    "Bob Offeree", "bob.offeree@example.com",
]


def _run(out_dir, extra=None):
    argv = ["--provider", "greenhouse", "--crosswalk", str(CROSSWALK),
            "--out", str(out_dir), "--fixture", str(FIX)]
    if extra:
        argv += extra
    ats_fetch.main(argv)


def _all_md(out_dir):
    return {p: p.read_text(encoding="utf-8") for p in Path(out_dir).rglob("*.md")}


class PiiExclusion(unittest.TestCase):
    def test_pii_never_written(self):
        """No candidate name/email from the fixtures may appear in any KB file."""
        with tempfile.TemporaryDirectory() as d:
            _run(d)
            files = _all_md(d)
            self.assertTrue(files, "expected the fetch to write at least one KB file")
            blob = "\n".join(files.values())
            for s in PII_SENTINELS:
                self.assertNotIn(s, blob, f"PII sentinel leaked into output: {s!r}")

    def test_no_candidate_object_keys_in_output(self):
        """Belt-and-suspenders: raw candidate-object key names should not appear."""
        with tempfile.TemporaryDirectory() as d:
            _run(d)
            blob = "\n".join(_all_md(d).values())
            for key in ("email_addresses", "candidate_id"):
                self.assertNotIn(key, blob)


class Provenance(unittest.TestCase):
    def test_every_file_has_source_pill(self):
        with tempfile.TemporaryDirectory() as d:
            _run(d)
            for path, text in _all_md(d).items():
                self.assertIn("Sourced · Greenhouse ", text,
                              f"missing provenance pill in {path.name}")


class Funnel(unittest.TestCase):
    def test_funnel_reports_n_and_stages(self):
        with tempfile.TemporaryDirectory() as d:
            _run(d)
            f = Path(d) / "internal" / "funnel" / "controls.md"
            self.assertTrue(f.exists(), "controls funnel file should exist")
            text = f.read_text(encoding="utf-8")
            # per-stage n table present, canonical buckets, and a total n line
            self.assertIn("| Application | 3 |", text)
            self.assertIn("| Screen | 2 |", text)
            self.assertIn("| Onsite | 1 |", text)
            self.assertIn("| Hire | 1 |", text)
            self.assertIn("total applications n=", text)
            self.assertIn("Pass-through", text)


class OffersAggregation(unittest.TestCase):
    def test_comp_stats_by_level(self):
        with tempfile.TemporaryDirectory() as d:
            _run(d)
            o = Path(d) / "internal" / "comp" / "offers-controls.md"
            self.assertTrue(o.exists(), "controls offers file should exist")
            text = o.read_text(encoding="utf-8")
            # L3 has 3 offers -> min 180000 / median 190000 / max 200000
            self.assertIn("| L3 | 3 | 180000 | 190000 | 200000 |", text)

    def test_level_below_floor_omitted(self):
        """L4 has a single offer (< MIN_COMP_N) and must be suppressed (re-id guard)."""
        with tempfile.TemporaryDirectory() as d:
            _run(d)
            o = Path(d) / "internal" / "comp" / "offers-controls.md"
            self.assertNotIn("L4", o.read_text(encoding="utf-8"))

    def test_offers_precedence_note_not_bands_csv(self):
        """Accepted-offer actuals must never be written to bands.csv (CSR-reserved)."""
        with tempfile.TemporaryDirectory() as d:
            _run(d)
            self.assertFalse((Path(d) / "internal" / "comp" / "bands.csv").exists())


class Silence(unittest.TestCase):
    def test_unmatched_department_writes_nothing(self):
        """Office Manager (301) matches no crosswalk family -> no file mentions it."""
        with tempfile.TemporaryDirectory() as d:
            _run(d)
            blob = "\n".join(_all_md(d).values())
            self.assertNotIn("Office Manager", blob)
            # and no office/g&a family directory was created
            self.assertFalse((Path(d) / "internal" / "funnel" / "office_manager.md").exists())

    def test_no_offers_means_no_offers_file(self):
        """embedded_sw has applications but no offers -> a funnel file, no offers file."""
        with tempfile.TemporaryDirectory() as d:
            _run(d)
            self.assertTrue((Path(d) / "internal" / "funnel" / "embedded_sw.md").exists())
            self.assertFalse((Path(d) / "internal" / "comp" / "offers-embedded_sw.md").exists())


class DryRun(unittest.TestCase):
    def test_dry_run_writes_nothing_and_no_network(self):
        # Make any accidental network call explode, then confirm dry-run never calls it.
        orig = ats_fetch.urllib.request.urlopen

        def boom(*a, **k):
            raise AssertionError("dry-run must not open a network connection")

        ats_fetch.urllib.request.urlopen = boom
        try:
            with tempfile.TemporaryDirectory() as d:
                _run(d, extra=["--dry-run"])
                self.assertEqual(list(Path(d).rglob("*.md")), [])
        finally:
            ats_fetch.urllib.request.urlopen = orig


class RunnerKbRootScan(unittest.TestCase):
    def test_resolves_kb_root(self):
        cfg = "resources:\n  kb_root: ./kb\n  web:\n    enabled: true\n"
        got = talent_kit.resolve_kb_root(cfg, Path("/tmp/cfgdir"))
        self.assertEqual(got, (Path("/tmp/cfgdir") / "kb").resolve())

    def test_null_kb_root_is_none(self):
        self.assertIsNone(talent_kit.resolve_kb_root("resources:\n  kb_root: null\n",
                                                     Path("/tmp/cfgdir")))

    def test_no_resources_block_is_none(self):
        self.assertIsNone(talent_kit.resolve_kb_root("organization:\n  name: X\n",
                                                     Path("/tmp/cfgdir")))

    def test_kb_root_outside_resources_ignored(self):
        # a kb_root: key at the top level (not under resources:) must be ignored
        cfg = "kb_root: ./nope\nresources:\n  web:\n    enabled: true\n"
        self.assertIsNone(talent_kit.resolve_kb_root(cfg, Path("/tmp/cfgdir")))


if __name__ == "__main__":
    unittest.main()
