# Report Generator Module
# Will later generate PDF investigation reports from the completed
# investigation result dictionary.

class ReportGenerator:
    """
    Generates PDF investigation reports from investigation results.

    Currently provides the skeleton structure. PDF generation will be
    implemented in a later phase.
    """

    def __init__(self, investigation_result):
        """
        Initialize with an investigation result dictionary.

        Input:
            investigation_result (dict): The output from run_investigation()
        """
        self.investigation_result = investigation_result
        self.report_data = None

    def _overall_confidence(self, data):
        """
        Overall confidence for the investigation.

        New structure: average of the per-entity attribution
        confidence_score values.
        """
        attributions = data.get("attributions", [])
        if attributions:
            scores = [
                a.get("confidence_score", 0.0)
                for a in attributions
                if isinstance(a, dict)
            ]
            if scores:
                return round(sum(scores) / len(scores), 3)

        # Backward-compatible fallback for the old "attribution" wrapper.
        attribution = data.get("attribution")
        if isinstance(attribution, dict):
            overall = attribution.get("overall_confidence")
            if overall is not None:
                return overall

        return 0.0

    def prepare_report_data(self):
        """
        Prepare the report data from the investigation result.

        Output:
            dict: Structured data ready for PDF template rendering.
        """
        data = self.investigation_result
        attributions = data.get("attributions", [])

        self.report_data = {
            "wallet": data.get("wallet", ""),
            "chain": data.get("chain", "ethereum"),
            "investigation_status": data.get("investigation_status", "unknown"),
            "generated_at": data.get("generated_at", ""),
            "total_transactions": data.get("total_transactions", 0),
            "overall_confidence": self._overall_confidence(data),
            "attributions": attributions,
            "entities_found": len(
                {
                    a.get("entity_name", "")
                    for a in attributions
                    if isinstance(a, dict)
                }
            ),
            "attribution_method": "",
            # Summary fields from evidence records
            "suspect_wallets": list(
                {
                    ev.get("suspect_wallet", "")
                    for ev in data.get("evidence", [])
                }
            ),
            "matched_entities": list(
                {
                    ev.get("entity_name", "")
                    for ev in data.get("evidence", [])
                }
            ),
            "transaction_hashes": [
                ev.get("transaction_hash", "")
                for ev in data.get("evidence", [])
            ],
            "amounts": [
                ev.get("amount", 0)
                for ev in data.get("evidence", [])
            ],
            "directions": [
                ev.get("direction", "UNKNOWN")
                for ev in data.get("evidence", [])
            ],
            "transaction_summary": data.get("transaction_summary", {}),
        }

        # Derive attribution_method from the strongest attribution.
        if attributions:
            first_att = attributions[0]
            self.report_data["attribution_method"] = first_att.get(
                "attribution_method", "database_match"
            )
        elif self.report_data["overall_confidence"] > 0:
            self.report_data["attribution_method"] = "database_match"

        return self.report_data

    def generate_pdf(self, output_path=None):
        """
        Generate a PDF investigation report.

        Raises:
            NotImplementedError: PDF generation not yet implemented.
        """
        raise NotImplementedError(
            "PDF report generation not yet implemented. "
            "This will be added in a later phase when the PDF "
            "generation library is configured."
        )

    def summary(self):
        """Return a text summary of the investigation result."""
        data = self.investigation_result
        attributions = data.get("attributions", [])

        lines = [
            "=" * 50,
            "INVESTIGATION REPORT SUMMARY",
            "=" * 50,
            f"Wallet: {data.get('wallet', 'N/A')}",
            f"Chain: {data.get('chain', 'N/A')}",
            f"Status: {data.get('investigation_status', 'N/A')}",
            f"Generated: {data.get('generated_at', 'N/A')}",
            "",
            f"Total Transactions: {data.get('total_transactions', 0)}",
            f"Overall Confidence: {self._overall_confidence(data)}",
            f"Matched VASP Entities: {len(attributions)}",
            f"Evidence Records: {len(data.get('evidence', []))}",
        ]

        if attributions:
            lines.append("")
            lines.append("-" * 50)
            for att in attributions:
                lines.append(
                    f"  {att.get('entity_name', 'Unknown')}: "
                    f"confidence={att.get('confidence_score', 0.0)}, "
                    f"interactions={att.get('interaction_count', 0)}, "
                    f"status={att.get('match_status', 'unknown')}"
                )

        return "\n".join(lines)