# 🔐 EU-CORE-BACKEND SSO Cookie Implementation

**Date:** November 18, 2025  
**Backend:** FastAPI + SQLAlchemy + JWT  
**Status:** ✅ SSO Cookie Support Complete

---

## 🎯 What Was Implemented

The EU-CORE-BACKEND now supports **HttpOnly cookie-based authentication** for Single Sign-On (SSO) across ALL EUsuite applications.

### Key Features:
1. ✅ **HttpOnly Cookie Authentication** - XSS protection
2. ✅ **Dual Authentication Support** - Cookie + Authorization header (backwards compatible)
3. ✅ **Automatic Cookie Setting** on login/register
4. ✅ **SSO Logout** - Clears cookie across all apps
5. ✅ **CORS with Credentials** - Cookie support for all EUsuite apps
6. ✅ **Test Endpoints** - Debug cookie presence

---

## 📝 Changes Overview

### 🔧 Modified Files

#### **1. `backend/auth.py`**

**Changes:**
- Added `Request` dependency to `get_current_user()`
- Cookie authentication support (priority: header → cookie)
- Auto-error disabled for HTTPBearer (optional auth)
- Cookie configuration constants

**New Code:**
```python
# Cookie Configuration
COOKIE_NAME = "eusuite_token"
COOKIE_MAX_AGE = 86400  # 24 hours

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db = Depends(get_db)
) -> User:
    # Try Authorization header first
    if credentials:
        token = credentials.credentials
    
    # Then try cookie
    if not token:
        token = request.cookies.get(COOKIE_NAME)
    
    # Validate JWT and return user
    ...
```

#### **2. `backend/routes/auth.py`**

**Changes:**
- `/login` - Sets HttpOnly cookie
- `/register` - Sets HttpOnly cookie (auto-login)
- `/logout` - Deletes cookie
- `/me` - Works with cookie auth
- `/test-cookie` - NEW endpoint for debugging

**Key Implementation:**
```python
@router.post("/login")
async def login(credentials: UserLogin, response: Response, ...):
    # Authenticate user
    access_token = create_access_token(user.user_id)
    
    # SET SSO COOKIE
    response.set_cookie(
        key="eusuite_token",
        value=access_token,
        httponly=True,
        secure=False,            # LAN-only
        samesite="lax",
        path="/",
        max_age=86400,
        domain="192.168.124.50"  # Shared across all apps
    )
    
    return {"access_token": access_token, "user": user.to_dict()}
```

#### **3. `backend/main.py`**

**Changes:**
- Updated CORS origins (added Login Portal + production ports)
- `allow_credentials=True` - CRITICAL for cookies
- Added all EUsuite app origins

**CORS Config:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://192.168.124.50:30080",  # EuCloud
        "http://192.168.124.50:30081",  # EuType
        "http://192.168.124.50:30090",  # Login Portal ⭐
        "http://192.168.124.50:30500",  # EuCloud (prod)
        "http://192.168.124.50:30600",  # EuType (prod)
        "http://192.168.124.50:30700",  # EuSheets (prod)
        ...
    ],
    allow_credentials=True,  # ⭐ REQUIRED for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🔄 Authentication Flow

### Before (JWT in localStorage)
```
Frontend → POST /auth/login
Backend → Return JWT token
Frontend → localStorage.setItem('token', jwt)
Frontend → Every request: Authorization: Bearer <token>
```

### After (SSO Cookie)
```
Frontend → POST /auth/login (credentials: "include")
Backend → Validate → Set HttpOnly Cookie
Frontend → Cookie automatically sent with all requests
Backend → Read token from cookie → Validate → Return data
```

---

## 🔐 Security Features

