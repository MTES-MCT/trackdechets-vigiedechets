import polars as pl
from polars.testing import assert_frame_equal

from sheets.constants import BSDA, BSDASRI, BSDD, BSFF

from ..graph_processors.html_components import BsdRefusedTableProcessor


def test_bsd_refused_processor(
    sample_data_bsdd,
    sample_data_bsda,
    sample_data_bsdasri,
    sample_data_bsff,
    sample_waste_codes,
    sample_packagings_data,
    data_date_interval,
):
    processor = BsdRefusedTableProcessor(
        company_siret="12345678900011",
        bs_data_dfs={
            BSDD: sample_data_bsdd,
            BSDA: sample_data_bsda,
            BSDASRI: sample_data_bsdasri,
            BSFF: sample_data_bsff,
        },
        waste_codes_df=sample_waste_codes,
        data_date_interval=data_date_interval,
        packagings_data_df=sample_packagings_data,
    )

    processor._preprocess_data()

    assert processor._check_empty_data() is False

    expected_results = {
        "readable_id": ["bsdd-4", "bsda-3", "bsdasri-3", "bsff-2"],
        "refused_at": [
            "25/04/2024 00:00",
            "04/03/2024 09:00",
            "02/12/2024 12:00",
            "13/02/2024 13:00",
        ],
        "emitter_company_siret": ["PARTICULIER", "77777777700031", "49016873200053", "24358764500022"],
        "recipient_company_siret": ["12345678900011", "12345678900011", "12345678900011", "12345678900011"],
        "waste_code": ["20 01 08*", "18 01 06*", "20 01 27*", "14 06 02*"],
        "waste_name": [
            "Solvant D",
            "Déchets infectieux",
            "peinture, encres, colles et résines contenant des substances dangereuses",
            "autres solvants et mélanges de solvants halogénés",
        ],
        "quantity_emitted": ["40", "200", "245", "80.5"],
        "quantity_refused": ["40", "197", "45", "N/A"],
        "refusal_reason": [
            "Refusal reason 2",
            "Refusal reason 1",
            "Refusal reason 2",
            "Refusal reason 1 | Refusal reason 2",
        ],
    }
    assert_frame_equal(processor.preprocessed_df, pl.DataFrame(data=expected_results))
