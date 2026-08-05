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
    siret: str
    gerepId: str


class Actor(TypedDict):
    company: Company


class BsdDisplay(TypedDict):
    bsd_type: str
    id: str
    readable_id: str
    updated_at: str
    status: str
    adr: str
    waste_details: WasteDetails
    emitter: Actor
    destination: Actor
    transporter: Actor
    transporter_plate: str
    packagings: str


class BsdDisplaySearchResult(TypedDict):
    bsd_type: str
    id: str
    readable_id: str
    updated_at: str
    status: str
    received_at: str
    emitted_at: str
    aiot_code: str
    waste_details: WasteDetails
    intermediaries: list
    destination: Actor
    emitter: Actor
    transporter: Actor
    transporter_plate: str
    packagings: str
    adr: str
    grouping: str
    grouping_list: list


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


def format_weight(val):
    return "N/A" if val is None else str(val)


def bsdd_to_bsd_display_search_result(bsdd) -> BsdDisplaySearchResult:
    return {
        "bsd_type": TYPE_BSDD,
        "id": deep_get(bsdd, "id"),
        "readable_id": deep_get(bsdd, "readableId", None) or deep_get(bsdd, "id"),
        "updated_at": format_date(deep_get(bsdd, "updatedAt")),
        "status": deep_get(bsdd, "bsddStatus"),
        "received_at": format_date(deep_get(bsdd, "receivedAt")),
        "emitted_at": format_date(deep_get(bsdd, "emittedAt")),
        "waste_details": {
            "code": deep_get(bsdd, "wasteDetails.code"),
            "name": deep_get(bsdd, "wasteDetails.name"),
            "weight": format_weight(
                deep_get(bsdd, "stateSummary.quantity") or deep_get(bsdd, "wasteDetails.quantity") or "N/A"
            ),
        },
        "intermediaries": [{"name": i.get("name")} for i in (deep_get(bsdd, "intermediaries") or [])],
        "destination": {
            "company": {
                "name": deep_get(bsdd, "recipient.company.name"),
                "siret": deep_get(bsdd, "recipient.company.siret"),
            }
        },
        "emitter": {
            "company": {
                "name": deep_get(bsdd, "emitter.company.name"),
                "siret": deep_get(bsdd, "emitter.company.siret"),
                "gerepId": deep_get(bsdd, "emitter.company.gerepId"),
            }
        },
        "transporter": {
            "company": {
                "name": deep_get(bsdd, "transporter.company.name"),
                "siret": deep_get(bsdd, "transporter.company.siret"),
            }
        },
        "adr": deep_get(bsdd, "wasteDetails.onuCode"),
        "transporter_plate": deep_get(bsdd, "transporter.numberPlate"),
        "packagings": format_bsdd_packagings(deep_get(bsdd, "wasteDetails.packagingInfos")),
        "grouping_list": [{"id": f.get("form", {}).get("id")} for f in (deep_get(bsdd, "grouping_bsdd") or []) if f.get("form") and f["form"].get("id")],
    }


def bsdasri_to_bsd_display_search_result(bsdasri) -> BsdDisplaySearchResult:
    waste_code = deep_get(bsdasri, "bsdasriWaste.code")
    return {
        "bsd_type": TYPE_BSDASRI,
        "id": deep_get(bsdasri, "id"),
        "readable_id": deep_get(bsdasri, "id"),
        "updated_at": format_date(deep_get(bsdasri, "bsdasriUpdatedAt")),
        "status": deep_get(bsdasri, "bsdasriStatus"),
        "received_at": format_date(deep_get(bsdasri, "destination.reception.date")),
        "emitted_at": format_date(deep_get(bsdasri, "bsdasriUpdatedAt")),
        "waste_details": {
            "code": waste_code,
            "name": "DASRI origine humaine" if waste_code == BSDASRI_HUMAN_WASTE_CODE else "DASRI origine animale",
            "weight": format_weight(deep_get(bsdasri, "transporter.transport.weight.value") or "N/A"),
        },
        "intermediaries": [],
        "destination": {
            "company": {
                "name": deep_get(bsdasri, "destination.company.name"),
                "siret": deep_get(bsdasri, "destination.company.siret"),
            }
        },
        "emitter": {
            "company": {
                "name": deep_get(bsdasri, "emitter.company.name"),
                "siret": deep_get(bsdasri, "emitter.company.siret"),
                "gerepId": deep_get(bsdasri, "emitter.company.gerepId"),
            }
        },
        "transporter": {
            "company": {
                "name": deep_get(bsdasri, "transporter.company.name"),
                "siret": deep_get(bsdasri, "transporter.company.siret"),
            }
        },
        "adr": deep_get(bsdasri, "bsdasriWaste.adr"),
        "transporter_plate": (deep_get(bsdasri, "transporter.transport.plates") or [""])[0],
        "packagings": format_bsdasri_packagings(deep_get(bsdasri, "transporter.transport.packagings")),
        "grouping_list": deep_get(bsdasri, "grouping_bsdasri") or [],
    }


