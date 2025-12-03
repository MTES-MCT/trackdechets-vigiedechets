import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from accounts.constants import UserCategoryChoice

from ..factories import (
    AssistancePageFactory,
    ContentBlockFactory,
    FaqPageFactory,
    SuggestedPageFactory,
    WebinarFactory,
)
from ..models import Message

pytestmark = pytest.mark.django_db


# faq views
def test_faq_home_view_deny_anon(anon_client):
    url = reverse("faq_home")
    res = anon_client.get(url)
    assert res.status_code == 302


def test_faq_home_view(verified_user):
    url = reverse("faq_home")

    block = ContentBlockFactory(no_media=True)

    res = verified_user.get(url)
    assert res.status_code == 200
    assert block.page.title in res.content.decode()
    assert f'hx-get="{reverse("faq_page", args=[block.page.pk])}"' in res.content.decode()


def test_faq_home_page_view(verified_user):
    ContentBlockFactory(no_media=True)
    block = ContentBlockFactory(no_media=True)

    url = reverse("faq", args=[block.page.pk])

    res = verified_user.get(url)
    assert res.status_code == 200
    assert block.page.title in res.content.decode()
    assert f'hx-get="{reverse("faq_page", args=[block.page.pk])}"' in res.content.decode()


def test_faq_page_deny_anon(htmx_client, anon_client):
    block = ContentBlockFactory(no_media=True)

    url = reverse("faq_page", args=[block.page.pk])
    hx = htmx_client(anon_client)
    res = hx.get(url)
    assert res.status_code == 302


def test_faq_page_deny_non_htmx_request(verified_user):
    block = ContentBlockFactory(no_media=True)

    url = reverse("faq_page", args=[block.page.pk])

    res = verified_user.get(url)
    assert res.status_code == 404


def test_faq_page_allow_htmx_request(htmx_client, verified_user):
    block = ContentBlockFactory(no_media=True, content="lorem ipsum")
    linked_page = FaqPageFactory()
    SuggestedPageFactory(parent_page=block.page, linked_page=linked_page)
    url = reverse("faq_page", args=[block.page.pk])
    hx = htmx_client(verified_user)
    res = hx.get(url)
    assert res.status_code == 200
    assert "lorem ipsum" in res.content.decode()
    # link to suggested page is displayed
    assert linked_page.title in res.content.decode()


def test_faq_page_only_displays_relevant_suggestions(htmx_client, verified_icpe):
    page = FaqPageFactory(user_categories=[UserCategoryChoice.INSPECTEUR_ICPE])  # not viewable by current user

    block = ContentBlockFactory(no_media=True, content="lorem ipsum", page=page)
    linked_page_icpe = FaqPageFactory(user_categories=[UserCategoryChoice.INSPECTEUR_ICPE])
    linked_page_gendarmerie = FaqPageFactory(user_categories=[UserCategoryChoice.GENDARMERIE])
    SuggestedPageFactory(parent_page=block.page, linked_page=linked_page_icpe)
    SuggestedPageFactory(parent_page=block.page, linked_page=linked_page_gendarmerie)
    url = reverse("faq_page", args=[block.page.pk])
    hx = htmx_client(verified_icpe)
    res = hx.get(url)

    # link to linked_page_icpe page is displayed
    assert linked_page_icpe.title in res.content.decode()
    # link to linked_page_gendarmerie page is not displayed
    assert linked_page_gendarmerie.title not in res.content.decode()


def test_faq_page_deny_user_with_wrong_category(htmx_client, verified_icpe):
    page = FaqPageFactory(user_categories=[UserCategoryChoice.GENDARMERIE])  # not viewable by current user
    block = ContentBlockFactory(no_media=True, content="lorem ipsum", page=page)

    url = reverse("faq_page", args=[block.page.pk])
    hx = htmx_client(verified_icpe)
    res = hx.get(url)
    assert res.status_code == 404


def test_faq_page_allow_user_with_right_category(htmx_client, verified_gendarme):
    page = FaqPageFactory(user_categories=[UserCategoryChoice.GENDARMERIE])  # not viewable by current user
    block = ContentBlockFactory(no_media=True, content="lorem ipsum", page=page)

    url = reverse("faq_page", args=[block.page.pk])
    hx = htmx_client(verified_gendarme)
    res = hx.get(url)
    assert res.status_code == 200


def test_faq_page_search_view_deny_anon(htmx_client, anon_client):
    url = reverse("faq_page_search")

    res = anon_client.get(url)
    assert res.status_code == 404

    hx = htmx_client(anon_client)
    res = hx.get(url)
    assert res.status_code == 302


def test_faq_page_search_view(htmx_client, verified_user):
    page_1 = FaqPageFactory()
    ContentBlockFactory(no_media=True, content="lorem ipsum", page=page_1)
    page_2 = FaqPageFactory()
    ContentBlockFactory(no_media=True, content="truc bidule", page=page_2)

    url = reverse("faq_page_search")

    hx = htmx_client(verified_user)
    res = hx.get(url, data={"q": "bidule"})
    assert res.status_code == 200
    assert '1 résultat pour "bidule"' in res.content.decode()
    assert page_2.title in res.content.decode()
    assert reverse("faq", args=[page_2.pk]) in res.content.decode()


