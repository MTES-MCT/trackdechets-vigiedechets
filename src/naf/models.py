import logging
import uuid

from django.conf import settings
from django.contrib.postgres import search
from django.core.cache import cache
from django.db import models
from pgvector.django import CosineDistance, HnswIndex, VectorField
from sentence_transformers import SentenceTransformer as ST

logger = logging.getLogger(__name__)

# Transformer = ST("Lajavaness/sentence-camembert-large")


class TransformerManager:
    """Singleton pattern for managing the sentence transformer model"""

    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_model(self):
        if self._model is None:
            model_name = getattr(settings, "SEMANTIC_SEARCH_MODEL", "Lajavaness/sentence-camembert-large")
            cache_key = f"transformer_model_{model_name}"

            # Try to get from cache first
            self._model = cache.get(cache_key)
            if self._model is None:
                try:
                    logger.info(f"Loading transformer model: {model_name}")
                    self._model = ST(model_name)
                    # Cache for 1 hour
                    cache.set(cache_key, self._model, 3600)
                except Exception as e:
                    logger.error(f"Failed to load transformer model: {e}")
                    raise
        return self._model


transformer_manager = TransformerManager()


class NafCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10)
    content = models.TextField()
    vector = models.GeneratedField(
        db_persist=True,
        expression=search.SearchVector("content", config="french"),
        output_field=search.SearchVectorField(),
    )
    embedding = VectorField(dimensions=1024, editable=False, null=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        model = transformer_manager.get_model()
        self.embedding = model.encode_document(self.content)
        super().save(force_insert, force_update, using, update_fields)

    @classmethod
    def search(cls, q, dmax=0.5):
        model = transformer_manager.get_model()
        dis = CosineDistance("embedding", model.encode_query(q))
        return cls.objects.alias(distance=dis).filter(distance__lt=dmax).order_by("distance")

    class Meta:
        verbose_name = "Naf code"
        verbose_name_plural = "Naf codes"

        indexes = [
            HnswIndex(
                name="embedding_idxx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            )
        ]
