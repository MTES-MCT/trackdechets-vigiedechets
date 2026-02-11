from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sheets', '0069_remove_waste_origin_map_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='computedinspectiondata',
            name='waste_origin_data',
        ),
        migrations.RemoveField(
            model_name='computedinspectiondata',
            name='waste_origin_graph',
        ),
        migrations.AddField(
            model_name='computedinspectiondata',
            name='bsdd_waste_origin_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='computedinspectiondata',
            name='bsdd_waste_origin_graph',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='computedinspectiondata',
            name='bsdd_non_dangerous_waste_origin_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='computedinspectiondata',
            name='bsdd_non_dangerous_waste_origin_graph',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='computedinspectiondata',
            name='bsda_waste_origin_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='computedinspectiondata',
            name='bsda_waste_origin_graph',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='computedinspectiondata',
            name='bsdasri_waste_origin_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='computedinspectiondata',
            name='bsdasri_waste_origin_graph',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='computedinspectiondata',
            name='bsff_waste_origin_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='computedinspectiondata',
            name='bsff_waste_origin_graph',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='computedinspectiondata',
            name='bsvhu_waste_origin_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='computedinspectiondata',
            name='bsvhu_waste_origin_graph',
            field=models.TextField(blank=True),
        ),
    ]
