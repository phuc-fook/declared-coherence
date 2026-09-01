import unittest

from declared_coherence import AdapterOutcome, InputUnit, validate


def artifact(name, revision=None, successor=None):
    return {"artifact_id": name, "repository_locator": None, "lifecycle_state": "current", "revision_token": revision, "successor_artifact": successor}


def relation(kind, source, target, observed=None):
    return {"relation_kind": kind, "from_artifact": source, "to_artifact": target, "observed_source_revision": observed}


def evaluate(artifacts, relations):
    value = {"artifacts": artifacts, "relations": relations}
    return validate((InputUnit("test", AdapterOutcome("DECODED_SOURCE", value)),))


class RepresentativeBehaviorTest(unittest.TestCase):
    def test_fresh_and_stale_derivations(self):
        target = artifact("contract", {"kind": "v", "value": "2"})
        fresh = evaluate([target, artifact("fresh-client")], [relation("derived_from", "fresh-client", "contract", {"kind": "v", "value": "2"})])
        stale = evaluate([target, artifact("stale-client")], [relation("derived_from", "stale-client", "contract", {"kind": "v", "value": "1"})])
        self.assertEqual("FRESH", fresh.result_records[0].freshness_state)
        self.assertEqual("STALE", stale.result_records[0].freshness_state)

    def test_unknown_is_distinct_from_stale(self):
        outcome = evaluate([artifact("contract"), artifact("client")], [relation("derived_from", "client", "contract")])
        self.assertEqual("UNKNOWN", outcome.result_records[0].freshness_state)

    def test_derivation_cycle_has_deterministic_witness(self):
        outcome = evaluate(
            [artifact("a"), artifact("b"), artifact("c")],
            [relation("derived_from", "a", "b"), relation("derived_from", "b", "c"), relation("derived_from", "c", "a")],
        )
        cycle = next(record for record in outcome.result_records if record.code == "DERIVED_FROM_CYCLE")
        self.assertEqual(("a", "b", "c", "a"), cycle.witness_path)

    def test_successor_chain_and_reciprocal_constraints_are_accepted(self):
        lineage = evaluate([artifact("v1", successor="v2"), artifact("v2", successor="v3"), artifact("v3")], [])
        reciprocal = evaluate([artifact("a"), artifact("b")], [relation("constrained_by", "a", "b"), relation("constrained_by", "b", "a")])
        self.assertEqual((), lineage.result_records)
        self.assertEqual((), reciprocal.result_records)


if __name__ == "__main__":
    unittest.main()