| Feature | Purpose | Implementation |
|---------|---------|----------------|
| **HttpOnly** | XSS Protection | JavaScript cannot access cookie |
| **SameSite=Lax** | CSRF Protection | Cookie only sent to same domain |
| **Secure=False** | LAN Development | Set to True for HTTPS production |
| **Domain=192.168.124.50** | Multi-App Sharing | All apps can use same cookie |
| **Path=/** | Global Access | Cookie available for all endpoints |
| **Max-Age=86400** | Auto-Expiry | 24 hour session lifetime |

---

## 🧪 Testing

### 1. Test Login with Cookie
```bash
curl -X POST http://192.168.124.50:30500/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  --cookie-jar cookies.txt \
  --verbose
```

**Expected Response Headers:**
```
Set-Cookie: eusuite_token=eyJhbGc...; HttpOnly; SameSite=Lax; Path=/; Domain=192.168.124.50; Max-Age=86400
```

**Expected JSON:**
```json
{
  "message": "Login successful",
  "access_token": "eyJhbGc...",
  "user": {
    "id": 1,
    "email": "test@example.com"
  }
}
```

### 2. Test Cookie Authentication
```bash
# Use cookie from previous request
curl -X GET http://192.168.124.50:30500/api/auth/me \
  --cookie cookies.txt \
  --verbose
```

**Expected:**
```json
{
  "user": {
    "id": 1,
    "email": "test@example.com"
  }
}
```

### 3. Test Cookie Debug Endpoint
```bash
curl -X GET http://192.168.124.50:30500/api/auth/test-cookie \
  --cookie cookies.txt
```

**Expected:**
```json
{
  "cookie_present": true,
  "cookie_name": "eusuite_token",
  "cookie_value_length": 215,
  "message": "SSO cookie is present and readable"
}
```

### 4. Test Logout
```bash
curl -X POST http://192.168.124.50:30500/api/auth/logout \
  --cookie cookies.txt \
  --cookie-jar cookies.txt \
  --verbose
```

**Expected:**
```json
{
  "message": "Logout successful"
}
```

Cookie should be deleted (check cookies.txt).

### 5. Test Protected Endpoint
```bash
curl -X GET http://192.168.124.50:30500/api/files/list \
  --cookie cookies.txt
```

Should return files (not 401).

---

## 🌐 Multi-App SSO Flow

```
┌─────────────────────────────────────────────────────────┐
│ 1. User visits Login Portal                            │
│    http://192.168.124.50:30090                          │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Login Portal → POST /auth/login                     │
│    credentials: "include"                               │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│ 3. EU-CORE-BACKEND validates credentials                │
│    Sets cookie: eusuite_token=...                       │
│    Domain: 192.168.124.50                               │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│ 4. Cookie stored in browser                             │
│    Applies to ALL apps on 192.168.124.50                │
│    - EuCloud (30500)                                    │
│    - EuType (30600)                                     │
│    - EuSheets (30700)                                   │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│ 5. User visits EuCloud                                  │
│    http://192.168.124.50:30500                          │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│ 6. EuCloud → GET /auth/me                               │
│    Cookie automatically sent (credentials: "include")   │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│ 7. EU-CORE-BACKEND validates cookie                     │
│    Returns user info → 200 OK                           │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│ 8. EuCloud shows dashboard (user is logged in)         │
└─────────────────────────────────────────────────────────┘

🎉 User is now logged into ALL apps without additional logins!
```

---

## 📊 API Endpoints

### Authentication Endpoints

| Endpoint | Method | Purpose | Cookie Action |
|----------|--------|---------|---------------|
| `/api/auth/register` | POST | Register new user | ✅ Sets cookie |
| `/api/auth/login` | POST | Login user | ✅ Sets cookie |
| `/api/auth/logout` | POST | Logout user | ❌ Deletes cookie |
| `/api/auth/me` | GET | Check auth status | 📖 Reads cookie |
| `/api/auth/test-cookie` | GET | Debug cookie | 📖 Reads cookie |

### Protected Endpoints

All file, folder, share, storage, and trash endpoints now support cookie authentication:

```
/api/files/*
/api/folders/*
/api/shares/*
/api/storage/*
/api/trash/*
/api/extras/*
```

**Usage:**
```javascript
// Frontend - All requests automatically include cookie
fetch('http://192.168.124.50:30500/api/files/list', {
  credentials: 'include'  // ⭐ This is all you need!
})
```

---

## 🔧 Configuration

### Cookie Settings

**File:** `backend/auth.py`

```python
COOKIE_NAME = "eusuite_token"        # Cookie key
COOKIE_MAX_AGE = 86400               # 24 hours

# In login/register:
response.set_cookie(
    key=COOKIE_NAME,
    value=access_token,
    httponly=True,                   # XSS protection
    secure=False,                    # True for HTTPS
    samesite="lax",                  # CSRF protection
    path="/",                        # All paths
    max_age=COOKIE_MAX_AGE,          # 24 hours
    domain="192.168.124.50"          # Shared domain
)
```

### CORS Settings

**File:** `backend/main.py`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://192.168.124.50:30090",  # Login Portal
        "http://192.168.124.50:30500",  # EuCloud
        "http://192.168.124.50:30600",  # EuType
        "http://192.168.124.50:30700",  # EuSheets
        # ... more apps
    ],
    allow_credentials=True,  # REQUIRED for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### JWT Settings

**File:** `backend/auth.py`

```python
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
```

---

## 🚨 Important Notes

### 1. Backwards Compatibility

The backend still supports Authorization header for backwards compatibility:

```javascript
// Old way (still works)
fetch('/api/files/list', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})

// New way (SSO)
fetch('/api/files/list', {
  credentials: 'include'
})
```

### 2. Authentication Priority

```
1. Check Authorization header
2. If not present → Check cookie
3. If both missing → 401
```

### 3. Production Deployment

For HTTPS production, change:
```python
secure=False  →  secure=True
```

### 4. Cookie Domain

Cookie domain MUST match all app URLs:
- ✅ `domain="192.168.124.50"` works for `http://192.168.124.50:*`
- ❌ `domain="localhost"` won't work for IP addresses

### 5. SameSite Policy

`samesite="lax"` allows:
- ✅ Navigation (redirects from Login Portal)
- ✅ GET requests
- ❌ CSRF from external sites

For stricter security (HTTPS), use `samesite="strict"`.

---

## ✅ SSO Best Practices Compliance

### Why This Implementation is Secure

1. **HttpOnly Cookie**
   - ✅ JavaScript cannot access token
   - ✅ XSS attacks cannot steal token
   - ✅ Token automatically managed by browser

2. **SameSite=Lax**
   - ✅ CSRF protection
   - ✅ Cookies not sent from external sites
   - ✅ Redirects work (Login Portal → Apps)

3. **Domain Sharing**
   - ✅ One cookie for all apps
   - ✅ True SSO experience
   - ✅ Single logout affects all apps

4. **Automatic Credential Handling**
   - ✅ Browser manages cookies
   - ✅ No manual token storage
   - ✅ Consistent across all apps

5. **Backwards Compatible**
   - ✅ Supports both cookie and header auth
   - ✅ Gradual migration possible
   - ✅ No breaking changes

6. **Centralized Authentication**
   - ✅ One backend for all apps
   - ✅ Consistent user experience
   - ✅ Easier to manage and secure

7. **Token Validation**
   - ✅ JWT with expiry
   - ✅ Server-side validation
   - ✅ Database user lookup

8. **Logging & Debugging**
   - ✅ Comprehensive logging
   - ✅ Test endpoints for debugging
   - ✅ Clear error messages

---

## 🔄 Migration Path

### Phase 1: Deploy Backend (Now)
1. ✅ Cookie support implemented
2. ✅ CORS configured
3. ✅ Backwards compatible

### Phase 2: Update Login Portal
1. Use `credentials: 'include'` in fetch
2. Handle cookie-based session
3. Test login flow

### Phase 3: Update Apps
1. EuCloud: Use cookie auth
2. EuType: Use cookie auth
3. EuSheets: Use cookie auth
4. Remove localStorage token code

### Phase 4: Remove Header Auth (Optional)
1. Once all apps use cookies
2. Remove Authorization header support
3. Simplify authentication code

---

## 🐛 Troubleshooting

### Issue: Cookie not being set

**Check:**
1. CORS `allow_credentials=True`
2. Frontend uses `credentials: 'include'`
3. Cookie domain matches request origin
4. Check browser DevTools → Application → Cookies

**Debug:**
```bash
curl -X POST .../login -v | grep Set-Cookie
```

### Issue: Cookie not being sent

**Check:**
1. `credentials: 'include'` in fetch
2. Cookie domain matches request URL
3. Cookie not expired
4. SameSite policy

**Debug:**
```bash
curl -X GET .../test-cookie --cookie cookies.txt
```

### Issue: CORS error

**Check:**
1. Origin in `allow_origins` list
2. `allow_credentials=True`
3. Not using wildcard `*` with credentials

**Fix:**
Add origin to CORS list in `main.py`

### Issue: 401 Unauthorized

**Check:**
1. Cookie present: `/test-cookie`
2. Token valid: Not expired
3. User exists in database

**Debug:**
```bash
curl -X GET .../auth/me --cookie cookies.txt -v
```

---

## 📈 Performance Notes

- Cookie authentication has **no performance impact**
- JWT validation is the same (header vs cookie)
- No database changes required
- No additional dependencies needed

---

## 📚 Related Documentation

- [Frontend SSO Integration](../SSO_INTEGRATION.md)
- [SSO Architecture](../SSO_ARCHITECTURE.md)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [HTTP Cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies)

---

## ✅ Checklist

### Backend Implementation
- [x] Cookie support in `get_current_user()`
- [x] `/login` sets cookie
- [x] `/register` sets cookie
- [x] `/logout` deletes cookie
- [x] `/me` works with cookie
- [x] `/test-cookie` endpoint added
- [x] CORS allows credentials
- [x] All origins configured
- [x] Backwards compatible with header auth
- [x] Comprehensive logging

### Testing
- [ ] Login with cookie
- [ ] Register with cookie
- [ ] Logout deletes cookie
- [ ] `/me` with cookie auth
- [ ] Protected endpoints with cookie
- [ ] Cookie shared across apps
- [ ] CORS headers correct

### Deployment
- [ ] Update environment variables
- [ ] Set `secure=True` for production
- [ ] Configure proper domain
- [ ] Test with HTTPS
- [ ] Monitor cookie metrics

---

**🎉 EU-CORE-BACKEND SSO Cookie Implementation Complete!**

The backend now supports enterprise-grade SSO authentication via HttpOnly cookies, providing a secure and seamless experience across ALL EUsuite applications.

---

**Author:** EU-CORE-BACKEND Team  
**Date:** November 18, 2025  
**Version:** 2.0.0 (SSO Cookie Support)
