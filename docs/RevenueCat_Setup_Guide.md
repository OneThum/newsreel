# RevenueCat Setup Guide for Newsreel

**Last Updated**: October 8, 2025

---

## Overview

RevenueCat simplifies subscription management for Newsreel by handling:
- ✅ Receipt validation (no need for App Store Server API)
- ✅ Webhooks for real-time subscription events
- ✅ Cross-platform subscriber management
- ✅ Analytics and subscriber insights
- ✅ Customer support tools

**Cost**: Free up to $2,500 MRR (~500 subscribers at $4.99/month)

---

## Step 1: Create RevenueCat Account

1. Go to https://app.revenuecat.com/signup
2. Sign up with your One Thum Software email
3. Verify your email
4. Create organization: "One Thum Software"

---

## Step 2: Create Project

1. Click "Create New Project"
2. **Project Name**: Newsreel
3. **Platform**: iOS
4. Click "Create Project"

---

## Step 3: Configure App Store Connect

### Get App Store Connect Credentials

1. Go to App Store Connect: https://appstoreconnect.apple.com/
2. Navigate to **Users and Access**
3. Click **Keys** tab (under Integrations)
4. Click **App Store Connect API** → **Generate Key**
   - **Name**: RevenueCat Integration
   - **Access**: App Manager or Admin
   - Click **Generate**
5. **Download the API Key** (.p8 file) - you can only do this once!
6. Note the **Key ID** and **Issuer ID**

### Add to RevenueCat

1. In RevenueCat, go to **Project Settings** → **App Store Connect**
2. Upload the .p8 file
3. Enter **Key ID**
4. Enter **Issuer ID**
5. Enter your **Bundle ID**: `com.onethum.newsreel`
6. Click **Save**

---

## Step 4: Create Products in App Store Connect

1. Go to App Store Connect → **My Apps** → **Newsreel**
2. Go to **Subscriptions** (under Features)
3. Click **Create Subscription Group**
   - **Group Name**: Newsreel Premium
   - **Reference Name**: newsreel_premium_group
4. Click **Create Subscription**
   - **Product ID**: `com.onethum.newsreel.premium.monthly`
   - **Reference Name**: Premium Monthly
   - **Subscription Duration**: 1 Month
   - **Price**: $4.99 USD
   - **Localization**: Add titles and descriptions
   - **Review Information**: Add screenshots if needed
5. Click **Save**

---

## Step 5: Configure Products in RevenueCat

1. In RevenueCat, go to **Products**
2. Click **Add Product**
   - **Product Identifier**: `com.onethum.newsreel.premium.monthly`
   - **Store**: App Store
   - Click **Add**
3. Product should sync automatically from App Store Connect

---

## Step 6: Create Entitlements

Entitlements represent the access level a user has.

1. In RevenueCat, go to **Entitlements**
2. Click **New Entitlement**
   - **Identifier**: `premium_access`
   - **Description**: Access to premium features
   - Click **Create**

---

## Step 7: Create Offering

Offerings organize which products to show to users.

1. In RevenueCat, go to **Offerings**
2. Click **New Offering**
   - **Identifier**: `default`
   - **Description**: Default premium offering
   - Click **Create**
3. Click **Add Package**
   - **Identifier**: `monthly`
   - **Product**: Select `com.onethum.newsreel.premium.monthly`
   - **Entitlements**: Select `premium_access`
   - Click **Add Package**
4. Set this offering as **Current** (toggle switch)

---

## Step 8: Get API Keys for iOS App

1. In RevenueCat, go to **API Keys** (in Project Settings)
2. Copy the **Public App-Specific API Key** for iOS
3. Store this securely - you'll need it in the iOS app

**Important**: This is a public key safe to include in the app binary.

---

## Step 9: Set Up Webhooks for Backend

1. In RevenueCat, go to **Integrations** → **Webhooks**
2. Click **Add Webhook**
3. **URL**: `https://api.newsreel.app/api/webhooks/revenuecat` (or your Container App URL)
4. **Events**: Select all (or at minimum):
   - `INITIAL_PURCHASE`
   - `RENEWAL`
   - `CANCELLATION`
   - `UNCANCELLATION`
   - `NON_RENEWING_PURCHASE`
   - `EXPIRATION`
   - `BILLING_ISSUE`
5. **Authorization Header**: Generate a secret token
   ```bash
   # Generate webhook secret
   openssl rand -hex 32
   ```
   - Add as: `Authorization: Bearer YOUR_SECRET_TOKEN`
