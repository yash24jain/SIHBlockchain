# VASP module tests (Member 6).
# Uses the real entity dataset (synthetic_demo=false). No network access.

import os
import sys
import unittest

_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import vasp
from vasp.attribution import (
    attribute_blockchain_data,
    attribute_entity,
    attribute_transactions,
    check_address_in_database,
    normalize_address,
)
from vasp.evidence import (
    EvidenceRecord,
    create_evidence_from_results,
    create_evidence_from_transaction,
)
from vasp.investigation import _build_investigation_result, run_investigation
from vasp.report_generator import ReportGenerator

# Real entity database addresses (from vasp/entity_database.json)
BINANCE_1 = "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be"  # Binance
BINANCE_2 = "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8"  # Binance
COINBASE = "0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43"  # Coinbase
GATE = "0xd793281182a0e3e023116004778f45c29fc14f19"  # Gate
KUKKOIN = "0xb8e6d31e7b212b2b7250ee9c26c56cebbfbe6b23"  # KuCoin
CRYPTO_COM = "0x7758e507850da48cd47df1fb5f875c23e3340c50"  # Crypto.com
UNKNOWN_A = "0x1111111111111111111111111111111111111111"
UNKNOWN_B = "0x2222222222222222222222222222222222222222"


def make_tx(tx_hash, frm, to, direction="IN", timestamp="2018-01-01T00:00:00+00:00", **overrides):
    tx = {
        "tx_hash": tx_hash,
        "from": frm,
        "to": to,
        "amount": 1.0,
        "amount_unit": "ETH",
        "direction": direction,
        "transaction_type": "NATIVE_TRANSFER",
        "chain": "ethereum",
        "timestamp": timestamp,
    }
    tx.update(overrides)
    return tx


def find_attribution(attributions, entity_name):
    for att in attributions:
        if att.get("entity_name") == entity_name:
            return att
    return None


class TestPackageImport(unittest.TestCase):
    def test_package_import(self):
        for name in vasp.__all__:
            self.assertTrue(hasattr(vasp, name), f"vasp is missing {name}")

    def test_entity_database_loaded(self):
        self.assertEqual(len(vasp.ENTITY_DATABASE.get("records", [])), 8)
        self.assertFalse(vasp.ENTITY_DATABASE.get("synthetic_demo"))
        entity_names = {
            r["entity_name"] for r in vasp.ENTITY_DATABASE.get("records", [])
        }
        self.assertIn("Binance", entity_names)
        self.assertIn("Coinbase", entity_names)


