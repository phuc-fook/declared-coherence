import unittest

import declared_coherence


class PublicApiTest(unittest.TestCase):
    def test_exact_top_level_exports(self):
        self.assertEqual(
            {
                "validate", "AdapterOutcome", "AdmissionDefect", "AdmissionLocus",
                "ArtifactRecord", "InputUnit", "InvalidInputUnitKey", "InvalidInvocation",
                "Lifecycle", "NormalizedModel", "RelationAssertion", "ResultRecord",
                "RevisionToken", "StructuralPathSegment", "ValidationOutcome",
            },
            set(declared_coherence.__all__),
        )

    def test_architecture_classes_are_not_top_level(self):
        for name in ("IntakeNormalizer", "CoreEvaluator", "DeterministicResultProjector"):
            self.assertFalse(hasattr(declared_coherence, name))


if __name__ == "__main__":
    unittest.main()

