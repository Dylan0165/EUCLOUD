# 🚀 Backend SSO Cookie - Quick Reference

## 🎯 Cookie Configuration

```python
# backend/auth.py
COOKIE_NAME = "eusuite_token"
COOKIE_MAX_AGE = 86400  # 24 hours
COOKIE_DOMAIN = "192.168.124.50"
```

---

## 🔐 How It Works

### Login Sets Cookie
```python
response.set_cookie(
    key="eusuite_token",
    value=jwt_token,
    httponly=True,        # XSS protection
    secure=False,         # True for HTTPS
    samesite="lax",       # CSRF protection
    path="/",
    max_age=86400,
    domain="192.168.124.50"
)
```

### Authentication Checks Cookie
```python
# Priority: Header → Cookie → 401
token = credentials.credentials if credentials else None
if not token:
    token = request.cookies.get("eusuite_token")
```

### Logout Deletes Cookie
```python
response.delete_cookie(
    key="eusuite_token",
    path="/",
    domain="192.168.124.50"
)
```

---

## 📡 API Endpoints

| Endpoint | Method | Cookie Action | Description |
|----------|--------|---------------|-------------|
| `/api/auth/login` | POST | ✅ Sets | Login user |
| `/api/auth/register` | POST | ✅ Sets | Register + auto-login |
| `/api/auth/logout` | POST | ❌ Deletes | Logout user |
| `/api/auth/me` | GET | 📖 Reads | Check if logged in |
| `/api/auth/test-cookie` | GET | 📖 Reads | Debug cookie presence |

---

## 🧪 Quick Test Commands

### 1. Login
```bash
curl -X POST http://192.168.124.50:30500/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  --cookie-jar cookies.txt -v
```

### 2. Check Auth
```bash
curl -X GET http://192.168.124.50:30500/api/auth/me \
  --cookie cookies.txt
```

### 3. Test Cookie
```bash
curl -X GET http://192.168.124.50:30500/api/auth/test-cookie \
  --cookie cookies.txt
```

### 4. Logout
```bash
curl -X POST http://192.168.124.50:30500/api/auth/logout \
  --cookie cookies.txt
```

---

## 🌐 CORS Configuration

```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://192.168.124.50:30090",  # Login Portal
        "http://192.168.124.50:30500",  # EuCloud
        "http://192.168.124.50:30600",  # EuType
        "http://192.168.124.50:30700",  # EuSheets
    ],
    allow_credentials=True,  # ⭐ REQUIRED
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🔄 Frontend Usage

### JavaScript/Fetch
```javascript
// Login
fetch('http://192.168.124.50:30500/api/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({email, password}),
  credentials: 'include'  // ⭐ Send/receive cookies
})

// Check auth
fetch('http://192.168.124.50:30500/api/auth/me', {
  credentials: 'include'  // ⭐ Send cookie
})
```

### Axios
```javascript
const api = axios.create({
  baseURL: 'http://192.168.124.50:30500/api',
  withCredentials: true  // ⭐ Send/receive cookies
})

// Login
await api.post('/auth/login', {email, password})

// Check auth
await api.get('/auth/me')
```

---

## 🐛 Troubleshooting

### Cookie Not Set?
```bash
# Check CORS
✓ allow_credentials = True
✓ Origin in allow_origins
✓ Frontend uses credentials: 'include'

# Check response headers
curl -X POST .../login -v | grep Set-Cookie
```

### Cookie Not Sent?
```bash
# Check cookie exists
curl -X GET .../test-cookie --cookie cookies.txt

# Check browser DevTools
→ Application → Cookies → Check "eusuite_token"
```

### 401 Unauthorized?
```bash
# Debug flow
1. Check cookie: /test-cookie
2. Check token valid: Not expired
3. Check user exists: Database
4. Check logs: Backend logs
```

---

## 🔒 Security Checklist

- [x] HttpOnly - JavaScript cannot access
- [x] SameSite=Lax - CSRF protection
- [x] Domain shared - All apps use same cookie
- [x] Max-Age set - Auto-expiry
- [x] Secure for HTTPS - Production setting
- [x] CORS credentials - Enabled
- [x] JWT validation - Server-side

---

## 📊 Key Files

| File | Purpose |
|------|---------|
| `backend/auth.py` | Cookie auth logic |
| `backend/routes/auth.py` | Login/logout/me endpoints |
| `backend/main.py` | CORS configuration |

---

## ✅ Production Checklist

Before deploying:
1. Set `secure=True` in cookie config
2. Use HTTPS
3. Set strong `JWT_SECRET_KEY` env var
4. Update cookie domain for production
5. Test all apps with cookie auth
6. Monitor cookie metrics

---

## 📚 Full Documentation

See `BACKEND_SSO_IMPLEMENTATION.md` for complete details.

---

**Last Updated:** November 18, 2025  
**Status:** ✅ SSO Cookie Support Complete
