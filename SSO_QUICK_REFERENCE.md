# 🎯 EuCloud SSO - Quick Reference

## 📍 URLs

```javascript
Login Portal:  http://192.168.124.50:30090/login
EuCloud App:   http://192.168.124.50:30500
Auth Check:    http://192.168.124.50:30500/api/auth/me
```

---

## 🔑 SSO Config Location

**File:** `frontend/src/config/sso.js`

```javascript
export const SSO_CONFIG = {
  LOGIN_PORTAL_URL: 'http://192.168.124.50:30090/login',
  AUTH_CHECK_URL: 'http://192.168.124.50:30500/api/auth/me',
  APP_URL: 'http://192.168.124.50:30500',
  COOKIE_NAME: 'session',
  COOKIE_DOMAIN: '192.168.124.50'
}
```

**Om URLs te wijzigen:** Edit alleen `sso.js`

---

## 🚀 How It Works

### 1️⃣ App Start
```
App loads → AuthContext.checkAuth()
```

### 2️⃣ SSO Check
```javascript
GET http://192.168.124.50:30500/api/auth/me
credentials: "include"  // Sends cookie
```

### 3️⃣ Response Handling
```
✅ 200 OK → User logged in → Show dashboard
❌ 401    → Redirect to Login Portal
```

### 4️⃣ Redirect
```javascript
window.location.href = 
  "http://192.168.124.50:30090/login?redirect=" + 
  encodeURIComponent("http://192.168.124.50:30500")
```

---

## 🔧 Key Files Changed

| File | Purpose |
|------|---------|
| `context/AuthContext.jsx` | SSO check + redirect |
| `services/api.js` | Cookie credentials |
| `App.jsx` | Remove login routes |
| `services/index.js` | Remove token logic |
| `config/sso.js` | ⭐ Centralized config |

---

## 🧪 Testing Commands

### Check SSO Session
```bash
curl -X GET http://192.168.124.50:30500/api/auth/me \
  -H "Cookie: session=YOUR_SESSION_ID" \
  --cookie-jar cookies.txt
```

### Verify Cookie Settings
```javascript
// In browser console
document.cookie
// Should see: session=...
```

### Test Without Login
```
1. Clear cookies
2. Visit http://192.168.124.50:30500
3. Should redirect to Login Portal
```

---

## 🐛 Common Issues

### Issue: Cookie not sent
**Check:**
```javascript
// In api.js
withCredentials: true  ✅
credentials: 'include' ✅
```

### Issue: CORS error
**Backend needs:**
```
Access-Control-Allow-Origin: http://192.168.124.50:30500
Access-Control-Allow-Credentials: true
```

### Issue: Redirect loop
**Check backend:**
```python
# /auth/me must return 200 with valid cookie
@app.route('/api/auth/me')
def get_me():
    if session.get('user_id'):
        return {"user": {...}}, 200
    return {"error": "Unauthorized"}, 401
```

---

## 📱 Multi-App Setup

Alle apps kunnen dezelfde cookie gebruiken:

```
┌─────────────────────────────────────┐
│   Login Portal (30090)              │
│   Sets cookie: session=xyz          │
│   Domain: 192.168.124.50            │
└──────────────┬──────────────────────┘
               │
       Cookie shared with:
               │
   ┌───────────┼───────────┐
   │           │           │
   ▼           ▼           ▼
EuCloud   EuType    EuSheets
(30500)   (30600)   (30700)
```

**Requirements:**
- Alle apps op zelfde domain: `192.168.124.50`
- Cookie domain: `192.168.124.50`
- SameSite: `Lax` (staat redirects toe)

---

## ✅ Verification Checklist

### Frontend
- [x] Login/Register pages gearchiveerd (.OLD)
- [x] localStorage token verwijderd
- [x] `withCredentials: true` in axios
- [x] SSO config centralized in `sso.js`
- [x] 401 → redirect to Login Portal
- [x] Loading screen met spinner

### Backend (TODO)
- [ ] Cookie-based sessions
- [ ] `/auth/me` endpoint
- [ ] CORS met credentials
- [ ] Cookie settings (HttpOnly, SameSite=Lax)

---

## 🚨 BELANGRIJK

1. **Geen localStorage meer**
   ```javascript
   ❌ localStorage.getItem('token')
   ✅ Cookie: session=xyz (automatic)
   ```

2. **Alle requests credentials**
   ```javascript
   axios.get('/api/...', {
     withCredentials: true  // ✅ Required
   })
   ```

3. **Logout via Portal**
   ```javascript
   // App heeft geen logout endpoint
   // Redirect naar Login Portal voor logout
   ```

---

## 📚 Documentatie

- [SSO_INTEGRATION.md](./SSO_INTEGRATION.md) - Volledige technische docs
- [SSO_MIGRATION_COMPLETE.md](./SSO_MIGRATION_COMPLETE.md) - Migratie overzicht
- [API_CONTRACT.md](./API_CONTRACT.md) - API endpoints

---

**Last Updated:** November 18, 2025  
**Status:** ✅ Frontend SSO Complete - Backend Implementation Pending
