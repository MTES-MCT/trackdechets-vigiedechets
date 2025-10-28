import polars as pl
from polars.testing import assert_frame_equal

from sheets.constants import BSDA, BSDASRI, BSDD, BSFF


from ..graph_processors.html_components_processors import (
    BsdRefusedTableProcessor,
)


def test_bsd_refused_processor(
    sample_data_bsdd, sample_data_bsda, sample_data_bsdasri, sample_data_bsff, data_date_interval
):
    processor = BsdRefusedTableProcessor(
        company_siret="12345678900011",
        bs_data_dfs={
            BSDD: sample_data_bsdd,
            BSDA: sample_data_bsda,
            BSDASRI: sample_data_bsdasri,
            BSFF: sample_data_bsff,
        },
        data_date_interval=data_date_interval,
    )

    processor._preprocess_data()

    assert processor._check_empty_data() is False

    expected_results = {
        "id": ["bsdd-4", "bsda-3", "bsdasri-3"],
        "refused_at": ["25/04/2024 00:00", "04/03/2024 09:00", "02/12/2024 12:00"],
        "emitter_company_siret": ["98765432100011", "77777777700031", "49016873200053"],
        "recipient_company_siret": ["12345678900011", "12345678900011", "12345678900011"],
        "waste_code": ["20 01 08*", "18 01 06*", "20 01 27*"],
        "quantity_received": [0.0, 197.0, 200.0],
        "quantity_refused": [40.0, 0.0, 45.0],
        "refusal_reason": ["", "Refusal reason 1", ""],
    }
    assert_frame_equal(
        processor.preprocessed_df,
        pl.DataFrame(data=expected_results),
    )


# TODO: Refactor queries : move them to separate files
# - Add sample for "revised" data sets
# - add missing columns to queries
# - add missing columns to data samples
# - run tests with BSDcanceled
# - Create a conftest for BSDcanceled data sets and BSDRefused so that they can be reused
# - Run test for BSDRefused
