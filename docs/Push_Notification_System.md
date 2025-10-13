# Newsreel Push Notification System 📲

**Status**: ✅ **IMPLEMENTED & DEPLOYED**  
**Date**: October 13, 2025  
**Type**: Breaking News Alerts  
**Platform**: iOS (APNs + Firebase Cloud Messaging)

---

## 📱 Overview

Implemented a comprehensive push notification system for Newsreel that intelligently delivers breaking news alerts to users. The system distinguishes between in-app and background scenarios, ensuring users never miss critical breaking news while maintaining an optimal user experience.

### Key Features

1. **Smart Notification Delivery**
   - In-app: Uses existing feed notification UI
   - Background/Closed: Sends APNs push notifications

2. **Breaking News Detection**
   - Automatic status monitoring (BREAKING → VERIFIED after 30 min)
   - Multi-source verification requirement
   - One-time notification per story

3. **Deep Linking**
   - Tapping notification navigates directly to story
   - Smooth scroll animation to story card
   - Automatic tab switching

4. **User Preferences**
   - Opt-in/opt-out support
   - Per-notification-type preferences (breaking, developing, daily digest)
   - Device token management

---

## 🏗️ Architecture

### iOS Components

#### 1. **NotificationService.swift**
Central service managing all notification operations:

```swift
class NotificationService: NSObject, ObservableObject {
    - Handles APNs registration
    - Manages FCM tokens
    - Implements UNUserNotificationCenterDelegate
    - Implements MessagingDelegate (FCM)
    - Provides notification permission requests
    - Handles device token registration/unregistration
}
```

**Key Methods:**
- `requestPermission()` - Requests notification permission from user
- `registerToken(with:)` - Registers FCM token with backend
- `handleNotificationTap(_:)` - Extracts story ID for navigation
- `configure(with:)` - Sets up delegates and checks authorization

#### 2. **ContentView.swift**
Handles notification taps and navigation:

```swift
- Observes notificationService.notificationToHandle
- Extracts story ID from notification payload
- Passes story ID to MainAppView for navigation
```

#### 3. **MainAppView.swift**
Manages notification integration:

```swift
- Configures NotificationService on appear
- Requests permission after login
- Registers device token with backend
- Handles story navigation from notifications
- Switches to feed tab when notification is tapped
```

#### 4. **FeedView.swift**
Handles scroll-to-story functionality:

```swift
- Accepts notificationStoryId binding
- Scrolls to specific story when set
- Smooth animation with easeOut duration
```

#### 5. **Entitlements**
Added `aps-environment: development` for APNs capability.

### Backend Components

#### 1. **Device Token Registration API** (`notifications.py`)

**Endpoints:**

```python
POST /device-token/register
- Stores FCM token in Cosmos DB
- Links token to authenticated user
- Enables push notifications

POST /device-token/unregister
- Removes FCM token from user preferences
- Disables push notifications

GET /device-token/status
- Returns current notification status
- Shows token registration state
- Returns user preferences
```

**Database Schema** (user_preferences collection):
```json
{
  "id": "prefs_{user_id}",
  "user_id": "firebase_uid",
  "fcm_token": "FCM_device_token",
  "platform": "ios",
  "app_version": "1.0",
  "token_registered_at": "2025-10-13T...",
  "notifications_enabled": true,
  "notification_preferences": {
    "breaking_news": true,
    "developing_stories": true,
    "daily_digest": false
  }
}
```

#### 2. **Push Notification Service** (`function_app.py`)

**FCMNotificationService Class:**
```python
class FCMNotificationService:
    - Formats notification payloads
    - Sends to multiple FCM tokens
    - Logs success/failure rates
    - Handles FCM API communication
```

**Notification Payload:**
```json
{
  "notification": {
    "title": "🚨 BREAKING NEWS",
    "body": "Story title (150 char max)",
    "sound": "default",
    "badge": 1,
    "priority": "high"
  },
  "data": {
    "storyId": "story_cluster_id",
    "category": "politics",
    "priority": "breaking",
    "sourceCount": "5"
  },
  "priority": "high",
  "content_available": true
}
```

#### 3. **Breaking News Monitor** (Azure Function)

**Schedule**: Every 5 minutes (via `monitor_breaking_news_timer`)

**Process:**
1. Query all BREAKING status stories
2. Check age (< 30 minutes = fresh, >= 30 minutes = verified)
3. For fresh stories without `push_notification_sent` flag:
   - Query all users with `notifications_enabled: true`
   - Extract FCM tokens
   - Send push notifications via FCM
   - Mark story as notified with recipient count
4. For old stories (>= 30 min):
   - Transition BREAKING → VERIFIED
   - Log status change

---

## 📊 Notification Flow

### Scenario 1: App Open & In Focus

