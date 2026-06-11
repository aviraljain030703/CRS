/**
 * College Complaint Management System — Main JS
 * Demonstrates: Functions, Event Handling, DOM Manipulation
 */

/* ---- Live Clock ---- */
(function liveClock() {
  const el = document.getElementById('liveClock');
  if (!el) return;
  const tick = () => {
    el.textContent = new Date().toLocaleString('en-IN', {
      weekday: 'short', day: 'numeric', month: 'short',
      hour: '2-digit', minute: '2-digit',
    });
  };
  tick();
  setInterval(tick, 30_000);
})();

/* ---- Sidebar toggle (mobile) ---- */
(function sidebarToggle() {
  const btn  = document.getElementById('sidebarToggle');
  const nav  = document.getElementById('sidebar');
  if (!btn || !nav) return;
  btn.addEventListener('click', () => nav.classList.toggle('open'));
  document.addEventListener('click', e => {
    if (!nav.contains(e.target) && !btn.contains(e.target)) {
      nav.classList.remove('open');
    }
  });
})();

/* ---- Auto-dismiss flash alerts ---- */
(function autoDismissAlerts() {
  document.querySelectorAll('.alert.alert-success, .alert.alert-info').forEach(el => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      bsAlert && bsAlert.close();
    }, 5000);
  });
})();

/* ---- Character counter for textareas ---- */
document.querySelectorAll('textarea[data-max]').forEach(ta => {
  const max = parseInt(ta.dataset.max, 10);
  const out = document.createElement('small');
  out.className = 'text-muted';
  ta.parentNode.insertBefore(out, ta.nextSibling);
  const update = () => {
    const left = max - ta.value.length;
    out.textContent = `${ta.value.length}/${max}`;
    out.classList.toggle('text-danger', left < 20);
  };
  ta.addEventListener('input', update);
  update();
});

/* ---- Confirm delete forms ---- */
document.querySelectorAll('form[data-confirm]').forEach(form => {
  form.addEventListener('submit', e => {
    if (!window.confirm(form.dataset.confirm || 'Are you sure?')) {
      e.preventDefault();
    }
  });
});

/* ---- Priority badge colouring in selects ---- */
function applyPriorityColor(select) {
  const map = {
    Low: 'success', Medium: 'warning', High: 'danger', Critical: 'dark'
  };
  select.className = select.className.replace(/\bborder-\w+\b/g, '');
  const cls = map[select.value];
  if (cls) select.classList.add('border-' + cls);
}
document.querySelectorAll('select[name="priority"]').forEach(s => {
  applyPriorityColor(s);
  s.addEventListener('change', () => applyPriorityColor(s));
});

/* ---- Notification badge refresh (polling every 30s) ---- */
(function pollNotifications() {
  const badges = document.querySelectorAll('[data-notif-badge]');
  if (!badges.length) return;

  const refresh = () => {
    fetch('/api/notifications', {
      headers: { 'Authorization': 'Bearer ' + (localStorage.getItem('cms_token') || '') }
    })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data) return;
        const unread = (data.data || []).filter(n => !n.is_read).length;
        badges.forEach(b => {
          b.textContent = unread || '';
          b.style.display = unread ? '' : 'none';
        });
      })
      .catch(() => {});
  };
  setInterval(refresh, 30_000);
})();

/* ---- Table row click navigation ---- */
document.querySelectorAll('table[data-row-link] tbody tr').forEach(tr => {
  const link = tr.querySelector('a[href]');
  if (link) {
    tr.style.cursor = 'pointer';
    tr.addEventListener('click', e => {
      if (!e.target.closest('button, form, a')) {
        window.location.href = link.href;
      }
    });
  }
});
