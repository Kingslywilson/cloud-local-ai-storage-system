/* ==========================================================================
   Dashboard Page Module
   ========================================================================== */

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();

  // Elements
  const welcomeText = document.getElementById("welcome-text");
  const cardTotalFiles = document.getElementById("card-total-files");
  const cardTotalFolders = document.getElementById("card-total-folders");
  const cardSharedFiles = document.getElementById("card-shared-files");
  const cardStorageUsed = document.getElementById("card-storage-used");
  
  const storageProgress = document.getElementById("storage-progress");
  const storageUsed = document.getElementById("storage-used");
  const storageTotal = document.getElementById("storage-total");
  const storagePercentage = document.getElementById("storage-percentage");
  
  const recentFilesTable = document.getElementById("recent-files-table");
  const dashboardLoading = document.getElementById("dashboard-loading");

  // Load User Profile for Welcome banner
  try {
    const user = await apiGet("/auth/me");
    if (welcomeText && user && user.name) {
      welcomeText.textContent = `Welcome back, ${user.name}!`;
    }
  } catch (e) {
    if (welcomeText) welcomeText.textContent = "Welcome back!";
  }

  // Load Overview Metrics & Recent Files
  async function loadDashboardData() {
    if (dashboardLoading) dashboardLoading.style.display = "block";
    
    try {
      const [files, folders, storage] = await Promise.all([
        apiGet("/files/").catch(() => []),
        apiGet("/folders/").catch(() => []),
        apiGet("/files/storage").catch(() => ({ total_files: 0, total_storage_bytes: 0, total_storage_mb: 0 }))
      ]);

      // Update Card Values
      if (cardTotalFiles) cardTotalFiles.textContent = files.length;
      if (cardTotalFolders) cardTotalFolders.textContent = folders.length;
      
      // Calculate shared files count (files with ai_analysis or shared link)
      const sharedCount = files.filter(f => f.ai_analysis && f.ai_analysis.tags).length;
      if (cardSharedFiles) cardSharedFiles.textContent = sharedCount;

      // Storage Calculation (Assuming 15GB standard free tier = 16106127360 bytes)
      const usedBytes = storage.total_storage_bytes || files.reduce((acc, f) => acc + (f.file_size || 0), 0);
      const totalCapacityBytes = 15 * 1024 * 1024 * 1024; // 15 GB
      const usedPercent = Math.min(100, ((usedBytes / totalCapacityBytes) * 100)).toFixed(1);

      if (cardStorageUsed) cardStorageUsed.textContent = formatFileSize(usedBytes);
      if (storageUsed) storageUsed.textContent = formatFileSize(usedBytes);
      if (storageTotal) storageTotal.textContent = "15 GB";
      if (storagePercentage) storagePercentage.textContent = `${usedPercent}%`;
      if (storageProgress) storageProgress.style.width = `${usedPercent}%`;

      // Render Recent Files Table (Top 5 newest files)
      if (recentFilesTable) {
        const sortedFiles = [...files].sort((a, b) => new Date(b.uploaded_at) - new Date(a.uploaded_at)).slice(0, 5);
        renderRecentFiles(sortedFiles, folders);
      }
    } catch (err) {
      showToast("Failed to load dashboard data: " + err.message, "error");
    } finally {
      if (dashboardLoading) dashboardLoading.style.display = "none";
    }
  }

  function renderRecentFiles(files, folders) {
    const tbody = recentFilesTable.querySelector("tbody");
    if (!tbody) return;

    if (files.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="state-box">
            <div class="state-icon">📁</div>
            <p>No files uploaded yet.</p>
            <a href="upload.html" class="btn btn-primary" style="margin-top:0.75rem;">Upload your first file</a>
          </td>
        </tr>
      `;
      return;
    }

    const folderMap = new Map(folders.map(f => [f.id, f.name]));

    tbody.innerHTML = files.map(file => {
      const folderName = file.folder_id ? (folderMap.get(file.folder_id) || `Folder #${file.folder_id}`) : 'Root Storage';
      const fileIcon = getFileIcon(file.file_type, file.original_name);
      
      return `
        <tr>
          <td>
            <div class="file-name-cell">
              <span class="file-icon">${fileIcon}</span>
              <a href="file-details.html?id=${file.id}" style="color:var(--text-main); text-decoration:none; font-weight:600;">
                ${file.original_name}
              </a>
            </div>
          </td>
          <td><span class="badge badge-secondary">${file.file_type || 'Unknown'}</span></td>
          <td>${formatFileSize(file.file_size)}</td>
          <td>${folderName}</td>
          <td>${formatDate(file.uploaded_at)}</td>
          <td>
            <div class="action-btns">
              <a href="file-details.html?id=${file.id}" class="icon-action-btn" title="View Details">👁️</a>
              <button onclick="downloadDashboardFile(${file.id})" class="icon-action-btn" title="Download">⬇️</button>
              <button onclick="deleteDashboardFile(${file.id})" class="icon-action-btn delete" title="Delete">🗑️</button>
            </div>
          </td>
        </tr>
      `;
    }).join("");
  }

  // Global functions for inline onclick handlers
  window.downloadDashboardFile = async (fileId) => {
    try {
      const blob = await apiGet(`/files/${fileId}/download`);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `file_${fileId}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      showToast("Download started", "success");
    } catch (e) {
      showToast("Download failed: " + e.message, "error");
    }
  };

  window.deleteDashboardFile = async (fileId) => {
    if (confirm("Are you sure you want to delete this file?")) {
      try {
        await apiDelete(`/files/${fileId}`);
        showToast("File deleted successfully", "success");
        loadDashboardData();
      } catch (e) {
        showToast("Delete failed: " + e.message, "error");
      }
    }
  };

  loadDashboardData();
});
