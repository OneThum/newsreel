# Push Notification Testing & Verification Guide 🧪

**Status**: Ready to Test  
**Date**: October 13, 2025

---

## ✅ Pre-Test Checklist

### 1. **Xcode Configuration**

**IMPORTANT**: You must manually add Push Notifications capability:

1. Open **Newsreel.xcodeproj** in Xcode
2. Select **Newsreel** target (blue app icon)
3. Go to **Signing & Capabilities** tab
4. Click **+ Capability** button (top left)
5. Search for and add **Push Notifications**
6. Verify it appears in the capabilities list

**Verify Entitlements:**
- ✅ `aps-environment: development` (already set)
- ✅ `com.apple.developer.applesignin` (already set)

### 2. **Firebase Console Verification**

Go to [Firebase Console](https://console.firebase.google.com) → Your Project → Settings → Cloud Messaging:

- ✅ APNs Authentication Key uploaded (.p8 file)
- ✅ Key ID entered
- ✅ Team ID entered
- ✅ iOS app registered (Bundle ID: com.onethum.Newsreel)

### 3. **Backend Configuration**

Check Azure Function App environment variables:

```bash
az functionapp config appsettings list \
  --name newsreel-func-51689 \
  --resource-group Newsreel-RG \
  --query "[?name=='FCM_SERVER_KEY']"
```

Should return your FCM server key.

---

## 🧪 Test 1: Token Registration Flow

### Goal
Verify the app can obtain FCM token and register it with backend.

### Steps

1. **Run the app** on a simulator or device
   ```bash
   # In Xcode, press Cmd+R to run
   ```

2. **Login** to the app

3. **Grant notification permission** when prompted

4. **Check iOS logs** in Xcode Console for:
   ```
   📢 Configuring notification service
   📢 Requesting notification permission
   ✅ Notification permission granted
   📱 APNs device token received
   🔑 FCM token received: abc123...
   📤 Registering FCM token with backend
   ✅ FCM token registered successfully
   ```

### Expected Results
- ✅ Permission dialog appears
- ✅ Token is generated
- ✅ Token is registered with backend (HTTP 200)

### Troubleshooting
- ❌ No permission dialog → Check if already denied in Settings
- ❌ No APNs token → Check Push Notifications capability in Xcode
- ❌ Registration fails → Check backend API is running

---

## 🧪 Test 2: Check Token in Database

### Goal
Verify the token is stored in Cosmos DB.

### Steps

1. **Query Cosmos DB** for your user:
   ```bash
   # Get your Firebase UID from app logs or Firebase Console
   # Then query:
   az cosmosdb sql query \
     --account-name newsreel-cosmos \
     --database-name newsreel-db \
     --container-name user_preferences \
     --query-text "SELECT * FROM c WHERE c.user_id = 'YOUR_FIREBASE_UID'"
   ```

### Expected Results
```json
{
  "id": "prefs_YOUR_FIREBASE_UID",
  "user_id": "YOUR_FIREBASE_UID",
  "fcm_token": "some_long_token...",
  "platform": "ios",
  "app_version": "1.0",
  "notifications_enabled": true,
  "notification_preferences": {
    "breaking_news": true,
    "developing_stories": true,
    "daily_digest": false
  }
}
```

---

## 🧪 Test 3: Manual Test Notification (Firebase Console)

### Goal
Send a test notification directly from Firebase to verify APNs connection.

### Steps

1. Go to **Firebase Console** → **Cloud Messaging**
2. Click **Send your first message**
3. Enter notification details:
   - **Title**: "Test Notification"
   - **Text**: "Testing push notifications for Newsreel"
4. Click **Next**
5. Select **iOS app**
6. Click **Next**
7. Click **Review** and **Publish**

### Expected Results
- ✅ Notification appears on your device/simulator
- ✅ If app is open: Banner appears at top
- ✅ If app is closed: Notification on lock screen

### Troubleshooting
- ❌ No notification received → Check FCM token is valid
- ❌ Error in Firebase → Check APNs key configuration

---

## 🧪 Test 4: Breaking News Notification (End-to-End)

### Goal
Test the complete flow: Backend detects breaking news → Sends notification → User receives it.

### Method A: Create Test Breaking Story in Cosmos DB

1. **Create a breaking story manually**:
   ```bash
   # Use Azure Portal → Cosmos DB → Data Explorer
   # Or use Azure CLI to insert a test story
   ```

2. **Insert into story_clusters**:
   ```json
   {
     "id": "test_breaking_story_123",
     "category": "world",
     "status": "BREAKING",
     "title": "TEST: Breaking News Notification",
     "first_seen": "2025-10-13T05:40:00Z",
     "last_updated": "2025-10-13T05:40:00Z",
     "push_notification_sent": false,
     "source_articles": [
       {
         "source_name": "Test Source",
         "url": "https://example.com/test",
         "published_at": "2025-10-13T05:40:00Z"
       }
     ]
   }
   ```

3. **Wait for next breaking news monitor cycle** (runs every 5 minutes)

4. **Check Azure Function logs**:
   ```bash
   az monitor app-insights query \
     --app YOUR_APP_INSIGHTS_ID \
     --analytics-query "traces | where message contains 'Push notification' | order by timestamp desc | take 10"
   ```

### Method B: Use Existing Breaking Story

Just wait for a real breaking news story to be detected by the system!

### Expected Results

**Backend Logs:**
```
📢 Sending push notification for: test_breaking_story_123 - TEST: Breaking News Notification
📲 Push notification results: 1 success, 0 failure, 1 total users
✅ Status monitor complete: 0 BREAKING→VERIFIED transitions, 1 notifications sent
```

**iOS App:**
- **If closed/background**: Notification on lock screen
- **If open**: Banner at top with "🚨 BREAKING NEWS"

**Tapping notification:**
- App opens (if closed)
- Navigates to Feed tab
- Scrolls to the breaking story

---

## 🧪 Test 5: Notification API Endpoint

### Goal
Test the device token registration API directly.

### Steps

1. **Get your JWT token** from iOS app logs (look for `Authorization: Bearer ...`)

2. **Check notification status**:
   ```bash
   curl -X GET \
     "https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/device-token/status" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

3. **Expected response**:
   ```json
   {
     "notifications_enabled": true,
     "has_token": true,
     "platform": "ios",
     "preferences": {
       "breaking_news": true,
       "developing_stories": true,
       "daily_digest": false
     }
   }
   ```

---

## 🔍 Debugging Commands

### Check Azure Function Logs (Real-Time)
```bash
func azure functionapp logstream newsreel-func-51689
```

### Check Recent Notification Logs
```bash
az monitor app-insights query \
  --app YOUR_APP_INSIGHTS_ID \
  --analytics-query "
    traces 
    | where message contains 'notification' or message contains 'FCM'
    | order by timestamp desc 
    | take 20
  "
```

### Check Breaking Stories in Database
```bash
az cosmosdb sql query \
  --account-name newsreel-cosmos \
  --database-name newsreel-db \
  --container-name story_clusters \
  --query-text "SELECT c.id, c.status, c.title, c.push_notification_sent FROM c WHERE c.status = 'BREAKING'"
```

### Check Registered Device Tokens
```bash
az cosmosdb sql query \
  --account-name newsreel-cosmos \
  --database-name newsreel-db \
  --container-name user_preferences \
  --query-text "SELECT c.user_id, c.platform, c.notifications_enabled FROM c WHERE c.fcm_token != null"
```

---

## 🚨 Common Issues & Solutions

### Issue 1: No Permission Dialog Appears

**Causes:**
- Already denied in iOS Settings
- Push Notifications capability not enabled in Xcode

**Solution:**
1. Go to iOS Settings → Newsreel → Notifications
2. Enable "Allow Notifications"
3. Or: Delete app and reinstall

### Issue 2: Token Registration Fails (500 Error)

**Causes:**
- Backend API not running
- Cosmos DB connection issue
- Invalid JWT token

**Solution:**
1. Check API is running: `curl https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/health`
2. Check Azure Container App logs
3. Verify JWT token is valid (not expired)

### Issue 3: Notification Not Received

**Causes:**
- FCM server key not configured
- APNs authentication key incorrect
- Token not registered

**Solution:**
1. Verify FCM_SERVER_KEY in Azure Function App settings
2. Re-upload APNs key to Firebase Console
3. Check token is in Cosmos DB `user_preferences`

### Issue 4: App Doesn't Navigate to Story

**Causes:**
- Story ID missing from payload
- Story not in current feed

**Solution:**
1. Check notification payload includes `storyId` in data
2. Verify story exists in `story_clusters` container
3. Check iOS logs for "Scrolling to story from notification"

---

## 📊 Success Criteria

### ✅ Complete Success
- [ ] Permission dialog appears on first launch
- [ ] Token is generated and logged
- [ ] Token is registered with backend (visible in Cosmos DB)
- [ ] Test notification from Firebase Console received
- [ ] Breaking news notification received when story is detected
- [ ] Tapping notification navigates to correct story
- [ ] Backend logs show successful FCM delivery

### ⚠️ Partial Success
- [ ] Token registered but notifications not received
  - → Check FCM server key and APNs key
- [ ] Notifications received but no navigation
  - → Check deep linking implementation

### ❌ Failure
- [ ] No permission dialog
  - → Enable Push Notifications capability in Xcode
- [ ] No token generated
  - → Check APNs is properly configured

---

## 🎯 Quick Test (5 Minutes)

**Fastest way to verify everything works:**

1. **Run app** → Login → Grant permission
2. **Check logs** for "✅ FCM token registered successfully"
3. **Send test from Firebase Console** → Verify you receive it
4. **Done!** 🎉

If all three work, your push notification system is fully operational!

---

## 📝 Next Steps After Successful Test

1. ✅ Change `aps-environment` from `development` to `production` in entitlements
2. ✅ Build and submit to TestFlight
3. ✅ Test on physical device with production APNs
4. ✅ Monitor notification delivery rates in Azure Application Insights
5. ✅ Set up alerts for failed notifications

---

**Good luck with testing!** 🚀📲

*If you encounter any issues, check the logs first, then refer to the troubleshooting section above.*