# assistance views
def test_assistance_wrapper_home_view_deny_anon(anon_client):
    url = reverse("assistance_wrapper_home")
    res = anon_client.get(url)
    assert res.status_code == 302


def test_assistance_wrapper_home_view(verified_user):
    url = reverse("assistance_wrapper_home")

    page = AssistancePageFactory()

    res = verified_user.get(url)
    assert res.status_code == 200
    assert f'hx-get="{reverse("assistance_page", args=[page.pk])}"' in res.content.decode()


def test_assistance_wrapper_page_view(verified_user):
    AssistancePageFactory()
    page = AssistancePageFactory()
    url = reverse("assistance_wrapper_page", args=[page.pk])

    res = verified_user.get(url)
    assert res.status_code == 200
    assert f'hx-get="{reverse("assistance_page", args=[page.pk])}"' in res.content.decode()


def test_assistance_page_deny_anon(htmx_client, anon_client):
    page = AssistancePageFactory()
    url = reverse("assistance_page", args=[page.pk])
    res = anon_client.get(url)
    assert res.status_code == 404

    hx = htmx_client(anon_client)
    res = hx.get(url)
    assert res.status_code == 302


def test_assistance_page(htmx_client, verified_user):
    page = AssistancePageFactory()
    sub_page_1 = AssistancePageFactory(parent=page)
    sub_page_2 = AssistancePageFactory(parent=page)
    url = reverse("assistance_page", args=[page.pk])

    res = verified_user.get(url)
    assert res.status_code == 404

    hx = htmx_client(verified_user)
    res = hx.get(url)
    assert res.status_code == 200
    assert page.title in res.content.decode()
    assert page.content in res.content.decode()

    assert sub_page_1.link_anchor in res.content.decode()
    assert sub_page_2.link_anchor in res.content.decode()

    assert "id_assistance_contact_form" not in res.content.decode()


def test_assistance_page_with_form(htmx_client, verified_user):
    page = AssistancePageFactory(with_open_form=True)

    url = reverse("assistance_page", args=[page.pk])

    res = verified_user.get(url)
    assert res.status_code == 404

    hx = htmx_client(verified_user)
    res = hx.get(url)

    assert "id_assistance_contact_form" in res.content.decode()


def test_assistance_contact_deny_anon(htmx_client, anon_client):
    url = reverse("assistance_contact")
    hx = htmx_client(anon_client)
    res = hx.get(url)

    assert res.status_code == 302


def test_assistance_contact_deny_get(htmx_client, verified_user):
    url = reverse("assistance_contact")
    hx = htmx_client(verified_user)
    res = hx.get(url)

    assert res.status_code == 404


def test_assistance_contact_post(mailoutbox, htmx_client, verified_user):
    url = reverse("assistance_contact")
    hx = htmx_client(verified_user)
    res = hx.post(
        url,
        data={"subject": "lorem", "body": "lorem ipsum dolor sit amet", "assistance_page_title": "the page"},
        follow=True,
    )

    assert res.status_code == 200
    assert Message.objects.filter(subject="lorem", user=verified_user.user).exists()

    assert len(mailoutbox) == 1
    m = mailoutbox[0]
    assert m.subject == "lorem"
    assert list(m.to) == [settings.SUPPORT_FORM_RECIPIENT]
    assert res.redirect_chain[-1] == (reverse("assistance_message_sent"), 302)


def test_assistance_message_sent_deny_anon(htmx_client, anon_client):
    url = reverse("assistance_message_sent")

    res = anon_client.get(url)

    assert res.status_code == 404

    hx = htmx_client(anon_client)
    res = hx.get(url)

    assert res.status_code == 302


def test_assistance_message_sent(htmx_client, verified_user):
    url = reverse("assistance_message_sent")

    res = verified_user.get(url)

    assert res.status_code == 404

    hx = htmx_client(verified_user)
    res = hx.get(url)

    assert res.status_code == 200
    assert "Votre demande a été envoyée et sera traitée dans les meilleurs délais" in res.content.decode()


def test_webinar_ics(anon_client):
    webinar = WebinarFactory(
        title="Test Webinar",
        scheduled_at=timezone.now() + timezone.timedelta(days=7),
        duration=60,
        visio_link="https://example.com/visio",
    )
    url = reverse("webinar_ics", args=[webinar.pk])
    res = anon_client.get(url)

    assert res.status_code == 200
    assert res["Content-Type"] == "text/calendar; charset=utf-8"
    assert res["Content-Disposition"] == f"attachment; filename={webinar.slug}.ics"
    assert b"BEGIN:VCALENDAR" in res.content
    assert webinar.title.encode() in res.content
