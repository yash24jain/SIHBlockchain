# VASP Module - Interface Output for Member 4 (Risk Engine)

These files are **SAMPLE OUTPUTS** produced by the existing VASP attribution
pipeline for Member 4 to consume in the Risk Engine.

## Files

- `vasp/output/vasp_output.json` - the **primary machine-readable interface**.
- `vasp/output/vasp_output.csv` - a tabular equivalent (one row per VASP match).
- `vasp/entity_database.json` - the **internal reference entity database**.
  This file is NOT the Risk Engine interface; it is a lookup source used by
  the VASP attribution logic only.

## Important semantics

- **VASP confidence is attribution confidence, NOT fraud probability.**
  `confidence_score` expresses how confident the VASP module is that a
  direct known-address match is correct, based on address normalization,
  database record completeness (source, source_url, verification_date) and
  the number of interactions. It says nothing about whether the wallet is
  risky or fraudulent.
- The VASP module does **NOT** provide `risk_score` or `risk_level`.
  Those belong to the Risk Engine.
- Member 4 should combine this VASP information with graph analysis, ML and
  other signals inside the Risk Engine to produce the final risk assessment.
- Direct known-address matching currently uses `hop_distance = 1`. No
  multi-hop / graph-based attribution is performed yet, so no hop distance
  other than 1 is ever produced.
- The output contains **attribution and supporting information only**.

## JSON structure

```json
{
  "suspect_wallet": "...",
  "chain": "ethereum",
  "vasp_matches": [
    {
      "address": "...",
      "entity_name": "...",
      "entity_type": "VASP",
      "vasp_category": "...",
      "chain": "ethereum",
      "jurisdiction": "...",
      "hop_distance": 1,
      "match_status": "confirmed",
      "confidence_score": 0.0,
      "confidence_reasons": [],
      "interaction_count": 0,
      "matched_transaction_hashes": [],
      "first_seen": null,
      "last_seen": null,
      "attribution_method": "known_address_match",
      "source": "...",
      "source_url": "..."
    }
  ]
}
```

## CSV columns (one row per VASP match)

`suspect_wallet, chain, address, entity_name, entity_type, vasp_category,
jurisdiction, hop_distance, match_status, confidence_score,
confidence_reasons, interaction_count, matched_transaction_hashes,
first_seen, last_seen, attribution_method, source, source_url`

List-valued fields (`confidence_reasons`, `matched_transaction_hashes`) are
serialized as JSON strings so they round-trip safely through CSV.

## How these samples were produced

A synthetic transaction dataset (suspect wallet + one known VASP address +
one non-VASP counterparty, multiple transactions with the VASP) was run
through the existing pipeline:
`attribute_blockchain_data() -> attributions`, then projected into this
output contract. No confidence values or attribution fields were invented;
they come directly from the VASP module.