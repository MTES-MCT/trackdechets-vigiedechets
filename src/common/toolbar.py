from debug_toolbar.middleware import show_toolbar

from django.urls import resolve

EXEMPTED_DEBUG_TOOLBAR_VIEWS = ["icpe_graph_view", ]


def do_show_toolbar(request):

    return show_toolbar and resolve(request.path).url_name not in EXEMPTED_DEBUG_TOOLBAR_VIEWS
