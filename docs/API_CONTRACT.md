# Campus Emergency Assistance System — API Contract (v1.0)
**Owner**: P1 — Backend & Data  
**Target Consumers**: P2 (Student App), P3 (Alert Queue & QA), P4 (Admin Dashboard), P5 (Escalation & Integration)

---

## 1. Overview & Architecture Protocol
All endpoints communicate via JSON over HTTP(S).
- **Base URL**: `http://localhost:8000/api`
- **Interactive Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **OpenAPI Schema**: `http://localhost:8000/api/openapi.json`
- **Authentication**: Bearer JWT in the `Authorization` header (`Authorization: Bearer <token>`).

---

## 2. Standard Response Format
### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional descriptive status message"
}
```

### Error Response
```json
{
  "detail": "Error description or validation failure message"
}
```

---

## 3. Endpoints Matrix

| Module | Method | Endpoint | Access Role | Description |
|---|---|---|---|---|
| **Auth** | `POST` | `/api/auth/login` | Public | Roll number & password login, returns JWT token + user profile |
| **Auth** | `GET` | `/api/auth/me` | Authenticated | Fetch current logged-in user profile & offense status |
| **Locations** | `GET` | `/api/locations/buildings` | Public / Any | Retrieve all campus buildings with floor count & metadata |
| **Locations** | `GET` | `/api/locations/buildings/{id}/rooms` | Public / Any | Retrieve structured rooms for a specific building |
| **Locations** | `GET` | `/api/locations/verify` | Public / Any | Verify if a given building code & room number combination exists |
| **Alerts** | `POST` | `/api/alerts/` | Student / Any | Submit one-tap emergency alert with structured location & type |
| **Alerts** | `GET` | `/api/alerts/` | Authenticated | List alerts (Admin sees all; Student sees own alerts) |
| **Alerts** | `GET` | `/api/alerts/{id}` | Authenticated | Detailed view of a single alert including status history |
| **Alerts** | `PATCH` | `/api/alerts/{id}/status` | Admin / Security | Update status (`ACKNOWLEDGED`, `RESOLVED_GENUINE`, `RESOLVED_FALSE`) |
| **Alerts** | `GET` | `/api/alerts/stream` | Admin / Security | SSE real-time event stream for live dashboard alert queue |
| **Escalation**| `GET` | `/api/escalation/logs` | Admin / HOD | View false alarm escalation audit trail |
| **Escalation**| `GET` | `/api/escalation/student/{roll_number}` | Admin / HOD | Check warning level & false alert offense count for student |

---

## 4. Detailed Data Schemas

### 4.1 Authentication (`POST /api/auth/login`)
**Request Body:**
```json
{
  "roll_number": "21CS001",
  "password": "emergency123"
}
```
**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "roll_number": "21CS001",
    "full_name": "Aarav Sharma",
    "email": "aarav.sharma@campus.edu",
    "phone": "+91-9876543210",
    "role": "student",
    "department": "Computer Science",
    "offense_count": 0,
    "warning_status": "none"
  }
}
```

### 4.2 Emergency Submission (`POST /api/alerts/`)
**Request Body:**
```json
{
  "emergency_type": "Medical Emergency",
  "building_id": 1,
  "room_number": "LAB-1",
  "floor": 1,
  "description": "Student collapsed near workbench",
  "latitude": 12.9716,
  "longitude": 77.5946
}
```
**Response (201 Created):**
```json
{
  "id": 1,
  "alert_code": "ALT-20261001-001",
  "student_roll_number": "21CS001",
  "student_name": "Aarav Sharma",
  "emergency_type": "Medical Emergency",
  "priority": "CRITICAL",
  "status": "NEW",
  "building_name": "Engineering Block A",
  "room_number": "LAB-1",
  "floor": 1,
  "created_at": "2026-10-01T10:15:30Z"
}
```

### 4.3 Status Update & Progressive Escalation (`PATCH /api/alerts/{id}/status`)
**Request Body:**
```json
{
  "status": "RESOLVED_FALSE",
  "remarks": "Prank alert triggered without emergency present"
}
```
**Response (200 OK):**
```json
{
  "alert_id": 1,
  "status": "RESOLVED_FALSE",
  "escalation_triggered": true,
  "escalation_detail": {
    "offense_number": 1,
    "warning_level": "warning",
    "action_taken": "First False Alert: Formal warning issued and logged"
  }
}
```
