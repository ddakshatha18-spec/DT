/**
 * Shared Alert-List Component (P3 - Alert Queue & QA)
 * Modular component reusable across P2 (Student View) and P4 (Admin Dashboard)
 */

class AlertQueueComponent {
  constructor(options = {}) {
    this.containerId = options.containerId || 'alert-queue-root';
    this.apiBaseUrl = options.apiBaseUrl || 'http://localhost:8000/api';
    this.token = options.token || null;
    this.mode = options.mode || 'admin'; // 'student' or 'admin'
    
    this.alerts = [];
    this.filterPriority = 'ALL';
    this.filterStatus = 'ALL';
    this.searchQuery = '';
    this.eventSource = null;

    this.init();
  }

  init() {
    this.renderLayout();
    this.bindEvents();
    this.fetchAlerts();
    this.connectLiveStream();
  }

  setToken(token) {
    this.token = token;
    this.fetchAlerts();
  }

  getHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  async fetchAlerts() {
    try {
      const res = await fetch(`${this.apiBaseUrl}/alerts/?limit=100`, {
        headers: this.getHeaders()
      });
      if (res.ok) {
        this.alerts = await res.json();
        this.renderList();
      }
    } catch (err) {
      console.warn('[AlertQueue] Failed to load alerts from API, using cached data:', err);
    }
  }