6. Click **Add Webhook**

**Store the webhook secret** in Azure Key Vault:
```bash
az keyvault secret set \
  --vault-name newsreel-prod-kv \
  --name "RevenueCatWebhookSecret" \
  --value "YOUR_SECRET_TOKEN"
```

---

## Step 10: iOS Integration

### Add RevenueCat SDK

Add to your Xcode project using Swift Package Manager:

1. Open Xcode → **File** → **Add Packages**
2. Enter: `https://github.com/RevenueCat/purchases-ios`
3. Select latest version
4. Click **Add Package**

### Initialize SDK

```swift
// NewsreelApp.swift

import SwiftUI
import RevenueCat

@main
struct NewsreelApp: App {
    
    init() {
        // Configure RevenueCat
        Purchases.logLevel = .debug // Remove in production
        Purchases.configure(
            withAPIKey: "appl_YOUR_API_KEY_HERE",
            appUserID: nil // Use Firebase UID later
        )
    }
    
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
```

### Link with Firebase User

```swift
// After Firebase authentication
import FirebaseAuth
import RevenueCat

func setupRevenueCat(firebaseUID: String) {
    Purchases.shared.logIn(firebaseUID) { (customerInfo, created, error) in
        if let error = error {
            print("Error logging in: \(error)")
            return
        }
        
        print("User logged in to RevenueCat")
        // Check subscription status
        checkSubscriptionStatus(customerInfo: customerInfo)
    }
}

func checkSubscriptionStatus(customerInfo: CustomerInfo?) {
    guard let customerInfo = customerInfo else { return }
    
    if customerInfo.entitlements["premium_access"]?.isActive == true {
        // User has premium access
        print("User has premium access")
    } else {
        // User is on free tier
        print("User is on free tier")
    }
}
```

### Implement Purchase Flow

```swift
// SubscriptionViewModel.swift

import RevenueCat
import Combine

class SubscriptionViewModel: ObservableObject {
    @Published var offerings: Offering?
    @Published var isPurchasing = false
    @Published var isPremium = false
    @Published var errorMessage: String?
    
    init() {
        loadOfferings()
        checkSubscriptionStatus()
    }
    
    func loadOfferings() {
        Purchases.shared.getOfferings { (offerings, error) in
            if let error = error {
                self.errorMessage = error.localizedDescription
                return
            }
            
            self.offerings = offerings?.current
        }
    }
    
    func checkSubscriptionStatus() {
        Purchases.shared.getCustomerInfo { (customerInfo, error) in
            if let error = error {
                self.errorMessage = error.localizedDescription
                return
            }
            
            self.isPremium = customerInfo?.entitlements["premium_access"]?.isActive == true
        }
    }
    
    func purchase() {
        guard let package = offerings?.monthly else {
            errorMessage = "No offering available"
            return
        }
        
        isPurchasing = true
        
        Purchases.shared.purchase(package: package) { (transaction, customerInfo, error, userCancelled) in
            self.isPurchasing = false
            
            if userCancelled {
                return
            }
            
            if let error = error {
                self.errorMessage = error.localizedDescription
                return
            }
            
            // Success!
            self.isPremium = customerInfo?.entitlements["premium_access"]?.isActive == true
        }
    }
    
    func restorePurchases() {
        Purchases.shared.restorePurchases { (customerInfo, error) in
            if let error = error {
                self.errorMessage = error.localizedDescription
                return
            }
            
            self.isPremium = customerInfo?.entitlements["premium_access"]?.isActive == true
        }
    }
}
```

---

## Step 11: Backend Webhook Handler

Create Azure Function or API endpoint to handle RevenueCat webhooks:

