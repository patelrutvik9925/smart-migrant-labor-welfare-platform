/**
 * API client — communicates with the Python FastAPI backend.
 */
const API_BASE = 'http://localhost:8000/api';

let authToken = localStorage.getItem('token') || null;
let currentRole = localStorage.getItem('role') || null;
let currentUserId = localStorage.getItem('user_id') || null;
let chatThreadId = null;

async function apiCall(method, path, body = null, isFormData = false) {
  const headers = {};
  if (authToken) headers['Authorization'] = `Bearer ${authToken}`;
  if (!isFormData) headers['Content-Type'] = 'application/json';

  const opts = { method, headers };
  if (body) opts.body = isFormData ? body : JSON.stringify(body);

  try {
    const resp = await fetch(API_BASE + path, opts);
    if (resp.status === 401) { logout(); return null; }
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || 'Request failed');
    return data;
  } catch (err) {
    console.error('API error:', err);
    throw err;
  }
}

// ── Auth ──────────────────────────────────────────────────────────────────

async function requestOTP() {
  const mobile = document.getElementById('mobile').value.trim();
  const role = document.getElementById('role-select').value;
  if (!mobile) { showError('login-error', 'Please enter mobile number'); return; }

  try {
    await apiCall('POST', '/auth/otp/request', { mobile_number: mobile, role });
    document.getElementById('otp-request-form').style.display = 'none';
    document.getElementById('otp-verify-form').style.display = 'block';
  } catch (err) {
    showError('login-error', err.message);
  }
}

async function verifyOTP() {
  const mobile = document.getElementById('mobile').value.trim();
  const otp = document.getElementById('otp-input').value.trim();
  if (!otp || otp.length !== 6) { showError('verify-error', 'Enter 6-digit OTP'); return; }

  try {
    const data = await apiCall('POST', '/auth/otp/verify', { mobile_number: mobile, otp });
    authToken = data.access_token;
    currentRole = data.role;
    currentUserId = data.user_id;
    localStorage.setItem('token', authToken);
    localStorage.setItem('role', currentRole);
    localStorage.setItem('user_id', currentUserId);
    afterLogin(data);
  } catch (err) {
    showError('verify-error', 'Invalid OTP. Try again.');
  }
}

function backToMobile() {
  document.getElementById('otp-request-form').style.display = 'block';
  document.getElementById('otp-verify-form').style.display = 'none';
}

function logout() {
  authToken = null; currentRole = null; currentUserId = null;
  localStorage.clear();
  document.getElementById('user-info').style.display = 'none';
  document.getElementById('logout-btn').style.display = 'none';
  document.getElementById('page-worker').style.display = 'none';
  document.getElementById('page-admin').style.display = 'none';
  document.getElementById('page-login').style.display = 'block';
}

// ── Chat ──────────────────────────────────────────────────────────────────

async function sendChat() {
  const input = document.getElementById('chat-input');
  const msg = input.value.trim();
  if (!msg) return;
  input.value = '';
  appendChatMsg('chat-messages', msg, 'user');
  const loading = appendChatMsg('chat-messages', '...', 'agent loading');
  try {
    const data = await apiCall('POST', '/agent/chat', { message: msg, language: currentLang, thread_id: chatThreadId });
    loading.remove();
    appendChatMsg('chat-messages', data.response || 'No response', 'agent');
    if (data.thread_id) chatThreadId = data.thread_id;
  } catch (err) {
    loading.remove();
    appendChatMsg('chat-messages', 'Sorry, the assistant is unavailable. Try again.', 'agent');
  }
}

let adminChatThreadId = null;
async function sendAdminChat() {
  const input = document.getElementById('admin-chat-input');
  const msg = input.value.trim();
  if (!msg) return;
  input.value = '';
  appendChatMsg('admin-chat-messages', msg, 'user');
  const loading = appendChatMsg('admin-chat-messages', '...', 'agent loading');
  try {
    const data = await apiCall('POST', '/agent/chat', { message: msg, language: currentLang, thread_id: adminChatThreadId });
    loading.remove();
    appendChatMsg('admin-chat-messages', data.response || 'No response', 'agent');
    if (data.thread_id) adminChatThreadId = data.thread_id;
  } catch (err) {
    loading.remove();
    appendChatMsg('admin-chat-messages', 'Sorry, the assistant is unavailable.', 'agent');
  }
}

