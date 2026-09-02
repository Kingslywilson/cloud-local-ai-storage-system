/* ==========================================================================
   Global Configuration & Shared Utility Functions
   ========================================================================== */

const API_BASE_URL = window.location.hostname.includes('loca.lt')
  ? "https://cloudstorageapi2026.loca.lt"
  : (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost')
    ? "http://127.0.0.1:8000"
    : `${window.location.protocol}//${window.location.hostname}:8000`;



/**
 * Format raw file size bytes into human readable KB, MB, GB string
 */
function formatFileSize(bytes) {
  if (bytes === 0 || bytes === undefined || bytes === null) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

/**
 * Format ISO Date string into human readable format (e.g. Aug 31, 2026, 10:30 AM)
 */
function formatDate(dateString) {
  if (!dateString) return "N/A";
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return dateString;
  
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

/**
 * Robust parse function for AI tags.
 * Converts JSON strings (e.g. '["tag1", "tag2"]') or arrays into JavaScript Array.
 */
function parseTags(tags) {
  if (!tags) return [];
  if (Array.isArray(tags)) return tags;
  if (typeof tags === 'string') {
    try {
      const parsed = JSON.parse(tags);
      if (Array.isArray(parsed)) return parsed;
    } catch (e) {
      // Fallback: split by comma if comma separated string
      if (tags.includes(',')) {
        return tags.split(',').map(t => t.trim()).filter(Boolean);
      }
      return [tags.trim()];
    }
  }
  return [];
}

/**
 * Determine file icon HTML/emoji based on MIME type or File Name extension
 */
function getFileIcon(fileType, fileName) {
  const type = (fileType || '').toLowerCase();
  const name = (fileName || '').toLowerCase();

  if (type.includes('pdf') || name.endsWith('.pdf')) return '📄';
  if (type.includes('word') || type.includes('document') || name.endsWith('.docx') || name.endsWith('.doc')) return '📝';
  if (type.includes('text') || name.endsWith('.txt') || name.endsWith('.md')) return '📑';
  if (type.includes('csv') || type.includes('excel') || type.includes('spreadsheet') || name.endsWith('.csv')) return '📊';
  if (type.includes('json') || name.endsWith('.json')) return '⚙️';
  if (type.includes('image') || /\.(jpg|jpeg|png|webp|gif|svg)$/.test(name)) return '🖼️';
  if (type.includes('audio') || /\.(mp3|wav|m4a|aac|ogg|flac)$/.test(name)) return '🎵';
  if (type.includes('video') || /\.(mp4|mov|avi|mkv|webm|mpeg|mpg)$/.test(name)) return '🎬';
  if (type.includes('zip') || type.includes('compressed') || type.includes('tar') || name.endsWith('.zip') || name.endsWith('.rar')) return '📦';
  if (/\.(py|js|jsx|java|c|cpp|h|html|css|sql)$/.test(name)) return '💻';

  return '📁';
}

function escapeHtml(text) {
  if (text === null || text === undefined) return "";
  const div = document.createElement("div");
  div.innerText = String(text);
  return div.innerHTML;
}
window.escapeHtml = escapeHtml;

function escapeJs(str) {
  if (!str) return "";
  return String(str).replace(/\\/g, "\\\\").replace(/'/g, "\\'").replace(/"/g, "&quot;");
}
window.escapeJs = escapeJs;

/**
 * Global Toast Notification System
 */
function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  let icon = 'ℹ️';
  if (type === 'success') icon = '✅';
  if (type === 'error') icon = '⚠️';
  if (type === 'warning') icon = '🔔';

  toast.innerHTML = `
    <div style="display: flex; align-items: center; gap: 0.5rem;">
      <span>${icon}</span>
      <span>${message}</span>
    </div>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

/**
 * Global Interactive Share Modal System
 */
function openGlobalShareModal(fileId, fileName) {
  let modalOverlay = document.getElementById('global-share-modal');
  if (!modalOverlay) {
    modalOverlay = document.createElement('div');
    modalOverlay.id = 'global-share-modal';
    modalOverlay.className = 'modal-overlay';
    modalOverlay.innerHTML = `
      <div class="modal" style="max-width:480px; position:relative;">
        <div class="modal-header" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
          <h3 class="modal-title" style="margin:0; font-size:1.2rem; color:var(--text-main);">🔗 Share File Access</h3>
          <button type="button" id="close-global-share" style="background:none; border:none; color:var(--text-muted); font-size:1.4rem; cursor:pointer;">✕</button>
        </div>

        <div style="margin-bottom:1.25rem;">
          <label class="form-label" style="font-size:0.8rem; color:var(--text-muted);">Target File</label>
          <div id="global-share-filename" style="font-weight:700; color:var(--text-main); font-size:1.05rem;"></div>
        </div>

        <div class="form-group" style="margin-bottom:1.25rem;">
          <label class="form-label">Sharing Access Type</label>
          <div style="display:flex; gap:1.25rem; margin-top:0.5rem;">
            <label style="display:flex; align-items:center; gap:0.4rem; cursor:pointer; font-weight:500;">
              <input type="radio" name="global-share-type" value="public" checked id="global-radio-public">
              <span>🌐 Public Link (Anyone)</span>
            </label>
            <label style="display:flex; align-items:center; gap:0.4rem; cursor:pointer; font-weight:500;">
              <input type="radio" name="global-share-type" value="user" id="global-radio-user">
              <span>👤 Specific User Email</span>
            </label>
          </div>
        </div>

        <div class="form-group" id="global-email-group" style="display:none; margin-bottom:1.25rem;">
          <label for="global-share-email" class="form-label">Recipient Registered Email</label>
          <input type="email" id="global-share-email" class="form-control" placeholder="user@company.com">
          <small style="color:var(--text-muted); font-size:0.75rem; display:block; margin-top:0.3rem;">Only a registered user with this email will be allowed access.</small>
        </div>

        <button type="button" id="global-generate-btn" class="btn btn-primary btn-block" style="width:100%; margin-bottom:1rem; padding:0.65rem;">
          ⚡ Generate Share Link
        </button>

        <div id="global-share-result" style="display:none; background:var(--bg-surface); padding:1rem; border-radius:var(--radius-md); border:1px solid var(--border-color);">
          <label class="form-label" style="font-size:0.8rem;">Generated Share URL</label>
          <div style="display:flex; gap:0.5rem; margin-top:0.3rem;">
            <input type="text" id="global-share-url-input" class="form-control" readonly style="font-family:monospace; font-size:0.8rem; flex:1;">
            <button type="button" id="global-copy-btn" class="btn btn-primary" style="padding:0.4rem 0.8rem; font-size:0.85rem;">📋 Copy</button>
          </div>
          <div id="global-share-badge" style="font-size:0.75rem; color:var(--success); margin-top:0.5rem; font-weight:600;"></div>
        </div>
      </div>
    `;
    document.body.appendChild(modalOverlay);

    const closeBtn = document.getElementById('close-global-share');
    const radioPublic = document.getElementById('global-radio-public');
    const radioUser = document.getElementById('global-radio-user');
    const emailGroup = document.getElementById('global-email-group');
    const generateBtn = document.getElementById('global-generate-btn');
    const copyBtn = document.getElementById('global-copy-btn');
    const urlInput = document.getElementById('global-share-url-input');

    closeBtn.addEventListener('click', () => {
      modalOverlay.classList.remove('active');
    });

    radioPublic.addEventListener('change', () => {
      if (radioPublic.checked) emailGroup.style.display = 'none';
    });

    radioUser.addEventListener('change', () => {
      if (radioUser.checked) emailGroup.style.display = 'block';
    });

    copyBtn.addEventListener('click', async () => {
      if (urlInput.value) {
        await navigator.clipboard.writeText(urlInput.value);
        showToast('Share link copied to clipboard!', 'success');
      }
    });

    generateBtn.addEventListener('click', async () => {
      const activeFileId = modalOverlay.dataset.fileId;
      const shareType = radioUser.checked ? 'user' : 'public';
      const emailVal = document.getElementById('global-share-email').value.trim();

      if (shareType === 'user' && !emailVal) {
        showToast('Please enter recipient email', 'warning');
        return;
      }

      generateBtn.disabled = true;
      generateBtn.textContent = 'Generating...';

      try {
        const res = await apiPost(`/files/${activeFileId}/share`, {
          share_type: shareType,
          shared_with_email: shareType === 'user' ? emailVal : null
        });

        if (res && res.share_url) {
          urlInput.value = res.share_url;
          document.getElementById('global-share-result').style.display = 'block';
          const badge = document.getElementById('global-share-badge');
          badge.textContent = shareType === 'user' 
            ? `✅ Shared specifically with ${emailVal}`
            : `✅ Public access link created`;

          await navigator.clipboard.writeText(res.share_url);
          showToast('Share link generated and copied to clipboard!', 'success');
        }
      } catch (err) {
        showToast('Sharing failed: ' + err.message, 'error');
      } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = '⚡ Generate Share Link';
      }
    });
  }

  modalOverlay.dataset.fileId = fileId;
  document.getElementById('global-share-filename').textContent = fileName || `File #${fileId}`;
  document.getElementById('global-share-result').style.display = 'none';
  document.getElementById('global-share-email').value = '';
  document.getElementById('global-radio-public').checked = true;
  document.getElementById('global-email-group').style.display = 'none';

  modalOverlay.classList.add('active');
}

/**
 * Global File Rename Modal
 */
function openGlobalRenameModal(fileId, currentName, callback) {
  let modalOverlay = document.getElementById('global-rename-modal');
  if (!modalOverlay) {
    modalOverlay = document.createElement('div');
    modalOverlay.id = 'global-rename-modal';
    modalOverlay.className = 'modal-overlay';
    modalOverlay.innerHTML = `
      <div class="modal" style="max-width:440px; position:relative;">
        <div class="modal-header" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
          <h3 class="modal-title" style="margin:0; font-size:1.2rem; color:var(--text-main);">✏️ Rename File</h3>
          <button type="button" id="close-global-rename" style="background:none; border:none; color:var(--text-muted); font-size:1.4rem; cursor:pointer;">✕</button>
        </div>
        <form id="global-rename-form">
          <div class="form-group" style="margin-bottom:1.25rem;">
            <label for="global-rename-input" class="form-label">New File Name</label>
            <input type="text" id="global-rename-input" class="form-control" required style="width:100%;">
          </div>
          <div style="display:flex; gap:0.5rem; justify-content:flex-end;">
            <button type="button" id="cancel-global-rename" class="btn btn-secondary">Cancel</button>
            <button type="submit" id="submit-global-rename" class="btn btn-primary">Rename</button>
          </div>
        </form>
      </div>
    `;
    document.body.appendChild(modalOverlay);

    const closeBtn = document.getElementById('close-global-rename');
    const cancelBtn = document.getElementById('cancel-global-rename');
    const form = document.getElementById('global-rename-form');

    const closeModal = () => modalOverlay.classList.remove('active');
    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const newName = document.getElementById('global-rename-input').value.trim();
      const activeId = modalOverlay.dataset.fileId;
      if (!newName) return;

      const submitBtn = document.getElementById('submit-global-rename');
      submitBtn.disabled = true;

      try {
        await apiPut(`/files/${activeId}/rename`, { new_name: newName });
        showToast('File renamed successfully!', 'success');
        closeModal();
        if (typeof modalOverlay.onSuccess === 'function') modalOverlay.onSuccess();
      } catch (err) {
        showToast('Rename failed: ' + err.message, 'error');
      } finally {
        submitBtn.disabled = false;
      }
    });
  }

  modalOverlay.dataset.fileId = fileId;
  modalOverlay.onSuccess = callback;
  document.getElementById('global-rename-input').value = currentName || '';
  modalOverlay.classList.add('active');
}

