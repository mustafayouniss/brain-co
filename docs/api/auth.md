# Authentication & User Management API Specification

> **Ring 0 Foundation**: Verified contract for authentication, current user profile, and administrative user provisioning.
> All examples below reflect actual responses asserted in automated test suites (`backend/tests/test_auth.py`, `backend/tests/test_auth_rbac.py`, and `backend/tests/test_users.py`). Any behavior outside these verified tests is explicitly noted or omitted.

---

## 1. Authentication Overview

- **Bearer Token Scheme**: Protected endpoints require an HTTP `Authorization` header formatted as:
  ```http
  Authorization: Bearer <access_token>
  ```
- **Token Format**: HS256 JWT containing strictly `sub` (User UUID string), `iat` (issued-at Unix timestamp), and `exp` (expiration Unix timestamp).
- **Token Lifetime**: 60 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES = 60`).
- **Uniform Error Envelope**: All API error responses adhere to the standard envelope:
  ```json
  {
    "error": {
      "code": "<MACHINE_READABLE_CODE>",
      "message": "<Human-readable summary>",
      "details": [...]
    }
  }
  ```
- **Password Policy**:
  - **Account Creation (`POST /api/v1/users` & CLI)**: 12 to 128 characters. No arbitrary composition rules (no mandatory special characters or numbers).
  - **Login (`POST /api/v1/auth/login`)**: 1 to 128 characters.

---

## 2. What Is NOT Built in Ring 0

The following capabilities are explicitly deferred and **not implemented**:
- **Refresh Tokens**: Not implemented; sessions expire when the 60-minute access token expires.
- **Token Revocation / Blocklists**: Stateless tokens remain valid until expiration timestamp `exp`.
- **Login Rate Limiting**: Not implemented in Ring 0.
- **Public User Registration / Sign-up**: No self-registration endpoint exists. The first admin is provisioned via CLI; subsequent users are created by admins via `POST /api/v1/users`.
- **User Listing / Deactivation / Deletion Endpoints**: Not implemented in Ring 0.

---

## 3. Endpoints

### 3.1 `POST /api/v1/auth/login`
Authenticates a user by email and password and returns a bearer access token.

#### Headers
```http
Content-Type: application/json
```

#### Request Body
```json
{
  "email": "alice@example.com",
  "password": "validpassword1234"
}
```
*Note: `email` is trimmed and normalized to lowercase automatically. Max length is 255 characters and must contain `@`. `password` length must be 1 to 128 characters.*

#### Responses

- **200 OK** — Authentication successful:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```

- **401 Unauthorized** — Invalid credentials or inactive account:
  - **Header**: `WWW-Authenticate: Bearer`
  - **Body**:
    ```json
    {
      "error": {
        "code": "UNAUTHORIZED",
        "message": "Invalid email or password"
      }
    }
    ```
  *Security Note: Unknown email, incorrect password, and inactive user accounts return the exact same 401 status code and identical body to prevent user enumeration.*

- **422 Unprocessable Entity** — Malformed payload (e.g., missing `@` in email, password over 128 characters):
  ```json
  {
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Request validation failed",
      "details": [
        {
          "field": "body.email",
          "message": "Value error, Invalid email address",
          "type": "value_error"
        }
      ]
    }
  }
  ```
  *Security Note: Submitted passwords are never echoed in 422 error messages or logs.*

---

### 3.2 `GET /api/v1/auth/me`
Retrieves the profile of the currently authenticated user.

#### Headers
```http
Authorization: Bearer <access_token>
```

#### Responses

- **200 OK** — Profile retrieved:
  ```json
  {
    "id": "18f99e4b-9d41-45ce-84f9-2f22b821be04",
    "email": "dave@example.com",
    "full_name": "Dave",
    "role": "employee",
    "is_active": true,
    "created_at": "2026-10-09T13:30:00+00:00"
  }
  ```
  *Security Note: `hashed_password` is never included in the response.*

- **401 Unauthorized** — Missing, invalid, expired, or deactivated credentials:
  - **Header**: `WWW-Authenticate: Bearer`
  - **Body**:
    ```json
    {
      "error": {
        "code": "UNAUTHORIZED",
        "message": "Could not validate credentials"
      }
    }
    ```
  *Security Note: Missing token, garbage token, expired token, deleted user, and inactive user produce the identical 401 body.*

---

### 3.3 `POST /api/v1/users`
Creates a new user account. Accessible **only by administrators** (`role == "admin"`).

#### Headers
```http
Authorization: Bearer <admin_access_token>
Content-Type: application/json
```

#### Request Body
```json
{
  "email": "new@example.com",
  "full_name": "New User",
  "password": "ValidPassword123!",
  "role": "employee"
}
```
*Constraints: `email` max 255 chars with `@`; `full_name` 1–255 chars; `password` 12–128 chars; `role` must be `"admin"` or `"employee"`.*

#### Responses

- **201 Created** — User account provisioned:
  ```json
  {
    "id": "2b311fc9-b6bb-49e0-811c-2c93d9b4db76",
    "email": "new@example.com",
    "full_name": "New User",
    "role": "employee",
    "is_active": true,
    "created_at": "2026-10-09T14:10:00+00:00"
  }
  ```
  *Security Note: `hashed_password` is never included in the response.*

- **401 Unauthorized** — Missing or invalid token:
  - **Header**: `WWW-Authenticate: Bearer`
  - **Body**:
    ```json
    {
      "error": {
        "code": "UNAUTHORIZED",
        "message": "Could not validate credentials"
      }
    }
    ```

- **403 Forbidden** — Caller is an employee or has non-admin role:
  ```json
  {
    "error": {
      "code": "FORBIDDEN",
      "message": "Insufficient privileges"
    }
  }
  ```
  *Security Note: Caller role is verified directly against the database row on each request, never trusted from token claims.*

- **409 Conflict** — Email address already registered:
  ```json
  {
    "error": {
      "code": "CONFLICT",
      "message": "An account with this email already exists"
    }
  }
  ```
  *Note: Case-insensitive enforcement via PostgreSQL unique index `uq_users_email_lower`.*

- **422 Unprocessable Entity** — Password too short (<12), too long (>128), or invalid role:
  ```json
  {
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Request validation failed",
      "details": [
        {
          "field": "body.password",
          "message": "String should have at least 12 characters",
          "type": "string_too_short"
        }
      ]
    }
  }
  ```
