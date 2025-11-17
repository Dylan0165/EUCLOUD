# EU-CORE-BACKEND API Contract

## Overview
This document describes the API contract for integrating with the EU-CORE-BACKEND service. This backend supports multiple applications including EuCloud (file browser), EuType (document editor), and future applications like EuSheets.

**Base URL**: `http://192.168.124.50:30500/api`

**Authentication**: JWT Bearer token (24-hour expiry)

---

## Authentication

### 1. Register User
**POST** `/auth/register`

Create a new user account.

**Request Body**:
```json
{
  "username": "string (min 3 chars)",
  "email": "valid email address",
  "password": "string (min 6 chars)"
}
```

**Response** (201 Created):
```json
{
  "message": "User registered successfully",
  "user": {
    "user_id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "storage_used": 0,
    "storage_quota": 5368709120,
    "created_at": "2024-01-15T10:30:00"
  }
}
```

**Errors**:
- `400`: Username or email already exists
- `422`: Validation error (invalid email, short password, etc.)

---

### 2. Login
**POST** `/auth/login`

Authenticate and receive JWT token.

**Request Body**:
```json
{
  "username": "testuser",
  "password": "password123"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Errors**:
- `401`: Invalid credentials

**Usage**: Include token in subsequent requests as:
```
Authorization: Bearer <access_token>
```

---

### 3. Get Current User
**GET** `/auth/me`

Get authenticated user information.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "user_id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "storage_used": 1024000,
  "storage_quota": 5368709120,
  "created_at": "2024-01-15T10:30:00"
}
```

**Errors**:
- `401`: Invalid or expired token

---

## File Operations

### 4. Upload File
**POST** `/files/upload`

Upload a new file to the system.

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Form Data**:
- `file`: File (required)
- `folder_id`: Integer (optional) - Parent folder ID
- `app_type`: String (optional, default: "generic") - One of: `generic`, `eutype`, `eusheets`

**Response** (201 Created):
```json
{
  "message": "File uploaded successfully",
  "file": {
    "file_id": 123,
    "filename": "document.ty",
    "file_path": "1/a1b2c3d4-e5f6-7890-abcd-ef1234567890.ty",
    "file_size": 2048,
    "mime_type": "application/octet-stream",
    "app_type": "eutype",
    "owner_id": 1,
    "folder_id": null,
    "is_favorite": false,
    "created_at": "2024-01-15T12:00:00",
    "modified_at": "2024-01-15T12:00:00"
  }
}
```

**Errors**:
- `400`: No file selected or file type not allowed
- `413`: Storage quota exceeded
- `403`: Invalid folder

**Allowed Extensions**: 
- Documents: pdf, doc, docx, txt, md, ty
- Images: jpg, jpeg, png, gif, svg, webp
- Archives: zip, rar, tar, gz
- Data: json, csv, xml
- And more (see config.py)

---

### 5. List Files
**GET** `/files/list`

List files and folders for the current user.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Query Parameters**:
- `folder_id`: Integer (optional) - Filter by folder. Omit for root level.

**Response** (200 OK):
```json
{
  "files": [
    {
      "file_id": 123,
      "filename": "document.ty",
      "file_size": 2048,
      "mime_type": "application/octet-stream",
      "app_type": "eutype",
      "is_favorite": false,
      "created_at": "2024-01-15T12:00:00",
      "modified_at": "2024-01-15T12:00:00"
    }
  ],
  "folders": [
    {
      "folder_id": 456,
      "folder_name": "Documents",
      "parent_folder_id": null,
      "created_at": "2024-01-15T11:00:00"
    }
  ]
}
```

---

### 6. Get File Metadata
**GET** `/files/{file_id}`

Get metadata for a specific file.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "file": {
    "file_id": 123,
    "filename": "document.ty",
    "file_path": "1/a1b2c3d4-e5f6-7890-abcd-ef1234567890.ty",
    "file_size": 2048,
    "mime_type": "application/octet-stream",
    "app_type": "eutype",
    "owner_id": 1,
    "folder_id": null,
    "is_favorite": false,
    "created_at": "2024-01-15T12:00:00",
    "modified_at": "2024-01-15T12:00:00"
  }
}
```

**Errors**:
- `404`: File not found or not owned by user

---

### 7. Download File
**GET** `/files/{file_id}/download`

Download file content as binary stream.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
- Binary file content
- `Content-Type`: File's MIME type
- `Content-Disposition`: attachment; filename="..."

**Errors**:
- `404`: File not found

---

### 8. Get File Content (NEW - for EuType)
**GET** `/files/{file_id}/content`

Get raw text content of a file for editing.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "file_id": 123,
  "filename": "document.ty",
  "content": "{\n  \"type\": \"document\",\n  \"content\": \"Hello world\"\n}",
  "app_type": "eutype",
  "modified_at": "2024-01-15T12:00:00"
}
```

**Errors**:
- `404`: File not found
- `400`: File is not text-based (binary file)

**Use Case**: EuType reads this to load document content into editor.

---

### 9. Update File Content (NEW - for EuType)
**PUT** `/files/{file_id}/content`

