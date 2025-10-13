# Azure CLI Authentication Reference

**Purpose**: Reference for Azure CLI authentication methods and troubleshooting  
**Relevance**: For Newsreel Azure backend deployment and management  
**Source**: Microsoft Azure Documentation

---

## 🔑 KEY INFORMATION

### Important Change (September 2025)

**MFA Requirement**:
- Microsoft will require multifactor authentication (MFA) for Azure CLI
- Applies to Microsoft Entra ID user identities only
- Does NOT affect service principals or managed identities
- **Impact on Newsreel**: Current deployment uses interactive login (user: dave@onethum.com)

**Action Needed Before September 2025**:
- For automation: Migrate to service principal or managed identity
- For manual access: MFA will be required (already using MFA)

---

## 🔐 AUTHENTICATION METHODS

### Interactive Login (Current Method)

**Command**:
```bash
az login
```

**How It Works**:
- Opens browser for authentication
- Supports MFA
- Subscription selector (CLI v2.61.0+)
- Stores refresh token

**Used For**:
- Manual deployment (what we did October 8, 2025)
- Ad-hoc management tasks
- Testing and development

### Login to Specific Tenant

**Command**:
```bash
az login --tenant 850aa381-fbfc-4184-8251-9cc8da42e20f
```

**Newsreel Tenant**:
- Tenant ID: `850aa381-fbfc-4184-8251-9cc8da42e20f`
- Domain: onethum.com
- Display Name: One Thum Software

### Login to Specific Subscription

**Command**:
```bash
az login
az account set --subscription d4abcc64-9e59-4094-8d89-10b5d36b6d4c
```

**Newsreel Subscription**:
- Name: Newsreel Subscription
- ID: `d4abcc64-9e59-4094-8d89-10b5d36b6d4c`

---

## 🔧 SUBSCRIPTION MANAGEMENT

### View All Subscriptions

```bash
az account list --output table
```

### Set Active Subscription

```bash
az account set --subscription "Newsreel Subscription"
# or
az account set --subscription d4abcc64-9e59-4094-8d89-10b5d36b6d4c
```

### Verify Current Subscription

```bash
az account show
```

**Expected for Newsreel**:
```json
{
  "name": "Newsreel Subscription",
  "id": "d4abcc64-9e59-4094-8d89-10b5d36b6d4c",
  "tenantId": "850aa381-fbfc-4184-8251-9cc8da42e20f",
  "state": "Enabled"
}
```

---

## 🛠️ TROUBLESHOOTING

### "Authentication failed against tenant"

**Cause**: User identity belongs to multiple tenants

**Solution**:
```bash
az login --tenant 850aa381-fbfc-4184-8251-9cc8da42e20f
```

### "Interactive authentication is needed"

**Cause**: Using username/password with MFA-enabled account

**Solution**: Use `az login` (browser-based) instead of `--username --password`

### "The connection for this site isn't secure" (Edge browser)

**Solution**: 
1. Visit `edge://net-internals/#hsts` in Microsoft Edge
2. Add "localhost" under "Delete domain security policy"
3. Click Delete

### Clear Subscription Cache

**When to use**: After subscription access changes

```bash
az account clear
az login
```

---

## 🔄 REFRESH TOKENS

### Get Access Token

```bash
# For active subscription
az account get-access-token

# For specific subscription
az account get-access-token --subscription "Newsreel Subscription"
```

### Token Information

**Properties**:
- `accessToken`: JWT token for API calls
- `expires_on`: POSIX timestamp (UTC)
- `expiresOn`: Local datetime (deprecated, use expires_on)
- `tokenType`: "Bearer"

**Recommendation**: Use `expires_on` (UTC) not `expiresOn` (local time issues)

---

## 📋 NEWSREEL-SPECIFIC COMMANDS

### Standard Login Flow

```bash
# 1. Login
az login

# 2. Set Newsreel subscription
az account set --subscription d4abcc64-9e59-4094-8d89-10b5d36b6d4c

# 3. Verify
az account show --query "{name:name, id:id}" -o table
```

### Quick Context Switch

```bash
# From another subscription
az account set --subscription "Newsreel Subscription"

# Verify resources
az resource list --resource-group Newsreel-RG -o table
```

### Logout

```bash
az logout
```

**When to logout**:
- Switching accounts
- Security requirement
- Clearing credentials

---

## 🎓 BEST PRACTICES FOR NEWSREEL

