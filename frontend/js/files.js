/* ==========================================================================
   All Files Page Module
   ========================================================================== */

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();

  // DOM Elements
  const filesSearch = document.getElementById("files-search");
  const fileTypeFilter = document.getElementById("file-type-filter");
  const folderFilter = document.getElementById("folder-filter");
  const sortFilter = document.getElementById("sort-filter");
  const filesTable = document.getElementById("files-table");
  const filesLoading = document.getElementById("files-loading");
  const filesEmpty = document.getElementById("files-empty");
  const filesError = document.getElementById("files-error");

  let allFiles = [];
  let allFolders = [];

  // Fetch initial files & folders
  async function loadFilesData() {
    if (filesLoading) filesLoading.style.display = "block";
    if (filesEmpty) filesEmpty.style.display = "none";
    if (filesError) filesError.style.display = "none";

    try {
      const [files, folders] = await Promise.all([
        apiGet("/files/"),
        apiGet("/folders/").catch(() => [])
      ]);

      allFiles = files || [];
      allFolders = folders || [];

      populateFolderFilter();
      renderFilteredFiles();
    } catch (err) {
      if (filesError) {
        filesError.textContent = "Unable to load files: " + err.message;
        filesError.style.display = "block";
      }
      showToast("Error loading files", "error");
    } finally {
      if (filesLoading) filesLoading.style.display = "none";
    }
  }

  function populateFolderFilter() {
    if (!folderFilter) return;
    folderFilter.innerHTML = `<option value="all">All Folders</option>`;
    allFolders.forEach(folder => {
      folderFilter.innerHTML += `<option value="${folder.id}">${folder.name}</option>`;
    });
  }

  function renderFilteredFiles() {
    if (!filesTable) return;
    const tbody = filesTable.querySelector("tbody");
    if (!tbody) return;

    let filtered = [...allFiles];

    // 1. Search Query
    const searchTerm = (filesSearch?.value || "").trim().toLowerCase();
    if (searchTerm) {
      filtered = filtered.filter(f => f.original_name.toLowerCase().includes(searchTerm));
    }

    // 2. File Type Filter
    const typeValue = fileTypeFilter?.value || "all";
    if (typeValue !== "all") {
      filtered = filtered.filter(f => {
        const type = (f.file_type || "").toLowerCase();
        const name = (f.original_name || "").toLowerCase();

        if (typeValue === "pdf") return type.includes("pdf") || name.endsWith(".pdf");
        if (typeValue === "docx") return type.includes("word") || name.endsWith(".docx");
        if (typeValue === "txt") return type.includes("text") || name.endsWith(".txt");
        if (typeValue === "csv") return type.includes("csv") || name.endsWith(".csv");
        if (typeValue === "image") return type.includes("image") || /\.(jpg|jpeg|png|webp|gif)$/.test(name);
        if (typeValue === "audio") return type.includes("audio") || /\.(mp3|wav|m4a|flac)$/.test(name);
        if (typeValue === "video") return type.includes("video") || /\.(mp4|mov|avi|mkv)$/.test(name);
        if (typeValue === "code") return /\.(py|js|jsx|java|c|cpp|h|html|css|sql)$/.test(name);
        return true;
      });
    }

    // 3. Folder Filter
    const folderValue = folderFilter?.value || "all";
    if (folderValue !== "all") {
      filtered = filtered.filter(f => String(f.folder_id) === String(folderValue));
    }

    // 4. Sort Filter
    const sortValue = sortFilter?.value || "newest";
    filtered.sort((a, b) => {
      if (sortValue === "newest") return new Date(b.uploaded_at) - new Date(a.uploaded_at);
      if (sortValue === "oldest") return new Date(a.uploaded_at) - new Date(b.uploaded_at);
      if (sortValue === "name-asc") return a.original_name.localeCompare(b.original_name);
      if (sortValue === "name-desc") return b.original_name.localeCompare(a.original_name);
      if (sortValue === "size-desc") return (b.file_size || 0) - (a.file_size || 0);
      if (sortValue === "size-asc") return (a.file_size || 0) - (b.file_size || 0);
      return 0;
    });

    // Check empty state
    if (filtered.length === 0) {
      tbody.innerHTML = "";
      if (filesEmpty) filesEmpty.style.display = "block";
      return;
    } else {
      if (filesEmpty) filesEmpty.style.display = "none";
    }

    const folderMap = new Map(allFolders.map(f => [f.id, f.name]));

    tbody.innerHTML = filtered.map(file => {
      const folderName = file.folder_id ? (folderMap.get(file.folder_id) || `Folder #${file.folder_id}`) : 'Root';
      const fileIcon = getFileIcon(file.file_type, file.original_name);
      
      const hasAi = file.ai_analysis && (file.ai_analysis.summary || file.ai_analysis.tags);
      const aiStatusBadge = hasAi 
        ? `<span class="badge badge-ai">✨ Analyzed</span>`
        : `<span class="badge badge-secondary">Pending</span>`;

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
          <td><span class="badge badge-secondary">${file.file_type || 'File'}</span></td>
          <td>${formatFileSize(file.file_size)}</td>
          <td>${folderName}</td>
          <td>${formatDate(file.uploaded_at)}</td>
          <td>${aiStatusBadge}</td>
          <td>
            <div class="action-btns">
              <a href="file-details.html?id=${file.id}" class="icon-action-btn" title="View Details">👁️</a>
              <button onclick="downloadFile(${file.id})" class="icon-action-btn" title="Download">⬇️</button>
              <button onclick="renameFile(${file.id}, '${escapeHtml(file.original_name)}')" class="icon-action-btn" title="Rename File">✏️</button>
              <button onclick="moveFile(${file.id}, ${file.folder_id || 'null'})" class="icon-action-btn" title="Move File">📁</button>
              <button onclick="shareFile(${file.id}, '${escapeHtml(file.original_name)}')" class="icon-action-btn" title="Share Link">🔗</button>
              <button onclick="deleteFile(${file.id})" class="icon-action-btn delete" title="Delete">🗑️</button>
            </div>
          </td>
        </tr>
      `;
    }).join("");
  }

  // Helper escape
  function escapeHtml(text) {
    if (!text) return "";
    return text.replace(/'/g, "&#39;").replace(/"/g, "&quot;");
  }

  // Event Listeners for Filters
  if (filesSearch) filesSearch.addEventListener("input", renderFilteredFiles);
  if (fileTypeFilter) fileTypeFilter.addEventListener("change", renderFilteredFiles);
  if (folderFilter) folderFilter.addEventListener("change", renderFilteredFiles);
  if (sortFilter) sortFilter.addEventListener("change", renderFilteredFiles);

  // Global Actions
  window.downloadFile = async (fileId) => {
    try {
      const blob = await apiGet(`/files/${fileId}/download`);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `file_${fileId}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      showToast("File download started", "success");
    } catch (e) {
      showToast("Download failed: " + e.message, "error");
    }
  };

  window.renameFile = (fileId, currentName) => {
    openGlobalRenameModal(fileId, currentName, () => loadFilesData());
  };

  window.moveFile = (fileId, currentFolderId) => {
    openGlobalMoveModal(fileId, currentFolderId, () => loadFilesData());
  };

  window.shareFile = (fileId, fileName) => {
    openGlobalShareModal(fileId, fileName);
  };

  window.deleteFile = async (fileId) => {
    if (confirm("Are you sure you want to delete this file?")) {
      try {
        await apiDelete(`/files/${fileId}`);
        showToast("File deleted successfully", "success");
        loadFilesData();
      } catch (e) {
        showToast("Delete failed: " + e.message, "error");
      }
    }
  };

  loadFilesData();
});