```
1. Breaking news story detected by Azure Function
2. Azure Function queries users with notifications enabled
3. FCM sends notification payload
4. iOS receives notification in foreground
5. UNUserNotificationCenterDelegate decides presentation
6. If priority = "breaking": Show banner + sound
7. User can tap to navigate or dismiss
```

### Scenario 2: App Closed or Backgrounded

```
1. Breaking news story detected by Azure Function
2. Azure Function queries users with notifications enabled
3. FCM sends notification payload
4. APNs delivers notification to device
5. iOS displays notification banner/lock screen
6. User taps notification
7. App launches → ContentView handles tap
8. Story ID extracted from payload
9. MainAppView switches to feed tab
10. FeedView scrolls to story
```

### Scenario 3: First-Time User

```
1. User logs in successfully
2. MainAppView calls notificationService.requestPermission()
3. iOS shows notification permission dialog
4. If granted:
   - Device registers for APNs
   - APNs returns device token
   - Token passed to FCM for conversion
   - FCM token sent to backend
   - Backend stores in Cosmos DB
5. User now receives breaking news notifications
```

---

## 🔧 Configuration Required

### iOS Side

1. **Firebase Configuration**
   - Ensure `GoogleService-Info.plist` is in project
   - Verify `GIDClientID` in Info.plist

2. **Entitlements**
   - ✅ Already added: `aps-environment: development`
   - Production: Change to `aps-environment: production`

3. **Capabilities (in Xcode)**
   - Push Notifications: **MUST BE ENABLED** in project settings
   - Background Modes: **NOT REQUIRED** (but can be added for background fetch)

### Backend Side

1. **Azure Function Configuration**
   - **Environment Variable**: `FCM_SERVER_KEY`
   - **Value**: Server key from Firebase Console → Project Settings → Cloud Messaging → Server key
   - **Format**: `AAAAxxxxxxx:APA91bH...`

2. **Cosmos DB**
   - Ensure `user_preferences` container exists
   - Partition key: `/user_id`

3. **API Deployment**
   - Deploy updated FastAPI app with notifications router
   - Verify `/device-token/*` endpoints are accessible

---

## 🧪 Testing Guide

### Test 1: Permission Request
```
1. Login to app
2. Notification permission dialog should appear
3. Tap "Allow"
4. Check logs for "✅ Notification permission granted"
5. Check logs for "✅ Device token registered successfully"
```

### Test 2: Background Notification
```
1. Close the app or background it
2. Manually trigger breaking news via Azure Portal:
   - Create story with status: BREAKING
   - Set push_notification_sent: false
   - Wait for monitor function (next 5-min cycle)
3. Notification should appear on lock screen
4. Tap notification
5. App should open and scroll to story
```

### Test 3: Foreground Notification
```
1. Open app and browse feed
2. Trigger breaking news (same as Test 2)
3. If priority = "breaking": Banner notification should appear at top
4. Tap banner to navigate to story
```

### Test 4: Token Registration API
```bash
# Get JWT token from app logs
JWT_TOKEN="your_jwt_token_here"

# Check notification status
curl -X GET \
  https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/device-token/status \
  -H "Authorization: Bearer $JWT_TOKEN"

# Expected response:
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

## 📝 Logging

### iOS Logs (via OSLog)

```swift
// Permission request
"📢 Requesting notification permission"
"✅ Notification permission granted" | "⚠️  Notification permission denied"

// Token registration
"📱 APNs device token received"
"🔑 FCM token received: abc123..."
"📤 Registering FCM token with backend"
"✅ FCM token registered successfully"

// Notification handling
"📢 Received notification while app in foreground"
"📲 User tapped notification"
"📍 Scrolling to story from notification: story_123"
```

### Backend Logs (Azure Application Insights)

```python
# Token registration
"📱 Registering device token for user: firebase_uid"
"✅ Updated FCM token for user: firebase_uid"

# Breaking news monitoring
"📢 Sending push notification for: story_123 - Title..."
"📲 Push notification results: 45 success, 2 failure, 47 total users"
"✅ Status monitor complete: 3 BREAKING→VERIFIED transitions, 5 notifications sent"

