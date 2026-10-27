from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import Shipment, ShipmentItem, StockItem
from .services import create_shipment


class StockItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockItem
        fields = ('id', 'book_id', 'title', 'quantity', 'updated_at')
        read_only_fields = ('id', 'updated_at')


class ShipmentItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentItem
        fields = ('book_id', 'title', 'quantity')
        read_only_fields = fields


class ShipmentSerializer(serializers.ModelSerializer):
    items = ShipmentItemSerializer(many=True, read_only=True)

    class Meta:
        model = Shipment
        fields = (
            'id',
            'order_id',
            'email',
            'status',
            'created_at',
            'updated_at',
            'items',
        )
        read_only_fields = fields


class ShipmentItemInputSerializer(serializers.Serializer):
    book_id = serializers.IntegerField(min_value=1)
    title = serializers.CharField(max_length=255)
    quantity = serializers.IntegerField(min_value=1)


class ShipmentCreateSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)
    email = serializers.EmailField()
    items = ShipmentItemInputSerializer(many=True, allow_empty=False)

    created = False

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError(
                'Список товарів не може бути порожнім.'
            )
        return value

    def create(self, validated_data):
        shipment, self.created = create_shipment(**validated_data)
        return shipment


class ShipmentStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Shipment.STATUS_CHOICES)

    def validate_status(self, value):
        current = self.instance.status

        if value not in Shipment.ALLOWED_TRANSITIONS[current]:
            raise serializers.ValidationError(
                _('Cannot change status from %(old)s to %(new)s.')
                % {'old': current, 'new': value}
            )

        return value