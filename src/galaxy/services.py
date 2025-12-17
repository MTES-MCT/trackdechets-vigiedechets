import logging

import polars as pl

from sheets.datawarehouse import get_wh_sqlachemy_engine

logger = logging.getLogger(__name__)


class GalaxyGraphService:
    """
    Service pour construire le graphe des relations entre établissements.
    """

    @staticmethod
    def build_graph(
        siret: str | None = None,
        bsd_types: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        min_weight: int = 1,
    ) -> dict:
        """
        Construit le graphe des relations entre établissements.

        Args:
            siret: SIRET pour filtrer autour d'un établissement (optionnel)
            bsd_types: Liste des types de BSD à inclure (optionnel)
            date_from: Date de début pour filtrer (optionnel)
            date_to: Date de fin pour filtrer (optionnel)
            min_weight: Nombre minimum de BSD en commun pour afficher un lien

        Returns:
            Dict avec 'nodes' et 'edges'
        """
        # Pour simplifier, on commence avec BSDD uniquement
        bsd_types = bsd_types or ["bsdd"]

        # Requête SQL simple pour extraire les relations emitter-destination
        # Version simplifiée - pour production, utiliser des paramètres SQLAlchemy
        conditions = [
            "emitter_company_siret IS NOT NULL",
            "recipient_company_siret IS NOT NULL",
            "emitter_company_siret != ''",
            "recipient_company_siret != ''",
            "NOT is_deleted",
            "status::text NOT IN ('DRAFT', 'INITIAL')",
        ]

        if siret and siret.strip():
            # Validation basique du SIRET (14 chiffres)
            siret_clean = siret.strip()
            logger.info(f"Galaxy filter: SIRET received = '{siret_clean}', length = {len(siret_clean)}, isdigit = {siret_clean.isdigit()}")
            if siret_clean.isdigit() and len(siret_clean) == 14:
                # Filtrer pour ne garder que les relations impliquant ce SIRET
                filter_condition = f"(emitter_company_siret = '{siret_clean}' OR recipient_company_siret = '{siret_clean}')"
                conditions.append(filter_condition)
                logger.info(f"Galaxy filter: Adding SIRET filter condition: {filter_condition}")
            else:
                # SIRET invalide, retourner un graphe vide
                logger.warning("Galaxy filter: Invalid SIRET format, returning empty graph")
                return {"nodes": [], "edges": []}

        if date_from:
            # Validation basique de la date
            if len(date_from) == 10:  # Format YYYY-MM-DD
                conditions.append(f"sent_at >= '{date_from}'")

        if date_to:
            if len(date_to) == 10:
                conditions.append(f"sent_at <= '{date_to}'")

        where_clause = " AND ".join(conditions)

        sql_query = f"""
        SELECT 
            b.emitter_company_siret as source_siret,
            b.recipient_company_siret as target_siret,
            MAX(e.name) as source_name,
            MAX(r.name) as target_name,
            COUNT(*) as weight
        FROM trusted_zone_trackdechets.bsdd b
        LEFT JOIN trusted_zone_trackdechets.company e ON b.emitter_company_siret = e.siret
        LEFT JOIN trusted_zone_trackdechets.company r ON b.recipient_company_siret = r.siret
        WHERE {where_clause}
        GROUP BY b.emitter_company_siret, b.recipient_company_siret
        HAVING COUNT(*) >= {min_weight}
        LIMIT 1000
        """

        logger.info(f"Galaxy query: Executing SQL with {len(conditions)} conditions")
        if siret and siret.strip():
            logger.info(f"Galaxy query: Filtering by SIRET = {siret.strip()}")
        
        # Log de la requête SQL (sans les valeurs sensibles en production)
        logger.debug(f"Galaxy query SQL: {sql_query[:500]}...")  # Limiter la longueur du log

        # Exécuter la requête
        engine = get_wh_sqlachemy_engine()
        df = pl.read_database(sql_query, connection=engine)

        logger.info(f"Galaxy query: Found {len(df)} relations")
        
        # Log des premiers résultats pour déboguer
        if len(df) > 0:
            first_rows = df.head(3)
            logger.debug(f"Galaxy query: First 3 relations: {first_rows.to_dicts()}")

        if df.is_empty():
            return {"nodes": [], "edges": []}

        # Construire les nœuds uniques avec leurs noms
        # Utiliser un dictionnaire pour stocker SIRET -> nom
        siret_to_name: dict[str, str] = {}
        
        for row in df.iter_rows(named=True):
            source_siret = row["source_siret"]
            target_siret = row["target_siret"]
            source_name = row.get("source_name") or ""
            target_name = row.get("target_name") or ""
            
            # Stocker les noms (garder le premier nom non vide trouvé)
            if source_siret and (source_siret not in siret_to_name or not siret_to_name[source_siret]):
                siret_to_name[source_siret] = source_name.strip() if source_name else source_siret
            
            if target_siret and (target_siret not in siret_to_name or not siret_to_name[target_siret]):
                siret_to_name[target_siret] = target_name.strip() if target_name else target_siret

        nodes = []
        for siret_value in sorted(siret_to_name.keys()):
            company_name = siret_to_name[siret_value]
            # Utiliser le nom de l'entreprise si disponible, sinon le SIRET
            label = company_name if company_name else siret_value
            nodes.append(
                {
                    "id": siret_value,
                    "label": label,
                    "size": 10,  # Taille par défaut
                }
            )

        # Construire les edges
        edges = []
        for row in df.iter_rows(named=True):
            edges.append(
                {
                    "source": row["source_siret"],
                    "target": row["target_siret"],
                    "weight": row["weight"],
                    "types": ["bsdd"],
                    "roles": ["emitter->destination"],
                }
            )

        return {"nodes": nodes, "edges": edges}
