


═══════════════════════════════════════════════════════
🚀 NEWSREEL APP LAUNCHING - YOU SHOULD SEE THIS!
═══════════════════════════════════════════════════════



┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  APP LAUNCH                                        ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
[00:58:56.324] [UI] ℹ️ INFO [NewsreelApp.swift:31 init()] - 🚀 Newsreel app launching...
[00:58:56.328] [Auth] ℹ️ INFO [NewsreelApp.swift:34 init()] - Configuring Firebase...
[Firebase/Crashlytics] Version 12.4.0
[00:58:56.420] [Auth] ℹ️ INFO [NewsreelApp.swift:36 init()] - ✅ Firebase configured
12.4.0 - [FirebaseMessaging][I-FCM001000] FIRMessaging Remote Notifications proxy enabled, will swizzle remote notification receiver handlers. If you'd prefer to manually integrate Firebase Messaging, add "FirebaseAppDelegateProxyEnabled" to your Info.plist, and set it to NO. Follow the instructions at:
https://firebase.google.com/docs/cloud-messaging/ios/client#method_swizzling_in_firebase_messaging
to ensure proper integration.
12.4.0 - [GoogleUtilities/AppDelegateSwizzler][I-SWZ001014] App Delegate does not conform to UIApplicationDelegate protocol.
[00:58:56.433] [UI] ℹ️ INFO [NewsreelApp.swift:59 init()] - Initializing services...
━━━━━━━━━━━━━━━━ AUTH SERVICE INIT ━━━━━━━━━━━━━━━━
[00:58:56.433] [Auth] ℹ️ INFO [Logger.swift:134 logAuth(_:level:)] - Initializing AuthService
[00:58:56.433] [Auth] 🔍 DEBUG [Logger.swift:134 logAuth(_:level:)] - Setting up auth state listener
[00:58:56.434] [Auth] ℹ️ INFO [Logger.swift:134 logAuth(_:level:)] - AuthService initialized
[00:58:56.435] [UI] ℹ️ INFO [NewsreelApp.swift:65 init()] - ✅ App initialization complete
[00:58:56.435] [API] ℹ️ INFO [NewsreelApp.swift:66 init()] -    Backend: https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io
[00:58:56.435] [API] ℹ️ INFO [NewsreelApp.swift:67 init()] -    Mock Mode: DISABLED (using live Azure backend)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[00:58:56.449] [Analytics] ℹ️ INFO [NewsreelApp.swift:95 application(_:didFinishLaunchingWithOptions:)] - 📱 App launched
⚠️ RevenueCat not configured - using mock subscription data
[00:58:56.626] [Auth] ℹ️ INFO [Logger.swift:134 logAuth(_:level:)] - 🔐 Auth state changed: Authenticated user (UID: DD0MgYGe...)
[00:58:56.626] [Auth] 🔍 DEBUG [Logger.swift:134 logAuth(_:level:)] -    Email: david@mclauchlan.com
[00:58:56.626] [Auth] 🔍 DEBUG [Logger.swift:134 logAuth(_:level:)] -    Display Name: David McLauchlan
[00:58:56.626] [Auth] 🔍 DEBUG [Logger.swift:134 logAuth(_:level:)] -    Is Anonymous: false

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  NOTIFICATION SERVICE                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
[00:58:56.685] [Analytics] ℹ️ INFO [NotificationService.swift:33 configure(with:)] - 📢 Configuring notification service
[00:58:56.686] [Analytics] ℹ️ INFO [NotificationService.swift:44 configure(with:)] - ✅ Notification service configured
[00:58:56.850] [Analytics] ℹ️ INFO [NotificationService.swift:49 requestPermission()] - 📢 Requesting notification permission
[00:58:56.850] [Analytics] 🔍 DEBUG [NotificationService.swift:85 checkAuthorizationStatus()] - 📊 Notification status: 2
[00:58:56.861] [UI] 🔍 DEBUG [MainAppView.swift:620 sortStories(_:)] - 🔝 Top 3 stories after sort:
[00:58:56.861] [UI] 🔍 DEBUG [MainAppView.swift:622 sortStories(_:)] -    1. [VERIFIED] Test Article 0 About Event...
[00:58:56.861] [UI] 🔍 DEBUG [MainAppView.swift:622 sortStories(_:)] -    2. [VERIFIED] Thailand’s Queen Mother Sirikit has died at age 93...
[00:58:56.861] [UI] 🔍 DEBUG [MainAppView.swift:622 sortStories(_:)] -    3. [VERIFIED] Kendrick Lamar leads 2026 Grammy nominations, foll...
[00:58:56.861] [UI] ℹ️ INFO [MainAppView.swift:579 loadFromCache()] - 📱 Loaded 20 stories from cache

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  FEED VIEW MODEL - LOAD STORIES                    ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
[00:58:56.861] [UI] ℹ️ INFO [MainAppView.swift:503 loadStories(apiService:refresh:)] - Refresh: false, Category: all, Page: 0
[00:58:56.862] [API] ℹ️ INFO [MainAppView.swift:516 loadStories(apiService:refresh:)] - 📡 Calling API with category: nil

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  GET FEED                                          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
[00:58:56.862] [API] ℹ️ INFO [APIService.swift:111 getFeed(offset:limit:category:)] - Fetching feed - offset: 0, limit: 20, category: all
[00:58:56.862] [API] 🔍 DEBUG [APIService.swift:130 getFeed(offset:limit:category:)] - Endpoint: /api/stories/feed?offset=0&limit=20
[00:58:56.863] [Auth] 🔍 DEBUG [Logger.swift:134 logAuth(_:level:)] - Getting Firebase ID token (force refresh: false)
[00:58:56.888] [UI] ℹ️ INFO [MainAppView.swift:262 body] - 🟢 App active - resuming polling
[00:58:56.925] [Analytics] ℹ️ INFO [NotificationService.swift:60 requestPermission()] - ✅ Notification permission granted
[00:58:56.925] [Analytics] ℹ️ INFO [NotificationService.swift:77 registerForRemoteNotifications()] - 📱 Registered for remote notifications
[00:58:56.925] [Analytics] ⚠️ WARNING [NotificationService.swift:94 registerToken(with:)] - ⚠️ No FCM token available to register
[00:58:56.939] [Auth] 🔍 DEBUG [Logger.swift:134 logAuth(_:level:)] - ✅ Firebase ID token obtained (length: 1040 chars)
[00:58:56.939] [Auth] 🔍 DEBUG [Logger.swift:134 logAuth(_:level:)] - Firebase JWT token obtained (preview: eyJhbGciOiJSUzI1NiIs...qK439HMTpg)
[00:58:56.939] [API] ℹ️ INFO [Logger.swift:105 logAPIRequest(_:endpoint:headers:body:)] - 🌐 API Request: GET /api/stories/feed?offset=0&limit=20
   Headers: Content-Type, User-Agent, Authorization
