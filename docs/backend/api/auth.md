# Authentication API Contract

> Generated from the actual tested API implementation in Ring 0.
> For frontend and mobile consumers (OPEN-5).
> Last updated: 2026-10-13

---

## Base URL

```
http://localhost:8000/api/v1
```

---

## Authentication Scheme

The API uses Bearer Token authentication (JWT HS256).

### Header Format

```
Authorization: Bearer <access_token>
```

### Token Payload

```json
{
  "sub": "<user_uuid>",
  "iat": 1728400000,
  "exp": 1728403600
}
```

- `sub`: User UUID string identifier
- `iat`: Issued-at timestamp (UTC)
- `exp`: Expiration timestamp (UTC, default 60 minutes)

### Token Security

- Roles and email are NOT included in the token payload
- Roles are resolved from the database on each request
- Tokens are stateless; "sign out" = client discards the token
- No refresh tokens or server-side revocation in Ring 0

---

## Endpoints

### POST /api/v1/auth/login

Authenticate a user and receive an access token.

#### Request

```http
POST /api/v1/auth/login HTTP/1.1
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "secure-password-here"
}
```

#### Request Schema

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| email | string | Yes | Valid email, case-insensitive, max 255 chars |
| password | string | Yes | Min 12 chars, max 128 chars |

#### Success Response (200 OK)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Error Responses

**401 Unauthorized** (Invalid credentials, unknown email, or inactive user)

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid email or password"
  }
}
```

**Note:** The same 401 response is returned for:
- Unknown email
- Wrong password
- Inactive user

This prevents user enumeration attacks.

**422 Unprocessable Entity** (Validation error)

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      {
        "loc": ["body", "email"],
        "message": "Invalid email address",
        "type": "value_error"
      }
    ]
  }
}
```

#### Security Notes

- Passwords are never returned in any response
- Email is case-insensitive during lookup
- Opportunistic rehash: if password hashing parameters are outdated, the hash is upgraded silently on successful login
- Dummy hash verification for unknown users defeats timing attacks

---

### GET /api/v1/auth/me

Get the authenticated user's profile.

#### Request

```http
GET /api/v1/auth/me HTTP/1.1
Authorization: Bearer <access_token>
```

#### Success Response (200 OK)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "admin@example.com",
  "full_name": "Alice Smith",
  "role": "admin",
  "is_active": true,
  "created_at": "2026-10-13T12:00:00Z"
}
```

#### Response Schema

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | User identifier |
| email | string | User email (lowercase) |
| full_name | string | User's full name |
| role | string | Either "admin" or "employee" |
| is_active | boolean | Account active status |
| created_at | string (ISO 8601) | Account creation timestamp |

**Note:** `hashed_password` is NEVER included in the response.

#### Error Responses

**401 Unauthorized** (Missing token, invalid token, expired token, or inactive user)

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Could not validate credentials"
  }
}
```

Headers include: `WWW-Authenticate: Bearer`

---

### POST /api/v1/users (Admin Only)

Create a new user account. Only accessible to users with `role="admin"`.

#### Request

```http
POST /api/v1/users HTTP/1.1
Authorization: Bearer <admin_access_token>
Content-Type: application/json

{
  "email": "employee@example.com",
  "full_name": "John Doe",
  "password": "secure-password-12-chars",
  "role": "employee"
}
```

#### Request Schema

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| email | string | Yes | Valid email, case-insensitive, max 255 chars |
| full_name | string | Yes | Min 1 char, max 255 chars |
| password | string | Yes | Min 12 chars, max 128 chars |
| role | string | Yes | Must be "admin" or "employee" |

#### Success Response (201 Created)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "email": "employee@example.com",
  "full_name": "John Doe",
  "role": "employee",
  "is_active": true,
  "created_at": "2026-10-13T12:30:00Z"
}
```

#### Error Responses

**401 Unauthorized** (Missing or invalid token)

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Could not validate credentials"
  }
}
```

**403 Forbidden** (Non-admin user attempts to create user)

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Insufficient privileges"
  }
}
```

**409 Conflict** (Email already exists, case-insensitive)

```json
{
  "error": {
    "code": "CONFLICT",
    "message": "An account with this email already exists"
  }
}
```

**422 Unprocessable Entity** (Validation error)

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      {
        "loc": ["body", "password"],
        "message": "String should have at least 12 characters",
        "type": "string_too_short"
      }
    ]
  }
}
```

**Note:** The password field is never echoed in error responses.

---

## Unified Error Format

All endpoints return errors in the following format:

```json
{
  "error": {
    "code": "<ERROR_CODE>",
    "message": "<Human-readable message>",
    "details": <Optional additional context>
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|------------|-------------|
| UNAUTHORIZED | 401 | Authentication failed or missing |
| FORBIDDEN | 403 | Authorization failed (insufficient privileges) |
| VALIDATION_ERROR | 422 | Request validation failed |
| CONFLICT | 409 | Resource conflict (e.g., duplicate email) |
| NOT_FOUND | 404 | Resource not found |
| INTERNAL_ERROR | 500 | Unexpected server error |

---

## Admin Seed Command

The first admin user is created via a CLI command, not a public endpoint.

```bash
cd backend
python -m app.scripts.create_admin --email admin@example.com --full-name "Alice Smith"
```

The command will:
1. Prompt for password twice (no terminal echo)
2. Validate password length (min 12 chars)
3. Create admin account with role="admin"
4. Exit with error if email already exists

**Note:** Do not use public sign-up endpoints. Only admins can create employee accounts.

---

## Authorization Requirements

### Endpoints Requiring Authentication

- `GET /api/v1/auth/me`
- `POST /api/v1/users`

### Endpoints Requiring Admin Role

- `POST /api/v1/users`

### Role Resolution

Roles are resolved from the database at request time, NOT from the JWT token payload. This ensures:
- Immediate role changes take effect
- Token tampering cannot elevate privileges
- Inactive users are rejected even with valid tokens

---

## Testing Examples

### Successful Login Flow

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"secure-password-12-chars"}'

# Response: {"access_token":"...","token_type":"bearer"}

# Get current user
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"

# Response: User profile JSON
```

### Create Employee (Admin Only)

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"email":"employee@example.com","full_name":"John Doe","password":"secure-password-12-chars","role":"employee"}'

# Response: 201 Created with user profile
```

---

## Integration Notes for Frontend/Mobile

1. **Store tokens securely** (e.g., httpOnly cookies or secure storage)
2. **Handle 401 responses** by redirecting to login or prompting re-authentication
3. **Do not cache role information** from tokens; fetch fresh user data from `/auth/me`
4. **Validate emails client-side** before sending (email format, length)
5. **Enforce password complexity** client-side (min 12 chars) before sending
6. **Display generic auth errors** to users; do not reveal whether email exists
7. **Include Bearer token** in Authorization header for protected endpoints
8. **Handle token expiration** by re-prompting login on 401 responses

---

## Dependencies

This contract depends on:
- Ring 0 Foundation (backend, database, auth skeleton)
- `users` table with UUID PK, case-insensitive email, role constraint
- Argon2id password hashing
- PyJWT HS256 token signing
- Server-side role enforcement

No CRM, domain-specific, or later-ring functionality is required for this contract.
