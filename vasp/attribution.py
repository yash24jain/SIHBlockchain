# Attribution Module
# Checks transaction counterparties against the entity database
# and returns VASP/entity attribution results with explainable confidence.
#
# ------------------------------------------------------------------
# CONFIDENCE FORMULA (deterministic, range 0.0 - 1.0)
# ------------------------------------------------------------------
# base score for a DIRECT known-address match .......... 0.50
# + entity record has verification_date ............... +0.15
# + entity record has source AND source_url ........... +0.10
# + per interaction .................................. +0.05 (max +0.25)
# ----------------------------------------------------------------
# total capped at .....................................  1.00
#
# Every score component above maps 1:1 to an entry in
# confidence_reasons, and confidence_reasons never claims
# evidence that is not actually present in the record.
# ------------------------------------------------------------------

import importlib
import json
import os
import sys


def _get_vasp_dir():
    """Get the vasp module directory."""
    return os.path.dirname(os.path.abspath(__file__))


def _load_entity_database():
    """Load the entity database from the JSON file."""
    vasp_dir = _get_vasp_dir()
    json_path = os.path.join(vasp_dir, "entity_database.json")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_address(address):
    """
    Normalize an address to lowercase for matching.

    Matches the normalization in blockchain_api.normalize_address.
    """
    if not address:
        return ""
    return address.strip().lower()


# Module-level entity database (loaded from JSON)
ENTITY_DATABASE = _load_entity_database()


def check_address_in_database(address):
    """
    Check if a given address exists in the entity database.

    Input:
        address (str): Ethereum address (checksum or lowercase)

    Output:
        dict or None: Entity record if found, None if not found
    """
    normalized = normalize_address(address)
    records = ENTITY_DATABASE.get("records", [])

    for record in records:
        db_address = normalize_address(record.get("address", ""))
        if normalized == db_address:
            return record

    return None


def _import_blockchain_api():
    """
    Import the sibling blockchain_api module without modifying it.

    blockchain/ is a sibling directory of vasp/. If it is not already
    on sys.path (because the repo root is not on sys.path), add it.
    """
    try:
        return importlib.import_module("blockchain_api")
    except ImportError:
        blockchain_dir = os.path.normpath(
            os.path.join(_get_vasp_dir(), "..", "blockchain")
        )
        if blockchain_dir not in sys.path:
            sys.path.insert(0, blockchain_dir)
        return importlib.import_module("blockchain_api")


def _determine_match_status(record):
    """
    Determine the match status for an entity record.

    "confirmed"  -> address is a known entity in the database
                    (direct known-address match, hop_distance 1)
    "unknown"    -> no database record

    "probable" is reserved for future graph/heuristic attribution
    and is never produced by this module today.
    """
    return "confirmed" if record else "unknown"


def _build_confidence_reasons(record, interaction_count):
    """
    Build the explainable confidence reasons for a matched entity.

    Each reason corresponds to a real, present piece of evidence and
    matches one term of the confidence formula in the module docstring.
    """
    reasons = ["Direct match with known entity address"]

    if interaction_count > 0:
        reasons.append(f"{interaction_count} interactions detected")

    if record.get("verification_date"):
        reasons.append("Entity record has a verification date")

    if record.get("source") and record.get("source_url"):
        reasons.append("Entity record contains source information")

    return reasons


def _calculate_confidence(record, interaction_count):
    """
    Calculate the deterministic confidence score (0.0 - 1.0).

    Formula is documented in the module docstring. Confidence is never
    inflated beyond 1.0 and never claims evidence that is not present.
    """
    score = 0.50

    if record.get("verification_date"):
        score += 0.15

    if record.get("source") and record.get("source_url"):
        score += 0.10

    score += min(interaction_count, 5) * 0.05

    return round(min(score, 1.0), 3)


