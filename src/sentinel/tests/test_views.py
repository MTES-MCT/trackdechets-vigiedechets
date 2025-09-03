from unittest.mock import patch

import pytest
from django.urls import reverse
from polars import DataFrame

from sentinel.constants import NON_REGISTERED

pytestmark = pytest.mark.django_db


def test_sentinel_anon(anon_client):
    url = reverse("sentinel")
    res = anon_client.get(url)
    assert res.status_code == 302


def test_sentinel_fully_logged(verified_user):
    url = reverse("sentinel")
    res = verified_user.get(url)
    assert res.status_code == 403


def set_allowed(client):
    user = client.user
    user.email = "allowed_for_sentinel@mail.test"  # mail in ALLOWED_USER_FOR_SENTINEL
    user.save()


def test_sentinel_fully_logged_and_allowed(verified_user):
    set_allowed(verified_user)
    url = reverse("sentinel")
    res = verified_user.get(url)
    assert res.status_code == 200


def test_sentinel_result_wrapper_anon(anon_client):
    url = reverse("sentinel_result_wrapper")
    res = anon_client.post(url, data={"selected_naf_code": "98.20Z", "department": "13", "page": 0})
    assert res.status_code == 302


def test_sentinel_result_wrapper_fully_logged(verified_user):
    url = reverse("sentinel_result_wrapper")
    res = verified_user.post(url, data={"selected_naf_code": "98.20Z", "department": "13", "page": 0})
    assert res.status_code == 403


@patch("sentinel.views.get_top_five_waste_code_by_naf")
def test_sentinel_result_wrapper_fully_logged_staff(mock_get_top_five, verified_staff):
    mock_get_top_five.return_value = []
    url = reverse("sentinel_result_wrapper")
    res = verified_staff.post(url, data={"selected_naf_code": "98.20Z", "department": "13", "page": 0})
    assert res.status_code == 200


@patch("sentinel.views.get_top_five_waste_code_by_naf")
def test_sentinel_result_wrapper_fully_logged_and_allowed(mock_get_top_five, verified_user):
    mock_get_top_five.return_value = []
    set_allowed(verified_user)
    url = reverse("sentinel_result_wrapper")
    res = verified_user.post(url, data={"selected_naf_code": "98.20Z", "department": "13", "page": 0})
    assert res.status_code == 200


def test_sentinel_national_result_anon(anon_client):
    url = reverse("sentinel_national_result")
    res = anon_client.post(url, data={"selected_naf_code": "98.20Z", "department": "13", "page": 0})
    assert res.status_code == 302


def test_sentinel_national_result_fully_logged(verified_user):
    url = reverse("sentinel_national_result")
    res = verified_user.post(url, data={"selected_naf_code": "98.20Z", "department": "13", "page": 0})
    assert res.status_code == 403


@patch("sentinel.views.build_national_graph")
@patch("sentinel.views.get_top_five_waste_code_by_naf")
def test_sentinel_national_result_fully_logged_staff(mock_get_top_five, mock_build_national_graph, verified_staff):
    mock_get_top_five.return_value = []
    mock_build_national_graph.return_value = []
    url = reverse("sentinel_national_result")
    res = verified_staff.post(url, data={"selected_naf_code": "98.20Z", "department": "13", "page": 0})
    assert res.status_code == 200


@patch("sentinel.views.build_national_graph")
@patch("sentinel.views.get_top_five_waste_code_by_naf")
def test_sentinel_national_result_fully_logged_and_allowed(
    mock_get_top_five, mock_build_national_graph, verified_user
):
    mock_get_top_five.return_value = []
    mock_build_national_graph.return_value = []
    set_allowed(verified_user)
    url = reverse("sentinel_national_result")
    res = verified_user.post(url, data={"selected_naf_code": "98.20Z", "department": "13", "page": 0})
    assert res.status_code == 200


