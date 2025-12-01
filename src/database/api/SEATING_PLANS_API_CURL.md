# Seating Plans API - Postman cURL Commands

## Base URL

Assuming the API is running on `http://localhost:8000` (adjust as needed)

## Authentication

All endpoints require authentication. First, login to get an access token, then use it in subsequent requests.

---

## 0. Login to Get Access Token

**POST** - Login with email and password to receive JWT access token

```bash
curl --location 'http://localhost:8000/auth/login' \
--header 'Content-Type: application/json' \
--data '{
    "email": "admin@example.com",
    "password": "your_password"
}'
```

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Success Response (200):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_type": "admin",
  "id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Error Response (401):**

```json
{
  "detail": "Invalid email or password"
}
```

**Note:**

- Save the `access_token` from the response
- Use it in the `Authorization: Bearer <token>` header for all protected endpoints
- Token expires after 1 hour (default)
- Works for all user types: admin, investigator, invigilator, and student

**Example with token extraction:**

```bash
# Login and save token to variable (Linux/Mac)
TOKEN=$(curl -s -X POST 'http://localhost:8000/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.com","password":"your_password"}' \
  | jq -r '.access_token')

# Use token in subsequent requests
curl --location 'http://localhost:8000/seating-plans' \
  --header "Authorization: Bearer $TOKEN"
```

---

## 1. Get All Seating Plans

**GET** - List all seating plans with pagination

```bash
curl --location 'http://localhost:8000/seating-plans?page=1&limit=20' \
--header 'Authorization: Bearer YOUR_AUTH_TOKEN' \
--header 'Cookie: session=YOUR_SESSION_COOKIE'
```

**With Status Filter:**

```bash
curl --location 'http://localhost:8000/seating-plans?page=1&limit=20&status=completed' \
--header 'Authorization: Bearer YOUR_AUTH_TOKEN' \
--header 'Cookie: session=YOUR_SESSION_COOKIE'
```

**Query Parameters:**

- `page` (optional, default: 1) - Page number
- `limit` (optional, default: 20, max: 100) - Items per page
- `status` (optional) - Filter by status: `completed`, `processing`, or `failed`

---

## 2. Get Seating Plan by ID

**GET** - Get a specific seating plan by UUID

```bash
curl --location 'http://localhost:8000/seating-plans/123e4567-e89b-12d3-a456-426614174000' \
--header 'Authorization: Bearer YOUR_AUTH_TOKEN' \
--header 'Cookie: session=YOUR_SESSION_COOKIE'
```

**Replace** `123e4567-e89b-12d3-a456-426614174000` with the actual plan UUID.

---

## 3. Assign Student to Seat

**POST** - Assign a student to a specific seat (Admin only)

```bash
curl --location 'http://localhost:8000/seating-plans/123e4567-e89b-12d3-a456-426614174000/assign' \
--header 'Authorization: Bearer YOUR_AUTH_TOKEN' \
--header 'Cookie: session=YOUR_SESSION_COOKIE' \
--header 'Content-Type: application/json' \
--data '{
    "student_id": "987fcdeb-51a2-43d7-8f9e-123456789abc",
    "room_id": "456e7890-bc12-34de-f567-890123456def",
    "seat_number": "C1R1"
}'
```

**Request Body:**

```json
{
  "student_id": "UUID of the student",
  "room_id": "UUID of the room",
  "seat_number": "Seat identifier (e.g., C1R1, C2R3)"
}
```

**Note:** This endpoint requires admin privileges.

---

## 4. Delete Seating Plan

**DELETE** - Delete a seating plan (Admin only)

```bash
curl --location --request DELETE 'http://localhost:8000/seating-plans/123e4567-e89b-12d3-a456-426614174000' \
--header 'Authorization: Bearer YOUR_AUTH_TOKEN' \
--header 'Cookie: session=YOUR_SESSION_COOKIE'
```

**Replace** `123e4567-e89b-12d3-a456-426614174000` with the actual plan UUID.

**Note:** This endpoint requires admin privileges and returns 204 No Content on success.

---

## Example Response (Get All Seating Plans)

```json
{
  "plans": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "filename": "Seating Plan - CS101",
      "uploaded_by": "System",
      "uploaded_at": "2024-11-24T23:00:00",
      "status": "processing",
      "total_seats": 60,
      "rooms": [
        {
          "room_id": "456e7890-bc12-34de-f567-890123456def",
          "room_name": "C 301",
          "capacity": 60,
          "seats": [
            {
              "seat_number": "C1R1",
              "assigned_student_id": "987fcdeb-51a2-43d7-8f9e-123456789abc",
              "assigned_student_name": "John Doe"
            }
          ]
        }
      ]
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 20
}
```

---

## Authentication Methods

Depending on your authentication setup, use one of these:

### JWT Token (Bearer)

```bash
--header 'Authorization: Bearer YOUR_JWT_TOKEN'
```

### Session Cookie

```bash
--header 'Cookie: session=YOUR_SESSION_COOKIE'
```

### Both (if required)

```bash
--header 'Authorization: Bearer YOUR_JWT_TOKEN' \
--header 'Cookie: session=YOUR_SESSION_COOKIE'
```

---

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid UUID format"
}
```

### 401 Unauthorized

```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden

```json
{
  "detail": "Only admins can assign seats"
}
```

### 404 Not Found

```json
{
  "detail": "Seating plan not found"
}
```

### 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "loc": ["query", "status"],
      "msg": "string does not match regex",
      "type": "value_error.str.regex"
    }
  ]
}
```

---

## Testing Tips

1. **Get your auth token first** by logging in through the auth endpoint
2. **Use a valid UUID** for plan_id, student_id, and room_id
3. **Check the response status** - 200 for success, 204 for delete
4. **Use `-v` flag** for verbose output to see headers:
   ```bash
   curl -v --location 'http://localhost:8000/seating-plans'
   ```