/**
 * Global File Move Modal
 */
function openGlobalMoveModal(fileId, currentFolderId, callback) {
  let modalOverlay = document.getElementById('global-move-modal');
  if (!modalOverlay) {
    modalOverlay = document.createElement('div');
    modalOverlay.id = 'global-move-modal';
    modalOverlay.className = 'modal-overlay';
    modalOverlay.innerHTML = `
      <div class="modal" style="max-width:440px; position:relative;">
        <div class="modal-header" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
          <h3 class="modal-title" style="margin:0; font-size:1.2rem; color:var(--text-main);">📁 Move File to Folder</h3>
          <button type="button" id="close-global-move" style="background:none; border:none; color:var(--text-muted); font-size:1.4rem; cursor:pointer;">✕</button>
        </div>
        <form id="global-move-form">
          <div class="form-group" style="margin-bottom:1.25rem;">
            <label for="global-move-select" class="form-label">Destination Folder</label>
            <select id="global-move-select" class="form-control" style="width:100%;">
              <option value="">Root Storage (No Folder)</option>
            </select>
          </div>
          <div style="display:flex; gap:0.5rem; justify-content:flex-end;">
            <button type="button" id="cancel-global-move" class="btn btn-secondary">Cancel</button>
            <button type="submit" id="submit-global-move" class="btn btn-primary">Move File</button>
          </div>
        </form>
      </div>
    `;
    document.body.appendChild(modalOverlay);

    const closeBtn = document.getElementById('close-global-move');
    const cancelBtn = document.getElementById('cancel-global-move');
    const form = document.getElementById('global-move-form');

    const closeModal = () => modalOverlay.classList.remove('active');
    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const folderVal = document.getElementById('global-move-select').value;
      const activeId = modalOverlay.dataset.fileId;

      const submitBtn = document.getElementById('submit-global-move');
      submitBtn.disabled = true;

      try {
        await apiPut(`/files/${activeId}/move`, { folder_id: folderVal ? parseInt(folderVal) : null });
        showToast('File moved successfully!', 'success');
        closeModal();
        if (typeof modalOverlay.onSuccess === 'function') modalOverlay.onSuccess();
      } catch (err) {
        showToast('Move failed: ' + err.message, 'error');
      } finally {
        submitBtn.disabled = false;
      }
    });
  }

  modalOverlay.dataset.fileId = fileId;
  modalOverlay.onSuccess = callback;

  // Populate Folders
  const select = document.getElementById('global-move-select');
  select.innerHTML = '<option value="">Root Storage (No Folder)</option>';
  apiGet('/folders/').then(folders => {
    (folders || []).forEach(f => {
      select.innerHTML += `<option value="${f.id}" ${String(f.id) === String(currentFolderId) ? 'selected' : ''}>${f.name}</option>`;
    });
  }).catch(() => {});

  modalOverlay.classList.add('active');
}

