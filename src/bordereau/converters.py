import datetime as dt
from functools import reduce
from typing import List, TypedDict

from roadcontrol.constants import (
    BSDASRI_HUMAN_WASTE_CODE,
    ES_TYPE_BSDA,
    ES_TYPE_BSDASRI,
    ES_TYPE_BSDD,
    ES_TYPE_BSFF,
    ES_TYPE_BSPAOH,
    ES_TYPE_BSVHU,
    TYPE_BSDA,
    TYPE_BSDASRI,
    TYPE_BSDD,
    TYPE_BSFF,
    TYPE_BSPAOH,
    TYPE_BSVHU,
)


class WasteDetails(TypedDict):
    code: str
    name: str
    weight: str


class Company(TypedDict):
    name: str


class Actor(TypedDict):
    company: Company


class BsdDisplay(TypedDict):
    bsd_type: str
    id: str
    readable_id: str
    updated_at: str
    adr: str
    waste_details: WasteDetails
    emitter: Actor
    destination: Actor
    transporter: Actor
    transporter_plate: str
    packagings: str


def deep_get(dictionary, keys, default=None):
    return reduce(lambda d, key: d.get(key, default) if isinstance(d, dict) else default, keys.split("."), dictionary)


def format_date(str):
    if not str:
        return ""
    try:
        return dt.datetime.fromisoformat(str).strftime("%d/%m/%Y")
    except ValueError:
        return ""


def format_bsdd_packagings(packagings):
    if not packagings:
        return ""
    return ", ".join([f"{p.get('quantity')} {p.get('other') or p.get('type')}" for p in packagings])


def format_bsdasri_packagings(packagings):
    if not packagings:
        return ""
    return ", ".join([f"{p.get('quantity')} {p.get('other') or p.get('type')}" for p in packagings])


def format_bsff_packagings(packagings):
    if not packagings:
        return ""
    return ", ".join(
        [f"{p.get('numero')} {p.get('type')} vol:{p.get('volume')} poids:{p.get('weight')}" for p in packagings]
    )


def format_bspaoh_packagings(packagings):
    if not packagings:
        return ""
    return ", ".join([f"{p.get('quantity')} {p.get('type')} vol:{p.get('volume')}" for p in packagings])

class BsdDisplaySearchResult(TypedDict):
    bsd_type: str
    id: str
    readable_id: str
    received_at: str      # Reçu le
    emitted_at: str       # Expédié le
    aiot_code: str        # Code AIOT — TODO: à définir selon la source de données MonAIOT
    waste_details: WasteDetails
    intermediaries: list  # Intermédiaire (raison sociale)
    destination: Actor    # Destination (raison sociale)
    emitter: Actor
    transporter: Actor

def bsdd_to_bsd_display_search_result(bsdd) -> BsdDisplaySearchResult:
    return {
        "bsd_type": TYPE_BSDD,
        "id": deep_get(bsdd, "id"),
        "readable_id": deep_get(bsdd, "readableId", None) or deep_get(bsdd, "id"),
        "received_at": format_date(deep_get(bsdd, "receivedAt")),
        "emitted_at": format_date(deep_get(bsdd, "emittedAt")),
        "aiot_code": None,  # TODO: à brancher depuis MonAIOT
        "waste_details": {
            "code": deep_get(bsdd, "wasteDetails.code"),
            "name": deep_get(bsdd, "wasteDetails.name"),
            "weight": str(deep_get(bsdd, "stateSummary.quantity") or deep_get(bsdd, "wasteDetails.quantity")),
        },
        "intermediaries": [
            {"name": i.get("name")} for i in (deep_get(bsdd, "intermediaries") or [])
        ],
        "destination": {"company": {"name": deep_get(bsdd, "recipient.company.name")}},
        "emitter": {"company": {"name": deep_get(bsdd, "emitter.company.name")}},
        "transporter": {"company": {"name": deep_get(bsdd, "transporter.company.name")}},
    }


def bsdasri_to_bsd_display_search_result(bsdasri) -> BsdDisplaySearchResult:
    waste_code = deep_get(bsdasri, "bsdasriWaste.code")
    return {
        "bsd_type": TYPE_BSDASRI,
        "id": deep_get(bsdasri, "id"),
        "readable_id": deep_get(bsdasri, "id"),
        "received_at": format_date(deep_get(bsdasri, "destination.reception.date")),
        "emitted_at": format_date(deep_get(bsdasri, "emitter.emission.signedAt")),
        "aiot_code": None,  # TODO: à brancher depuis MonAIOT
        "waste_details": {
            "code": waste_code,
            "name": "DASRI origine humaine" if waste_code == BSDASRI_HUMAN_WASTE_CODE else "DASRI origine animale",
            "weight": str(deep_get(bsdasri, "transporter.transport.weight.value", default=0)),
        },
        "intermediaries": [],  # BSDASRI n'a pas d'intermédiaires
        "destination": {"company": {"name": deep_get(bsdasri, "destination.company.name")}},
        "emitter": {"company": {"name": deep_get(bsdasri, "emitter.company.name")}},
        "transporter": {"company": {"name": deep_get(bsdasri, "transporter.company.name")}},
    }