class TestAttribution(unittest.TestCase):
    EXPECTED_KEYS = {
        "address", "entity_name", "entity_type", "vasp_category", "chain",
        "jurisdiction", "match_status", "hop_distance", "confidence_score",
        "confidence_reasons", "interaction_count", "matched_transaction_hashes",
        "first_seen", "last_seen", "attribution_method", "source",
        "source_url", "evidence",
    }

    def test_exact_direct_match(self):
        tx = make_tx("0x1", UNKNOWN_A, BINANCE_1)
        attributions = attribute_transactions([tx])
        self.assertEqual(len(attributions), 1)
        att = attributions[0]
        self.assertEqual(att["entity_name"], "Binance")
        self.assertEqual(att["address"], BINANCE_1)
        self.assertEqual(att["match_status"], "confirmed")
        self.assertEqual(att["hop_distance"], 1)
        self.assertEqual(att["attribution_method"], "known_address_match")

    def test_no_match(self):
        tx = make_tx("0x1", UNKNOWN_A, UNKNOWN_B)
        attributions = attribute_transactions([tx])
        self.assertEqual(attributions, [])

    def test_from_address_match(self):
        tx = make_tx("0x1", GATE, UNKNOWN_A, direction="OUT")
        attributions = attribute_transactions([tx])
        self.assertEqual(len(attributions), 1)
        self.assertEqual(attributions[0]["entity_name"], "Gate")

    def test_to_address_match(self):
        tx = make_tx("0x1", UNKNOWN_A, COINBASE)
        attributions = attribute_transactions([tx])
        self.assertEqual(len(attributions), 1)
        self.assertEqual(attributions[0]["entity_name"], "Coinbase")

    def test_repeated_interactions(self):
        txs = [
            make_tx("0x1", UNKNOWN_A, BINANCE_1, timestamp="2018-01-01T00:00:00+00:00"),
            make_tx("0x2", UNKNOWN_A, BINANCE_1, timestamp="2018-01-02T00:00:00+00:00"),
            make_tx("0x3", UNKNOWN_A, BINANCE_1, timestamp="2018-01-03T00:00:00+00:00"),
        ]
        attributions = attribute_transactions(txs)
        self.assertEqual(len(attributions), 1)
        att = attributions[0]
        self.assertEqual(att["entity_name"], "Binance")
        self.assertEqual(att["interaction_count"], 3)
        self.assertEqual(
            set(att["matched_transaction_hashes"]), {"0x1", "0x2", "0x3"}
        )
        self.assertEqual(att["first_seen"], "2018-01-01T00:00:00+00:00")
        self.assertEqual(att["last_seen"], "2018-01-03T00:00:00+00:00")
        self.assertIn("3 interactions detected", att["confidence_reasons"])
        self.assertGreaterEqual(att["confidence_score"], 0.0)
        self.assertLessEqual(att["confidence_score"], 1.0)
        # More interactions raise (never lower) confidence.
        single = attribute_transactions([txs[0]])[0]["confidence_score"]
        self.assertGreater(att["confidence_score"], single)

    def test_multiple_vasps(self):
        txs = [
            make_tx("0x1", UNKNOWN_A, BINANCE_1),
            make_tx("0x2", UNKNOWN_A, GATE),
            make_tx("0x3", COINBASE, UNKNOWN_A, direction="OUT"),
        ]
        attributions = attribute_transactions(txs)
        names = {a["entity_name"] for a in attributions}
        self.assertEqual(names, {"Binance", "Gate", "Coinbase"})

    def test_duplicate_hashes(self):
        duplicate = make_tx("0xdup", UNKNOWN_A, BINANCE_1)
        txs = [duplicate, dict(duplicate)]
        attributions = attribute_transactions(txs)
        self.assertEqual(len(attributions), 1)
        att = attributions[0]
        self.assertEqual(att["entity_name"], "Binance")
        self.assertEqual(att["interaction_count"], 1)
        self.assertEqual(att["matched_transaction_hashes"], ["0xdup"])
        # A duplicated hash must not inflate confidence beyond a single match.
        single = attribute_transactions([duplicate])[0]["confidence_score"]
        self.assertEqual(att["confidence_score"], single)
        self.assertGreaterEqual(att["confidence_score"], 0.0)
        self.assertLessEqual(att["confidence_score"], 1.0)

    def test_same_entity_both_sides(self):
        tx = make_tx("0x1", COINBASE, COINBASE, direction="OUT")
        attributions = attribute_transactions([tx])
        self.assertEqual(len(attributions), 1)
        self.assertEqual(attributions[0]["entity_name"], "Coinbase")
        self.assertEqual(attributions[0]["interaction_count"], 1)

    def test_missing_timestamp(self):
        tx = make_tx("0x1", UNKNOWN_A, BINANCE_1, timestamp=None)
        attributions = attribute_transactions([tx])
        self.assertEqual(len(attributions), 1)
        self.assertIsNone(attributions[0]["first_seen"])
        self.assertIsNone(attributions[0]["last_seen"])
        self.assertEqual(attributions[0]["interaction_count"], 1)

    def test_missing_optional_fields(self):
        tx = {
            "tx_hash": "0x1",
            "from": UNKNOWN_A,
            "to": BINANCE_1,
            # amount, amount_unit, direction, transaction_type, chain,
            # timestamp all intentionally missing
        }
        attributions = attribute_transactions([tx])
        self.assertEqual(len(attributions), 1)
        att = attributions[0]
        self.assertEqual(att["entity_name"], "Binance")
        self.assertEqual(att["interaction_count"], 1)
        self.assertEqual(att["evidence"][0]["amount"], None)
        self.assertEqual(att["evidence"][0]["direction"], "UNKNOWN")
        self.assertEqual(att["evidence"][0]["transaction_type"], "TRANSFER")

    def test_empty_transactions(self):
        self.assertEqual(attribute_transactions([]), [])
        result = attribute_blockchain_data(
            {"wallet": UNKNOWN_A, "chain": "ethereum", "transactions": []}
        )
        self.assertEqual(result["total_transactions"], 0)
        self.assertEqual(result["attributions"], [])
        self.assertEqual(result["overall_confidence"], 0.0)

    def test_invalid_address(self):
        tx = make_tx("0x1", None, None)
        self.assertEqual(attribute_transactions([tx]), [])
        tx2 = {"tx_hash": "", "from": "", "to": "not-an-address"}
        self.assertEqual(attribute_transactions([tx2]), [])

    def test_confidence_bounds(self):
        txs = [
            make_tx(f"0x{i}", UNKNOWN_A, BINANCE_1, timestamp=f"2018-01-0{i}T00:00:00+00:00")
            for i in range(1, 12)
        ]
        attributions = attribute_transactions(txs)
        self.assertEqual(len(attributions), 1)
        score = attributions[0]["confidence_score"]
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertEqual(score, 1.0)  # capped at 1.0

        # smaller case: every score must be in range
        for att in attribute_transactions([make_tx("0xa", UNKNOWN_A, GATE)]):
            self.assertGreaterEqual(att["confidence_score"], 0.0)
            self.assertLessEqual(att["confidence_score"], 1.0)

    def test_confidence_reasons_match_evidence(self):
        tx = make_tx("0x1", UNKNOWN_A, BINANCE_1)
        att = attribute_transactions([tx])[0]
        self.assertIn("Direct match with known entity address", att["confidence_reasons"])
        self.assertIn("Entity record has a verification date", att["confidence_reasons"])
        self.assertIn("Entity record contains source information", att["confidence_reasons"])
        self.assertIn("1 interactions detected", att["confidence_reasons"])

    def test_attribution_output_keys(self):
        tx = make_tx("0x1", UNKNOWN_A, BINANCE_1)
        att = attribute_transactions([tx])[0]
        self.assertEqual(set(att.keys()), self.EXPECTED_KEYS)
        self.assertIsInstance(att["evidence"], list)
        self.assertEqual(att["evidence"][0]["transaction_hash"], "0x1")


