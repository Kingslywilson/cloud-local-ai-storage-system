/* ==========================================================================
   Activity History Page Module
   ========================================================================== */

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();

  const activityTable = document.getElementById("activity-table");
  const activityLoading = document.getElementById("activity-loading");
  const activityEmpty = document.getElementById("activity-empty");

  function getActionBadge(action) {
    const act = (action || '').toUpperCase();
    if (act === 'UPLOAD') return '<span class="badge badge-success">📤 UPLOAD</span>';
    if (act === 'DOWNLOAD') return '<span class="badge badge-primary">⬇️ DOWNLOAD</span>';
    if (act === 'VIEW') return '<span class="badge badge-secondary">👁️ VIEW</span>';
    if (act === 'DELETE') return '<span class="badge badge-danger">🗑️ DELETE</span>';
    if (act === 'RENAME') return '<span class="badge badge-warning">✏️ RENAME</span>';
    if (act === 'MOVE') return '<span class="badge badge-secondary">📁 MOVE</span>';
    if (act === 'SHARE') return '<span class="badge badge-primary">🔗 SHARE</span>';
    if (act === 'SHARE_ACCESS') return '<span class="badge badge-success">🔗 SHARE ACCESS</span>';
    if (act === 'SHARE_REVOKE') return '<span class="badge badge-danger">🚫 SHARE REVOKE</span>';
    if (act === 'LOGIN') return '<span class="badge badge-success">🔑 LOGIN</span>';
    if (act === 'LOGOUT') return '<span class="badge badge-secondary">🚪 LOGOUT</span>';
    if (act === 'REGISTER') return '<span class="badge badge-ai">✨ REGISTER</span>';
    if (act.includes('FOLDER')) return `<span class="badge badge-primary">📂 ${act}</span>`;
    return `<span class="badge badge-secondary">${act}</span>`;
  }

  async function loadActivityHistory() {
    if (activityLoading) activityLoading.style.display = "block";
    if (activityEmpty) activityEmpty.style.display = "none";

    try {
      const activityData = await apiGet("/activity").catch(() => []);

      const tbody = activityTable?.querySelector("tbody");
      if (!tbody) return;

      if (!activityData || !Array.isArray(activityData) || activityData.length === 0) {
        tbody.innerHTML = "";
        if (activityEmpty) activityEmpty.style.display = "block";
      } else {
        if (activityEmpty) activityEmpty.style.display = "none";
        tbody.innerHTML = activityData.map(act => `
          <tr>
            <td>${getActionBadge(act.action)}</td>
            <td><strong>${escapeHtml(act.file_name || 'System / Account')}</strong></td>
            <td>${formatDate(act.created_at)}</td>
            <td style="color:var(--text-muted); font-size:0.85rem;">${escapeHtml(act.details || '-')}</td>
          </tr>
        `).join("");
      }

    } catch (e) {
      console.warn("Activity fetch error:", e);
      showToast("Could not load activity history", "error");
    } finally {
      if (activityLoading) activityLoading.style.display = "none";
    }
  }

  function escapeHtml(text) {
    if (!text) return "";
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  loadActivityHistory();
});

