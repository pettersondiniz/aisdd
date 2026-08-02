from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InterfaceValidationGuidanceTests(unittest.TestCase):
    # @spec:AC-001
    def test_declares_capability_preference_order(self) -> None:
        reference = (ROOT / "references" / "interface-validation.md").read_text(encoding="utf-8")
        self.assertIn("`playwright-cli`", reference)
        self.assertIn("Playwright MCP", reference)
        self.assertIn("another approved browser tool", reference)

    # @spec:AC-002
    def test_requires_honest_evidence_when_browser_validation_is_unavailable(self) -> None:
        reference = (ROOT / "references" / "interface-validation.md").read_text(encoding="utf-8")
        self.assertIn("`not-run`", reference)
        self.assertIn("Never claim `real-browser` without an actual execution.", reference)


if __name__ == "__main__":
    unittest.main()
