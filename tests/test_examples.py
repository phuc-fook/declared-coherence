import importlib.util
from pathlib import Path
import unittest


EXAMPLE_PATH = Path(__file__).resolve().parents[1] / "examples" / "declared_relationships.py"
SPEC = importlib.util.spec_from_file_location("declared_relationship_examples", EXAMPLE_PATH)
EXAMPLES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXAMPLES)


class WorkedExamplesTest(unittest.TestCase):
    def test_all_examples_call_real_api(self):
        self.assertEqual("FRESH", EXAMPLES.valid_derivation().result_records[0].freshness_state)
        self.assertEqual("STALE", EXAMPLES.stale_derivation().result_records[0].freshness_state)
        self.assertTrue(any(record.code == "DERIVED_FROM_CYCLE" for record in EXAMPLES.derivation_cycle().result_records))
        self.assertEqual((), EXAMPLES.successor_lineage().result_records)
        self.assertEqual((), EXAMPLES.reciprocal_constraints().result_records)


if __name__ == "__main__":
    unittest.main()

