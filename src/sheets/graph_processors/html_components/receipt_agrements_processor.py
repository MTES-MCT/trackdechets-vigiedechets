from datetime import datetime
from typing import Dict
from zoneinfo import ZoneInfo

import polars as pl


class ReceiptAgrementsProcessor:
    """Component that displays informations about the company receipts and agreements.

    Parameters
    ----------
    receipts_agreements_data : dict
        Dict with keys being the name of the receipt/agreement and values being LazyFrames
        with one line per receipt/agreement (usually there is only one receipt for a receipt type for an establishment but
        there might be more).
    """

    def __init__(self, receipts_agreements_data: Dict[str, pl.LazyFrame]) -> None:
        self.receipts_agreements_data = {k: v.collect() for k, v in receipts_agreements_data.items()}

    def _check_data_empty(self) -> bool:
        if len(self.receipts_agreements_data) == 0:
            return True

        return False

    def build(self):
        res = []
        for name, data in self.receipts_agreements_data.items():
            for line in data.iter_rows(named=True):
                validity_str = ""
                if "validity_limit" in line.keys():
                    # todo: utcnow
                    if line["validity_limit"] < datetime.now(tz=ZoneInfo("Europe/Paris")):
                        validity_str = f"expiré depuis le {line['validity_limit']:%d/%m/%Y}"
                    else:
                        validity_str = f"valide jusqu'au {line['validity_limit']:%d/%m/%Y}"
                res.append(
                    {
                        "name": name,
                        "number": line["receipt_number"],
                        "validity_str": validity_str,
                    }
                )

        return res
