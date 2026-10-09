# API Conventions — Organizational Brain (Backend)

> Source of truth for API URL conventions, standardized error responses, and HTTP status codes.
> Verified against test suite in `backend/tests/test_api_v1_health.py` and `backend/tests/test_errors.py`.

---

## 1. URL Structure & Versioning

- **Root Endpoints**:
  - `GET /health`: Minimal root health check returning `{"status": "ok"}`.
- **Versioned Base Path**:
  - All version 1 domain routes and operations are mounted under `/api/v1`.
- **Infrastructure Health**:
  - `GET /api/v1/health/db`: Tests database reachability via `SELECT 1`.
    - Success (200 OK): `{"status": "ok", "database": "up"}`.
    - Failure (503 Service Unavailable): Standardized error envelope with `"code": "SERVICE_UNAVAILABLE"`, strictly omitting database credentials, hostnames, and connection strings.

---

## 2. Standardized Error Response Format

Every API error response (whether from `HTTPException`, request validation, or unhandled exceptions) returns a JSON object following this exact envelope:

```json
{
  "error": {
    "code": "<machine_code>",
    "message": "<human text>",
    "details": <optional>
  }
}
```

- `code` (string, required): A deterministic, machine-readable string in upper snake case (e.g., `NOT_FOUND`, `VALIDATION_ERROR`, `INTERNAL_SERVER_ERROR`).
- `message` (string, required): Human-readable error description safe for client consumption.
- `details` (any, optional): Present only when structured diagnostic information is available (e.g., list of validation field errors or custom structured error objects). Omitted when empty.

---

## 3. Status Codes and Standard Error Code Mapping

| HTTP Status | Standard Code | Description & Behavior |
|---|---|---|
| `200 OK` | — | Successful request. |
| `400 Bad Request` | `BAD_REQUEST` | Malformed request or business logic rejection. |
| `401 Unauthorized` | `UNAUTHORIZED` | Authentication missing or invalid. |
| `403 Forbidden` | `FORBIDDEN` | Authenticated actor lacks permission. |
| `404 Not Found` | `NOT_FOUND` | Requested route or entity not found. |
| `405 Method Not Allowed` | `METHOD_NOT_ALLOWED` | HTTP method not supported for route. |
| `409 Conflict` | `CONFLICT` | State conflict (e.g. duplicate unique key). |
| `422 Unprocessable Content` | `VALIDATION_ERROR` | Schema or field validation failure. `details` is a list of objects with `field`, `message`, and `type`. Submitted inputs and internal contexts are omitted. |
| `500 Internal Server Error` | `INTERNAL_SERVER_ERROR` | Unhandled server error. Message is always `"Internal server error"`. Full stack trace logged server-side only. |
| `503 Service Unavailable` | `SERVICE_UNAVAILABLE` | Downstream infrastructure unavailable (e.g., database connection loss). Credentials sanitized. |
| *Other statuses* | `HTTP_<status>` | Automatic fallback for unmapped HTTP status codes. |

---

## 4. Validation Error Details Schema

When request validation fails (HTTP 422), `error.details` contains a list of field error objects:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "body.quantity",
        "message": "Input should be a valid integer, unable to parse string as an integer",
        "type": "int_parsing"
      }
    ]
  }
}
```

Each detail object contains:
- `field` (string): Dotted path indicating the location of the error (e.g. `body.email`, `query.limit`).
- `message` (string): Human-readable validation description.
- `type` (string): Machine-readable validator type identifier.
- Raw submitted values (`input`) and internal validator contexts (`ctx`) are never exposed to prevent secret leakage.

---

## 5. Header Preservation

Custom headers attached to `HTTPException` instances (such as `WWW-Authenticate`, `Retry-After`, or custom tracking headers) are preserved on the outgoing response.

---

## 6. Error Message Content Policy

**Error messages (including custom validator messages) must never contain the submitted value.**

- This applies to all layers: ORM validators, HTTP handlers, validation error details, and any custom exception message.
- Reason: submitted values may contain passwords, tokens, PII, or attacker-controlled input. Echoing them in error responses creates security and privacy vulnerabilities.
- The `details` list in 422 errors exposes `field` (location), `message` (description), and `type` (validator kind) only. The raw `input` field from Pydantic's error output is stripped before returning.
