# Redirect Normalisatie - SSO Backend

## Overzicht

De backend auth endpoints (`/api/auth/login` en `/api/auth/register`) accepteren nu een **redirect** query parameter die automatisch genormaliseerd wordt naar een veilige relative path.

## Security Features

✅ **Alleen relative paths toegestaan** - voorkomt open redirect vulnerabilities  
✅ **Automatische fallback** - invalide redirects worden vervangen door `/dashboard`  
✅ **Path traversal bescherming** - blokkeert `..` en `//` in paths  
✅ **Absolute URL blokkering** - voorkomt phishing attacks via externe URLs  

## API Response Format

Beide endpoints retourneren nu consistente JSON:

```json
{
  "success": true,
  "redirect": "/eutype",
  "user": {
    "user_id": 123,
    "email": "user@example.com",
    "username": "user@example.com"
  }
}
```

## Frontend Implementatie

### ✅ CORRECT: Gebruik alleen relative paths

```javascript
// Login met redirect naar specifieke app
const response = await fetch(
  'http://192.168.124.50:30500/api/auth/login?redirect=/eutype',
  {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  }
);

const data = await response.json();
if (data.success) {
  // CORRECT: Gebruik de genormaliseerde redirect path
  window.location.href = `http://192.168.124.50:30080${data.redirect}`;
}
```

### ❌ FOUT: Plak geen base URLs samen

```javascript
// ❌ NOOIT DOEN - double base URL
window.location.href = data.redirect;  
// Als redirect = "http://192.168.124.50:30080/dashboard"

// ✅ CORRECT
window.location.href = `http://192.168.124.50:30080${data.redirect}`;
// Als redirect = "/dashboard"
```

## Voorbeelden

### Login Portal → EuType

```javascript
// Login portal stuurt gebruiker naar EuType na login
const loginUrl = new URL('http://192.168.124.50:30500/api/auth/login');
loginUrl.searchParams.set('redirect', '/eutype');

const response = await fetch(loginUrl, {
  method: 'POST',
  credentials: 'include',
  body: JSON.stringify({ username, password })
});

const { success, redirect } = await response.json();
if (success) {
  window.location.href = `http://192.168.124.50:30081${redirect}`;
}
```

### EuCloud → Dashboard (default)

```javascript
// Geen redirect parameter = automatisch /dashboard
const response = await fetch(
  'http://192.168.124.50:30500/api/auth/login',
  {
    method: 'POST',
    credentials: 'include',
    body: JSON.stringify({ username, password })
  }
);

const { success, redirect } = await response.json();
// redirect = "/dashboard" (default)
```

## Supported Redirect Values

| Input | Output | Status |
|-------|--------|--------|
| `null` / `undefined` | `/dashboard` | ✅ Default |
| `/dashboard` | `/dashboard` | ✅ Valid |
| `/eutype` | `/eutype` | ✅ Valid |
| `/cloud` | `/cloud` | ✅ Valid |
| `/api/files` | `/api/files` | ✅ Valid |
| `http://evil.com` | `/dashboard` | 🚫 Blocked (absolute URL) |
| `//evil.com` | `/dashboard` | 🚫 Blocked (protocol-relative) |
| `dashboard` | `/dashboard` | 🚫 Blocked (missing /) |
| `/../etc/passwd` | `/dashboard` | 🚫 Blocked (path traversal) |
| `/api//files` | `/dashboard` | 🚫 Blocked (double slash) |

## Testing

```bash
# Test redirect normalisatie
cd backend
python test_redirect_normalization.py
```

## Security Notes

1. **Open Redirect Preventie**: Backend blokkeert absolute URLs om phishing te voorkomen
2. **Path Traversal Bescherming**: `..` en `//` worden gedetecteerd en geblokkeerd
3. **Whitespace Trimming**: Leading/trailing spaces worden automatisch verwijderd
4. **Case Sensitive**: Paths zijn case-sensitive (`/Dashboard` ≠ `/dashboard`)

## Migration Guide

Als je oude code hebt die volledige URLs stuurt:

```javascript
// ❌ OUD (werkt niet meer)
const redirect = 'http://192.168.124.50:30080/dashboard';

// ✅ NIEUW
const redirect = '/dashboard';
```

De backend zal automatisch absolute URLs blokkeren en fallback naar `/dashboard`.
