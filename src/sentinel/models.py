from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey


class NafCode(MPTTModel):
    code = models.CharField(max_length=10)
    content = models.TextField()
    parent = TreeForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")

    @classmethod
    def search(cls, q):
        content_vector = SearchVector("content", config="french_unaccent")
        code_vector = SearchVector("code")
        query = SearchQuery(q, config="french_unaccent")
        rank = SearchRank(content_vector + code_vector, query)
        return cls.objects.annotate(rank=rank).order_by("-rank").filter(rank__gt=0.05).order_by("code")

    class MPTTMeta:
        order_insertion_by = ["code"]

    class Meta:
        verbose_name = "Naf code"
        verbose_name_plural = "Naf codes"
