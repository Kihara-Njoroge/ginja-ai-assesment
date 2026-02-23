# Deploying Ginja AI to Azure Container Apps

This guide provides step-by-step instructions on setting up the necessary Azure infrastructure (Azure Container Registry and Azure Container Apps) to deploy the Ginja AI application using the configured GitHub Actions pipeline.

---

## Step 1: Install the Azure CLI
If you haven't already, install the Azure CLI to authenticate and provision resources directly from your terminal.
- Run: `az login` to authenticate via your browser.

---

## Step 2: Create a Resource Group
A Resource Group (RG) acts as a logical container for your Azure services.

```bash
# Variables (You can change "ginja-rg" and "eastus" to your preference)
RG_NAME="devsecops-rg"
LOCATION="eastus"

az group create --name $RG_NAME --location $LOCATION
```
> **Action:** Copy your chosen `$RG_NAME` into your GitHub secrets as `AZURE_RESOURCE_GROUP`.

---

## Step 3: Create an Azure Container Registry (ACR)
This registry securely stores your built Docker images before they are deployed to the Container App. Container registry names must be globally unique.

```bash
# Use a highly unique name with no spaces or dashes
ACR_NAME="ginjaaiappregistry"

az acr create \
  --resource-group $RG_NAME \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true
```

### Get your ACR GitHub Secrets:
Run the following command to retrieve your login credentials:
```bash
az acr credential show --name $ACR_NAME
```

> **Action:** Add the following to your GitHub secrets:
> - `REGISTRY_LOGIN_SERVER`: This is usually `$ACR_NAME.azurecr.io`.
> - `REGISTRY_USERNAME`: Provide the `username` output from the command above.
> - `REGISTRY_PASSWORD`: Provide the `password` output from the command above.

---

## Step 4: Create an Azure Container Apps Environment
Before launching your app, you must create a hosting Environment.

```bash
ENV_NAME="ginja-env"

# Required extension
az extension add --name containerapp --upgrade

az containerapp env create \
  --name $ENV_NAME \
  --resource-group $RG_NAME \
  --location $LOCATION
```

---

## Step 5: Create the Azure Container App
Create the actual Container App using a temporary placeholder image (your GitHub Actions pipeline will instantly replace this image on its first run).

```bash
APP_NAME="ginja-api"

az containerapp create \
  --name $APP_NAME \
  --resource-group $RG_NAME \
  --environment $ENV_NAME \
  --image mcr.microsoft.com/k8se/quickstart:latest \
  --target-port 8000 \
  --ingress external \
  --registry-server ${ACR_NAME}.azurecr.io \
  --registry-username <YOUR_REGISTRY_USERNAME> \
  --registry-password <YOUR_REGISTRY_PASSWORD>
```
> **Action:** Copy your chosen `$APP_NAME` into your GitHub secrets as `CONTAINER_APP_NAME`.

---

## Step 6: Generate Azure Deployment Credentials (`AZURE_CREDENTIALS`)
To allow GitHub Actions to securely log into your Azure account to trigger the deployment, you must create a Service Principal.

1. First, retrieve your Subscription ID:
```bash
SUBSCRIPTION_ID=$(az account show --query id --output tsv)
```

2. Generate the Service Principal RBAC (Role-Based Access Control) credentials:
```bash
az ad sp create-for-rbac \
  --name "github-actions-ginja" \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RG_NAME \
  --json-auth
```


This command will output a JSON object that looks exactly like this:
```json
{
  "clientId": "<GUID>",
  "clientSecret": "<GUID>",
  "subscriptionId": "<GUID>",
  "tenantId": "<GUID>",
  ...
}
```

> **Action:** Copy that **entire JSON output block** and save it as your `AZURE_CREDENTIALS` GitHub Secret.

---

## Final Review
You should now have the following 6 secrets saved under your repository's **Settings > Secrets and variables > Actions**:
1. `AZURE_RESOURCE_GROUP` (e.g., `ginja-rg`)
2. `CONTAINER_APP_NAME` (e.g., `ginja-api`)
3. `REGISTRY_LOGIN_SERVER` (e.g., `ginjaairegistry123.azurecr.io`)
4. `REGISTRY_USERNAME`
5. `REGISTRY_PASSWORD`
6. `AZURE_CREDENTIALS` (The full JSON object)

Once these are set, simply run `git push` to your `main` branch. GitHub Actions will handle testing, tracking, Dockerizing, and natively deploying the new image to your active Azure URL!
