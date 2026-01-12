# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maps', '0006_remove_cartocompany_maps_cartoc_process_d1e834_gin_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartocompany',
            name='is_dormant',
            field=models.BooleanField(db_index=True, null=True, blank=True),
        ),
    ]
