# Shared Alert Queue Component (P3)

This component is developed and maintained by **P3 (Alert Queue & QA)** for seamless shared use between:
- **P2 (Student App)**: View submitted personal alerts and live resolution status.
- **P4 (Admin Dashboard)**: View full campus emergency stream with Acknowledge, Genuine, and False Alarm action buttons.

## Features
- **Real-Time SSE Sync**: Subscribes directly to `GET /api/alerts/stream` for $<50\text{ms}$ incident arrival updates.
- **Pulsing Triage Badges**: `CRITICAL` (Red with glow), `HIGH` (Amber), `MEDIUM` (Blue).
- **Search & Filters**: Instant filtering by priority, status (`NEW`, `ACKNOWLEDGED`, `RESOLVED_...`), and room text.
- **Audible Beep**: Optional Web Audio API chime when a new distress signal arrives.

## How to Integrate
### 1. In Vanilla HTML / CSS / JS
Include the CSS and JS files:
```html
<link rel="stylesheet" href="/shared/components/alert_queue/alert_list.css">
<div id="alert-queue-container"></div>
<script src="/shared/components/alert_queue/alert_list.js"></script>
<script>
  const queue = new AlertQueueComponent({
    containerId: 'alert-queue-container',
    apiBaseUrl: 'http://localhost:8000/api',
    mode: 'admin', // or 'student'
    token: userAccessToken
  });
</script>
```

### 2. In React (P2 or P4)
Can be imported as a component or wrapped via `useEffect` with the `AlertQueueComponent` class.
