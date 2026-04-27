# Generated manually

import datetime
import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import registry.models
from registry.constants import RegistryV2WasteCode


class Migration(migrations.Migration):

    dependencies = [
        ('registry', '0005_alter_registryv2export_registry_type'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RegistryV2ExportSiren',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('siren', models.CharField(db_index=True, max_length=9, verbose_name='SIREN')),
                ('registry_type', models.CharField(choices=[('INCOMING', 'Registre entrant'), ('MANAGED', 'Registre des courtiers/négociants'), ('OUTGOING', 'Registre sortant'), ('SSD', 'Registre Sortie de statut de déchet'), ('TRANSPORTED', 'Registre des transporteurs')], default='INCOMING', max_length=20, verbose_name='Type de registre')),
                ('declaration_type', models.CharField(choices=[('ALL', 'Tous'), ('BSD', 'Tracé (bordereaux)'), ('REGISTRY', 'Déclaré (registre national)')], default='ALL', max_length=20, verbose_name='Type de déclaration')),
                ('waste_types_dnd', models.BooleanField(blank=True, default=False, verbose_name='Déchets non dangereux')),
                ('waste_types_dd', models.BooleanField(blank=True, default=False, verbose_name='Déchets dangereux')),
                ('waste_types_texs', models.BooleanField(blank=True, default=False, verbose_name='Terres et sédiments')),
                ('waste_codes', registry.models.ChoiceArrayField(base_field=models.CharField(blank=True, choices=RegistryV2WasteCode.choices, max_length=32), blank=True, default=list, size=None, verbose_name='Codes déchets')),
                ('start_date', models.DateTimeField(default=datetime.datetime(2022, 1, 1, 0, 0), verbose_name='Data Start Date')),
                ('end_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='End Date')),
                ('export_format', models.CharField(choices=[('CSV', 'Texte (.csv)'), ('XLSX', 'Excel (.xlsx)')], default='CSV', max_length=20, verbose_name="Format d'export")),
                ('state', models.CharField(choices=[('PENDING', 'En attente'), ('STARTED', 'En cours'), ('SUCCESSFUL', 'Terminé'), ('FAILED', 'Erreur'), ('CANCELED', 'Annulé')], default='PENDING', max_length=20, verbose_name='State')),
                ('total_sirets', models.IntegerField(default=0, verbose_name='Total SIRETs')),
                ('completed_sirets', models.IntegerField(default=0, verbose_name='Completed SIRETs')),
                ('failed_sirets', models.IntegerField(default=0, verbose_name='Failed SIRETs')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Created')),
                ('created_by_email', models.EmailField(blank=True, max_length=254, verbose_name='Created by email')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Created by')),
            ],
            options={
                'verbose_name': 'Téléchargement de registre V2 (SIREN)',
                'verbose_name_plural': 'Téléchargements de registre V2 (SIREN)',
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='RegistryV2ExportSiret',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('siret', models.CharField(db_index=True, max_length=14, verbose_name='SIRET')),
                ('state', models.CharField(choices=[('PENDING', 'En attente'), ('STARTED', 'En cours'), ('SUCCESSFUL', 'Terminé'), ('FAILED', 'Erreur'), ('CANCELED', 'Annulé')], default='PENDING', max_length=20, verbose_name='State')),
                ('registry_export_id', models.CharField(blank=True, verbose_name='Trackdéchets Export id')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Created')),
                ('parent', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name='siret_exports', to='registry.registryv2exportsiren', verbose_name='Parent')),
            ],
            options={
                'verbose_name': 'Export SIRET (enfant)',
                'verbose_name_plural': 'Exports SIRET (enfants)',
                'ordering': ('siret',),
            },
        ),
        migrations.AddIndex(
            model_name='registryv2exportsiren',
            index=models.Index(fields=['siren'], name='registry_re_siren_abc123_idx'),
        ),
        migrations.AddIndex(
            model_name='registryv2exportsiren',
            index=models.Index(fields=['state'], name='registry_re_state_def456_idx'),
        ),
        migrations.AddIndex(
            model_name='registryv2exportsiret',
            index=models.Index(fields=['parent', 'state'], name='registry_re_parent__ghi789_idx'),
        ),
        migrations.AddIndex(
            model_name='registryv2exportsiret',
            index=models.Index(fields=['siret'], name='registry_re_siret_jkl012_idx'),
        ),
    ]
