import factory
from factory.django import DjangoModelFactory

from accounts.factories import UserFactory

from .models import RegistryV2Export, RegistryV2ExportSiren, RegistryV2ExportSiret


class RegistryV2ExportFactory(DjangoModelFactory):
    """Factory for the RegistryV2Export model."""

    class Meta:
        model = RegistryV2Export

    siret = factory.Sequence(lambda n: str(n))
    created_by = factory.SubFactory(UserFactory)


class RegistryV2ExportSirenFactory(DjangoModelFactory):
    """Factory for the RegistryV2ExportSiren model."""

    class Meta:
        model = RegistryV2ExportSiren

    siren = factory.Sequence(lambda n: str(n).zfill(9))
    created_by = factory.SubFactory(UserFactory)


class RegistryV2ExportSiretFactory(DjangoModelFactory):
    """Factory for the RegistryV2ExportSiret model."""

    class Meta:
        model = RegistryV2ExportSiret

    parent = factory.SubFactory(RegistryV2ExportSirenFactory)
    siret = factory.Sequence(lambda n: str(n).zfill(14))
