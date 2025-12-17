from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from maps.permissions import UserIsVerifedPermission

from .services import GalaxyGraphService


class GalaxyGraphAPI(APIView):
    """
    API endpoint pour récupérer les données du graphe Galaxy.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [UserIsVerifedPermission]

    def get(self, request):
        import logging

        logger = logging.getLogger(__name__)

        siret = request.query_params.get("siret")
        bsd_types = request.query_params.getlist("bsd_types")
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        min_weight = int(request.query_params.get("min_weight", 1))

        logger.info(f"Galaxy API: Request params - siret={siret}, min_weight={min_weight}")

        graph_data = GalaxyGraphService.build_graph(
            siret=siret,
            bsd_types=bsd_types if bsd_types else None,
            date_from=date_from,
            date_to=date_to,
            min_weight=min_weight,
        )

        logger.info(f"Galaxy API: Returning {len(graph_data.get('nodes', []))} nodes and {len(graph_data.get('edges', []))} edges")

        return Response(graph_data)
