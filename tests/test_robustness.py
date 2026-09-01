from dataclasses import FrozenInstanceError
import unittest

from declared_coherence import AdapterOutcome, InputUnit, InvalidInputUnitKey, InvalidInvocation, validate


class PublicRobustnessTest(unittest.TestCase):
    def test_deep_successor_chain_uses_public_api_without_recursion_failure(self):
        count = 2000
        artifacts = [
            {"artifact_id": f"a{i:04d}", "repository_locator": None, "lifecycle_state": "current", "revision_token": None, "successor_artifact": f"a{i + 1:04d}" if i + 1 < count else None}
            for i in range(count)
        ]
        outcome = validate((InputUnit("deep", AdapterOutcome("DECODED_SOURCE", {"artifacts": artifacts, "relations": []})),))
        self.assertEqual("ADMITTED", outcome.intake_disposition)
        self.assertEqual((), outcome.result_records)

    def test_repeated_validation_is_equal_and_outcome_is_immutable(self):
        value = {"artifacts": [], "relations": []}
        units = (InputUnit("same", AdapterOutcome("DECODED_SOURCE", value)),)
        first = validate(units)
        self.assertEqual(first, validate(units))
        with self.assertRaises(FrozenInstanceError):
            first.intake_disposition = "changed"

    def test_interface_misuse_uses_bounded_exceptions(self):
        with self.assertRaises(InvalidInvocation):
            validate(None)
        with self.assertRaises(InvalidInputUnitKey):
            validate((InputUnit("", AdapterOutcome("DECODED_SOURCE", {"artifacts": [], "relations": []})),))


if __name__ == "__main__":
    unittest.main()

