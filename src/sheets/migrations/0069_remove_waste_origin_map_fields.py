from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sheets', '0068_add_eco_organisme_partners_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='computedinspectiondata',
            name='waste_origin_map_data',
        ),
        migrations.RemoveField(
            model_name='computedinspectiondata',
            name='waste_origin_map_graph',
        ),
    ]