### For Development/Testing (Current)

**Use**: Interactive login (`az login`)
- ✅ Supports MFA
- ✅ Easy for manual operations
- ✅ No credential management
- ✅ Works on macOS

### For CI/CD (Future)

**Use**: Service Principal or Managed Identity
- Required for automation
- No interactive login needed
- Secure credential storage

**Create Service Principal**:
```bash
az ad sp create-for-rbac \
  --name "newsreel-deployment-sp" \
  --role Contributor \
  --scopes /subscriptions/d4abcc64-9e59-4094-8d89-10b5d36b6d4c/resourceGroups/Newsreel-RG
```

---

## ⚠️ IMPORTANT NOTES

### Subscription Selector (CLI v2.61.0+)

**Enabled by default**: You're prompted to select subscription at login

**To disable** (if needed):
```bash
az config set core.login_experience_v2=off
```

**For Newsreel**: Keep enabled (helps select correct subscription)

### Platform-Specific

**macOS** (what we use):
- Browser-based authentication
- Opens default browser for login
- Stores credentials securely
- Works with MFA

**Windows**:
- Uses Web Account Manager (WAM) by default
- Can fall back to browser if needed

---

## 📖 RELEVANT TO NEWSREEL DEPLOYMENT

### What We Used (October 8-9, 2025)

1. ✅ `az login` - Interactive browser auth
2. ✅ `az account set --subscription d4abcc64-9e59-4094-8d89-10b5d36b6d4c`
3. ✅ Various `az` commands for deployment
4. ✅ MFA worked correctly

### Authentication Issues Encountered

**Issue**: Subscription not initially visible
**Solution**: Granted Owner role via Azure Portal, then `az account clear && az login`

**Issue**: Provider registration needed
**Solution**: `az provider register --namespace Microsoft.DocumentDB` (etc.)

---

## 🔒 SECURITY CONSIDERATIONS

### Current Setup

**Account**: dave@onethum.com  
**Role**: Owner (on Newsreel Subscription)  
**MFA**: Enabled ✅  
**Method**: Interactive browser login

**Secure**: ✅ Yes for development/deployment

### For Production/Automation

**Should use**:
- Service Principal with limited scope
- Managed Identity for Functions/Container Apps
- Azure Key Vault for secrets
- Not interactive login

---

## 📝 QUICK REFERENCE

### Common Newsreel Commands

```bash
# Login and set context
az login
az account set --subscription "Newsreel Subscription"

# Verify
az account show

# Deploy function
cd Azure/functions
func azure functionapp publish newsreel-func-51689

# Deploy API
cd Azure/api
az acr build --registry newsreelacr --image newsreel-api:latest .

# Check resources
az resource list --resource-group Newsreel-RG -o table

# Check costs
az consumption usage list --start-date $(date +%Y-%m-01)

# Logout
az logout
```

---

## 🔍 TROUBLESHOOTING CHECKLIST

**If authentication fails**:
1. ✅ Check if logged in: `az account show`
2. ✅ Clear cache: `az account clear && az login`
3. ✅ Verify subscription: `az account list -o table`
4. ✅ Set correct subscription: `az account set --subscription <id>`
5. ✅ Check tenant: Ensure onethum.com tenant selected

**If MFA issues**:
- Use `az login` (browser-based), not username/password
- Ensure MFA codes are accessible
- Try `az login --tenant <tenant-id>` if needed

---

## 📅 FUTURE MIGRATION (Before September 2025)

### For Automated Deployments

**Create GitHub Actions or Azure DevOps pipeline**:
```yaml
# Use service principal for automation
az login --service-principal \
  --username $AZURE_CLIENT_ID \
  --password $AZURE_CLIENT_SECRET \
  --tenant $AZURE_TENANT_ID
```

**Or use Managed Identity** (preferred):
- Assign MI to deployment environment
- No credentials needed
- Most secure

---

## ✅ SAVED FOR FUTURE REFERENCE

This document captures key Azure CLI authentication information relevant to Newsreel deployment and management.

**Last Updated**: October 9, 2025  
**CLI Version Used**: 2.74.0  
**Platform**: macOS (darwin 25.0.0)  
**Account**: dave@onethum.com

---

**For current Newsreel deployment procedures, see**:
- [AZURE_CLOUD_DOCUMENTATION.md](../AZURE_CLOUD_DOCUMENTATION.md) - Main reference
- [Azure/QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick commands

