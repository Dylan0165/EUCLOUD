# 🔐 EuCloud SSO Integration

EuCloud is nu volledig geïntegreerd met de **EUsuite Login Portal** voor centralized authentication.

## 🎯 Wat is veranderd?

### ❌ VERWIJDERD
- Eigen login/register pagina's
- localStorage token opslag
- JWT token in Authorization headers
- Lokale auth endpoints (login/register)

### ✅ TOEGEVOEGD
- SSO cookie-based authentication
- Automatische redirect naar EUsuite Login Portal
- Cookie credentials in alle API requests
- Centralized user session management

---

## 🔄 Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User bezoekt EuCloud                                      │
│    http://192.168.124.50:30500                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. App checkt SSO sessie                                     │
│    GET http://192.168.124.50:30500/api/auth/me               │
│    credentials: "include"                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
    ✅ 200 OK              ❌ 401 Unauthorized
         │                       │
         ▼                       ▼
┌────────────────┐      ┌──────────────────────────────────────┐
│ App laadt      │      │ Redirect naar EUsuite Login Portal:   │
│ Dashboard      │      │ http://192.168.124.50:30090/login?   │
│                │      │ redirect=http://192.168.124.50:30500 │
└────────────────┘      └──────────────────────────────────────┘
                                       │
                                       ▼
                        ┌───────────────────────────────────┐
                        │ User logt in via Login Portal     │
                        │ SSO cookie wordt gezet            │
                        └───────────────┬───────────────────┘
                                       │
                                       ▼
                        ┌───────────────────────────────────┐
                        │ Redirect terug naar EuCloud      │
                        │ met geldige SSO cookie            │
                        └───────────────┬───────────────────┘
                                       │
                                       ▼
                        ┌───────────────────────────────────┐
                        │ App checkt opnieuw → 200 OK       │
                        │ Dashboard laadt                   │
                        └───────────────────────────────────┘
```

---

## 🔧 Technische Details

### Frontend Changes

#### **1. AuthContext.jsx**
- Gebruikt `axios.get()` met `withCredentials: true` voor SSO check
- Redirect naar Login Portal bij 401 response
- Geen localStorage meer
- Geen login/register methods meer

```javascript
const SSO_LOGIN_PORTAL = 'http://192.168.124.50:30090/login'
const SSO_AUTH_CHECK_URL = 'http://192.168.124.50:30500/api/auth/me'

const checkAuth = async () => {
  try {
    const response = await axios.get(SSO_AUTH_CHECK_URL, {
      withCredentials: true,
      credentials: 'include'
    })
    setUser(response.data.user)
  } catch (error) {
    if (error.response?.status === 401) {
      redirectToSSOLogin()
    }
  }
}
```

#### **2. api.js**
- Axios instance met `withCredentials: true` en `credentials: 'include'`
- Geen Authorization header meer
- 401 errors triggeren redirect naar Login Portal

```javascript
const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  credentials: 'include'
})
```

#### **3. App.jsx**
- Geen login/register routes meer
- Alleen dashboard route
- PrivateRoute checkt user status

#### **4. services/index.js**
- authService minimaal (alleen getCurrentUser)
- Geen login/register/logout methods
- Preview URLs zonder token parameter

---

## 🌐 URL Configuration

| Service | URL | Port |
|---------|-----|------|
| **EuCloud** | `http://192.168.124.50:30500` | 30500 |
| **EUsuite Login Portal** | `http://192.168.124.50:30090` | 30090 |
| **SSO Auth Check** | `http://192.168.124.50:30500/api/auth/me` | 30500 |

---

## 🔒 Cookie Requirements

De backend moet een **HTTP-only secure cookie** zetten met:

```
Set-Cookie: session=<session_id>; 
  HttpOnly; 
  Secure; 
  SameSite=Lax; 
  Path=/; 
  Domain=192.168.124.50
```

### Cookie Properties:
- **HttpOnly**: Voorkomt JavaScript toegang (XSS protection)
- **Secure**: Alleen via HTTPS (gebruik in productie)
- **SameSite=Lax**: CSRF protection, maar staat redirects toe
- **Path=/**: Cookie geldig voor hele domain
- **Domain**: Shared tussen alle EUsuite apps op zelfde IP

---

## 🧪 Testing

### 1. Test SSO Check
```bash
curl -X GET http://192.168.124.50:30500/api/auth/me \
  -H "Cookie: session=<your_session_id>" \
  --cookie-jar cookies.txt
```

**Expected Response:**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com"
  }
}
```

### 2. Test Without Cookie
```bash
curl -X GET http://192.168.124.50:30500/api/auth/me
```

**Expected Response:**
```json
{
  "error": "Unauthorized"
}
```
**Expected Status:** 401

### 3. Test in Browser
1. Open Developer Tools → Application → Cookies
2. Verify `session` cookie exists after login
3. Check cookie properties (HttpOnly, Path, Domain)
4. Clear cookie and verify redirect to Login Portal

---

## 🐛 Troubleshooting

### Issue: "Cookie not being sent"
**Solution:**
- Check `withCredentials: true` in axios config
- Verify backend sets `Access-Control-Allow-Credentials: true`
- Check cookie Domain matches request origin

### Issue: "CORS error"
**Solution:**
Backend moet deze headers zetten:
```
Access-Control-Allow-Origin: http://192.168.124.50:30500
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

### Issue: "Infinite redirect loop"
**Solution:**
- Check `/auth/me` endpoint correct returnt 200 bij geldige cookie
- Verify Login Portal correct redirect parameter gebruikt
- Check cookie Path en Domain settings

---

## 📝 Backend Requirements

De backend moet:

1. **Cookie-based sessies ondersteunen**
   - Session ID in HTTP-only cookie
   - Sessie opslag (Redis/database)

2. **CORS correct configureren**
   ```python
   from flask_cors import CORS
   
   CORS(app, 
        origins=["http://192.168.124.50:30500"],
        supports_credentials=True)
   ```

3. **Auth middleware**
   - Check session cookie in requests
   - Return 401 als geen geldige sessie
   - Populate request.user met user data

4. **`/auth/me` endpoint**
   ```python
   @app.route('/api/auth/me')
   def get_current_user():
       if not session.get('user_id'):
           return jsonify({"error": "Unauthorized"}), 401
       
       user = User.query.get(session['user_id'])
       return jsonify({"user": user.to_dict()})
   ```

---

## ✅ Benefits van SSO

1. **Single Sign-On**: Login één keer, toegang tot alle apps
2. **Centralized Security**: Één plek voor wachtwoord policies
3. **Better UX**: Geen herhaalde logins tussen apps
4. **Unified Session Management**: Één logout, alle apps uitgelogd
5. **Simplified Code**: Geen complex token management per app

---

## 🚀 Next Steps

1. ✅ Frontend SSO integratie compleet
2. ⏳ Backend moet cookie-based auth implementeren
3. ⏳ EUsuite Login Portal moet redirect handling afmaken
4. ⏳ Test complete flow tussen alle apps

---

## 📚 Related Documentation

- [EUsuite Login Portal Docs]
- [Cookie Security Best Practices]
- [CORS Configuration Guide]
