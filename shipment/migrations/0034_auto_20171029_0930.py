from __future__ import unicode_literals
from django.db import migrations
import uuid


def gen_uuid(apps, schema_editor):
    MyModel = apps.get_model('shipment', 'Product')
    for row in MyModel.objects.all():
        while True:
            row.uid = uuid.uuid4()
            if not MyModel.objects.filter(uid=row.uid).exists():
                break

        row.save()


class Migration(migrations.Migration):

    dependencies = [
        ('shipment', '0033_product_uid'),
    ]

    operations = [
        migrations.RunPython(gen_uuid, reverse_code=migrations.RunPython.noop),
    ]
