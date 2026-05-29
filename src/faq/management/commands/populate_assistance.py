import datetime as dt
import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from ...models import AssistancePage, ContentBlock, FaqPage, SuggestedPage, Webinar

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Remplit la base de données avec des fausses données pour l'assistance, la FAQ et les webinaires."

    def handle(self, *args, **options):
        try:
            self.stdout.write("🧹 Nettoyage des anciennes données...")
            AssistancePage.objects.all().delete()
            FaqPage.objects.all().delete()
            Webinar.objects.all().delete()

            # --- ÉTAPE 1 : Création des pages d'assistance ---
            self.stdout.write("🛠️ Création des pages d'assistance...")

            assistance_root = AssistancePage.objects.create(
                title="Accueil de l'Assistance",
                link_anchor="Accueil Assistance",
                content="<h2>Besoin d'aide ?</h2><p>Bienvenue sur notre centre d'assistance. Choisissez une catégorie ci-dessous.</p>",
                display_contact_form="NO",
            )

            AssistancePage.objects.create(
                title="Signaler un bug technique",
                parent=assistance_root,
                link_anchor="Bug Technique",
                content="<p>Si vous rencontrez une erreur sur la plateforme, merci de nous la détailler via le formulaire ci-dessous.</p>",
                display_contact_form="OPEN",
            )

            AssistancePage.objects.create(
                title="Demande de partenariat",
                parent=assistance_root,
                content="<p>Les demandes de partenariat sont actuellement fermées pour la période estivale.</p>",
                display_contact_form="CLOSED",
            )

            # --- ÉTAPE 2 : Création de la FAQ ---
            self.stdout.write("📚 Création des pages de FAQ...")

            faq_root = FaqPage.objects.create(title="FAQ Générale", position=1)

            faq_child_1 = FaqPage.objects.create(
                title="Comment réinitialiser mon mot de passe ?", parent=faq_root, position=1
            )

            faq_child_2 = FaqPage.objects.create(title="Où trouver mes bordereaux ?", parent=faq_root, position=2)

            ContentBlock.objects.create(
                page=faq_child_1,
                order=1,
                content="<p>Pour réinitialiser votre mot de passe, cliquez sur 'Mot de passe oublié' sur la page de connexion. Si le problème persiste, contactez notre #ASSISTANCE.</p>",
            )

            ContentBlock.objects.create(
                page=faq_child_2,
                order=1,
                content="<p>Vos bordereaux se trouvent dans l'onglet <strong>Mes Documents</strong>.</p>",
            )

            SuggestedPage.objects.create(parent_page=faq_child_1, linked_page=faq_child_2, order=1)

            # --- ÉTAPE 3 : Création des webinaires ---
            self.stdout.write("🎥 Création des webinaires...")

            now = timezone.now()

            Webinar.objects.create(
                title="Webinaire de découverte de la plateforme",
                scheduled_at=now + dt.timedelta(days=10),
                duration=60,
                display_days_before=30,
                visio_link="https://meet.jit.si/webinaire-demo-123",
            )

            Webinar.objects.create(
                title="Nouveautés de la version 2.0",
                scheduled_at=now - dt.timedelta(days=5),
                duration=90,
                display_days_before=30,
                visio_link="https://meet.jit.si/webinaire-v2",
            )

            Webinar.objects.create(
                title="Point de fin d'année",
                scheduled_at=now + dt.timedelta(days=60),
                duration=120,
                display_days_before=15,
                visio_link="https://meet.jit.si/webinaire-fin-annee",
            )

            self.stdout.write(self.style.SUCCESS("✅ Base de données peuplée avec succès !"))

        except Exception as e:
            logger.error(f"Erreur lors du peuplement de l'assistance : {e}")
            self.stdout.write(self.style.ERROR(f"❌ Une erreur est survenue : {e}"))