```python
# api/webhooks/revenuecat.py

from fastapi import APIRouter, Request, HTTPException, Header
import hmac
import hashlib
import os

router = APIRouter()

WEBHOOK_SECRET = os.environ.get("REVENUECAT_WEBHOOK_SECRET")

@router.post("/webhooks/revenuecat")
async def handle_revenuecat_webhook(
    request: Request,
    authorization: str = Header(None)
):
    """
    Handle RevenueCat webhook events
    """
    
    # Verify webhook signature
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    if token != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Parse webhook payload
    payload = await request.json()
    event_type = payload.get("event", {}).get("type")
    
    # Extract user and subscription info
    app_user_id = payload.get("event", {}).get("app_user_id")  # Firebase UID
    product_id = payload.get("event", {}).get("product_id")
    entitlements = payload.get("event", {}).get("entitlement_ids", [])
    
    # Update user profile in Cosmos DB
    from cosmos_db import get_cosmos_client
    
    cosmos_client = get_cosmos_client()
    container = cosmos_client.get_container("newsapp-db", "user_profiles")
    
    try:
        # Get user profile
        profile = container.read_item(item=app_user_id, partition_key=app_user_id)
        
        # Update subscription status based on event type
        if event_type in ["INITIAL_PURCHASE", "RENEWAL", "UNCANCELLATION"]:
            profile["subscription"]["tier"] = "paid"
            profile["subscription"]["product_id"] = product_id
            profile["subscription"]["status"] = "active"
            profile["subscription"]["revenuecat_customer_id"] = payload.get("event", {}).get("id")
            profile["subscription"]["entitlements"] = entitlements
            
        elif event_type == "CANCELLATION":
            profile["subscription"]["status"] = "cancelled"
            profile["subscription"]["will_renew"] = False
            
        elif event_type == "EXPIRATION":
            profile["subscription"]["tier"] = "free"
            profile["subscription"]["status"] = "expired"
            
        elif event_type == "BILLING_ISSUE":
            profile["subscription"]["status"] = "billing_issue"
        
        # Update timestamp
        from datetime import datetime
        profile["subscription"]["last_updated"] = datetime.utcnow().isoformat()
        
        # Save updated profile
        container.upsert_item(profile)
        
        return {"success": True, "event": event_type}
        
    except Exception as e:
        logging.error(f"Error handling webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## Step 12: Testing

### Test Sandbox Purchases

1. In App Store Connect, create a **Sandbox Tester**:
   - Go to **Users and Access** → **Sandbox Testers**
   - Click **+** to add tester
   - Use unique email (e.g., `newsreel-test@onethum.com`)
   - Set region to **United States**

2. On iOS device/simulator:
   - Sign out of App Store (Settings → App Store)
   - Run your app
   - Attempt purchase
   - When prompted, sign in with sandbox tester account

3. Verify in RevenueCat Dashboard:
   - Go to **Customers**
   - Search for test user
   - Verify subscription appears

### Test Webhook Events

1. In RevenueCat Dashboard, go to **Integrations** → **Webhooks**
2. Click **Send Test Event**
3. Select event type
4. Check your backend logs to verify receipt

---

## Step 13: Production Checklist

Before going live:

- [ ] Subscription created in App Store Connect
- [ ] App Store Connect API key configured
- [ ] Products synced to RevenueCat
- [ ] Entitlements configured (`premium_access`)
- [ ] Offering created and set as current
- [ ] Webhook endpoint deployed to production
- [ ] Webhook secret stored in Azure Key Vault
- [ ] iOS app uses production RevenueCat API key
- [ ] Tested sandbox purchases
- [ ] Tested webhook events
- [ ] Remove debug logging (`Purchases.logLevel = .debug`)
- [ ] Privacy policy mentions subscription terms
- [ ] Terms of service include cancellation policy

---

## Monitoring & Analytics

### RevenueCat Dashboard

1. **Overview**: MRR, active subscriptions, churn rate
2. **Charts**: Revenue trends, subscriber growth
3. **Customers**: Individual subscriber details
4. **Products**: Product performance

### Key Metrics to Track

- **MRR (Monthly Recurring Revenue)**: Target >$1k in first month
- **Active Subscriptions**: Track growth rate
- **Churn Rate**: Target <5% monthly
- **Conversion Rate**: % of users who subscribe
- **Revenue per User**: Average lifetime value

---

## Troubleshooting

### Products Not Syncing

1. Verify App Store Connect API key permissions
2. Check bundle ID matches exactly
3. Wait 5-10 minutes for sync
4. Try manual refresh in RevenueCat Products page

### Purchases Not Working

1. Check sandbox tester is signed in
2. Verify product is available in region
3. Check RevenueCat API key is correct
4. Review iOS console logs for errors

### Webhooks Not Received

1. Verify webhook URL is publicly accessible
2. Check authorization header matches
3. Test with "Send Test Event" in dashboard
4. Review Azure Function/Container App logs

---

## Support Resources

- **RevenueCat Docs**: https://docs.revenuecat.com/
- **iOS SDK Reference**: https://sdk.revenuecat.com/ios/
- **Community**: https://community.revenuecat.com/
- **Support**: support@revenuecat.com

---

**Document Owner**: iOS Lead  
**Review Cadence**: After implementation  
**Next Review**: Post-launch

