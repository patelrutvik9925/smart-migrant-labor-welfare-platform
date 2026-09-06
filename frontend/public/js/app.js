/**
 * App initialization and navigation logic.
 */

function afterLogin(data) {
  document.getElementById('user-info').textContent = `Role: ${data.role}`;
  document.getElementById('user-info').style.display = 'inline';
  document.getElementById('logout-btn').style.display = 'inline';
  document.getElementById('page-login').style.display = 'none';

  if (data.role === 'worker') {
    document.getElementById('page-worker').style.display = 'flex';
    loadProfile();
    loadWorkerDashboard();
  } else {
    document.getElementById('page-admin').style.display = 'flex';
    loadAdminDashboard();
  }
}

function showTab(tabId) {
  document.querySelectorAll('#page-worker .tab').forEach(t => t.style.display = 'none');
  document.querySelectorAll('#page-worker .nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(tabId).style.display = 'block';
  const buttons = document.querySelectorAll('#page-worker .nav-btn');
  buttons.forEach(b => { if (b.getAttribute('onclick')?.includes(tabId)) b.classList.add('active'); });
  if (tabId === 'tab-dashboard') loadWorkerDashboard();
  if (tabId === 'tab-profile') loadProfile();
}

function showAdminTab(tabId) {
  document.querySelectorAll('#page-admin .tab').forEach(t => t.style.display = 'none');
  document.querySelectorAll('#page-admin .nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(tabId).style.display = 'block';
  const buttons = document.querySelectorAll('#page-admin .nav-btn');
  buttons.forEach(b => { if (b.getAttribute('onclick')?.includes(tabId)) b.classList.add('active'); });
}

// Auto-login if token exists
window.addEventListener('DOMContentLoaded', () => {
  setLang('en');
  if (authToken && currentRole) {
    afterLogin({ role: currentRole, user_id: currentUserId });
  }
});
