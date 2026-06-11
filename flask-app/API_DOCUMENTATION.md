# API Documentation — College Complaint Management System

Base URL: `http://localhost:5000/api`

All protected endpoints require: `Authorization: Bearer <jwt_token>`

---

## Authentication

### POST /api/auth/register
Register a new student account.

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@college.edu",
  "password": "secret123",
  "confirm_password": "secret123"
}
```

**Response 201:**
```json
{
  "message": "Registered successfully.",
  "data": {
    "token": "<jwt_token>",
    "user": { "id": 1, "name": "John Doe", "email": "john@college.edu", "role": "student" }
  }
}
```

---

### POST /api/auth/login
Authenticate and receive a JWT token.

**Request Body:**
```json
{ "email": "admin@college.edu", "password": "admin123" }
```

**Response 200:**
```json
{
  "message": "ok",
  "data": { "token": "<jwt_token>", "user": { ... } }
}
```

---

## Complaints

### GET /api/complaints *(Protected)*
- Students: returns own complaints only
- Admins: returns all complaints

### POST /api/complaints *(Protected)*
Create a new complaint.

**Request Body:**
```json
{
  "title": "WiFi not working",
  "description": "The WiFi in Room 204 has been down for 2 days.",
  "category": "Network",
  "priority": "High"
}
```

### GET /api/complaints/:id *(Protected)*
Get a single complaint by ID.

### PATCH /api/complaints/:id *(Admin only)*
Update complaint status, priority, or admin response.

```json
{
  "status": "Resolved",
  "priority": "High",
  "admin_response": "Issue has been fixed.",
  "remarks": "Router replaced"
}
```

### DELETE /api/complaints/:id *(Admin only)*
Permanently delete a complaint.

---

## Notifications

### GET /api/notifications *(Protected)*
Returns last 20 notifications for the authenticated user.

### POST /api/notifications/mark-read *(Protected)*
Marks all unread notifications as read.

---

## Analytics

### GET /api/analytics *(Admin only)*
Returns full analytics dashboard data:
```json
{
  "summary": { "total": 50, "pending": 10, "resolved": 30, ... },
  "by_category": { "labels": [...], "data": [...] },
  "by_status": { "labels": [...], "data": [...] },
  "by_priority": { "labels": [...], "data": [...] },
  "monthly_trend": { "labels": [...], "data": [...] },
  "top_categories": [{ "category": "Network", "count": 12 }]
}
```

---

## Reference Data

### GET /api/meta *(Public)*
Returns enumeration values used by the system.

```json
{
  "categories": ["Hostel", "Library", "Transport", ...],
  "statuses": ["Pending", "In Progress", "Resolved", ...],
  "priorities": ["Low", "Medium", "High", "Critical"]
}
```

---

## Reports (Web only, session-authenticated)

| Endpoint | Method | Description |
|---|---|---|
| `/reports/pdf` | GET | Download PDF report (admin only) |
| `/reports/excel` | GET | Download Excel report (admin only) |

Both accept optional query params: `?status=Pending&category=Network&priority=High`

---

## Demo Credentials

| Role | Email | Password |
|---|---|---|
| Admin | admin@college.edu | admin123 |
| Student | student1@college.edu | student123 |
