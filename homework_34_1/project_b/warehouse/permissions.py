from rest_framework.permissions import BasePermission


def has_permission_class(codename):

    class HasPermission(BasePermission):
        def has_permission(self, request, view):
            user = request.user
            return bool(user and user.is_authenticated and user.has_perm(codename))

    HasPermission.__name__ = 'Has_' + codename.replace('.', '_')

    return HasPermission


CanManageStock = has_permission_class('warehouse.manage_stock')
CanManageShipments = has_permission_class('warehouse.manage_shipments')
CanCreateShipment = has_permission_class('warehouse.add_shipment')
CanViewShipments = has_permission_class('warehouse.view_shipment')