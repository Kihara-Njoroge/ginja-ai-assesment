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

## Step 7: Provision Azure PostgreSQL Flexible Server
Ginja AI relies on PostgreSQL with asynchronous connectivity. You need a dedicated cloud database instance.

```bash
DB_SERVER_NAME="ginja-postgres-server"
DB_ADMIN_USER="ginjaadmin"
DB_ADMIN_PASS="StrongPassword123!"

az postgres flexible-server create \
  --resource-group $RG_NAME \
  --name $DB_SERVER_NAME \
  --location $LOCATION \
  --admin-user $DB_ADMIN_USER \
  --admin-password $DB_ADMIN_PASS \
  --database-name ginja_ai \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --public-access 0.0.0.0 # Warning: In raw production, restrict this to your ACA subnets
```

---

## Step 8: Configure the Database Connection
Your deployed Azure Container App needs to know where this database is located. You must explicitly inject the secure `DATABASE_URL` routing path generated from the previous step.

```bash
DB_ENDPOINT="${DB_SERVER_NAME}.postgres.database.azure.com"
# Construct the asyncpg connection string
DB_URL="postgresql+asyncpg://${DB_ADMIN_USER}:${DB_ADMIN_PASS}@${DB_ENDPOINT}:5432/ginja_ai"

# Inject the environment variable natively into the Azure Container App configurations
az containerapp update \
  --name $APP_NAME \
  --resource-group $RG_NAME \
  --set-env-vars DATABASE_URL="$DB_URL"
```

---

## Step 9: Initialize Database Schema and Data
You do **NOT** need to trigger the migrations or seed script manually!

The deployed Ginja API runtime has been securely updated to leverage an autonomous Docker container `ENTRYPOINT` script (`bin/prestart.sh`).

Whenever Azure spins up a fresh replica, or when the GitHub Actions CI/CD rolls out a fresh deployment, the sequence autonomously triggers:
1. `alembic upgrade head` (Creating required tables mapping)
2. `python bin/seed_data.py` (Seeding the initial test data idempotently)

Once you map the `DATABASE_URL` environment string (from Step 8), the Container App configures itself entirely autonomously. Your platform is 100% live and ready for production API invocations!

---

## GitHub Actions: Final Review
You should ensure you have the following **6 secrets** correctly saved under your remote GitHub repository's `Settings > Secrets and variables > Actions`:
1. `AZURE_RESOURCE_GROUP` (e.g., `devsecops-rg`)
2. `CONTAINER_APP_NAME` (e.g., `ginja-api`)
3. `REGISTRY_LOGIN_SERVER` (e.g., `ginjaaiappregistry.azurecr.io`)
4. `REGISTRY_USERNAME`
5. `REGISTRY_PASSWORD`
6. `AZURE_CREDENTIALS` (The full JSON payload object)

Every time you execute `git push` against the `master` repository, the GitHub Actions runner will handle running testing, tracing, Dockerizing, checking for strict CVEs, and natively updating the container image mapped to your active Azure URL!
