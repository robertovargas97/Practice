# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2020-04-07 17:02
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('wiretap', '0002_message_interaction_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_id', models.IntegerField(db_index=True)),
                ('mode', models.CharField(blank=True, choices=[('live', 'Live'), ('test', 'Test')], max_length=16, null=True)),
                ('test_request', models.BooleanField(default=False)),
                ('interaction_id', models.CharField(blank=True, db_index=True, max_length=64, null=True)),
                ('interaction_type', models.CharField(blank=True, choices=[('call', 'Call'), ('text', 'Text'), ('web', 'Web')], max_length=32, null=True)),
                ('client_reference_code', models.CharField(blank=True, max_length=128, null=True)),
                ('customer_id', models.CharField(blank=True, db_index=True, max_length=32, null=True)),
                ('processor_result', models.CharField(blank=True, choices=[('approved', 'Approved'), ('review', 'Held For Review'), ('error', 'Error'), ('declined', 'Declined')], db_index=True, max_length=32, null=True)),
                ('processor_transaction_id', models.CharField(blank=True, db_index=True, max_length=128, null=True)),
                ('processor_message', models.TextField(blank=True, null=True)),
                ('processor_request', models.TextField(blank=True, null=True)),
                ('processor_response', models.TextField(blank=True, null=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modified_on', models.DateTimeField(auto_now=True, db_index=True)),
                ('processor', models.CharField(blank=True, choices=[('payrazr', 'Payrazr'), ('payrazr_rest', 'Payrazr REST'), ('convenient_payments', 'Convenient Payments')], db_index=True, max_length=128, null=True)),
                ('account_number', models.CharField(blank=True, db_index=True, max_length=32, null=True)),
                ('invoice_number', models.CharField(blank=True, db_index=True, max_length=32, null=True)),
                ('bill_year', models.CharField(blank=True, db_index=True, max_length=8, null=True)),
                ('date_of_birth', models.DateField(blank=True, db_index=True, max_length=32, null=True)),
                ('zip_code', models.CharField(blank=True, db_index=True, max_length=16, null=True)),
                ('balance_amount', models.DecimalField(blank=True, db_index=True, decimal_places=2, max_digits=10, null=True)),
                ('balance_due_date', models.DateField(blank=True, db_index=True, null=True)),
                ('message', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='lookups', to='wiretap.Message')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['interaction_id', 'interaction_type'], name='lookup_tran_interac_f84156_idx'),
        ),
    ]
