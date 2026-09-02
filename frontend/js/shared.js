/* ==========================================================================
   Shared Files Page Module
   ========================================================================== */

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();

  // Elements
  const tabMyShares = document.getElementById("tab-my-shares");
  const tabSharedWithMe = document.getElementById("tab-shared-with-me");

  const sectionMyShares = document.getElementById("section-my-shares");
  const sectionSharedWithMe = document.getElementById("section-shared-with-me");

  const mySharesTable = document.getElementById("my-shares-table");
  const mySharesEmpty = document.getElementById("my-shares-empty");

  const sharedWithMeTable = document.getElementById("shared-with-me-table");
  const sharedWithMeEmpty = document.getElementById("shared-with-me-empty");

  // Tab Toggle Handler
  if (tabMyShares && tabSharedWithMe) {
    tabMyShares.addEventListener("click", () => {
      tabMyShares.classList.add("active");
      tabSharedWithMe.classList.remove("active");
      if (sectionMyShares) sectionMyShares.style.display = "block";
      if (sectionSharedWithMe) sectionSharedWithMe.style.display = "none";
      loadMyShares();
    });

    tabSharedWithMe.addEventListener("click", () => {
      tabSharedWithMe.classList.add("active");
      tabMyShares.classList.remove("active");
      if (sectionMyShares) sectionMyShares.style.display = "none";
      if (sectionSharedWithMe) sectionSharedWithMe.style.display = "block";
      loadSharedWithMe();
    });
  }

  // Load My Created Share Links
  async function loadMyShares() {
    const tbody = mySharesTable?.querySelector("tbody");
    if (!tbody) return;

    try {
      const shares = await apiGet("/files/my-shares");

      if (!shares || shares.length === 0) {
        tbody.innerHTML = "";
        if (mySharesEmpty) mySharesEmpty.style.display = "block";
        return;
      } else {
        if (mySharesEmpty) mySharesEmpty.style.display = "none";
      }

      tbody.innerHTML = shares.map(share => {
        const icon = getFileIcon(share.file_type, share.original_name);
        const accessBadge = share.share_type === "user" 
          ? `<span class="badge badge-primary">👤 Specific User</span>`
          : `<span class="badge badge-success">🌐 Public Link</span>`;

        const targetUserText = share.share_type === "user"
          ? `<strong style="color:var(--text-main);">${escapeHtml(share.shared_with_email)}</strong>`
          : `<span style="color:var(--text-muted);">Anyone with link</span>`;

        return `
          <tr>
            <td>
              <div class="file-name-cell">
                <span class="file-icon">${icon}</span>
                <a href="file-details.html?id=${share.file_id}" style="color:var(--text-main); font-weight:600; text-decoration:none;">
                  ${escapeHtml(share.original_name)}
                </a>
              </div>
            </td>
            <td>${accessBadge}</td>
            <td>${targetUserText}</td>
            <td>
              <input type="text" readonly value="${share.share_url}" class="form-control" style="padding:0.3rem 0.6rem; font-size:0.8rem; width:220px;">
            </td>
            <td>${formatDate(share.created_at)}</td>
            <td>
              <div class="action-btns">
                <button onclick="copyShareUrl('${share.share_url}')" class="btn btn-secondary" style="padding:0.3rem 0.75rem; font-size:0.8rem;">📋 Copy</button>
                <button onclick="revokeShareToken('${share.share_token}')" class="icon-action-btn delete" title="Revoke Link">🚫</button>
              </div>
            </td>
          </tr>
        `;
      }).join("");

    } catch (e) {
      showToast("Error loading share links: " + e.message, "error");
    }
  }

  // Load Files Shared With Logged-in User
  async function loadSharedWithMe() {
    const tbody = sharedWithMeTable?.querySelector("tbody");
    if (!tbody) return;

    try {
      const shares = await apiGet("/files/shared-with-me");

      if (!shares || shares.length === 0) {
        tbody.innerHTML = "";
        if (sharedWithMeEmpty) sharedWithMeEmpty.style.display = "block";
        return;
      } else {
        if (sharedWithMeEmpty) sharedWithMeEmpty.style.display = "none";
      }

      tbody.innerHTML = shares.map(share => {
        const icon = getFileIcon(share.file_type, share.original_name);

        return `
          <tr>
            <td>
              <div class="file-name-cell">
                <span class="file-icon">${icon}</span>
                <a href="file-details.html?id=${share.file_id}" style="color:var(--text-main); font-weight:600; text-decoration:none;">
                  ${escapeHtml(share.original_name)}
                </a>
              </div>
            </td>
            <td>
              <div><strong>${escapeHtml(share.shared_by_name)}</strong></div>
              <div style="font-size:0.75rem; color:var(--text-muted);">${escapeHtml(share.shared_by_email)}</div>
            </td>
            <td>${formatFileSize(share.file_size)}</td>
            <td>${formatDate(share.created_at)}</td>
            <td>
              <div class="action-btns">
                <button onclick="downloadSharedFile('${share.share_url}', '${escapeHtml(share.original_name)}')" class="btn btn-primary" style="padding:0.35rem 0.85rem; font-size:0.85rem;">⬇️ Download</button>
              </div>
            </td>
          </tr>
        `;
      }).join("");

    } catch (e) {
      showToast("Error loading shared files: " + e.message, "error");
    }
  }

  // Global Actions
  window.copyShareUrl = async (url) => {
    try {
      await navigator.clipboard.writeText(url);
      showToast("Share link copied to clipboard!", "success");
    } catch (e) {
      showToast("Failed to copy link", "error");
    }
  };

  window.downloadSharedFile = async (url, filename) => {
    try {
      const response = await fetch(url, {
        headers: { "Authorization": `Bearer ${getToken()}` }
      });

      if (!response.ok) {
        let msg = "Download failed";
        try {
          const err = await response.json();
          if (err.detail) msg = err.detail;
        } catch (e) {}
        throw new Error(msg);
      }

      const blob = await response.blob();
      const link = document.createElement("a");
      link.href = window.URL.createObjectURL(blob);
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      showToast("Download started", "success");
    } catch (e) {
      showToast("Download error: " + e.message, "error");
    }
  };

  window.revokeShareToken = async (token) => {
    if (confirm("Are you sure you want to revoke this share link? Access will be removed immediately.")) {
      try {
        await apiDelete(`/files/share/${token}`);
        showToast("Share link revoked", "success");
        loadMyShares();
      } catch (e) {
        showToast("Revoke failed: " + e.message, "error");
      }
    }
  };

  function escapeHtml(text) {
    if (!text) return "";
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  // Initial Load
  loadMyShares();
});