def test_sentinel_department_result_anon(anon_client):
    url = reverse("sentinel_department_result")
    res = anon_client.post(url, data={"selected_naf_code": "98.20Z", "department": "13", "page": 0})
    assert res.status_code == 302


def test_sentinel_department_result_fully_logged(verified_user):
    url = reverse("sentinel_department_result")
    res = verified_user.post(url, data={"selected_naf_code": "98.20Z", "department": "13", "page": 0})
    assert res.status_code == 403


@patch("sentinel.views.get_no_account_company_count")
@patch("sentinel.views.get_with_account_company_count")
@patch("sentinel.views.get_no_activity_company_count")
@patch("sentinel.views.build_department_graph")
@patch("sentinel.views.get_top_five_waste_code_by_naf")
def test_sentinel_department_result_fully_logged_staff(
    mock_get_top_five,
    mock_build_department_graph,
    mock_get_no_account_company_count,
    mock_get_with_account_company_count,
    mock_get_no_activity_company_count,
    verified_staff,
):
    mock_get_top_five.return_value = []
    mock_build_department_graph.return_value = []
    mock_get_no_account_company_count.return_value = 1
    mock_get_no_activity_company_count.return_value = 1
    mock_get_with_account_company_count.return_value = 1
    url = reverse("sentinel_department_result")
    res = verified_staff.post(url, data={"selected_naf_code": "98.20Z", "department": "13", "page": 0})
    assert res.status_code == 200


@patch("sentinel.views.get_no_account_company_count")
@patch("sentinel.views.get_with_account_company_count")
@patch("sentinel.views.get_no_activity_company_count")
@patch("sentinel.views.build_department_graph")
@patch("sentinel.views.get_top_five_waste_code_by_naf")
def test_sentinel_department_result_fully_logged_and_allowed(
    mock_get_top_five,
    mock_build_department_graph,
    mock_get_no_account_company_count,
    mock_get_with_account_company_count,
    mock_get_no_activity_company_count,
    verified_user,
):
    mock_get_top_five.return_value = []
    mock_build_department_graph.return_value = []
    mock_get_no_account_company_count.return_value = 1
    mock_get_no_activity_company_count.return_value = 1
    mock_get_with_account_company_count.return_value = 1
    set_allowed(verified_user)
    url = reverse("sentinel_department_result")
    res = verified_user.post(url, data={"selected_naf_code": "98.20Z", "department": "13", "page": 0})
    assert res.status_code == 200


def test_sentinel_result_tabs_anon(anon_client):
    url = reverse("sentinel_result_tabs", args=[NON_REGISTERED])
    res = anon_client.post(url, data={"selected_naf_code": "98.20Z", "department": "13", "page": 0})
    assert res.status_code == 302


def test_sentinel_result_tabs_fully_logged(verified_user):
    url = reverse("sentinel_result_tabs", args=[NON_REGISTERED])
    res = verified_user.post(url, data={"selected_naf_code": "98.20Z", "department": "13", "page": 0})
    assert res.status_code == 403


@patch("sentinel.views.get_company_not_on_td_list")
@patch("sentinel.views.get_abnormal_company_count")
@patch("sentinel.views.get_no_activity_company_count")
@patch("sentinel.views.get_no_account_company_count")
@patch("sentinel.views.get_top_five_waste_code_by_naf")
def test_sentinel_result_tabs_fully_logged_staff(
    mock_get_top_five,
    mock_get_no_account_company_count,
    mock_get_no_activity_company_count,
    mock_get_abnormal_company_count,
    mock_get_company_not_on_td_list,
    verified_staff,
):
    mock_get_top_five.return_value = []
    mock_get_no_account_company_count.return_value = 1
    mock_get_no_activity_company_count.return_value = 1
    mock_get_abnormal_company_count.return_value = 1
    mock_get_company_not_on_td_list.return_value = DataFrame()
    url = reverse("sentinel_result_tabs", args=[NON_REGISTERED])
    res = verified_staff.post(url, data={"selected_naf_code": "98.20Z", "department": "13", "page": 0})
    assert res.status_code == 200