class TestEvidence(unittest.TestCase):
    def test_evidence_uses_new_attribution_format(self):
        tx = make_tx("0xabc", UNKNOWN_A, BINANCE_1)
        att = attribute_transactions([tx])[0]
        ev = create_evidence_from_transaction(tx, att, UNKNOWN_A)
        d = ev.to_dict()
        self.assertEqual(d["entity_name"], "Binance")
        self.assertEqual(d["entity_type"], "VASP")
        self.assertEqual(d["matched_address"], BINANCE_1)
        self.assertEqual(d["attribution_method"], "known_address_match")
        self.assertEqual(d["source"], "Etherscan")
        self.assertEqual(
            d["source_url"],
            "https://etherscan.io/address/" + BINANCE_1,
        )

    def test_evidence_contains_actual_transaction_hash(self):
        tx = make_tx("0xrealhash789", UNKNOWN_A, BINANCE_1)
        att = attribute_transactions([tx])[0]
        evs = create_evidence_from_results(UNKNOWN_A, {"attributions": [att]}, [tx])
        self.assertEqual(len(evs), 1)
        d = evs[0].to_dict()
        self.assertEqual(d["transaction_hash"], "0xrealhash789")
        self.assertEqual(d["amount"], 1.0)
        self.assertEqual(d["amount_unit"], "ETH")
        self.assertEqual(d["direction"], "IN")
        self.assertEqual(d["chain"], "ethereum")
        self.assertEqual(d["suspect_wallet"], UNKNOWN_A)

    def test_evidence_never_replaces_match_with_unknown(self):
        tx = make_tx("0x1", UNKNOWN_A, BINANCE_1)
        att = attribute_transactions([tx])[0]
        ev = create_evidence_from_transaction(tx, att, UNKNOWN_A)
        self.assertNotEqual(ev.entity_name, "Unknown")
        self.assertEqual(ev.entity_name, "Binance")

    def test_evidence_missing_optional_fields_safe(self):
        tx = {"tx_hash": "0x1", "from": UNKNOWN_A, "to": BINANCE_1}
        att = attribute_transactions([tx])[0]
        ev = create_evidence_from_transaction(tx, att, UNKNOWN_A)
        self.assertIsNone(ev.amount)
        self.assertIsNone(ev.amount_unit)
        self.assertIsNone(ev.timestamp)
        self.assertEqual(ev.direction, "UNKNOWN")

    def test_evidence_by_hash_only(self):
        att = {
            "address": BINANCE_1,
            "entity_name": "Binance",
            "entity_type": "VASP",
            "matched_transaction_hashes": ["0xknown"],
            "first_seen": "2018-01-01T00:00:00+00:00",
            "chain": "ethereum",
            "attribution_method": "known_address_match",
            "source": "Etherscan",
            "source_url": "https://etherscan.io/address/" + BINANCE_1,
        }
        evs = create_evidence_from_results(UNKNOWN_A, {"attributions": [att]}, [])
        self.assertEqual(len(evs), 1)
        d = evs[0].to_dict()
        self.assertEqual(d["transaction_hash"], "0xknown")
        self.assertEqual(d["entity_name"], "Binance")


