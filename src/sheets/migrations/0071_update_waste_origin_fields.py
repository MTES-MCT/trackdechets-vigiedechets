from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sheets", "0070_add_per_bs_type_waste_origin_fields"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="computedinspectiondata",
            name="dangerous_waste_origin_data",
        ),
        migrations.RemoveField(
            model_name="computedinspectiondata",
            name="dangerous_waste_origin_graph",
        ),
        migrations.RemoveField(
            model_name="computedinspectiondata",
            name="non_dangerous_waste_origin_data",
        ),
        migrations.RemoveField(
            model_name="computedinspectiondata",
            name="non_dangerous_waste_origin_graph",
        ),
        migrations.RemoveField(
            model_name="computedinspectiondata",
            name="amiante_waste_origin_data",
        ),
        migrations.RemoveField(
            model_name="computedinspectiondata",
            name="amiante_waste_origin_graph",
        ),
        migrations.AddField(
            model_name="computedinspectiondata",
            name="bsdd_waste_origin_data",
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name="computedinspectiondata",
            name="bsdd_waste_origin_graph",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="computedinspectiondata",
            name="bsda_waste_origin_data",
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name="computedinspectiondata",
            name="bsda_waste_origin_graph",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="computedinspectiondata",
            name="texs_waste_origin_data",
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name="computedinspectiondata",
            name="texs_waste_origin_graph",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="computedinspectiondata",
            name="dnd_waste_origin_data",
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name="computedinspectiondata",
            name="dnd_waste_origin_graph",
            field=models.TextField(blank=True),
        ),
    ]
