import polars as pl
from polars.testing import assert_frame_equal

from sheets.constants import BSDA, BSDASRI, BSDD

from ..graph_processors.html_components_processors import (
    BsdCanceledTableProcessor,
)  # Remplace "your_module" par le bon module


def test_bsd_canceled_processor(
    sample_data_bsdd, sample_data_bsda, sample_data_bsdasri, sample_revised_data, data_date_interval
):
    processor = BsdCanceledTableProcessor(
        company_siret="12345678900011",
        bs_data_dfs={
            BSDD: sample_data_bsdd,
            BSDA: sample_data_bsda,
            BSDASRI: sample_data_bsdasri,
            # BSFF: sample_data_bsff,
            # No cancellation (revised_data) for bsff for in current implementation
        },
        bs_revised_data={
            BSDD: sample_revised_data,
            BSDA: sample_revised_data,
            BSDASRI: sample_revised_data,
            # BSFF: sample_revised_data,
            # No cancellation (revised_data) for bsff for in current implementation
        },
        data_date_interval=data_date_interval,
    )

    processor._preprocess_data()

    assert processor._check_empty_data() is False
    processor.preprocessed_df.to_dict(as_series=False)

    expected_results = [
        {
            "id": "bsdd-1",
            "quantity_received": 9.0,
            "emitter_company_siret": "98765432100022",
            "recipient_company_siret": "12345678900011",
            "waste_code": "20 01 01*",
            "updated_at": "12/01/2024 10:00",
            "comment": None,
            "readable_id": "bsdd-1",
            "waste_name": "Solvant A",
            "quantity_refused": 1.0,
        },
        {
            "id": "bsda-2",
            "quantity_received": None,
            "emitter_company_siret": "66666666600030",
            "recipient_company_siret": "12345678900011",
            "waste_code": "18 01 02",
            "updated_at": "10/02/2024 10:00",
            "comment": "C1",
            "readable_id": "bsda-2",
            "waste_name": "Déchets ménagers",
            "quantity_refused": None,
        },
        {
            "id": "bsdasri-3",
            "quantity_received": 200.0,
            "emitter_company_siret": "49016873200053",
            "recipient_company_siret": "12345678900011",
            "waste_code": "20 01 27*",
            "updated_at": "12/03/2024 11:00",
            "comment": "C2",
            "readable_id": "bsdasri-3",
            "waste_name": None,
            "quantity_refused": 45.0,
        },
    ]

    assert_frame_equal(
        processor.preprocessed_df,
        pl.DataFrame(data=expected_results),
    )

    assert processor.build() == expected_results