nw_connection_copy_connected_local_endpoint_block_invoke [C2] Connection has no local endpoint
nw_connection_copy_connected_local_endpoint_block_invoke [C2] Connection has no local endpoint
quic_conn_process_inbound [C2.1.1.1:2] [-eed6f699383a25de] unable to parse packet
[00:58:58.210] [API] ℹ️ INFO [Logger.swift:129 logAPIResponse(_:endpoint:data:duration:)] - ✅ API Response: 200 for /api/stories/feed?offset=0&limit=20 (1347.01ms)
   Size: 8 KB
   Data: [{"id":"story_20251109_235628_3163e3be","title":"Test Article 0 About Event","category":"world","tags":["test","event"],"status":"BREAKING","verification_level":100,"summary":null,"source_count":0,"first_seen":"2025-11-09T14:13:06.786159Z","last_updated":"2025-11-09T23:56:57.229655Z","importance_sco...
[00:58:58.217] [Network] ℹ️ INFO [Logger.swift:158 logTiming(_:duration:)] - 🐌 GET /api/stories/feed?offset=0&limit=20 took 1347.01ms
[00:58:58.218] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235628_3163e3be
[00:58:58.218] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.218] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.218] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.218] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_234927_9d1ca58c
[00:58:58.218] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.218] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.218] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.218] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235124_fd372a08
[00:58:58.218] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.219] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.219] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.219] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_234736_966d94a5
[00:58:58.219] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.219] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.219] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.219] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_234653_e7f3d1
[00:58:58.219] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.219] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.219] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.219] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235001_7733d346
[00:58:58.219] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.219] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.219] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.219] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235802_41c3a8fa
[00:58:58.219] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.219] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.219] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.220] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235802_1d303763
[00:58:58.220] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.220] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.220] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.220] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235802_c050c09f
[00:58:58.220] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.220] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.220] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.221] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235802_a2452c80
[00:58:58.221] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.221] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.222] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.222] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235802_f6306aec
[00:58:58.222] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.222] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.222] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.223] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235801_6cc371f8
[00:58:58.223] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.223] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.223] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.223] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235801_8dc0f5be
[00:58:58.223] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.223] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.223] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.223] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235800_190743fe
[00:58:58.223] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.223] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.223] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.223] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235800_66c511f3
[00:58:58.223] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.223] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.223] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.223] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235800_a33cce87
[00:58:58.223] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.223] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.223] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.224] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235800_4253fcbb
[00:58:58.224] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.224] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.224] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.224] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235800_d17e964a
[00:58:58.224] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.224] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.224] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.224] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235800_7f679e7c
[00:58:58.224] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.224] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.224] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.225] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235759_0d837943
[00:58:58.225] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.225] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.225] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.225] [API] ℹ️ INFO [APIService.swift:136 getFeed(offset:limit:category:)] - ✅ Feed loaded successfully: 20 stories
[00:58:58.225] [API] 🔍 DEBUG [APIService.swift:137 getFeed(offset:limit:category:)] -    Sources included: 0 sources in first story
[00:58:58.225] [API] ℹ️ INFO [MainAppView.swift:524 loadStories(apiService:refresh:)] - 📥 Received 20 stories from API
[00:58:58.225] [UI] 🔍 DEBUG [MainAppView.swift:620 sortStories(_:)] - 🔝 Top 3 stories after sort:
[00:58:58.225] [UI] 🔍 DEBUG [MainAppView.swift:622 sortStories(_:)] -    1. [DEVELOPING] Landmark Paris Agreement set a path to slow warmin...
[00:58:58.226] [UI] 🔍 DEBUG [MainAppView.swift:622 sortStories(_:)] -    2. [VERIFIED] Test Article 0 About Event...
[00:58:58.226] [UI] 🔍 DEBUG [MainAppView.swift:622 sortStories(_:)] -    3. [VERIFIED] Thailand’s Queen Mother Sirikit has died at age 93...
[00:58:58.226] [UI] ℹ️ INFO [MainAppView.swift:539 loadStories(apiService:refresh:)] - ✅ Stories loaded successfully: 20 new stories, 35 total
[00:58:58.227] [UI] ℹ️ INFO [MainAppView.swift:545 loadStories(apiService:refresh:)] - 📊 Status distribution: DEVELOPING: 17, BREAKING: 3
[00:58:58.227] [UI] ℹ️ INFO [MainAppView.swift:589 loadBreakingNews(apiService:)] - 📰 Loading breaking news
[00:58:58.227] [API] ℹ️ INFO [APIService.swift:225 getBreakingNews()] - Fetching breaking news (public endpoint)
[00:58:58.227] [API] 🔍 DEBUG [APIService.swift:233 getBreakingNews()] - Endpoint: /api/stories/breaking?limit=20 (no auth required)
[00:58:58.227] [API] 🔍 DEBUG [APIService.swift:496 request(endpoint:method:body:requiresAuth:retryCount:)] - Request does not require authentication
[00:58:58.227] [API] ℹ️ INFO [Logger.swift:105 logAPIRequest(_:endpoint:headers:body:)] - 🌐 API Request: GET /api/stories/breaking?limit=20
   Headers: User-Agent, Content-Type
