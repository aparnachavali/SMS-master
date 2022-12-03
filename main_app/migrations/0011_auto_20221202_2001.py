# Generated by Django 3.2.13 on 2022-12-03 02:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0010_remove_sectiontimeslot_unique_timeslot'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='sectionstudents',
            name='unique_section_students',
        ),
        migrations.AddConstraint(
            model_name='sectiontimeslot',
            constraint=models.UniqueConstraint(fields=('section', 'timeslot', 'day'), name='unique_timeslot'),
        ),
    ]