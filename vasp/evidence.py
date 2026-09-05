# Evidence Module
# Creates structured evidence records from attribution results.

from .attribution import _import_blockchain_api, normalize_address


class EvidenceRecord:
    """Structured evidence record for a single transaction's investigation."""

    def __init__(
        self,
        suspect_wallet,
        matched_address,
        entity_name,
        entity_type,
        transaction_hash,
        timestamp,
        chain,
        amount,
        amount_unit,
        direction,
        transaction_type,
        attribution_method,
        source,
        source_url,
    ):
        self.suspect_wallet = suspect_wallet
        self.matched_address = matched_address
        self.entity_name = entity_name
        self.entity_type = entity_type
        self.transaction_hash = transaction_hash
        self.timestamp = timestamp
        self.chain = chain
        self.amount = amount
        self.amount_unit = amount_unit
        self.direction = direction
        self.transaction_type = transaction_type
        self.attribution_method = attribution_method
        self.source = source
        self.source_url = source_url

    def to_dict(self):
        """Convert the evidence record to a Python dictionary."""
        return {
            "suspect_wallet": self.suspect_wallet,
            "matched_address": self.matched_address,
            "entity_name": self.entity_name,
            "entity_type": self.entity_type,
            "transaction_hash": self.transaction_hash,
            "timestamp": self.timestamp,
            "chain": self.chain,
            "amount": self.amount,
            "amount_unit": self.amount_unit,
            "direction": self.direction,
            "transaction_type": self.transaction_type,
            "attribution_method": self.attribution_method,
            "source": self.source,
            "source_url": self.source_url,
        }

    def __repr__(self):
        return (
            f"EvidenceRecord(entity='{self.entity_name}', "
            f"wallet='{self.suspect_wallet[:8]}...', "
            f"tx='{self.transaction_hash[:16]}...')"
        )


def create_evidence_from_transaction(
    transaction,
    attribution_result,
    suspect_wallet=None,
):
    """
    Create an EvidenceRecord from a cleaned blockchain transaction and
    its per-entity attribution record (NEW format).

    `attribution_result` is ONE entity attribution dict:

        {
            "address", "entity_name", "entity_type", "vasp_category",
            "chain", "jurisdiction", "match_status", "hop_distance",
            "confidence_score", "confidence_reasons", "interaction_count",
            "matched_transaction_hashes", "first_seen", "last_seen",
            "attribution_method", "source", "source_url", "evidence"
        }

    A confirmed match is NEVER replaced with "Unknown". Missing optional
    values safely become null/empty values.

    Input:
        transaction (dict): Normalized transaction from
            get_clean_blockchain_data() output.
        attribution_result (dict): Per-entity attribution from
            attribute_transactions() / attribute_blockchain_data().
        suspect_wallet (str, optional): The wallet being investigated.
            Defaults to the transaction's wallet.

    Output:
        EvidenceRecord: A structured evidence record.
    """
    wallet = (
        normalize_address(suspect_wallet)
        if suspect_wallet
        else normalize_address(transaction.get("from", ""))
    )

    attribution_result = attribution_result or {}

    # A confirmed match is always preserved; it is never "Unknown".
    matched_address = attribution_result.get("address") or ""
    entity_name = attribution_result.get("entity_name") or ""
    entity_type = attribution_result.get("entity_type") or ""
    attribution_method = attribution_result.get(
        "attribution_method", "known_address_match"
    )
    source = attribution_result.get("source") or ""
    source_url = attribution_result.get("source_url") or ""

    return EvidenceRecord(
        suspect_wallet=wallet,
        matched_address=matched_address,
        entity_name=entity_name,
        entity_type=entity_type,
        transaction_hash=transaction.get("tx_hash", ""),
        timestamp=transaction.get("timestamp"),
        chain=transaction.get("chain", "ethereum"),
        amount=transaction.get("amount"),
        amount_unit=transaction.get("amount_unit"),
        direction=transaction.get("direction", "UNKNOWN"),
        transaction_type=transaction.get("transaction_type", "TRANSFER"),
        attribution_method=attribution_method,
        source=source,
        source_url=source_url,
    )


def create_evidence_from_results(
    wallet_address,
    attribution_result,
    transactions=None,
):
    """
    Create evidence records for every matched transaction.

    Input:
        wallet_address (str): The investigated wallet address
        attribution_result (dict): Output of attribute_entity() /
            attribute_blockchain_data(), containing "attributions".
        transactions (list, optional): Transaction list used to look up
            full transaction data by hash. If None, fetched via
            blockchain_api.

    Output:
        list[EvidenceRecord]: List of evidence records for all matched
            transactions.
    """
    wallet = normalize_address(wallet_address)

    if not isinstance(attribution_result, dict):
        return []

    if transactions is None:
        try:
            blockchain_api = _import_blockchain_api()
            blockchain_data = blockchain_api.get_clean_blockchain_data(wallet)
            transactions = blockchain_data.get("transactions", [])
        except Exception:
            transactions = []

    transactions = transactions or []

    # Last-write-wins index of hash -> full transaction (handles
    # duplicate hashes gracefully: only the original tx is preserved).
    tx_by_hash = {}
    for tx in transactions:
        if isinstance(tx, dict) and tx.get("tx_hash"):
            tx_by_hash.setdefault(tx["tx_hash"], tx)

    records = []

    for attribution in attribution_result.get("attributions", []):
        if not isinstance(attribution, dict):
            continue

        for tx_hash in attribution.get("matched_transaction_hashes", []):
            tx = tx_by_hash.get(tx_hash)

            if tx is not None:
                records.append(
                    create_evidence_from_transaction(
                        transaction=tx,
                        attribution_result=attribution,
                        suspect_wallet=wallet,
                    )
                )
            else:
                # Hash known from attribution but full tx not available:
                # build evidence from the attribution record itself.
                records.append(
                    EvidenceRecord(
                        suspect_wallet=wallet,
                        matched_address=attribution.get("address", ""),
                        entity_name=attribution.get("entity_name", ""),
                        entity_type=attribution.get("entity_type", ""),
                        transaction_hash=tx_hash,
                        timestamp=attribution.get("first_seen"),
                        chain=attribution.get("chain", "ethereum"),
                        amount=None,
                        amount_unit=None,
                        direction=None,
                        transaction_type=None,
                        attribution_method=attribution.get(
                            "attribution_method", "known_address_match"
                        ),
                        source=attribution.get("source", ""),
                        source_url=attribution.get("source_url", ""),
                    )
                )

    return records