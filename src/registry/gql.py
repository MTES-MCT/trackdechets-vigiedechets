graphql_generate_registry_export = """
  mutation GenerateRegistryV2ExportAsAdmin (
    $registryType: RegistryV2ExportType!
    $siret: String!
    $format: RegistryExportFormat!
    $dateRange: DateFilter!
    $where: RegistryV2ExportWhere
  ) {
    generateRegistryV2ExportAsAdmin(
     registryType: $registryType, 
     format: $format, 
     siret: $siret, 
     dateRange: $dateRange,
     where: $where
    ) {
      id
      status
    }
  }
"""

graphql_read_registry_export = """
query RegistryV2Export($id: ID!)
  {
  registryV2Export(id: $id)
  {
        id
        createdBy {id name}
        status
        format
  }
} 
"""


graphql_registry_V2_export_download_signed_url = """
query RegistryV2ExportDownloadSignedUrl($exportId: String!) {
  registryV2ExportDownloadSignedUrl(exportId: $exportId) {
    signedUrl
  }
}
"""
