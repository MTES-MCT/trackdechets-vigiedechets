from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sheets", "0070_add_per_bs_type_waste_origin_fields"),
    ]

    operations = [
        # Rename existing fields to new waste type naming
        migrations.RenameField(
            model_name="computedinspectiondata",
            old_name="bsdd_waste_origin_data",
            new_name="dangerous_waste_origin_data",
        ),
        migrations.RenameField(
            model_name="computedinspectiondata",
            old_name="bsdd_waste_origin_graph",
            new_name="dangerous_waste_origin_graph",
        ),
        migrations.RenameField(
            model_name="computedinspectiondata",
            old_name="bsdd_non_dangerous_waste_origin_data",
            new_name="non_dangerous_waste_origin_data",
        ),
        migrations.RenameField(
            model_name="computedinspectiondata",
            old_name="bsdd_non_dangerous_waste_origin_graph",
            new_name="non_dangerous_waste_origin_graph",
        ),
        migrations.RenameField(
            model_name="computedinspectiondata",
            old_name="bsda_waste_origin_data",
            new_name="amiante_waste_origin_data",
        ),
        migrations.RenameField(
            model_name="computedinspectiondata",
            old_name="bsda_waste_origin_graph",
            new_name="amiante_waste_origin_graph",
        ),
        # Remove fields that are no longer needed
        migrations.RemoveField(
            model_name="computedinspectiondata",
            name="bsdasri_waste_origin_data",
        ),
        migrations.RemoveField(
            model_name="computedinspectiondata",
            name="bsdasri_waste_origin_graph",
        ),
        migrations.RemoveField(
            model_name="computedinspectiondata",
            name="bsff_waste_origin_data",
        ),
        migrations.RemoveField(
            model_name="computedinspectiondata",
            name="bsff_waste_origin_graph",
        ),
        migrations.RemoveField(
            model_name="computedinspectiondata",
            name="bsvhu_waste_origin_data",
        ),
        migrations.RemoveField(
            model_name="computedinspectiondata",
            name="bsvhu_waste_origin_graph",
        ),
    ]
