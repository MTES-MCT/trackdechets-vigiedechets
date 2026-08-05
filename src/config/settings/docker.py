from .dev import *  # noqa

GDAL_LIBRARY_PATH = "/lib/aarch64-linux-gnu/libgdal.so"
GEOS_LIBRARY_PATH = "/lib/aarch64-linux-gnu/libgeos_c.so"

# Fix CSRF trusted origins for Docker
CSRF_TRUSTED_ORIGINS = ["http://localhost:8000", "http://127.0.0.1:8000"]
