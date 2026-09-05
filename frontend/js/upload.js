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

      // UI Reset & Progress Animation
      if (uploadSubmit) uploadSubmit.disabled = true;
      if (uploadProgress) uploadProgress.style.display = "block";
      if (uploadProgressBar) uploadProgressBar.style.width = "15%";
      if (uploadStatus) uploadStatus.textContent = "Uploading file to storage...";
      
      if (uploadResult) uploadResult.style.display = "none";
      if (aiResult) aiResult.style.display = "none";
      if (aiError) aiError.style.display = "none";
      if (aiLoading) aiLoading.style.display = "block";

      // Progress animation ticker while waiting for backend + AI processing
      let currentProgress = 15;
      const progressInterval = setInterval(() => {
        if (currentProgress < 40) {
          currentProgress += 10;
          if (uploadProgressBar) uploadProgressBar.style.width = `${currentProgress}%`;
          if (uploadStatus) uploadStatus.textContent = "Running 3-Tier Security & ML Behavioral Scan...";
        } else if (currentProgress < 85) {
          currentProgress += 5;
          if (uploadProgressBar) uploadProgressBar.style.width = `${currentProgress}%`;
          if (uploadStatus) uploadStatus.textContent = "Generating AI Summary, Tags & Insights with Gemini Flash...";
        } else if (currentProgress < 95) {
          currentProgress += 1;
          if (uploadProgressBar) uploadProgressBar.style.width = `${currentProgress}%`;
          if (uploadStatus) uploadStatus.textContent = "Finalizing AI Analysis & saving record...";
        }
      }, 1500);

      try {
        const response = await apiUpload("/files/upload", formData);
        clearInterval(progressInterval);

        if (uploadProgressBar) uploadProgressBar.style.width = "100%";
        if (uploadStatus) uploadStatus.textContent = "Upload & AI Analysis complete!";

        showToast("File uploaded successfully!", "success");

        // Display File Upload Metadata
        if (uploadResult) {
          uploadResult.style.display = "block";
          if (uploadedFileName) uploadedFileName.textContent = response.file_name || file.name;
          if (uploadedFileType) uploadedFileType.textContent = response.file_type || file.type || "Unknown";
          if (uploadedFileSize) uploadedFileSize.textContent = formatFileSize(response.file_size || file.size);
          if (uploadedFileId) uploadedFileId.textContent = response.file_id || "-";
        }

        // Render ML & AI Analysis Output
        renderMlAnalysis(response.ml_analysis);
        renderAiAnalysis(response.ai_analysis);

      } catch (err) {
        showToast("Upload canceled due to security threat!", "error");
        if (uploadStatus) uploadStatus.textContent = "Upload canceled.";
        
        if (aiError) {
          let detailObj = null;
          try {
            detailObj = JSON.parse(err.message);
          } catch(e) {}

          if (detailObj && detailObj.reason) {
            let riskListHtml = "";
            if (detailObj.risk_factors && detailObj.risk_factors.length > 0) {
              riskListHtml = `<ul style="margin-top:0.5rem; margin-left:1.25rem; font-size:0.9rem;">` +
                detailObj.risk_factors.map(r => `<li>${r}</li>`).join("") +
                `</ul>`;
            }
            aiError.innerHTML = `
              <div style="font-weight:700; font-size:1.05rem; margin-bottom:0.35rem; color:#b91c1c;">
                🛑 Upload Canceled By 3-Tier Security Scanner
              </div>
              <div style="font-size:0.95rem; font-weight:600; color:#7f1d1d;">${detailObj.reason}</div>
              ${riskListHtml}
              <div style="font-size:0.8rem; margin-top:0.5rem; color:#991b1b; font-style:italic;">
                🛡️ Security Action: The file was permanently deleted from disk and rejected before storing.
              </div>
            `;
          } else {
            aiError.innerHTML = `<strong>Upload Failed:</strong> ${err.message}`;
          }
          aiError.style.display = "block";
        }
      } finally {
        if (typeof progressInterval !== "undefined") clearInterval(progressInterval);
        if (uploadSubmit) uploadSubmit.disabled = false;
        if (aiLoading) aiLoading.style.display = "none";
      }
    });
  }

  function renderMlAnalysis(ml) {
    const mlResultBox = document.getElementById("ml-result");
    const mlCategoryVal = document.getElementById("ml-category-val");
    const mlConfidenceVal = document.getElementById("ml-confidence-val");
    const mlSecurityVal = document.getElementById("ml-security-val");

    if (!mlResultBox || !ml) return;

    mlResultBox.style.display = "block";
    if (mlCategoryVal) mlCategoryVal.textContent = ml.predicted_category || "Document / General";
    if (mlConfidenceVal) {
      const pct = ml.confidence_percentage ? `${ml.confidence_percentage}%` : (ml.confidence ? `${(ml.confidence * 100).toFixed(1)}%` : "90.0%");
      mlConfidenceVal.textContent = pct;
    }
    if (mlSecurityVal) {
      if (ml.is_suspicious) {
        mlSecurityVal.innerHTML = `<span style="color:#ef4444; font-weight:700;">⚠️ Suspicious Activity Flagged</span> (${ml.suspicious_details || "Unusual pattern"})`;
      } else {
        mlSecurityVal.innerHTML = `<span style="color:#10b981; font-weight:700;">✅ Normal Upload</span> (${ml.suspicious_details || "No anomalies detected"})`;
      }
    }
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