// ── Profile ───────────────────────────────────────────────────────────────

async function saveProfile() {
  const body = {
    full_name: v('p-name'), age: parseInt(v('p-age')) || null,
    gender: v('p-gender') || null,
    home_state: v('p-home-state'), current_state: v('p-current-state'),
    current_city: v('p-current-city'), occupation: v('p-occupation'),
    experience_years: parseFloat(v('p-experience')) || null,
    education: v('p-education'), employer_name: v('p-employer'),
    current_wage: parseFloat(v('p-wage')) || null,
    wage_period: v('p-wage-period'),
    working_hours_per_day: parseFloat(v('p-hours')) || null,
  };
  try {
    const data = await apiCall('POST', '/worker/profile', body);
    showSuccess('profile-msg', 'Profile saved! Worker ID: ' + data.worker_id);
  } catch (err) { showError('profile-msg', err.message); }
}

async function addSkill() {
  const body = { skill_name: v('skill-name'), skill_level: v('skill-level') };
  if (!body.skill_name) return;
  try {
    await apiCall('POST', '/worker/profile/skills', body);
    document.getElementById('skill-name').value = '';
    loadProfile();
  } catch (err) { alert(err.message); }
}

async function uploadDocument() {
  const file = document.getElementById('doc-file').files[0];
  const docType = v('doc-type');
  if (!file) return;
  const fd = new FormData();
  fd.append('document_type', docType);
  fd.append('file', file);
  try {
    const data = await apiCall('POST', '/worker/profile/documents', fd, true);
    showSuccess('doc-msg', 'Document uploaded. Extraction: ' + data.extraction_status);
  } catch (err) { showError('doc-msg', err.message); }
}

async function loadProfile() {
  try {
    const data = await apiCall('GET', '/worker/profile');
    if (data.has_profile) {
      setv('p-name', data.full_name); setv('p-age', data.age);
      setv('p-gender', data.gender); setv('p-home-state', data.home_state);
      setv('p-current-state', data.current_state); setv('p-current-city', data.current_city);
      setv('p-occupation', data.occupation); setv('p-experience', data.experience_years);
      setv('p-education', data.education); setv('p-employer', data.employer_name);
      setv('p-wage', data.current_wage); setv('p-wage-period', data.wage_period);
      setv('p-hours', data.working_hours_per_day);
      const sl = document.getElementById('skills-list');
      sl.innerHTML = data.skills.map(s => `<span class="skill-tag">${s.skill_name} (${s.skill_level || 'N/A'})</span>`).join('');
    }
  } catch (err) { console.error(err); }
}

// ── Welfare ───────────────────────────────────────────────────────────────

async function checkWelfare() {
  const query = v('welfare-query');
  if (!query) return;
  const result = document.getElementById('welfare-result');
  result.style.display = 'block';
  result.textContent = t('dashboard.loading');
  try {
    const data = await apiCall('POST', '/welfare/check', { query, language: currentLang });
    result.textContent = data.response || JSON.stringify(data);
  } catch (err) { result.textContent = 'Error: ' + err.message; }
}

async function searchKnowledge(category) {
  const query = v('kb-query');
  if (!query) return;
  const result = document.getElementById('kb-welfare-result');
  result.style.display = 'block';
  result.textContent = t('dashboard.loading');
  try {
    const data = await apiCall('POST', '/knowledge/search', { query, category, limit: 5 });
    if (!data.results || data.results.length === 0) {
      result.textContent = 'No matching records found.';
      return;
    }
    result.innerHTML = data.results.map(r =>
      `<div style="margin-bottom:14px;padding-bottom:14px;border-bottom:1px solid var(--border)">
        <strong>${r.title}</strong><br>
        <span style="font-size:12px;color:var(--muted)">[${r.category.toUpperCase()}] — ${r.source_name}</span><br>
        <p style="margin-top:6px">${r.content}</p>
        ${r.source_url ? `<a href="${r.source_url}" target="_blank" rel="noopener" style="font-size:12px;color:var(--primary)">Official source ↗</a>` : ''}
      </div>`
    ).join('');
  } catch (err) { result.textContent = 'Error: ' + err.message; }
}

