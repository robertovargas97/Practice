# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-10-27 21:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments_api', '0004_remove_transaction_currency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='ach_account_type',
            field=models.CharField(blank=True, choices=[('savings', 'Savings'), ('checking', 'Checking'), ('commercial', 'Commercial'), ('individual', 'Individual'), ('company', 'Company')], db_index=True, max_length=32, null=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='card_type',
            field=models.CharField(blank=True, choices=[('visa', 'Visa'), ('mastercard', 'MasterCard'), ('american_express', 'American Express'), ('discover', 'Discover'), ('jcb', 'JCB'), ('amex', 'Amex'), ('diners club', 'Diners Club')], db_index=True, max_length=32, null=True),
        ),
    ]
