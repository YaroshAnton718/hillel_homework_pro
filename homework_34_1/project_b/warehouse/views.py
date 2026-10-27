import logging

from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .cache_utils import get_cached_stock
from .models import Shipment, StockItem
from .permissions import (
    CanCreateShipment,
    CanManageShipments,
    CanManageStock,
    CanViewShipments,
)
from .serializers import (
    ShipmentCreateSerializer,
    ShipmentSerializer,
    ShipmentStatusSerializer,
    StockItemSerializer,
)
from .services import change_status

logger = logging.getLogger('warehouse')


class ActionPermissionMixin:
    """Resolve permissions per action: read, write or an explicit override."""

    read_actions = ('list', 'retrieve')
    read_permissions = [IsAuthenticated]
    write_permissions = [IsAuthenticated, IsAdminUser]
    action_permissions = {}

    def get_permissions(self):
        classes = self.action_permissions.get(self.action)

        if classes is None:
            classes = (
                self.read_permissions
                if self.action in self.read_actions
                else self.write_permissions
            )

        return [permission() for permission in classes]


class WarehouseViewSet(ActionPermissionMixin, viewsets.ModelViewSet):
    """Common base class for all warehouse API viewsets."""

    lookup_value_regex = r'\d+'


class StockItemViewSet(WarehouseViewSet):
    queryset = StockItem.objects.all()
    serializer_class = StockItemSerializer
    lookup_field = 'book_id'
    filterset_fields = ('book_id',)
    write_permissions = [CanManageStock]

    def retrieve(self, request, *args, **kwargs):
        stock = get_cached_stock(kwargs[self.lookup_field])

        return Response(self.get_serializer(stock).data)


class ShipmentViewSet(WarehouseViewSet):
    queryset = Shipment.objects.prefetch_related('items').order_by('-created_at')
    lookup_field = 'order_id'
    filterset_fields = ('status', 'email')
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    read_permissions = [CanViewShipments]
    action_permissions = {
        'create': [CanCreateShipment],
        'partial_update': [CanManageShipments],
    }

    def get_serializer_class(self):
        if self.action == 'create':
            return ShipmentCreateSerializer

        if self.action == 'partial_update':
            return ShipmentStatusSerializer

        return ShipmentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shipment = serializer.save()

        output = ShipmentSerializer(shipment, context=self.get_serializer_context())

        return Response(output.data, status=201 if serializer.created else 200)

    def partial_update(self, request, *args, **kwargs):
        shipment = self.get_object()

        serializer = self.get_serializer(shipment, data=request.data)
        serializer.is_valid(raise_exception=True)

        shipment = change_status(shipment, serializer.validated_data['status'])

        output = ShipmentSerializer(shipment, context=self.get_serializer_context())

        return Response(output.data)