// ── Wage ──────────────────────────────────────────────────────────────────

async function checkWage() {
  const body = {
    current_wage: parseFloat(v('w-wage')), wage_period: v('w-period'),
    occupation: v('w-occupation'), location_state: v('w-state'),
    working_hours_per_day: parseFloat(v('w-hours')) || null,
    language: currentLang,
  };
  if (!body.current_wage || !body.occupation || !body.location_state) { alert('Please fill wage, occupation and state'); return; }
  const result = document.getElementById('wage-result');
  result.style.display = 'block';
  result.textContent = t('dashboard.loading');
  try {
    const data = await apiCall('POST', '/wage/check', body);
    result.textContent = data.response || JSON.stringify(data);
  } catch (err) { result.textContent = 'Error: ' + err.message; }
}

// ── Grievance ─────────────────────────────────────────────────────────────

async function submitComplaint() {
  const body = {
    complaint_type: v('g-type'), description: v('g-desc'),
    location_state: v('g-state'), employer_name: v('g-employer'),
    is_anonymous: document.getElementById('g-anonymous').checked,
    language: currentLang,
  };
  if (!body.description) { alert('Please describe your complaint'); return; }
  const result = document.getElementById('grievance-result');
  result.style.display = 'block';
  try {
    const data = await apiCall('POST', '/grievance/submit', body);
    result.textContent = `✅ Complaint submitted!\nNumber: ${data.complaint_number}\nPriority: ${data.priority}\nStatus: ${data.status}`;
    document.getElementById('g-complaint-num').value = data.complaint_number;
  } catch (err) { result.textContent = 'Error: ' + err.message; }
}

async function uploadEvidence() {
  const num = v('g-complaint-num');
  const file = document.getElementById('g-evidence-file').files[0];
  if (!num || !file) { alert('Enter complaint number and select a file'); return; }
  const fd = new FormData();
  fd.append('evidence_type', v('g-evidence-type'));
  fd.append('file', file);
  try {
    const data = await apiCall('POST', `/grievance/${num}/evidence`, fd, true);
    showSuccess('evidence-msg', 'Evidence uploaded.');
  } catch (err) { showError('evidence-msg', err.message); }
}

async function checkStatus() {
  const num = v('status-number').trim().toUpperCase();
  if (!num) return;
  const result = document.getElementById('status-result');
  result.style.display = 'block';
  result.textContent = t('dashboard.loading');
  try {
    const data = await apiCall('GET', `/grievance/${num}/status`);
    result.innerHTML = `<strong>Number:</strong> ${data.complaint_number}<br>
<strong>Status:</strong> ${data.status}<br>
<strong>Priority:</strong> <span class="priority-${data.priority}">${data.priority.toUpperCase()}</span><br>
<strong>Submitted:</strong> ${new Date(data.submitted_at).toLocaleString()}<br>
<strong>Last Updated:</strong> ${new Date(data.last_updated_at).toLocaleString()}`;
  } catch (err) { result.textContent = 'Complaint not found. Check the number.'; }
}

// ── Dashboard ─────────────────────────────────────────────────────────────

