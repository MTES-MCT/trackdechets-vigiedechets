from rest_framework import serializers


class NodeSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()
    size = serializers.IntegerField()
    type = serializers.ListField(child=serializers.CharField(), required=False)
    metadata = serializers.DictField(required=False)


class EdgeSerializer(serializers.Serializer):
    source = serializers.CharField()
    target = serializers.CharField()
    weight = serializers.IntegerField()
    types = serializers.ListField(child=serializers.CharField())
    roles = serializers.ListField(child=serializers.CharField())


class GalaxyGraphSerializer(serializers.Serializer):
    nodes = NodeSerializer(many=True)
    edges = EdgeSerializer(many=True)
