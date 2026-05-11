from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sheets", "0071_update_waste_origin_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="computedinspectiondata",
            name="bsd_auto_approved_revision_data",
            field=models.JSONField(default=list),
        ),
    ]