Update raw text content of a file.

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/x-www-form-urlencoded
```

**Form Data**:
- `content`: String (required) - New file content

**Response** (200 OK):
```json
{
  "message": "File content updated successfully",
  "file": {
    "file_id": 123,
    "filename": "document.ty",
    "file_size": 2150,
    "modified_at": "2024-01-15T12:05:00"
  }
}
```

**Errors**:
- `404`: File not found
- `413`: Storage quota exceeded
- `500`: Error writing file

**Use Case**: EuType saves document changes by sending updated content.

**Important**: 
- File size is recalculated and quota is updated
- `modified_at` timestamp is updated automatically
- Storage quota is enforced

---

### 10. Rename File
**PUT** `/files/{file_id}/rename`

Rename a file.

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/x-www-form-urlencoded
```

**Form Data**:
- `new_name`: String (required)

**Response** (200 OK):
```json
{
  "message": "File renamed successfully",
  "file": { ... }
}
```

**Errors**:
- `400`: Invalid filename or extension
- `404`: File not found

---

### 11. Delete File
**DELETE** `/files/{file_id}`

Move file to trash (soft delete).

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "message": "File moved to trash"
}
```

**Errors**:
- `404`: File not found

---

## Storage Information

### 12. Get Storage Usage
**GET** `/storage/usage`

Get current storage usage statistics.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "storage_used": 1024000,
  "storage_quota": 5368709120,
  "percentage_used": 0.019,
  "storage_used_mb": 0.98,
  "storage_quota_mb": 5120.0
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request (validation error, invalid input)
- `401`: Unauthorized (missing or invalid token)
- `403`: Forbidden (permission denied)
- `404`: Not Found
- `413`: Payload Too Large (quota exceeded)
- `422`: Unprocessable Entity (validation error)
- `500`: Internal Server Error

---

## Integration Guide for EuType

### Workflow for Document Editing

1. **User Authentication**:
   ```javascript
   // Login
   const loginResponse = await fetch('http://192.168.124.50:30500/api/auth/login', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ username: 'user', password: 'pass' })
   });
   const { access_token } = await loginResponse.json();
   ```

2. **List Available Documents**:
   ```javascript
   const filesResponse = await fetch('http://192.168.124.50:30500/api/files/list', {
     headers: { 'Authorization': `Bearer ${access_token}` }
   });
   const { files } = await filesResponse.json();
   // Filter for .ty files: files.filter(f => f.filename.endsWith('.ty'))
   ```

3. **Load Document Content**:
   ```javascript
   const contentResponse = await fetch(`http://192.168.124.50:30500/api/files/${fileId}/content`, {
     headers: { 'Authorization': `Bearer ${access_token}` }
   });
   const { content } = await contentResponse.json();
   // Parse JSON if needed: JSON.parse(content)
   ```

4. **Save Document Changes**:
   ```javascript
   const formData = new FormData();
   formData.append('content', JSON.stringify(documentData));
   
   const saveResponse = await fetch(`http://192.168.124.50:30500/api/files/${fileId}/content`, {
     method: 'PUT',
     headers: { 'Authorization': `Bearer ${access_token}` },
     body: formData
   });
   ```

5. **Create New Document**:
   ```javascript
   const formData = new FormData();
   const blob = new Blob([JSON.stringify({ type: 'document', content: '' })], { type: 'application/json' });
   formData.append('file', blob, 'New Document.ty');
   formData.append('app_type', 'eutype');
   
   const uploadResponse = await fetch('http://192.168.124.50:30500/api/files/upload', {
     method: 'POST',
     headers: { 'Authorization': `Bearer ${access_token}` },
     body: formData
   });
   ```

---

## Storage Architecture

### User-Based Directory Structure

Files are stored in user-specific directories:

```
uploads/
├── 1/                          # User ID 1
│   ├── uuid1.ty               # File for user 1
│   ├── uuid2.pdf
│   └── uuid3.png
├── 2/                          # User ID 2
│   ├── uuid4.ty
│   └── uuid5.docx
└── ...
```

### File Path Format
- **Database**: Stores relative path `{owner_id}/{file_id}.{ext}`
- **Filesystem**: Full path `uploads/{owner_id}/{file_id}.{ext}`
- **File ID**: UUID v4 (unique identifier)
- **Filename**: Original user-provided name (stored separately)

---

## Multi-App Type System

The `app_type` field categorizes files by application:

| App Type  | Description           | Example Files |
|-----------|-----------------------|---------------|
| generic   | Standard files        | PDFs, images  |
| eutype    | EuType documents      | .ty files     |
| eusheets  | Spreadsheet files     | Future        |

**Usage**: Filter files by app_type when listing documents for specific applications.

---

## Rate Limits & Quotas

- **JWT Expiry**: 24 hours
- **Default Storage Quota**: 5 GB per user
- **Max File Size**: Limited by storage quota
- **Request Rate**: No explicit limit (use responsibly)

---

## CORS Configuration

Allowed origins:
- `http://192.168.124.50:30080` (EuCloud)
- `http://192.168.124.50:30081` (EuType)
- `http://localhost:5173` (Development)
- `http://localhost:30080`
- `http://localhost:30081`

---

## Version History

- **v2.0.0** (Current): FastAPI migration, multi-app support, content endpoints
- **v1.0.0**: Original Flask implementation

---

## Support & Contact

For issues or questions about this API, contact the backend development team or refer to the main project documentation.