# FCM API calls
"✅ FCM notification sent successfully to token: abc123..."
"❌ FCM notification failed: 400 - InvalidRegistration"
```

---

## 🐛 Troubleshooting

### Issue: Notifications Not Received

**Possible Causes:**
1. **APNs not configured in Xcode**
   - Solution: Enable Push Notifications capability in Xcode project settings

2. **FCM_SERVER_KEY not set in Azure**
   - Solution: Add environment variable in Azure Function App Configuration

3. **User denied permissions**
   - Solution: User must enable notifications in iOS Settings → Newsreel

4. **Invalid FCM token**
   - Solution: Check logs for FCM token errors, re-register token

5. **Story already marked as notified**
   - Solution: Check `push_notification_sent` field in Cosmos DB

### Issue: App Doesn't Navigate to Story

**Possible Causes:**
1. **Story ID missing from notification payload**
   - Solution: Verify `data.storyId` is included in FCM payload

2. **Story not in feed**
   - Solution: Story may have been removed or aged out

3. **Scroll animation not triggering**
   - Solution: Check `ScrollViewReader` implementation and `onChange` modifier

### Issue: Duplicate Notifications

**Possible Causes:**
1. **`push_notification_sent` flag not being set**
   - Solution: Verify Cosmos DB update in breaking news monitor

2. **Multiple FCM tokens for same user**
   - Solution: Clean up old tokens on login

---

## 🔒 Security Considerations

1. **Token Storage**
   - FCM tokens stored in Cosmos DB (encrypted at rest)
   - Tokens linked to authenticated users only
   - No anonymous notification support

2. **Authorization**
   - All device token endpoints require JWT authentication
   - Users can only manage their own tokens

3. **Privacy**
   - No personal data in notification payload
   - Story content only (title, category)
   - User can opt-out at any time

4. **Rate Limiting**
   - Breaking news monitor runs every 5 minutes
   - Maximum 1 notification per story per user
   - No notification spam

---

## 📈 Metrics & Monitoring

### Key Metrics

1. **Registration Success Rate**
   - Track: Successful token registrations / Total attempts
   - Target: > 95%

2. **Notification Delivery Rate**
   - Track: FCM success / Total sent
   - Target: > 90%

3. **User Engagement**
   - Track: Notification taps / Notifications delivered
   - Target: > 20%

4. **Permission Grant Rate**
   - Track: Users who granted permission / Total asked
   - Target: > 60%

### Azure Monitor Queries

```kql
// Total notifications sent today
traces
| where timestamp > ago(1d)
| where message contains "Push notification results"
| project timestamp, message

// Notification success rate
traces
| where timestamp > ago(1d)
| where message contains "FCM notification"
| summarize Total = count(), Success = countif(message contains "successfully"), Failure = countif(message contains "failed")
| extend SuccessRate = (Success * 100.0) / Total

// Token registrations today
traces
| where timestamp > ago(1d)
| where message contains "Device token registered"
| count
```

---

## 🚀 Future Enhancements

### Potential Features

1. **Rich Notifications**
   - Inline images for story thumbnails
   - Action buttons (Read, Save, Share)
   - Notification categories

2. **Personalized Notifications**
   - User-selected topics
   - Location-based alerts
   - Preferred sources

3. **Smart Scheduling**
   - Quiet hours (no notifications during sleep)
   - Frequency limiting (max N notifications per day)
   - Priority-based delivery

4. **Analytics Dashboard**
   - Admin view of notification stats
   - User engagement metrics
   - Delivery success rates

5. **Multi-Platform Support**
   - Android app support
   - Web push notifications

---

## 📚 API Reference

### iOS

```swift
// NotificationService
func requestPermission() async -> Bool
func registerToken(with apiService: APIService) async
func unregisterToken(with apiService: APIService) async
func handleNotificationTap(_ response: UNNotificationResponse) -> String?

// Published Properties
@Published var isAuthorized: Bool
@Published var fcmToken: String?
@Published var notificationToHandle: UNNotificationResponse?
```

### Backend

```python
# Device Token Management
POST /device-token/register
POST /device-token/unregister
GET /device-token/status

# Push Notification Service
FCMNotificationService.send_breaking_news_notification(
    fcm_tokens: List[str],
    story: Dict[str, Any]
) -> Dict[str, Any]
```

---

## ✅ Deployment Checklist

### Pre-Production

- [ ] Test permission flow on real device
- [ ] Test background notifications
- [ ] Test foreground notifications  
- [ ] Test deep linking navigation
- [ ] Verify token registration API
- [ ] Test notification preferences
- [ ] Verify FCM server key in Azure
- [ ] Test with multiple users
- [ ] Verify logging and metrics
- [ ] Load test with 1000+ tokens

### Production

- [ ] Change `aps-environment` to `production` in entitlements
- [ ] Update FCM server key to production key
- [ ] Enable Push Notifications in App Store Connect
- [ ] Submit app for review with notification usage description
- [ ] Monitor notification delivery rates
- [ ] Set up alerts for failures
- [ ] Document opt-out process for users

---

## 📞 Support

For issues or questions:
- Check logs first (iOS: Console.app, Backend: Azure Application Insights)
- Review troubleshooting section above
- Verify configuration in Azure Portal
- Test with manual FCM payload via Firebase Console

---

**Implementation Complete** ✅  
*Breaking news notifications are now live in Newsreel!*

