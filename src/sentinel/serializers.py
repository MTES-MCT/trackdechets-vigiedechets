from rest_framework import serializers

from .models import NafCode


class NafCodeNestedSerializer(serializers.ModelSerializer):
    """Serializer for nested NAF Code structure."""

    children = serializers.SerializerMethodField()

    class Meta:
        model = NafCode
        fields = ["code", "content", "children"]

    def get_children(self, obj):
        """Get nested children recursively."""
        children_queryset = obj.get_children()
        if children_queryset.exists():
            return NafCodeNestedSerializer(children_queryset, many=True).data
        return []