def bsff_to_bsd_display_search_result(bsff) -> BsdDisplaySearchResult:
    return {
        "bsd_type": TYPE_BSFF,
        "id": deep_get(bsff, "id"),
        "readable_id": deep_get(bsff, "id"),
        "updated_at": format_date(deep_get(bsff, "bsffUpdatedAt")),
        "status": deep_get(bsff, "bsffStatus"),
        "received_at": format_date(deep_get(bsff, "bsffDestination.reception.date")),
        "emitted_at": format_date(deep_get(bsff, "bsffUpdatedAt")),
        "waste_details": {
            "code": deep_get(bsff, "waste.code"),
            "name": deep_get(bsff, "waste.description"),
            "weight": format_weight(deep_get(bsff, "bsffWeight.value") or "N/A"),
        },
        "intermediaries": [],
        "destination": {
            "company": {
                "name": deep_get(bsff, "bsffDestination.company.name"),
                "siret": deep_get(bsff, "bsffDestination.company.siret"),
            }
        },
        "emitter": {
            "company": {
                "name": deep_get(bsff, "emitter.company.name"),
                "siret": deep_get(bsff, "emitter.company.siret"),
                "gerepId": deep_get(bsff, "emitter.company.gerepId"),
            }
        },
        "transporter": {
            "company": {
                "name": deep_get(bsff, "bsffTransporter.company.name"),
                "siret": deep_get(bsff, "bsffTransporter.company.siret"),
            }
        },
        "adr": deep_get(bsff, "waste.adr"),
        "transporter_plate": (deep_get(bsff, "bsffTransporter.transport.plates") or [""])[0],
        "packagings": format_bsff_packagings(deep_get(bsff, "packagings")),
        "grouping_list": [{"id": prev.get("id")} for pkg in (deep_get(bsff, "grouping_bsff") or []) for prev in (pkg.get("previousBsffs") or []) if prev.get("id")],
    }


def bsda_to_bsd_display_search_result(bsda) -> BsdDisplaySearchResult:
    waste_code = deep_get(bsda, "waste.bsdaWasteCode")
    return {
        "bsd_type": TYPE_BSDA,
        "id": deep_get(bsda, "id"),
        "readable_id": deep_get(bsda, "id"),
        "updated_at": format_date(deep_get(bsda, "bsdaUpdatedAt")),
        "status": deep_get(bsda, "bsdaStatus"),
        "received_at": format_date(deep_get(bsda, "destination.reception.date")),
        "emitted_at": format_date(deep_get(bsda, "bsdaUpdatedAt")),
        "waste_details": {
            "code": waste_code,
            "name": deep_get(bsda, "waste.materialName"),
            "weight": format_weight(deep_get(bsda, "weight.value", default="N/A")),
        },
        "intermediaries": [],
        "destination": {
            "company": {
                "name": deep_get(bsda, "destination.company.name"),
                "siret": deep_get(bsda, "destination.company.siret"),
            }
        },
        "emitter": {
            "company": {
                "name": deep_get(bsda, "emitter.company.name"),
                "siret": deep_get(bsda, "emitter.company.siret"),
                "gerepId": deep_get(bsda, "emitter.company.gerepId"),
            }
        },
        "transporter": {
            "company": {
                "name": deep_get(bsda, "transporter.company.name"),
                "siret": deep_get(bsda, "transporter.company.siret"),
            }
        },
        "adr": deep_get(bsda, "waste.adr"),
        "transporter_plate": (deep_get(bsda, "transporter.transport.plates") or [""])[0],
        "packagings": format_bsdd_packagings(deep_get(bsda, "bsdaPackagings")),
        "grouping": ", ".join([g.get("id", "") for g in (deep_get(bsda, "grouping_bsda") or [])]),
        "grouping_list": deep_get(bsda, "grouping_bsda") or [],
    }


