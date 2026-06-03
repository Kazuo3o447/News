// IT News Hub — Azure Infrastructure
// Deploy: az deployment group create --resource-group rg-itnews --template-file main.bicep

param location string = resourceGroup().location
param appName string = 'it-news-hub'
param env string = 'dev'  // dev | prod
param articleRetentionDays int = 7

// --- App Service Plan ---
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: 'asp-${appName}-${env}'
  location: location
  sku: {
    name: env == 'prod' ? 'B2' : 'B1'
    tier: 'Basic'
  }
  properties: {
    reserved: true  // Linux
  }
}

// --- App Service (Backend: FastAPI) ---
resource appService 'Microsoft.Web/sites@2023-01-01' = {
  name: 'app-${appName}-${env}'
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      pythonVersion: '3.12'
      linuxFxVersion: 'PYTHON|3.12'
      appSettings: [
        { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT', value: 'true' }
        { name: 'APP_ENV',                        value: env }
      ]
      minTlsVersion: '1.2'
    }
  }
}

// --- Cosmos DB ---
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-02-15-preview' = {
  name: 'cosmos-${appName}-${env}'
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    capabilities: [{ name: 'EnableServerless' }]
    locations: [{ locationName: location }]
    consistencyPolicy: { defaultConsistencyLevel: 'Session' }
  }
}

resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-02-15-preview' = {
  parent: cosmosAccount
  name: 'newsdb'
  properties: { resource: { id: 'newsdb' } }
}

resource cosmosContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-02-15-preview' = {
  parent: cosmosDb
  name: 'articles'
  properties: {
    resource: {
      id: 'articles'
      partitionKey: { paths: ['/category'], kind: 'Hash' }
      defaultTtl: articleRetentionDays * 86400
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [{ path: '/*' }]
      }
    }
  }
}

// --- Key Vault ---
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'kv-${appName}-${env}'
  location: location
  properties: {
    sku: { family: 'A', name: 'standard' }
    tenantId: subscription().tenantId
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    enableRbacAuthorization: true
  }
}

// --- Application Insights ---
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'ai-${appName}-${env}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    RetentionInDays: 30
  }
}

// --- Static Web App (Frontend) ---
resource staticWebApp 'Microsoft.Web/staticSites@2023-01-01' = {
  name: 'swa-${appName}-${env}'
  location: location
  sku: { name: env == 'prod' ? 'Standard' : 'Free' }
  properties: {}
}

output backendUrl string = 'https://${appService.properties.defaultHostName}'
output frontendUrl string = 'https://${staticWebApp.properties.defaultHostname}'