  connectLiveStream() {
    if (this.eventSource) {
      this.eventSource.close();
    }
    try {
      this.eventSource = new EventSource(`${this.apiBaseUrl}/alerts/stream`);
      
      this.eventSource.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.event === 'NEW_ALERT') {
            this.handleNewAlert(payload.data);
          } else if (payload.event === 'ALERT_STATUS_UPDATED') {
            this.handleStatusUpdate(payload.data);
          }
        } catch (e) {
          // Heartbeat or malformed frame
        }
      };

      this.eventSource.onerror = () => {
        // SSE auto-reconnects natively
      };
    } catch (e) {
      console.warn('[AlertQueue] SSE stream connection not available in current environment.');
    }
  }

  handleNewAlert(newAlert) {
    // Avoid duplicate inserts
    if (!this.alerts.some(a => a.id === newAlert.id)) {
      this.alerts.unshift(newAlert);
      this.renderList();
      this.playAlertSound();
    }
  }

  handleStatusUpdate(update) {
    const target = this.alerts.find(a => a.id === update.alert_id);
    if (target) {
      target.status = update.new_status;
      this.renderList();
    }
  }

  playAlertSound() {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, ctx.currentTime);
      gain.gain.setValueAtTime(0.1, ctx.currentTime);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.2);
    } catch (e) {}
  }

  async updateStatus(alertId, newStatus, remarks = '') {
    try {
      const res = await fetch(`${this.apiBaseUrl}/alerts/${alertId}/status`, {
        method: 'PATCH',
        headers: this.getHeaders(),
        body: JSON.stringify({ status: newStatus, remarks: remarks })
      });
      if (res.ok) {
        const result = await res.json();
        this.handleStatusUpdate({ alert_id: alertId, new_status: newStatus });
        return result;
      } else {
        const err = await res.json();
        alert(err.detail || 'Failed to update alert status');
      }
    } catch (e) {
      console.error('[AlertQueue] Error updating status:', e);
    }
  }

  renderLayout() {
    const root = document.getElementById(this.containerId);
    if (!root) return;

    root.innerHTML = `
      <div class="alert-queue-container">
        <div class="alert-queue-header">
          <div class="alert-queue-title">
            <h2>Campus Emergency Alert Queue</h2>
            <div class="live-indicator">
              <span class="live-dot"></span>
              Live Feed
            </div>
          </div>
          <div class="alert-counts" id="queue-counts"></div>
        </div>

        <div class="alert-filter-bar">
          <input type="text" id="queue-search" class="search-input" placeholder="Search by student, room, or emergency..." />
          <select id="queue-priority-filter" class="filter-select">
            <option value="ALL">All Priorities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
          </select>
          <select id="queue-status-filter" class="filter-select">
            <option value="ALL">All Statuses</option>
            <option value="NEW">New</option>
            <option value="ACKNOWLEDGED">Acknowledged</option>
            <option value="RESOLVED_GENUINE">Resolved (Genuine)</option>
            <option value="RESOLVED_FALSE">Resolved (False Alarm)</option>
          </select>
        </div>

        <div id="queue-list" class="alert-grid"></div>
      </div>
    `;
  }

  bindEvents() {
    const searchInput = document.getElementById('queue-search');
    const prioritySelect = document.getElementById('queue-priority-filter');
    const statusSelect = document.getElementById('queue-status-filter');

    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.searchQuery = e.target.value.toLowerCase();
        this.renderList();
      });
    }
    if (prioritySelect) {
      prioritySelect.addEventListener('change', (e) => {
        this.filterPriority = e.target.value;
        this.renderList();
      });
    }
    if (statusSelect) {
      statusSelect.addEventListener('change', (e) => {
        this.filterStatus = e.target.value;
        this.renderList();
      });
    }
  }

  getFilteredAlerts() {
    return this.alerts.filter(a => {
      const matchPriority = this.filterPriority === 'ALL' || a.priority === this.filterPriority;
      const matchStatus = this.filterStatus === 'ALL' || a.status === this.filterStatus;
      const text = `${a.alert_code} ${a.emergency_type} ${a.student_name || ''} ${a.student_roll_number || ''} ${a.building_name || ''} ${a.room_number || ''}`.toLowerCase();
      const matchSearch = !this.searchQuery || text.includes(this.searchQuery);
      return matchPriority && matchStatus && matchSearch;
    });
  }

  renderList() {
    const listEl = document.getElementById('queue-list');
    const countsEl = document.getElementById('queue-counts');
    if (!listEl) return;

    const filtered = this.getFilteredAlerts();

    if (countsEl) {
      const activeCount = this.alerts.filter(a => a.status === 'NEW' || a.status === 'ACKNOWLEDGED').length;
      countsEl.innerHTML = `<span style="font-size: 13px; color: #94a3b8;">Active Incidents: <b style="color: #ef4444;">${activeCount}</b> / Total: ${this.alerts.length}</span>`;
    }

    if (filtered.length === 0) {
      listEl.innerHTML = `<div class="empty-state">No emergency alerts matching current criteria.</div>`;
      return;
    }

    listEl.innerHTML = filtered.map(a => {
      const priorityClass = `priority-${(a.priority || 'MEDIUM').toLowerCase()}`;
      const badgeClass = `badge-${(a.priority || 'MEDIUM').toLowerCase()}`;
      const statusClass = `status-${(a.status || 'NEW').toLowerCase()}`;

      return `
        <div class="alert-card-item ${priorityClass}" id="card-${a.id}">
          <div class="alert-priority-col">
            <span class="priority-badge ${badgeClass}">${a.priority}</span>
            <div style="font-size: 11px; color: #64748b; margin-top: 6px; font-weight: 600;">${a.alert_code}</div>
          </div>

          <div class="alert-info-col">
            <h4>${a.emergency_type}</h4>
            <div class="location-badges">
              <span class="loc-chip">🏛️ ${a.building_name || a.building_code || 'Building ' + a.building_id}</span>
              <span class="loc-chip">📍 Floor ${a.floor}</span>
              <span class="loc-chip">🚪 Room ${a.room_number}</span>
              <span class="loc-chip">👤 ${a.student_name || a.student_roll_number || 'Student'}</span>
            </div>
            ${a.description ? `<p style="font-size: 13px; color: #cbd5e1; margin-top: 6px;">"${a.description}"</p>` : ''}
          </div>

          <div class="alert-actions-col">
            <span class="status-tag ${statusClass}">${a.status}</span>
            ${this.mode === 'admin' && a.status === 'NEW' ? `
              <button class="btn-action" onclick="alertQueueInstance.updateStatus(${a.id}, 'ACKNOWLEDGED', 'Responders dispatched')">Acknowledge</button>
            ` : ''}
            ${this.mode === 'admin' && a.status === 'ACKNOWLEDGED' ? `
              <div style="display: flex; gap: 6px;">
                <button class="btn-action" style="color: #10b981;" onclick="alertQueueInstance.updateStatus(${a.id}, 'RESOLVED_GENUINE', 'Handled on site')">Genuine</button>
                <button class="btn-action" style="color: #ef4444;" onclick="alertQueueInstance.updateStatus(${a.id}, 'RESOLVED_FALSE', 'Verified as false alarm')">False Alarm</button>
              </div>
            ` : ''}
          </div>
        </div>
      `;
    }).join('');
  }
}

// Global export for vanilla HTML inclusion
window.AlertQueueComponent = AlertQueueComponent;