def bspaoh_to_bsd_display_search_result(bspaoh) -> BsdDisplaySearchResult:
    waste_code = deep_get(bspaoh, "bspaohWaste.code")
    waste_type = deep_get(bspaoh, "bspaohWaste.type")
    return {
        "bsd_type": TYPE_BSPAOH,
        "id": deep_get(bspaoh, "id"),
        "readable_id": deep_get(bspaoh, "id"),
        "updated_at": format_date(deep_get(bspaoh, "bspaohUpdatedAt")),
        "status": deep_get(bspaoh, "bspaohStatus"),
        "received_at": format_date(deep_get(bspaoh, "destination.reception.date")),
        "emitted_at": "",
        "waste_details": {
            "code": waste_code,
            "name": "Foetus" if waste_type == "FOETUS" else "Pièces anatomiques d'origine humaine",
            "weight": format_weight(deep_get(bspaoh, "emitter.emission.detail.weight.value", default="N/A")),
        },
        "intermediaries": [],
        "destination": {
            "company": {
                "name": deep_get(bspaoh, "destination.company.name"),
                "siret": deep_get(bspaoh, "destination.company.siret"),
            }
        },
        "emitter": {
            "company": {
                "name": deep_get(bspaoh, "emitter.company.name"),
                "siret": deep_get(bspaoh, "emitter.company.siret"),
                "gerepId": deep_get(bspaoh, "emitter.company.gerepId"),
            }
        },
        "transporter": {
            "company": {
                "name": deep_get(bspaoh, "transporter.company.name"),
                "siret": deep_get(bspaoh, "transporter.company.siret"),
            }
        },
        "adr": None,
        "transporter_plate": (deep_get(bspaoh, "transporter.transport.plates") or [""])[0],
        "packagings": format_bspaoh_packagings(deep_get(bspaoh, "bspaohWaste.packagings")),
        "grouping_list": [],
    }


def bsvhu_to_bsd_display_search_result(bsvhu) -> BsdDisplaySearchResult:
    waste_code = deep_get(bsvhu, "wasteCode")
    return {
        "bsd_type": TYPE_BSVHU,
        "id": deep_get(bsvhu, "id"),
        "readable_id": deep_get(bsvhu, "id"),
        "updated_at": format_date(deep_get(bsvhu, "bsvhuUpdatedAt")),
        "status": deep_get(bsvhu, "bsvhuStatus"),
        "received_at": format_date(deep_get(bsvhu, "destination.reception.date")),
        "emitted_at": format_date(deep_get(bsvhu, "bsvhuUpdatedAt")),
        "waste_details": {
            "code": waste_code,
            "name": "VHU non dépollués" if waste_code == "16 01 04*" else "VHU dépollués",
            "weight": format_weight(
                deep_get(bsvhu, "destination.reception.weight", default="N/A")
                or deep_get(bsvhu, "weight.value", default="N/A")
            ),
        },
        "intermediaries": [],
        "destination": {
            "company": {
                "name": deep_get(bsvhu, "destination.company.name"),
                "siret": deep_get(bsvhu, "destination.company.siret"),
            }
        },
        "emitter": {
            "company": {
                "name": deep_get(bsvhu, "emitter.company.name"),
                "siret": deep_get(bsvhu, "emitter.company.siret"),
                "gerepId": deep_get(bsvhu, "emitter.company.gerepId"),
            }
        },
        "transporter": {
            "company": {
                "name": deep_get(bsvhu, "transporter.company.name"),
                "siret": deep_get(bsvhu, "transporter.company.siret"),
            }
        },
        "adr": None,
        "transporter_plate": (deep_get(bsvhu, "transporter.transport.plates") or [""])[0],
        "packagings": "",
        "grouping_list": [],
    }


class BsdsToBsdsDisplaySearchResult:
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
