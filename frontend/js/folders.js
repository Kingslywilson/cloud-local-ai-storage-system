/* ==========================================================================
   Folders Page Module
   ========================================================================== */

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();

  const escapeHtml = (text) => {
    if (text === null || text === undefined) return "";
    const div = document.createElement("div");
    div.innerText = String(text);
    return div.innerHTML;
  };

  const escapeJs = (str) => {
    if (!str) return "";
    return String(str).replace(/\\/g, "\\\\").replace(/'/g, "\\'").replace(/"/g, "&quot;");
  };

  // DOM Elements
  const foldersContainer = document.getElementById("folders-container");
  const createFolderBtn = document.getElementById("create-folder-btn");
  const folderModal = document.getElementById("folder-modal");
  const folderForm = document.getElementById("folder-form");
  const folderNameInput = document.getElementById("folder-name");
  const folderSubmitBtn = document.getElementById("folder-submit");
  const folderCancelBtn = document.getElementById("folder-cancel");

  const folderFilesSection = document.getElementById("folder-files-section");
  const folderFilesTitle = document.getElementById("folder-files-title");
  const folderFilesTable = document.getElementById("folder-files-table");

  let foldersList = [];
  let filesList = [];
  let selectedFolderId = null;

  async function loadFoldersData() {
    try {
      const [folders, files] = await Promise.all([
        apiGet("/folders/"),
        apiGet("/files/").catch(() => [])
      ]);

      foldersList = Array.isArray(folders) ? folders : [];
      filesList = Array.isArray(files) ? files : [];

      renderFolderCards();
    } catch (err) {
      console.error("Error loading folders:", err);
      showToast("Failed to load folders: " + err.message, "error");
    }
  }

  function renderFolderCards() {
    if (!foldersContainer) return;

    if (foldersList.length === 0) {
      foldersContainer.innerHTML = `
        <div class="state-box" style="grid-column: 1/-1;">
          <div class="state-icon">📁</div>
          <p>No folders created yet.</p>
          <button id="empty-create-folder-btn" class="btn btn-primary" style="margin-top:1rem;">Create Folder</button>
        </div>
      `;
      const emptyBtn = document.getElementById("empty-create-folder-btn");
      if (emptyBtn) emptyBtn.addEventListener("click", openModal);
      return;
    }

    foldersContainer.innerHTML = foldersList.map(folder => {
      // Calculate file count for folder
      const count = filesList.filter(f => String(f.folder_id) === String(folder.id)).length;
      const safeName = escapeHtml(folder.name);
      const safeJsName = escapeJs(folder.name);
      
      return `
        <div class="stat-card" style="cursor:pointer;" onclick="openFolderContent(${folder.id}, '${safeJsName}')">
          <div class="stat-icon purple">📁</div>
          <div class="stat-info" style="flex:1;">
            <div style="font-weight:700; font-size:1.1rem; color:var(--text-main);">${safeName}</div>
            <div style="font-size:0.8rem; color:var(--text-muted); margin-top:0.25rem;">
              ${count} ${count === 1 ? 'file' : 'files'} • ${formatDate(folder.created_at)}
            </div>
          </div>
          <div class="action-btns" onclick="event.stopPropagation();">
            <button onclick="renameFolderPrompt(event, ${folder.id}, '${safeJsName}')" class="icon-action-btn" title="Rename Folder">✏️</button>
            <button onclick="deleteFolderPrompt(event, ${folder.id}, '${safeJsName}')" class="icon-action-btn delete" title="Delete Folder">🗑️</button>
          </div>
        </div>
      `;
    }).join("");
  }

  // View Files inside selected folder
  window.openFolderContent = async (folderId, folderName) => {
    selectedFolderId = folderId;
    if (folderFilesSection) folderFilesSection.style.display = "block";
    if (folderFilesTitle) folderFilesTitle.textContent = `Files in "${folderName}"`;

    try {
      const folderFiles = await apiGet(`/files/folder/${folderId}`).catch(() => 
        filesList.filter(f => String(f.folder_id) === String(folderId))
      );

      renderFolderFilesTable(folderFiles);
      folderFilesSection.scrollIntoView({ behavior: 'smooth' });
    } catch (e) {
      showToast("Error loading folder contents: " + e.message, "error");
    }
  };

  function renderFolderFilesTable(files) {
    if (!folderFilesTable) return;
    const tbody = folderFilesTable.querySelector("tbody");
    if (!tbody) return;

    if (!files || files.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" class="state-box">
            <p>No files inside this folder yet.</p>
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = files.map(file => {
      const icon = getFileIcon(file.file_type, file.original_name);
      return `
        <tr>
          <td>
            <div class="file-name-cell">
              <span class="file-icon">${icon}</span>
              <a href="file-details.html?id=${file.id}" style="color:var(--text-main); text-decoration:none; font-weight:600;">
                ${file.original_name}
              </a>
            </div>
          </td>
          <td><span class="badge badge-secondary">${file.file_type || 'File'}</span></td>
          <td>${formatFileSize(file.file_size)}</td>
          <td>${formatDate(file.uploaded_at)}</td>
          <td>
            <div class="action-btns">
              <a href="file-details.html?id=${file.id}" class="icon-action-btn" title="View Details">👁️</a>
              <button onclick="downloadFolderFile(${file.id})" class="icon-action-btn" title="Download">⬇️</button>
            </div>
          </td>
        </tr>
      `;
    }).join("");
  }

  window.downloadFolderFile = async (fileId) => {
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
      showToast("Download error: " + e.message, "error");
    }
  };

  // Modal Controls
  function openModal() {
    if (folderModal) folderModal.classList.add("active");
    if (folderNameInput) {
      folderNameInput.value = "";
      folderNameInput.focus();
    }
  }

  function closeModal() {
    if (folderModal) folderModal.classList.remove("active");
  }

  if (createFolderBtn) createFolderBtn.addEventListener("click", openModal);
  if (folderCancelBtn) folderCancelBtn.addEventListener("click", closeModal);

  // Submit Create Folder
  if (folderForm) {
    folderForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = folderNameInput?.value.trim();

      if (!name) {
        showToast("Folder name is required", "warning");
        return;
      }

      if (folderSubmitBtn) folderSubmitBtn.disabled = true;

      try {
        await apiPost("/folders/", { name: name });
        showToast("Folder created successfully!", "success");
        closeModal();
        loadFoldersData();
      } catch (err) {
        showToast("Create folder failed: " + err.message, "error");
      } finally {
        if (folderSubmitBtn) folderSubmitBtn.disabled = false;
      }
    });
  }

  window.renameFolderPrompt = async (e, folderId, currentName) => {
    if (e && e.stopPropagation) e.stopPropagation();
    const newName = prompt("Enter new folder name:", currentName);
    if (newName && newName.trim() && newName.trim() !== currentName) {
      try {
        await apiPut(`/folders/${folderId}/rename`, { new_name: newName.trim() });
        showToast("Folder renamed successfully!", "success");
        loadFoldersData();
      } catch (err) {
        showToast("Rename failed: " + err.message, "error");
      }
    }
  };

  window.deleteFolderPrompt = async (e, folderId, folderName) => {
    if (e && e.stopPropagation) e.stopPropagation();
    if (confirm(`Are you sure you want to delete folder "${folderName}"? Files inside will be moved to root storage.`)) {
      try {
        await apiDelete(`/folders/${folderId}`);
        showToast("Folder deleted successfully!", "success");
        if (selectedFolderId === folderId && folderFilesSection) {
          folderFilesSection.style.display = "none";
        }
        loadFoldersData();
      } catch (err) {
        showToast("Delete failed: " + err.message, "error");
      }
    }
  };

  loadFoldersData();
});