async function loadWorkerDashboard() {
  try {
    const data = await apiCall('GET', '/dashboard/worker');
    const el = document.getElementById('worker-dashboard-content');
    if (!data.has_profile) {
      el.innerHTML = '<div class="card"><p>Complete your profile to see your dashboard.</p></div>'; return;
    }
    el.innerHTML = `
      <div class="dash-grid">
        <div class="dash-card"><div class="dash-num">${data.skills_count || 0}</div><div class="dash-label">Skills Registered</div></div>
        <div class="dash-card"><div class="dash-num">${data.recent_complaints?.length || 0}</div><div class="dash-label">Recent Complaints</div></div>
        <div class="dash-card"><div class="dash-num">${data.profile_complete ? '✅' : '⚠️'}</div><div class="dash-label">Profile Status</div></div>
      </div>
      <div class="card">
        <strong>${data.full_name || 'Worker'}</strong><br>
        ${data.occupation || ''} · ${data.current_location || ''}<br>
        Worker ID: ${data.worker_id || 'N/A'}
      </div>`;
  } catch (err) { console.error(err); }
}

async function loadAdminDashboard() {
  try {
    const data = await apiCall('GET', '/dashboard/admin');
    document.getElementById('admin-overview-content').innerHTML = `
      <div class="dash-grid">
        <div class="dash-card"><div class="dash-num">${data.total_workers || 0}</div><div class="dash-label">Total Workers</div></div>
        <div class="dash-card"><div class="dash-num priority-danger">${data.critical_complaints || 0}</div><div class="dash-label">Critical Complaints</div></div>
        <div class="dash-card"><div class="dash-num">${data.open_complaints || 0}</div><div class="dash-label">Open Complaints</div></div>
        <div class="dash-card"><div class="dash-num">${data.flagged_for_review || 0}</div><div class="dash-label">Flagged for Review</div></div>
      </div>`;
  } catch (err) { console.error(err); }
}

async function loadAdminKnowledge() {
  const el = document.getElementById('admin-knowledge-content');
  try {
    const data = await apiCall('GET', '/knowledge/status');
    const cats = data.categories || {};
    el.innerHTML = `<div class="dash-grid">` +
      Object.entries(cats).map(([cat, count]) =>
        `<div class="dash-card"><div class="dash-num">${count}</div><div class="dash-label">${cat.charAt(0).toUpperCase() + cat.slice(1)} Records</div></div>`
      ).join('') +
      `</div><p style="font-size:13px;color:var(--muted)">Status: ${data.status || 'ok'}</p>`;
  } catch (err) { el.innerHTML = '<p>Unable to load knowledge status.</p>'; }
}

async function adminSearchKnowledge() {
  const query = v('admin-kb-query');
  const category = v('admin-kb-cat') || null;
  if (!query) return;
  const result = document.getElementById('admin-kb-results');
  result.style.display = 'block';
  result.textContent = 'Searching...';
  try {
    const data = await apiCall('POST', '/knowledge/search', { query, category, limit: 10 });
    if (!data.results || data.results.length === 0) {
      result.textContent = 'No matching records found.';
      return;
    }
    result.innerHTML = data.results.map(r =>
      `<div style="margin-bottom:12px;padding-bottom:12px;border-bottom:1px solid var(--border)">
        <strong>[${r.category.toUpperCase()}]</strong> ${r.title}<br>
        <span style="font-size:12px;color:var(--muted)">${r.source_name}</span><br>
        <small>${r.content.slice(0, 200)}...</small><br>
        ${r.tags.length ? `<span style="font-size:11px;color:var(--primary)">Tags: ${r.tags.join(', ')}</span>` : ''}
      </div>`
    ).join('');
  } catch (err) { result.textContent = 'Error: ' + err.message; }
}

// ── Helpers ───────────────────────────────────────────────────────────────

function v(id) { return document.getElementById(id)?.value || ''; }
function setv(id, val) { const el = document.getElementById(id); if (el && val != null) el.value = val; }
function showError(id, msg) { const el = document.getElementById(id); if (el) { el.textContent = msg; el.className = 'error-msg'; } }
function showSuccess(id, msg) { const el = document.getElementById(id); if (el) { el.textContent = msg; el.className = 'success-msg'; } }

function appendChatMsg(containerId, text, cls) {
  const box = document.getElementById(containerId);
  const el = document.createElement('div');
  el.className = 'chat-msg ' + cls;
  el.textContent = text;
  box.appendChild(el);
  box.scrollTop = box.scrollHeight;
  return el;
}
