from django.urls import path

from .api import ApiNafSearch
from .views import DepartmentResult, GenerateExcelView, NationalResult, ResultTabs, ResultWrapper, Sentinel

urlpatterns = [
    path("", Sentinel.as_view(), name="sentinel"),
    path("api-naf", ApiNafSearch.as_view(), name="api_naf_search"),
    path("result-wrapper", ResultWrapper.as_view(), name="sentinel_result_wrapper"),
    path("national-result", NationalResult.as_view(), name="sentinel_national_result"),
    path("department-result", DepartmentResult.as_view(), name="sentinel_department_result"),
    path("result-tabs/<str:category>", ResultTabs.as_view(), name="sentinel_result_tabs"),
    path("xls/<str:category>", GenerateExcelView.as_view(), name="sentinel_xls"),
]
