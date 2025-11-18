import datetime as dt
import logging

from config.celery_app import app

from .rendering_helpers import prepare_sheet_fn, render_pdf_fn, render_pdf_graph_fn

logger = logging.getLogger(__name__)


@app.task()
def render_indiv_graph(computed_pk, name):
    render_pdf_graph_fn(computed_pk, name)
    return True


@app.task()
def prepare_sheet(computed_pk):
    """
    Pollable task to prepare html view.

    :param computed_pk: ComputedInspectionData pk
    """
    return prepare_sheet_fn(computed_pk)


@app.task()
def render_pdf(computed_pk: str):
    return render_pdf_fn(computed_pk, render_indiv_graph)


@app.task
def create_dummy_file():
    fn = f"celerytest_{dt.datetime.now()}.txt"

    with open(fn, "w") as f:
        print(f"Create file: {fn}")
        f.write("test")
