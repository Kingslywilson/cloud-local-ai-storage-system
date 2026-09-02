/* ==========================================================================
   File Details Page Module
   ========================================================================== */

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();

  // Get file_id from URL search params
  const urlParams = new URLSearchParams(window.location.search);
  const fileId = urlParams.get("id");

  if (!fileId) {
    showToast("Invalid File ID", "error");
    window.location.href = "files.html";
    return;
  }

  // DOM Elements
  const fileNameEl = document.getElementById("file-name");
  const fileTypeEl = document.getElementById("file-type");
  const fileSizeEl = document.getElementById("file-size");
  const fileFolderEl = document.getElementById("file-folder");
  const fileUploadedEl = document.getElementById("file-uploaded");

  const downloadBtn = document.getElementById("download-file-btn");
  const shareBtn = document.getElementById("share-file-btn");
  const deleteBtn = document.getElementById("delete-file-btn");

  const mediaPreviewContainer = document.getElementById("media-preview");
  const imagePreview = document.getElementById("image-preview");
  const audioPreview = document.getElementById("audio-preview");
  const videoPreview = document.getElementById("video-preview");

  const aiAnalysisSection = document.getElementById("ai-analysis-section");
  const aiSummary = document.getElementById("ai-summary");
  const aiDescription = document.getElementById("ai-description");
  const aiTags = document.getElementById("ai-tags");
  const aiInsights = document.getElementById("ai-insights");
  const aiCreatedAt = document.getElementById("ai-created-at");

  async function loadFileDetails() {
    try {
      // 1. Fetch file list to find file metadata & folder info
      const [files, folders] = await Promise.all([
        apiGet("/files/"),
        apiGet("/folders/").catch(() => [])
      ]);

      const file = files.find(f => String(f.id) === String(fileId));
      if (!file) {
        showToast("File not found", "error");
        window.location.href = "files.html";
        return;
      }

      const folderMap = new Map(folders.map(f => [f.id, f.name]));
      const folderName = file.folder_id ? (folderMap.get(file.folder_id) || `Folder #${file.folder_id}`) : 'Root';

      // Fill Metadata
      if (fileNameEl) fileNameEl.textContent = file.original_name;
      if (fileTypeEl) fileTypeEl.textContent = file.file_type || "Unknown";
      if (fileSizeEl) fileSizeEl.textContent = formatFileSize(file.file_size);
      if (fileFolderEl) fileFolderEl.textContent = folderName;
      if (fileUploadedEl) fileUploadedEl.textContent = formatDate(file.uploaded_at);

      // Setup Media Preview
      setupMediaPreview(file);

      // Setup Action Buttons
      setupActions(file);

      // Fetch AI Analysis details
      loadAiAnalysis(file);

    } catch (err) {
      showToast("Error loading file details: " + err.message, "error");
    }
  }

  function setupMediaPreview(file) {
    if (!mediaPreviewContainer) return;

    const fileType = (file.file_type || "").toLowerCase();
    const fileName = (file.original_name || "").toLowerCase();

    // Reset previews
    if (imagePreview) imagePreview.style.display = "none";
    if (audioPreview) audioPreview.style.display = "none";
    if (videoPreview) videoPreview.style.display = "none";

    const downloadUrl = `${API_BASE_URL}/files/${file.id}/download`;

    // IMAGE
    if (fileType.includes("image") || /\.(jpg|jpeg|png|webp|gif|svg)$/.test(fileName)) {
      if (imagePreview) {
        imagePreview.src = downloadUrl;
        imagePreview.style.display = "block";
      }
    } 
    // AUDIO
    else if (fileType.includes("audio") || /\.(mp3|wav|m4a|aac|ogg|flac)$/.test(fileName)) {
      if (audioPreview) {
        audioPreview.src = downloadUrl;
        audioPreview.style.display = "block";
      }
    } 
    // VIDEO
    else if (fileType.includes("video") || /\.(mp4|mov|avi|mkv|webm)$/.test(fileName)) {
      if (videoPreview) {
        videoPreview.src = downloadUrl;
        videoPreview.style.display = "block";
      }
    } 
    // PDF
    else if (fileType.includes("pdf") || fileName.endsWith(".pdf")) {
      mediaPreviewContainer.innerHTML = `
        <iframe src="${downloadUrl}" style="width:100%; height:450px; border:none; border-radius:var(--radius-lg);"></iframe>
      `;
    } 
    // UNSUPPORTED MEDIA
    else {
      const fileIcon = getFileIcon(file.file_type, file.original_name);
      mediaPreviewContainer.innerHTML = `
        <div style="padding: 3rem; text-align: center;">
          <div style="font-size: 4rem; margin-bottom: 1rem;">${fileIcon}</div>
          <p style="color:var(--text-muted); margin-bottom: 1rem;">Preview not available for this file format.</p>
          <a href="${downloadUrl}" target="_blank" class="btn btn-primary">Download File</a>
        </div>
      `;
    }
  }

  function setupActions(file) {
    const renameBtn = document.getElementById("rename-file-btn");
    const moveBtn = document.getElementById("move-file-btn");

    if (downloadBtn) {
      downloadBtn.addEventListener("click", async () => {
        try {
          const blob = await apiGet(`/files/${file.id}/download`);
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = file.original_name;
          document.body.appendChild(a);
          a.click();
          a.remove();
          showToast("Download started", "success");
        } catch (e) {
          showToast("Download error: " + e.message, "error");
        }
      });
    }

    if (renameBtn) {
      renameBtn.addEventListener("click", () => {
        openGlobalRenameModal(file.id, file.original_name, () => loadFileDetails());
      });
    }

    if (moveBtn) {
      moveBtn.addEventListener("click", () => {
        openGlobalMoveModal(file.id, file.folder_id, () => loadFileDetails());
      });
    }

    if (shareBtn) {
      shareBtn.addEventListener("click", () => {
        openGlobalShareModal(file.id, file.original_name);
      });
    }

    if (deleteBtn) {
      deleteBtn.addEventListener("click", async () => {
        if (confirm(`Are you sure you want to delete "${file.original_name}"?`)) {
          try {
            await apiDelete(`/files/${file.id}`);
            showToast("File deleted successfully", "success");
            window.location.href = "files.html";
          } catch (e) {
            showToast("Delete failed: " + e.message, "error");
          }
        }
      });
    }
  }

  async function loadAiAnalysis(file) {
    try {
      const aiData = await apiGet(`/files/${file.id}/ai-analysis`).catch(() => file.ai_analysis);

      if (!aiData || (!aiData.summary && !aiData.description && !aiData.tags && !aiData.insights)) {
        if (aiAnalysisSection) {
          aiAnalysisSection.innerHTML = `
            <div class="ai-card" style="border-color: var(--border-color);">
              <div class="ai-card-header">
                <span class="ai-sparkle-icon">✨</span>
                <span class="ai-title">AI File Analysis</span>
              </div>
              <p style="color:var(--text-muted); font-size:0.9rem;">AI analysis not available for this file.</p>
            </div>
          `;
        }
        return;
      }

      if (aiSummary) aiSummary.textContent = aiData.summary || "No summary provided.";
      if (aiDescription) aiDescription.textContent = aiData.description || "No description provided.";
      if (aiInsights) aiInsights.textContent = aiData.insights || "No insights provided.";
      if (aiCreatedAt && aiData.created_at) aiCreatedAt.textContent = formatDate(aiData.created_at);

      if (aiTags) {
        const tagList = parseTags(aiData.tags);
        if (tagList.length > 0) {
          aiTags.innerHTML = tagList.map(tag => `<span class="tag-badge">[${tag}]</span>`).join(" ");
        } else {
          aiTags.innerHTML = `<span style="color:var(--text-muted);">No tags</span>`;
        }
      }
    } catch (e) {
      if (aiAnalysisSection) {
        aiAnalysisSection.innerHTML = `
          <div class="ai-card" style="border-color: var(--border-color);">
            <div class="ai-card-header">
              <span class="ai-sparkle-icon">✨</span>
              <span class="ai-title">AI File Analysis</span>
            </div>
            <p style="color:var(--text-muted); font-size:0.9rem;">AI analysis not available.</p>
          </div>
        `;
      }
    }
  }

  loadFileDetails();
});
