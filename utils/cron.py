from shipment.models import Shipment


def archive_shipped_shipments():
    Shipment.objects.filter(is_archived=False, status=5).update(is_archived=True)