def bsff_to_bsd_display_search_result(bsff) -> BsdDisplaySearchResult:
    return {
        "bsd_type": TYPE_BSFF,
        "id": deep_get(bsff, "id"),
        "readable_id": deep_get(bsff, "id"),
        "received_at": format_date(deep_get(bsff, "destination.reception.date")),
        "emitted_at": format_date(deep_get(bsff, "emitter.emission.signedAt")),
        "aiot_code": None,  # TODO: à brancher depuis MonAIOT
        "waste_details": {
            "code": deep_get(bsff, "waste.code"),
            "name": deep_get(bsff, "waste.description"),
            "weight": str(deep_get(bsff, "bsffWeight.value")),
        },
        "intermediaries": [],  # BSFF n'a pas d'intermédiaires
        "destination": {"company": {"name": deep_get(bsff, "bsffDestination.company.name")}},
        "emitter": {"company": {"name": deep_get(bsff, "emitter.company.name")}},
        "transporter": {"company": {"name": deep_get(bsff, "bsffTransporter.company.name")}},
    }


def bsda_to_bsd_display_search_result(bsda) -> BsdDisplaySearchResult:
    waste_code = deep_get(bsda, "waste.bsdaWasteCode")
    return {
        "bsd_type": TYPE_BSDA,
        "id": deep_get(bsda, "id"),
        "readable_id": deep_get(bsda, "id"),
        "received_at": format_date(deep_get(bsda, "destination.reception.date")),
        "emitted_at": format_date(deep_get(bsda, "emitter.emission.signedAt")),
        "aiot_code": None,  # TODO: à brancher depuis MonAIOT
        "waste_details": {
            "code": waste_code,
            "name": deep_get(bsda, "waste.materialName"),
            "weight": str(deep_get(bsda, "weight.value", default=0)),
        },
        "intermediaries": [],  # BSDA n'a pas d'intermédiaires
        "destination": {"company": {"name": deep_get(bsda, "destination.company.name")}},
        "emitter": {"company": {"name": deep_get(bsda, "emitter.company.name")}},
        "transporter": {"company": {"name": deep_get(bsda, "transporter.company.name")}},
    }


def bspaoh_to_bsd_display_search_result(bspaoh) -> BsdDisplaySearchResult:
    waste_code = deep_get(bspaoh, "bspaohWaste.code")
    waste_type = deep_get(bspaoh, "bspaohWaste.type")
    return {
        "bsd_type": TYPE_BSPAOH,
        "id": deep_get(bspaoh, "id"),
        "readable_id": deep_get(bspaoh, "id"),
        "received_at": format_date(deep_get(bspaoh, "destination.reception.date")),
        "emitted_at": format_date(deep_get(bspaoh, "emitter.emission.signedAt")),
        "aiot_code": None,  # TODO: à brancher depuis MonAIOT
        "waste_details": {
            "code": waste_code,
            "name": "Foetus" if waste_type == "FOETUS" else "Pièces anatomiques d'origine humaine",
            "weight": str(deep_get(bspaoh, "emitter.emission.detail.weight.value", default=0)),
        },
        "intermediaries": [],  # BSPAOH n'a pas d'intermédiaires
        "destination": {"company": {"name": deep_get(bspaoh, "destination.company.name")}},
        "emitter": {"company": {"name": deep_get(bspaoh, "emitter.company.name")}},
        "transporter": {"company": {"name": deep_get(bspaoh, "transporter.company.name")}},
    }


def bsvhu_to_bsd_display_search_result(bsvhu) -> BsdDisplaySearchResult:
    waste_code = deep_get(bsvhu, "wasteCode")
    return {
        "bsd_type": TYPE_BSVHU,
        "id": deep_get(bsvhu, "id"),
        "readable_id": deep_get(bsvhu, "id"),
        "received_at": format_date(deep_get(bsvhu, "destination.reception.date")),
        "emitted_at": format_date(deep_get(bsvhu, "emitter.emission.signedAt")),
        "aiot_code": None,  # TODO: à brancher depuis MonAIOT
        "waste_details": {
            "code": waste_code,
            "name": "VHU non dépollués" if waste_code == "16 01 04*" else "VHU dépollués",
            "weight": str(
                deep_get(bsvhu, "destination.reception.weight", default=0)
                or deep_get(bsvhu, "weight.value", default=0)
            ),
        },
        "intermediaries": [],  # BSVHU n'a pas d'intermédiaires
        "destination": {"company": {"name": deep_get(bsvhu, "destination.company.name")}},
        "emitter": {"company": {"name": deep_get(bsvhu, "emitter.company.name")}},
        "transporter": {"company": {"name": deep_get(bsvhu, "transporter.company.name")}},
    }

class BsdsToBsdsDisplaySearchResult():
    def __init__(self, bsds):
        self.bsds: List[BsdDisplay] = bsds
        self.bsds_display = []

    def map_bsd_to_bsd_display(self, bsd):
        converters = {
            ES_TYPE_BSDD: bsdd_to_bsd_display_search_result,
            ES_TYPE_BSDASRI: bsdasri_to_bsd_display_search_result,
            ES_TYPE_BSFF: bsff_to_bsd_display_search_result,
            ES_TYPE_BSDA: bsda_to_bsd_display_search_result,
            ES_TYPE_BSPAOH: bspaoh_to_bsd_display_search_result,
            ES_TYPE_BSVHU: bsvhu_to_bsd_display_search_result,
        }

        bsd_type = bsd["__typename"]
        converter = converters.get(bsd_type)
        if converter:
            return converter(bsd)

        return None

    def convert(self):
        for bsd in self.bsds:
            bsd_display = self.map_bsd_to_bsd_display(bsd)
            if bsd_display:
                self.bsds_display.append(bsd_display)
