# Team Integration Guide — Campus Emergency Assistance

This document provides clear integration instructions for each sub-module team member to interface with the **P1 Backend & Data** services.

---

## Guide for P2: Student App
### 1. Authentication
1. Call `POST /api/auth/login` with student roll number and password:
   ```json
   { "roll_number": "21CS001", "password": "emergency123" }
   ```
2. Store `access_token` in memory or `localStorage`.
3. Include header on subsequent requests:
   `Authorization: Bearer <access_token>`

### 2. Loading Buildings and Rooms
- Call `GET /api/locations/buildings` to populate your building dropdown.
- When student picks a building, call `GET /api/locations/buildings/{id}/rooms` to populate room choices.
- To verify a typed room: `GET /api/locations/verify?building=ENG-A&room_number=LAB-1`.

### 3. Triggering Panic / Emergency Alert
- Call `POST /api/alerts/`:
  ```json
  {
    "emergency_type": "Fire / Smoke",
    "building_id": 1,
    "room_number": "LAB-1",
    "description": "Optional notes"
  }
  ```
- **Error Handling**: If the student double-taps within 45 seconds, the API returns `429 Too Many Requests` with:
  ```json
  { "detail": "An active emergency alert (ALT-...) is already in progress for your account." }
  ```
  Display a reassurance modal: "Responders have already been notified!"

---

## Guide for P3: Alert Queue & QA
- **Dataset Integration**: Query all campus locations directly via `GET /api/locations/buildings` or import seed data from [`backend/data/seed_data.py`](file:///c:/Users/DELL/OneDrive/Desktop/campus%20emergency%20assistance/backend/data/seed_data.py).
- **Test Suite**: Run `python -m pytest -v backend/tests` to execute automated end-to-end integration tests.

---

## Guide for P4: Admin Dashboard
### 1. Live SSE Stream
To receive real-time push updates the instant an alert is submitted by a student:
```javascript
const eventSource = new EventSource("http://localhost:8000/api/alerts/stream");

eventSource.onmessage = (event) => {
  const payload = JSON.parse(event.data);
  if (payload.event === "NEW_ALERT") {
    // Prepend new alert to dashboard table
    console.log("New emergency:", payload.data);
  } else if (payload.event === "ALERT_STATUS_UPDATED") {
    // Update existing row status in table
  }
};
```

### 2. Reviewing & Updating Alert Status
- To acknowledge:
  ```http
  PATCH /api/alerts/{id}/status
  Authorization: Bearer <admin_token>
  { "status": "ACKNOWLEDGED", "remarks": "Team dispatched" }
  ```
- To mark genuine:
  ```http
  PATCH /api/alerts/{id}/status
  { "status": "RESOLVED_GENUINE", "remarks": "Handled successfully" }
  ```
- To mark false alarm (triggers escalation):
  ```http
  PATCH /api/alerts/{id}/status
  { "status": "RESOLVED_FALSE", "remarks": "Prank button press" }
  ```

---

## Guide for P5: Escalation & Integration
- **Escalation Rules**:
  - Offense 1: `warning`
  - Offense 2: `strong_warning`
  - Offense 3+: `referred_to_higher_authority`
- **Escalation Query API**:
  - `GET /api/escalation/logs`
  - `GET /api/escalation/student/{roll_number}`
- **Git Branching Strategy**:
  - All P1 backend development resides in `feature/p1-backend`.
  - Merged into `dev` during scheduled integration milestones.