[00:58:58.266] [UI] 🔍 DEBUG [MainAppView.swift:557 loadStories(apiService:refresh:)] - 📱 Cached 20 stories
nw_connection_copy_connected_local_endpoint_block_invoke [C2] Connection has no local endpoint
[00:58:58.883] [API] ℹ️ INFO [Logger.swift:129 logAPIResponse(_:endpoint:data:duration:)] - ✅ API Response: 200 for /api/stories/breaking?limit=20 (655.35ms)
   Size: 8 KB
   Data: [{"id":"story_20251109_235857_ddd78c9c","title":"AFL's wildcard round shake-up confirmed","category":"sports","tags":[],"status":"DEVELOPING","verification_level":2,"summary":null,"source_count":0,"first_seen":"2025-11-09T19:47:24Z","last_updated":"2025-11-09T23:58:58.260777Z","importance_score":50,...
[00:58:58.883] [Network] ℹ️ INFO [Logger.swift:158 logTiming(_:duration:)] - 🐌 GET /api/stories/breaking?limit=20 took 655.35ms
[00:58:58.884] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235857_ddd78c9c
[00:58:58.884] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.884] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.884] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.884] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235802_41c3a8fa
[00:58:58.884] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.884] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.884] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.885] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235802_1d303763
[00:58:58.885] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.885] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.885] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.885] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235802_c050c09f
[00:58:58.885] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.885] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.885] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.885] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235802_a2452c80
[00:58:58.886] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.886] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.886] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.886] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235802_f6306aec
[00:58:58.886] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.886] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.886] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.887] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235801_6cc371f8
[00:58:58.887] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.887] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.887] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.887] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235801_8dc0f5be
[00:58:58.887] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.887] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.887] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.888] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235801_d6a0a8ee
[00:58:58.888] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.888] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.888] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.888] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235801_8e1cdae8
[00:58:58.888] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.889] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.889] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.889] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235801_2204eee0
[00:58:58.889] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.889] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.889] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.890] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235800_190743fe
[00:58:58.890] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.890] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.890] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.890] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235800_66c511f3
[00:58:58.890] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.890] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.891] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.891] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235800_4659bb58
[00:58:58.891] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.891] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.891] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.891] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235800_a33cce87
[00:58:58.891] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.891] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.891] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.892] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235800_4253fcbb
[00:58:58.892] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.892] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.892] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.892] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235800_d17e964a
[00:58:58.892] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.892] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.892] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.893] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235800_7f679e7c
[00:58:58.893] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.893] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.893] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.893] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235759_0d837943
[00:58:58.893] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.893] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.893] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.893] [API] 🔍 DEBUG [APIService.swift:721 toStory()] - 📦 [API DECODE] Story: story_20251109_235759_74fe4325
[00:58:58.893] [API] 🔍 DEBUG [APIService.swift:722 toStory()] -    API returned 0 source objects
[00:58:58.893] [API] 🔍 DEBUG [APIService.swift:723 toStory()] -    Converted to 0 SourceArticle objects
[00:58:58.893] [API] 🔍 DEBUG [APIService.swift:783 toStory()] - 📦 [API DECODE] Creating Story object with 0 deduplicated sources (was 0 raw)
[00:58:58.893] [API] ℹ️ INFO [APIService.swift:239 getBreakingNews()] - ✅ Breaking news loaded: 20 stories
[00:58:58.893] [API] 🔍 DEBUG [APIService.swift:240 getBreakingNews()] -    Sources per story: 0
[00:58:58.894] [UI] ℹ️ INFO [MainAppView.swift:593 loadBreakingNews(apiService:)] - ✅ Loaded 5 breaking news items
[01:00:07.379] [API] ℹ️ INFO [APIService.swift:577 getAdminMetrics()] - Fetching admin metrics
[01:00:07.379] [Auth] 🔍 DEBUG [Logger.swift:134 logAuth(_:level:)] - Getting Firebase ID token (force refresh: false)
[01:00:07.381] [Auth] 🔍 DEBUG [Logger.swift:134 logAuth(_:level:)] - ✅ Firebase ID token obtained (length: 1040 chars)
[01:00:07.381] [Auth] 🔍 DEBUG [Logger.swift:134 logAuth(_:level:)] - Firebase JWT token obtained (preview: eyJhbGciOiJSUzI1NiIs...qK439HMTpg)
[01:00:07.381] [API] ℹ️ INFO [Logger.swift:105 logAPIRequest(_:endpoint:headers:body:)] - 🌐 API Request: GET /api/admin/metrics
   Headers: Content-Type, User-Agent, Authorization
