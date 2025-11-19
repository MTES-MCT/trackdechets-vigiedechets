from django import template

register = template.Library()


@register.inclusion_tag("sheets/components/stats_graph.html")
def stats_graph(computed, bsd_type):
    return_dict = {"bsd_type": bsd_type}
    if bsd_type == "bsdd":
        return_dict.update(computed.bsdd_stats_data)
    if bsd_type == "bsdd_non_dangerous":
        return_dict.update(computed.bsdd_non_dangerous_stats_data)
    if bsd_type == "bsda":
        return_dict.update(computed.bsda_stats_data)
    if bsd_type == "bsdasri":
        return_dict.update(computed.bsdasri_stats_data)
    if bsd_type == "bsff":
        return_dict.update(computed.bsff_stats_data)
    if bsd_type == "bsvhu":
        return_dict.update(computed.bsvhu_stats_data)

    return return_dict


@register.inclusion_tag("sheets/components/waste_flows_table.html")
def render_waste_flows_table(computed, graph_context="web"):
    return {
        "waste_flows_data": computed.waste_flows_data,
        "graph_context": graph_context,
    }


@register.inclusion_tag("sheets/components/bsd_canceled_table.html")
def render_bsd_canceled_table(computed, graph_context="web"):
    return {
        "bsd_canceled_data": computed.bsd_canceled_data,
        "company_siret": computed.org_id,
        "graph_context": graph_context,
    }


@register.inclusion_tag("sheets/components/same_emitter_recipient_table.html")
def render_same_emitter_recipient_table(computed, graph_context="web"):
    return {
        "same_emitter_recipient_data": computed.same_emitter_recipient_data,
        "graph_context": graph_context,
    }


@register.inclusion_tag("sheets/components/icpe.html")
def render_icpe(computed, graph_context="web"):
    return {
        "icpe_data": computed.icpe_data,
        "graph_context": graph_context,
    }


@register.inclusion_tag("sheets/components/traceabilty_break.html")
def render_traceabilty_break(computed, graph_context="web"):
    return {
        "traceability_interruptions_data": computed.traceability_interruptions_data,
        "graph_context": graph_context,
    }


@register.inclusion_tag("sheets/components/waste_is_dangerous_statements.html")
def render_waste_is_dangerous_statements(computed, graph_context="web"):
    return {
        "waste_is_dangerous_statements_data": computed.waste_is_dangerous_statements_data,
        "graph_context": graph_context,
    }


@register.inclusion_tag("sheets/components/private_individuals_collections_table.html")
def render_private_individuals_collections_table(computed, graph_context="web"):
    return {
        "private_individuals_collections_data": computed.private_individuals_collections_data,
        "company_siret": computed.org_id,
        "graph_context": graph_context,
    }


@register.inclusion_tag("sheets/components/quantity_outliers_table.html")
def render_quantity_outliers_table(computed, graph_context="web"):
    return {
        "quantity_outliers_data": computed.quantity_outliers_data,
        "company_siret": computed.org_id,
        "graph_context": graph_context,
    }


@register.inclusion_tag("sheets/components/outliers.html")
def render_outliers(computed):
    return {
        "outliers_data": computed.outliers_data,
    }


@register.inclusion_tag("sheets/components/bs_without_icpe_authorization_tables.html")
def render_bs_without_icpe_authorization_tables(computed, graph_context="web"):
    data = computed.bs_processed_without_icpe_authorization
    return {
        "dangerous_data": data.get("dangerous", None),  # Trackdéchets data
        "non_dangerous_data": data.get("non_dangerous", None),  # Non dangerous waste registries data
        "graph_context": graph_context,
    }


@register.inclusion_tag("sheets/components/agreements.html")
def render_agreements(computed):
    return {
        "agreement_data": computed.agreement_data,
    }


@register.inclusion_tag("sheets/components/linked_companies.html")
def render_linked_companies_data(computed, graph_context="web"):
    return {
        "linked_companies_data": computed.linked_companies_data,
        "graph_context": graph_context,
    }


@register.inclusion_tag("sheets/components/bsda_worker_bordereaux_counts_stats.html")
def render_bsda_worker_counts_stats_data(computed, graph_context="web"):
    return {
        "bsda_worker_stats_data": computed.bsda_worker_stats_data,
        "graph_context": graph_context,
    }


@register.inclusion_tag("sheets/components/bsda_worker_bordereaux_durations_stats.html")
def render_bsda_worker_durations_stats_data(computed, graph_context="web"):
    return {
        "bsda_worker_stats_data": computed.bsda_worker_stats_data,
        "graph_context": graph_context,
    }


@register.inclusion_tag("sheets/components/transported_bordereaux_stats.html")
def render_transported_bordereaux_stats_data(computed, graph_context="web"):
    return {
        "transporter_bordereaux_stats_data": computed.transporter_bordereaux_stats_data,
        "graph_context": graph_context,
    }


@register.inclusion_tag("sheets/components/followed_with_pnttd_table.html")
def render_followed_with_pnttd_table(computed, graph_context="web"):
    return {
        "followed_with_pnttd_data": computed.followed_with_pnttd_data,
        "graph_context": graph_context,
    }


@register.inclusion_tag("sheets/components/gistrid_stats_table.html")
def render_gistrid_stats_table(computed, graph_context="web"):
    return {
        "gistrid_stats_data": computed.gistrid_stats_data,
        "graph_context": graph_context,
    }


@register.inclusion_tag("sheets/components/registry_stats.html")
def render_registry_stats(registry_data, graph_context="web"):
    return_dict = {
        "registry_stats_data": registry_data,
        "graph_context": graph_context,
    }

    return return_dict


@register.inclusion_tag("sheets/components/ssd_stats.html")
def render_ssd_stats(ssd_data):
    return_dict = {
        "ssd_stats_data": ssd_data,
    }
    return return_dict


@register.inclusion_tag("sheets/components/ssd_table.html")
def render_ssd_table(computed, graph_context="web"):
    return_dict = {
        "ssd_data": computed.ssd_table_data,
        "graph_context": graph_context,
    }
    return return_dict


@register.inclusion_tag("sheets/components/intermediary_bordereaux_stats.html")
def render_intermediary_bordereaux_stats_data(stats, graph_context="web"):
    return {
        "bordereaux_stats_data": stats,
        "graph_context": graph_context,
    }


@register.inclusion_tag("sheets/components/incinerator_outgoing_waste_table.html")
def render_incinerator_outgoing_waste_table(computed, graph_context="web"):
    dangerous_data = computed.incinerator_outgoing_waste_data.get("dangerous", [])
    non_dangerous_data = computed.incinerator_outgoing_waste_data.get("non_dangerous", [])
    return {
        "dangerous_data": dangerous_data,
        "non_dangerous_data": non_dangerous_data,
        "graph_context": graph_context,
    }