@patch("sentinel.views.get_company_not_on_td_list")
@patch("sentinel.views.get_abnormal_company_count")
@patch("sentinel.views.get_no_activity_company_count")
@patch("sentinel.views.get_no_account_company_count")
@patch("sentinel.views.get_top_five_waste_code_by_naf")
def test_sentinel_result_tabs_fully_logged_and_allowed(
    mock_get_top_five,
    mock_get_no_account_company_count,
    mock_get_no_activity_company_count,
    mock_get_abnormal_company_count,
    mock_get_company_not_on_td_list,
    verified_user,
):
    mock_get_top_five.return_value = []
    mock_get_no_account_company_count.return_value = 1
    mock_get_no_activity_company_count.return_value = 1
    mock_get_abnormal_company_count.return_value = 1
    mock_get_company_not_on_td_list.return_value = DataFrame()
    set_allowed(verified_user)
    url = reverse("sentinel_result_tabs", args=[NON_REGISTERED])
    res = verified_user.post(url, data={"selected_naf_code": "98.20Z", "department": "13", "page": 0})
    assert res.status_code == 200


def test_sentinel_xls_anon(anon_client):
    url = reverse("sentinel_xls", args=[NON_REGISTERED])
    res = anon_client.post(url, data={"selected_naf_code": "98.20Z", "department": "13"})
    assert res.status_code == 302


def test_sentinel_xls_fully_logged(verified_user):
    url = reverse("sentinel_xls", args=[NON_REGISTERED])
    res = verified_user.post(url, data={"selected_naf_code": "98.20Z", "department": "13"})
    assert res.status_code == 403


@patch("sentinel.views.get_company_not_on_td_list")
@patch("sentinel.views.get_abnormal_company_count")
@patch("sentinel.views.get_no_activity_company_count")
@patch("sentinel.views.get_no_account_company_count")
@patch("sentinel.views.get_top_five_waste_code_by_naf")
def test_sentinel_xls_fully_logged_staff(
    mock_get_top_five,
    mock_get_no_account_company_count,
    mock_get_no_activity_company_count,
    mock_get_abnormal_company_count,
    mock_get_company_not_on_td_list,
    verified_staff,
):
    mock_get_top_five.return_value = []
    mock_get_no_account_company_count.return_value = 1
    mock_get_no_activity_company_count.return_value = 1
    mock_get_abnormal_company_count.return_value = 1
    mock_get_company_not_on_td_list.return_value = DataFrame()
    url = reverse("sentinel_xls", args=[NON_REGISTERED])
    res = verified_staff.post(url, data={"selected_naf_code": "98.20Z", "department": "13"})
    assert res.status_code == 200


@patch("sentinel.views.get_company_not_on_td_list")
@patch("sentinel.views.get_abnormal_company_count")
@patch("sentinel.views.get_no_activity_company_count")
@patch("sentinel.views.get_no_account_company_count")
@patch("sentinel.views.get_top_five_waste_code_by_naf")
def test_sentinel_xls_fully_logged_and_allowed(
    mock_get_top_five,
    mock_get_no_account_company_count,
    mock_get_no_activity_company_count,
    mock_get_abnormal_company_count,
    mock_get_company_not_on_td_list,
    verified_user,
):
    mock_get_top_five.return_value = []
    mock_get_no_account_company_count.return_value = 1
    mock_get_no_activity_company_count.return_value = 1
    mock_get_abnormal_company_count.return_value = 1
    mock_get_company_not_on_td_list.return_value = DataFrame()
    set_allowed(verified_user)
    url = reverse("sentinel_xls", args=[NON_REGISTERED])
    res = verified_user.post(url, data={"selected_naf_code": "98.20Z", "department": "13"})
    assert res.status_code == 200
