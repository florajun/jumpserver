# Generated by Django 2.2.10 on 2020-07-21 11:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('orgs', '0003_auto_20190916_1057'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationMember',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('role', models.CharField(choices=[('Admin', 'Administrator'), ('User', 'User'), ('Auditor', 'Auditor')], default='User', max_length=16, verbose_name='Role')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('date_updated', models.DateTimeField(auto_now=True, verbose_name='Date updated')),
                ('created_by', models.CharField(max_length=128, null=True, verbose_name='Created by')),
                ('org', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members_through', to='orgs.Organization', verbose_name='Organization')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='m2m_org_members', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'db_table': 'orgs_organization_members',
                'unique_together': {('org', 'user', 'role')},
            },
        ),
    ]