def _process_entity_match(
    accumulator,
    record,
    tx,
    matched_address,
    dedup_key,
    suspect_wallet=None,
):
    """
    Record one matched counterparty interaction into the aggregation
    accumulator for a single entity.

    Duplicate transaction hashes are skipped so a repeated/duplicated
    hash is never counted twice for the same entity.
    """
    if dedup_key in accumulator["seen_hashes"]:
        return

    accumulator["seen_hashes"].add(dedup_key)

    # suspect_wallet is the investigated wallet when known, otherwise
    # the transaction's 'from' address.
    wallet = suspect_wallet or normalize_address(tx.get("from"))

    accumulator["evidence"].append(
        {
            "suspect_wallet": wallet,
            "matched_address": matched_address,
            "entity_name": record.get("entity_name", ""),
            "entity_type": record.get("entity_type", ""),
            "transaction_hash": tx.get("tx_hash") or "",
            "timestamp": tx.get("timestamp"),
            "chain": tx.get("chain") or record.get("chain", "ethereum"),
            "amount": tx.get("amount"),
            "amount_unit": tx.get("amount_unit"),
            "direction": tx.get("direction", "UNKNOWN"),
            "transaction_type": tx.get("transaction_type", "TRANSFER"),
            "attribution_method": "known_address_match",
            "source": record.get("source", ""),
            "source_url": record.get("source_url", ""),
        }
    )

    timestamp = tx.get("timestamp")
    if timestamp:
        accumulator["timestamps"].append(timestamp)


def attribute_transactions(transactions, wallet=None):
    """
    Match transaction counterparties against the entity database.

    Input:
        transactions (list of dicts): cleaned transaction list, e.g.
            blockchain_data["transactions"] as returned by
            blockchain_api.get_clean_blockchain_data().
        wallet (str, optional): The investigated wallet address. When
            provided, it is used as the suspect_wallet in the evidence
            records embedded in each attribution.

    Output:
        list of per-entity attribution dicts, one per matched entity.
        Aggregates repeated interactions, supports many entities in the
        same transaction list, and never creates duplicate records for
        the same entity/address.

        Sorted by interaction_count (descending), then entity_name.
    """
    transactions = transactions or []
    suspect_wallet = normalize_address(wallet)

    records = ENTITY_DATABASE.get("records", [])
    records_by_address = {}
    for record in records:
        records_by_address[normalize_address(record.get("address", ""))] = record

    # Accumulators keyed by normalized matched entity address.
    accumulators = {}

    for index, tx in enumerate(transactions):
        if not isinstance(tx, dict):
            continue

        from_addr = normalize_address(tx.get("from"))
        to_addr = normalize_address(tx.get("to"))

        # Deduplicate matched addresses within one transaction (a
        # transaction where from == to == the same entity counts once).
        matched = []
        for addr in (from_addr, to_addr):
            if not addr:
                continue
            if addr not in records_by_address:
                continue
            if addr in matched:
                continue
            matched.append(addr)

        if not matched:
            continue

        # Deduplication key: use the tx hash when present, otherwise a
        # synthetic per-transaction key so differing txs still count.
        dedup_key = tx.get("tx_hash")
        if not dedup_key:
            dedup_key = f"__missing_hash__{index}"

        for addr in matched:
            if addr not in accumulators:
                accumulators[addr] = {
                    "seen_hashes": set(),
                    "timestamps": [],
                    "evidence": [],
                }
            _process_entity_match(
                accumulator=accumulators[addr],
                record=records_by_address[addr],
                tx=tx,
                matched_address=addr,
                dedup_key=dedup_key,
                suspect_wallet=suspect_wallet or None,
            )

    attributions = []

    for address, acc in accumulators.items():
        record = records_by_address[address]
        timestamps = sorted(t for t in acc["timestamps"] if t)
        interaction_count = len(acc["seen_hashes"])

        attributions.append(
            {
                "address": address,
                "entity_name": record.get("entity_name", ""),
                "entity_type": record.get("entity_type", ""),
                "vasp_category": record.get("vasp_category", ""),
                "chain": record.get("chain", "ethereum"),
                "jurisdiction": record.get("jurisdiction", ""),
                "match_status": _determine_match_status(record),
                "hop_distance": 1,
                "confidence_score": _calculate_confidence(
                    record, interaction_count
                ),
                "confidence_reasons": _build_confidence_reasons(
                    record, interaction_count
                ),
                "interaction_count": interaction_count,
                "matched_transaction_hashes": sorted(acc["seen_hashes"]),
                "first_seen": timestamps[0] if timestamps else None,
                "last_seen": timestamps[-1] if timestamps else None,
                "attribution_method": "known_address_match",
                "source": record.get("source", ""),
                "source_url": record.get("source_url", ""),
                "evidence": acc["evidence"],
            }
        )

    attributions.sort(key=lambda a: (-a["interaction_count"], a["entity_name"]))

    return attributions


