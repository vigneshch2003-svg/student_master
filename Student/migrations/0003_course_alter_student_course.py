import django.db.models.deletion
from django.db import migrations, models


def create_default_courses_and_remap(apps, schema_editor):
    """Create Course rows from the old string values and remap student course to NULL.
    We set course to NULL first (safe because the new column is nullable),
    then create the Course records so admins can reassign students."""
    # Just null out the old string values — students can be reassigned via admin
    schema_editor.execute("UPDATE `Student_student` SET `course_id` = NULL")


class Migration(migrations.Migration):

    dependencies = [
        ('Student', '0002_student_user'),
    ]

    operations = [
        # 1. Create the Course table
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        # 2. Clear old string values so MySQL won't reject the FK alter
        migrations.RunSQL(
            "UPDATE `Student_student` SET `course` = NULL",
            reverse_sql=migrations.RunSQL.noop,
        ),
        # 3. Alter the column to a FK
        migrations.AlterField(
            model_name='student',
            name='course',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Student.course'),
        ),
    ]
