from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from maps.permissions import UserIsVerifedPermission

from .models import NafCode
from .serializers import NafCodeNestedSerializer


class ApiNafSearch(APIView):
    """
    API endpoint for searching NAF codes with nested structure.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [UserIsVerifedPermission]

    def get(self, request):
        q = request.GET.get("naf", "").strip()

        if q:
            # Search and get matching codes
            results = NafCode.search(q)
            # Get root nodes from search results or their ancestors
            root_codes = results
        else:
            # Get all root nodes (no parent)
            root_codes = NafCode.objects.all().order_by("code")

        serializer = NafCodeNestedSerializer(root_codes, many=True)

        return Response(
            {
                "data": serializer.data,
            }
        )

    def get_root_nodes_from_results(self, search_results):
        """
        Get root nodes that contain the search results in their tree.
        This ensures we show the complete hierarchy for found items.
        """
        root_ids = set()

        for result in search_results:
            # Get the root of this node
            root = result.get_root()
            root_ids.add(root.id)

        return NafCode.objects.filter(id__in=root_ids).order_by("code")