def _build_summary(blockchain_data, transactions, attributions):
    """Build the deterministic transaction summary counts."""
    wallet = normalize_address(blockchain_data.get("wallet", ""))

    incoming = sum(1 for tx in transactions if tx.get("direction") == "IN")
    outgoing = sum(1 for tx in transactions if tx.get("direction") == "OUT")

    counterparties = set()
    for tx in transactions:
        if not isinstance(tx, dict):
            continue
        from_addr = normalize_address(tx.get("from"))
        to_addr = normalize_address(tx.get("to"))
        if from_addr and from_addr != wallet:
            counterparties.add(from_addr)
        if to_addr and to_addr != wallet:
            counterparties.add(to_addr)

    return {
        "total_transactions": len(transactions),
        "incoming_transactions": incoming,
        "outgoing_transactions": outgoing,
        "unique_counterparties": len(counterparties),
        "matched_vasp_entities": len(attributions),
    }


def _empty_result(wallet="", chain="ethereum"):
    """Empty attribution result shared by error/empty paths."""
    return {
        "wallet": normalize_address(wallet),
        "chain": chain,
        "total_transactions": 0,
        "overall_confidence": 0.0,
        "attributions": [],
        "summary": {
            "total_transactions": 0,
            "incoming_transactions": 0,
            "outgoing_transactions": 0,
            "unique_counterparties": 0,
            "matched_vasp_entities": 0,
        },
    }


def attribute_blockchain_data(blockchain_data):
    """
    Attribute all counterparties in standardized blockchain data against
    the entity database.

    Accepts the output of get_clean_blockchain_data():

        {"wallet": "...", "chain": "ethereum", "transactions": [...]}

    Output:
        {
            "wallet", "chain", "total_transactions",
            "overall_confidence", "attributions", "summary"
        }
    """
    blockchain_data = blockchain_data or {}
    wallet = normalize_address(blockchain_data.get("wallet", ""))
    chain = blockchain_data.get("chain", "ethereum")
    transactions = blockchain_data.get("transactions", []) or []

    attributions = attribute_transactions(transactions, wallet=wallet)

    confidences = [a["confidence_score"] for a in attributions]
    overall_confidence = (
        round(sum(confidences) / len(confidences), 3) if confidences else 0.0
    )

    return {
        "wallet": wallet,
        "chain": chain,
        "total_transactions": len(transactions),
        "overall_confidence": overall_confidence,
        "attributions": attributions,
        "summary": _build_summary(blockchain_data, transactions, attributions),
    }


def attribute_entity(wallet_address):
    """
    Fetch standardized blockchain data for a wallet and attribute
    counterparties against the entity database.

    Input:
        wallet_address (str): Ethereum wallet address to investigate

    Output:
        Same fields as attribute_blockchain_data(), plus
        "blockchain_data" so downstream modules can re-use the
        fetched transactions instead of fetching them again.
    """
    wallet = normalize_address(wallet_address)

    if not wallet:
        result = _empty_result(wallet, "ethereum")
        result["blockchain_data"] = {
            "wallet": "",
            "chain": "ethereum",
            "transactions": [],
        }
        return result

    try:
        blockchain_api = _import_blockchain_api()
        blockchain_data = blockchain_api.get_clean_blockchain_data(wallet)
    except Exception as exc:
        result = _empty_result(wallet, "ethereum")
        result["blockchain_data"] = {
            "wallet": wallet,
            "chain": "ethereum",
            "transactions": [],
        }
        result["error"] = str(exc)
        return result

    result = attribute_blockchain_data(blockchain_data)
    result["blockchain_data"] = blockchain_data
    return result