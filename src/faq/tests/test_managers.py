import pytest

from accounts.constants import UserCategoryChoice
from accounts.factories import UserFactory

from ..factories import FaqPageFactory
from ..models import FaqPage

pytestmark = pytest.mark.django_db


def test_for_user():
    p1 = FaqPageFactory()
    p2 = FaqPageFactory(user_categories=[UserCategoryChoice.ARS, UserCategoryChoice.ADMINISTRATION_CENTRALE])
    p3 = FaqPageFactory(user_categories=[UserCategoryChoice.GENDARMERIE, UserCategoryChoice.INSPECTION_TRAVAIL])
    p4 = FaqPageFactory(user_categories=[UserCategoryChoice.GENDARMERIE, UserCategoryChoice.DOUANE])

    staff_user = UserFactory(is_staff=True)
    qs = FaqPage.objects.for_user(staff_user)
    assert len(qs) == 4

    ctt_user = UserFactory(user_category=UserCategoryChoice.CTT)
    qs = FaqPage.objects.for_user(ctt_user).values_list("pk", flat=True)
    assert list(qs) == [p1.id]

    admin_centrale_user = UserFactory(user_category=UserCategoryChoice.ADMINISTRATION_CENTRALE)
    qs = FaqPage.objects.for_user(admin_centrale_user).values_list("pk", flat=True)
    assert list(qs) == [p1.id, p2.id]

    gendarmerie_user = UserFactory(user_category=UserCategoryChoice.GENDARMERIE)
    qs = FaqPage.objects.for_user(gendarmerie_user).values_list("pk", flat=True)
    assert list(qs) == [p1.id, p3.id, p4.id]