[01:00:08.231] [API] ❌ ERROR [Logger.swift:129 logAPIResponse(_:endpoint:data:duration:)] - ❌ API Response: 500 for /api/admin/metrics (852.44ms)
   Size: 73 bytes
   Data: {"error":"Internal server error","detail":"An unexpected error occurred"}
[01:00:08.232] [API] ❌ ERROR [APIService.swift:560 request(endpoint:method:body:requiresAuth:retryCount:)] - ❌ Server error: 500
[01:00:08.243] [Error] ❌ ERROR [APIService.swift:565 request(endpoint:method:body:requiresAuth:retryCount:)] - 
╔══════════════════════════════════════════════════════════
║ ERROR: GET /api/admin/metrics
╟──────────────────────────────────────────────────────────
║ Error: Server error (500). Please try again later.
║ Type: APIError
╚══════════════════════════════════════════════════════════
[01:00:08.243] [Error] ❌ ERROR [AdminDashboardView.swift:673 loadMetrics(apiService:)] - 
╔══════════════════════════════════════════════════════════
║ ERROR: loadAdminMetrics
╟──────────────────────────────────────────────────────────
║ Error: Server error (500). Please try again later.
║ Type: APIError
╚══════════════════════════════════════════════════════════
[01:00:09.582] [API] ℹ️ INFO [APIService.swift:577 getAdminMetrics()] - Fetching admin metrics
[01:00:09.583] [Auth] 🔍 DEBUG [Logger.swift:134 logAuth(_:level:)] - Getting Firebase ID token (force refresh: false)
[01:00:09.587] [Auth] 🔍 DEBUG [Logger.swift:134 logAuth(_:level:)] - ✅ Firebase ID token obtained (length: 1040 chars)
[01:00:09.587] [Auth] 🔍 DEBUG [Logger.swift:134 logAuth(_:level:)] - Firebase JWT token obtained (preview: eyJhbGciOiJSUzI1NiIs...qK439HMTpg)
[01:00:09.587] [API] ℹ️ INFO [Logger.swift:105 logAPIRequest(_:endpoint:headers:body:)] - 🌐 API Request: GET /api/admin/metrics
   Headers: User-Agent, Authorization, Content-Type
[01:00:10.390] [API] ❌ ERROR [Logger.swift:129 logAPIResponse(_:endpoint:data:duration:)] - ❌ API Response: 500 for /api/admin/metrics (807.65ms)
   Size: 73 bytes
   Data: {"error":"Internal server error","detail":"An unexpected error occurred"}
[01:00:10.390] [API] ❌ ERROR [APIService.swift:560 request(endpoint:method:body:requiresAuth:retryCount:)] - ❌ Server error: 500
[01:00:10.391] [Error] ❌ ERROR [APIService.swift:565 request(endpoint:method:body:requiresAuth:retryCount:)] - 
╔══════════════════════════════════════════════════════════
║ ERROR: GET /api/admin/metrics
╟──────────────────────────────────────────────────────────
║ Error: Server error (500). Please try again later.
║ Type: APIError
╚══════════════════════════════════════════════════════════
[01:00:10.391] [Error] ❌ ERROR [AdminDashboardView.swift:673 loadMetrics(apiService:)] - 
╔══════════════════════════════════════════════════════════
║ ERROR: loadAdminMetrics
╟──────────────────────────────────────────────────────────
║ Error: Server error (500). Please try again later.
║ Type: APIError
╚══════════════════════════════════════════════════════════