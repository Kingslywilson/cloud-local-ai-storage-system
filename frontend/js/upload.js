/* ==========================================================================
   Upload Page Module
   ========================================================================== */

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();

  // Elements
  const uploadForm = document.getElementById("upload-form");
  const fileInput = document.getElementById("file-input");
  const folderSelect = document.getElementById("folder-select");
  const uploadSubmit = document.getElementById("upload-submit");
  const dropzone = document.getElementById("dropzone");
  
  const uploadProgress = document.getElementById("upload-progress");
  const uploadProgressBar = document.getElementById("upload-progress-bar");
  const uploadStatus = document.getElementById("upload-status");

  const uploadResult = document.getElementById("upload-result");
  const uploadedFileName = document.getElementById("uploaded-file-name");
  const uploadedFileType = document.getElementById("uploaded-file-type");
  const uploadedFileSize = document.getElementById("uploaded-file-size");
  const uploadedFileId = document.getElementById("uploaded-file-id");

  const aiResult = document.getElementById("ai-result");
  const aiSummary = document.getElementById("ai-summary");
  const aiDescription = document.getElementById("ai-description");
  const aiTags = document.getElementById("ai-tags");
  const aiInsights = document.getElementById("ai-insights");
  const aiLoading = document.getElementById("ai-loading");
  const aiError = document.getElementById("ai-error");

  // Load Folders for select dropdown
  async function loadFolders() {
    if (!folderSelect) return;
    try {
      const folders = await apiGet("/folders/");
      folderSelect.innerHTML = `<option value="">Root (No Folder)</option>`;
      folders.forEach(f => {
        folderSelect.innerHTML += `<option value="${f.id}">${f.name}</option>`;
      });
    } catch (e) {
      console.warn("Could not load folders:", e);
    }
  }

  // Drag & Drop handlers
  if (dropzone && fileInput) {
    dropzone.addEventListener("click", () => fileInput.click());

    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
      });
    });

    dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files.length > 0) {
        fileInput.files = files;
        updateSelectedFileName(files[0].name);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) {
        updateSelectedFileName(fileInput.files[0].name);
      }
    });
  }

  function updateSelectedFileName(name) {
    const selectedText = document.getElementById("selected-file-text");
    if (selectedText) {
      selectedText.textContent = `Selected: ${name}`;
      selectedText.style.color = "var(--primary)";
      selectedText.style.fontWeight = "600";
    }
  }

  // Form Submit Handler
  if (uploadForm) {
    uploadForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      if (!fileInput.files || fileInput.files.length === 0) {
        showToast("Please select a file to upload.", "warning");
        return;
      }

      const file = fileInput.files[0];
      const folderId = folderSelect?.value;

      const formData = new FormData();
      formData.append("file", file);
      if (folderId) {
        formData.append("folder_id", folderId);
      }

      // UI Reset
      if (uploadSubmit) uploadSubmit.disabled = true;
      if (uploadProgress) uploadProgress.style.display = "block";
      if (uploadProgressBar) uploadProgressBar.style.width = "40%";
      if (uploadStatus) uploadStatus.textContent = "Uploading & Analyzing file with Generative AI...";
      
      if (uploadResult) uploadResult.style.display = "none";
      if (aiResult) aiResult.style.display = "none";
      if (aiError) aiError.style.display = "none";
      if (aiLoading) aiLoading.style.display = "block";

      try {
        const response = await apiUpload("/files/upload", formData);

        if (uploadProgressBar) uploadProgressBar.style.width = "100%";
        if (uploadStatus) uploadStatus.textContent = "Upload complete!";

        showToast("File uploaded successfully!", "success");

        // Display File Upload Metadata
        if (uploadResult) {
          uploadResult.style.display = "block";
          if (uploadedFileName) uploadedFileName.textContent = response.file_name || file.name;
          if (uploadedFileType) uploadedFileType.textContent = response.file_type || file.type || "Unknown";
          if (uploadedFileSize) uploadedFileSize.textContent = formatFileSize(response.file_size || file.size);
          if (uploadedFileId) uploadedFileId.textContent = response.file_id || "-";
        }

        // Render AI Analysis Output
        renderAiAnalysis(response.ai_analysis);

      } catch (err) {
        showToast("Upload failed: " + err.message, "error");
        if (uploadStatus) uploadStatus.textContent = "Upload failed.";
        if (aiError) {
          aiError.textContent = "AI Analysis Error: " + err.message;
          aiError.style.display = "block";
        }
      } finally {
        if (uploadSubmit) uploadSubmit.disabled = false;
        if (aiLoading) aiLoading.style.display = "none";
      }
    });
  }

  function renderAiAnalysis(ai) {
    if (!aiResult) return;

    if (!ai || (!ai.summary && !ai.description && !ai.tags && !ai.insights)) {
      if (aiError) {
        aiError.textContent = "AI Analysis is currently unavailable for this file format.";
        aiError.style.display = "block";
      }
      return;
    }

    aiResult.style.display = "block";
    
    if (aiSummary) aiSummary.textContent = ai.summary || "No summary generated.";
    if (aiDescription) aiDescription.textContent = ai.description || "No description available.";
    if (aiInsights) aiInsights.textContent = ai.insights || "No additional insights.";

    // Render Smart Tags as Badges
    if (aiTags) {
      const tagsList = parseTags(ai.tags);
      if (tagsList.length > 0) {
        aiTags.innerHTML = tagsList.map(tag => `<span class="tag-badge">#${tag}</span>`).join(" ");
      } else {
        aiTags.innerHTML = `<span style="color:var(--text-muted);">No tags</span>`;
      }
    }
  }

  loadFolders();
});