class TestInvestigation(unittest.TestCase):
    def test_investigation_expected_structure(self):
        txs = [
            make_tx("0x1", UNKNOWN_A, BINANCE_1, timestamp="2018-01-01T00:00:00+00:00"),
            make_tx("0x2", UNKNOWN_A, BINANCE_1, timestamp="2018-01-02T00:00:00+00:00"),
            make_tx("0x3", COINBASE, UNKNOWN_A, direction="OUT", timestamp="2018-01-03T00:00:00+00:00"),
            make_tx("0x4", UNKNOWN_A, UNKNOWN_B, timestamp="2018-01-04T00:00:00+00:00"),
        ]
        blockchain_data = {"wallet": UNKNOWN_A, "chain": "ethereum", "transactions": txs}
        result = _build_investigation_result(UNKNOWN_A, blockchain_data)

        expected_keys = {
            "wallet", "chain", "investigation_status", "total_transactions",
            "attributions", "evidence", "transaction_summary", "generated_at",
        }
        self.assertEqual(set(result.keys()), expected_keys)
        self.assertEqual(result["wallet"], UNKNOWN_A)
        self.assertEqual(result["chain"], "ethereum")
        self.assertEqual(result["investigation_status"], "complete")
        self.assertEqual(result["total_transactions"], 4)
        self.assertEqual(len(result["attributions"]), 2)
        self.assertEqual(len(result["evidence"]), 3)

        entities = {a["entity_name"] for a in result["attributions"]}
        self.assertEqual(entities, {"Binance", "Coinbase"})

        summary = result["transaction_summary"]
        self.assertEqual(summary["total_transactions"], 4)
        self.assertEqual(summary["incoming_transactions"], 3)
        self.assertEqual(summary["outgoing_transactions"], 1)
        self.assertEqual(summary["unique_counterparties"], 3)
        self.assertEqual(summary["matched_vasp_entities"], 2)

        self.assertNotIn("risk_score", result)
        self.assertNotIn("risk_level", result)

    def test_run_investigation_empty_wallet(self):
        result = run_investigation("")
        self.assertEqual(result["investigation_status"], "error")
        self.assertEqual(result["total_transactions"], 0)
        self.assertEqual(result["attributions"], [])

    def test_run_investigation_invalid_wallet(self):
        result = run_investigation("not-an-address")
        self.assertEqual(result["investigation_status"], "error")
        self.assertIn("error", result)

    def test_report_generator_with_investigation_result(self):
        txs = [make_tx("0x1", UNKNOWN_A, BINANCE_1)]
        blockchain_data = {"wallet": UNKNOWN_A, "chain": "ethereum", "transactions": txs}
        result = _build_investigation_result(UNKNOWN_A, blockchain_data)

        rg = ReportGenerator(result)
        prepared = rg.prepare_report_data()
        self.assertEqual(prepared["entities_found"], 1)
        self.assertEqual(prepared["attribution_method"], "known_address_match")
        self.assertGreaterEqual(prepared["overall_confidence"], 0.0)
        self.assertLessEqual(prepared["overall_confidence"], 1.0)
        self.assertGreater(prepared["overall_confidence"], 0.0)

        with self.assertRaises(NotImplementedError):
            rg.generate_pdf()

    def test_report_generator_no_matches(self):
        result = _build_investigation_result(
            UNKNOWN_A, {"wallet": UNKNOWN_A, "chain": "ethereum", "transactions": []}
        )
        rg = ReportGenerator(result)
        prepared = rg.prepare_report_data()
        self.assertEqual(prepared["overall_confidence"], 0.0)
        self.assertEqual(prepared["entities_found"], 0)


class TestHelpers(unittest.TestCase):
    def test_normalize_address(self):
        self.assertEqual(normalize_address(" 0xABC "), "0xabc")
        self.assertEqual(normalize_address(None), "")
        self.assertEqual(normalize_address(""), "")

    def test_check_address_in_database(self):
        record = check_address_in_database(BINANCE_1)
        self.assertIsNotNone(record)
        self.assertEqual(record["entity_name"], "Binance")
        self.assertIsNone(check_address_in_database(UNKNOWN_A))

    def test_attribute_entity_empty(self):
        result = attribute_entity("")
        self.assertEqual(result["attributions"], [])
        self.assertEqual(result["total_transactions"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)