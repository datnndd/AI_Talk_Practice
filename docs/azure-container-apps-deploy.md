# Deploy to Azure Container Apps

This project deploys as two Azure Container Apps:

- `backend`: FastAPI app on port `8000`
- `frontend`: Nginx static Vite app on port `80`

GitHub Actions builds both images, pushes them to Azure Container Registry, then updates both Container Apps on every push to `main`.

## 1. Prerequisites

Install and log in:

```powershell
az version
az login
az extension add --name containerapp --upgrade
```

Pick a globally unique ACR name:

```powershell
$RESOURCE_GROUP="rg-ai-talk-practice"
$LOCATION="southeastasia"
$ACR_NAME="<unique_acr_name>"
$CONTAINER_ENV="cae-ai-talk-practice"
$BACKEND_APP="ai-talk-backend"
$FRONTEND_APP="ai-talk-frontend"
```

## 2. Create Azure resources

```powershell
az group create --name $RESOURCE_GROUP --location $LOCATION

az acr create `
  --resource-group $RESOURCE_GROUP `
  --name $ACR_NAME `
  --sku Basic `
  --admin-enabled false

az containerapp env create `
  --name $CONTAINER_ENV `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION
```

## 3. Build first images

Build backend first:

```powershell
az acr build `
  --registry $ACR_NAME `
  --image ai-talk-backend:initial `
  ./backend
```

Build placeholder frontend. Rebuild it after backend URL exists:

```powershell
az acr build `
  --registry $ACR_NAME `
  --image ai-talk-frontend:initial `
  --build-arg VITE_API_URL=https://placeholder.example/api `
  ./frontend
```

Get ACR login server:

```powershell
$ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer --output tsv)
```

## 4. Create backend Container App

Create secrets. Replace placeholder values with production values from `backend/.env.example`.

```powershell
az containerapp create `
  --name $BACKEND_APP `
  --resource-group $RESOURCE_GROUP `
  --environment $CONTAINER_ENV `
  --image "$ACR_LOGIN_SERVER/ai-talk-backend:initial" `
  --registry-server $ACR_LOGIN_SERVER `
  --registry-identity system `
  --target-port 8000 `
  --ingress external `
  --min-replicas 1 `
  --max-replicas 3 `
  --secrets `
    database-url="<DATABASE_URL>" `
    jwt-secret-key="<JWT_SECRET_KEY>" `
    dashscope-api-key="<DASHSCOPE_API_KEY>" `
    deepgram-api-key="<DEEPGRAM_API_KEY>" `
    openai-api-key="<OPENAI_API_KEY>" `
  --env-vars `
    DATABASE_URL=secretref:database-url `
    JWT_SECRET_KEY=secretref:jwt-secret-key `
    DASHSCOPE_API_KEY=secretref:dashscope-api-key `
    DEEPGRAM_API_KEY=secretref:deepgram-api-key `
    OPENAI_API_KEY=secretref:openai-api-key `
    ASR_PROVIDER=deepgram `
    LLM_PROVIDER=openai `
    TTS_PROVIDER=dashscope `
    HOST=0.0.0.0 `
    PORT=8000 `
    IS_DEBUG=false `
    FRONTEND_URL=https://placeholder.example `
    CORS_ORIGINS='["https://placeholder.example"]'
```

Get backend URL:

```powershell
$BACKEND_FQDN=$(az containerapp show --name $BACKEND_APP --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn --output tsv)
$BACKEND_URL="https://$BACKEND_FQDN"
Write-Host $BACKEND_URL
```

## 5. Create frontend Container App

Rebuild frontend with real backend API URL:

```powershell
az acr build `
  --registry $ACR_NAME `
  --image ai-talk-frontend:initial `
  --build-arg VITE_API_URL="$BACKEND_URL/api" `
  ./frontend
```

Create frontend app:

```powershell
az containerapp create `
  --name $FRONTEND_APP `
  --resource-group $RESOURCE_GROUP `
  --environment $CONTAINER_ENV `
  --image "$ACR_LOGIN_SERVER/ai-talk-frontend:initial" `
  --registry-server $ACR_LOGIN_SERVER `
  --registry-identity system `
  --target-port 80 `
  --ingress external `
  --min-replicas 1 `
  --max-replicas 3
```

Get frontend URL:

```powershell
$FRONTEND_FQDN=$(az containerapp show --name $FRONTEND_APP --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn --output tsv)
$FRONTEND_URL="https://$FRONTEND_FQDN"
Write-Host $FRONTEND_URL
```

Update backend frontend/CORS values:

```powershell
az containerapp update `
  --name $BACKEND_APP `
  --resource-group $RESOURCE_GROUP `
  --set-env-vars `
    FRONTEND_URL=$FRONTEND_URL `
    CORS_ORIGINS="[\"$FRONTEND_URL\"]"
```

## 6. Configure GitHub Actions OIDC

Create app registration and service principal:

```powershell
$SUBSCRIPTION_ID=$(az account show --query id --output tsv)
$APP_JSON=$(az ad app create --display-name "ai-talk-practice-github-actions" --query "{appId:appId,id:id}" --output json)
$CLIENT_ID=($APP_JSON | ConvertFrom-Json).appId
$APP_OBJECT_ID=($APP_JSON | ConvertFrom-Json).id

az ad sp create --id $CLIENT_ID
```

Create federated credential. Replace owner/repo:

```powershell
$GITHUB_OWNER="<github_owner>"
$GITHUB_REPO="<github_repo>"

$credential = @{
  name = "main-branch"
  issuer = "https://token.actions.githubusercontent.com"
  subject = "repo:$GITHUB_OWNER/$GITHUB_REPO:ref:refs/heads/main"
  audiences = @("api://AzureADTokenExchange")
} | ConvertTo-Json

$credential | Out-File -FilePath github-federated-credential.json -Encoding utf8

az ad app federated-credential create `
  --id $APP_OBJECT_ID `
  --parameters github-federated-credential.json

Remove-Item github-federated-credential.json
```

Assign Azure roles:

```powershell
$ACR_ID=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query id --output tsv)
$RG_ID=$(az group show --name $RESOURCE_GROUP --query id --output tsv)

az role assignment create --assignee $CLIENT_ID --role AcrPush --scope $ACR_ID
az role assignment create --assignee $CLIENT_ID --role Contributor --scope $RG_ID
```

## 7. Add GitHub repository secrets

Add these secrets in GitHub repository settings:

```text
AZURE_CLIENT_ID=<CLIENT_ID>
AZURE_TENANT_ID=<tenant_id_from_az_account_show>
AZURE_SUBSCRIPTION_ID=<subscription_id>
AZURE_RESOURCE_GROUP=rg-ai-talk-practice
AZURE_ACR_NAME=<unique_acr_name>
AZURE_BACKEND_APP_NAME=ai-talk-backend
AZURE_FRONTEND_APP_NAME=ai-talk-frontend
VITE_API_URL=https://<backend-url>/api
```

Keep app runtime secrets in Azure Container Apps, not GitHub Actions.

## 8. Verify deployment

Local Docker checks:

```powershell
docker build -t ai-talk-backend ./backend
docker run --rm -p 8000:8000 --env-file backend/.env ai-talk-backend

docker build --build-arg VITE_API_URL=http://localhost:8000/api -t ai-talk-frontend ./frontend
docker run --rm -p 8080:80 ai-talk-frontend
```

Azure checks:

```powershell
Invoke-RestMethod "$BACKEND_URL/"
Start-Process $FRONTEND_URL
```

CI check:

- Push to `main`.
- Confirm GitHub Actions completes.
- Confirm Container App revisions use image tag matching commit SHA.
