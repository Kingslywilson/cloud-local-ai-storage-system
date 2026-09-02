/* ==========================================================================
   Storage Analytics Page Module
   ========================================================================== */

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();

  const storageTotal = document.getElementById("storage-total");
  const storageUsed = document.getElementById("storage-used");
  const storageRemaining = document.getElementById("storage-remaining");
  const storagePercentage = document.getElementById("storage-percentage");
  const storageProgress = document.getElementById("storage-progress");
  const storageFileCount = document.getElementById("storage-file-count");

  // Breakdown Elements
  const docSizeEl = document.getElementById("breakdown-doc-size");
  const docBarEl = document.getElementById("breakdown-doc-bar");
  
  const imgSizeEl = document.getElementById("breakdown-img-size");
  const imgBarEl = document.getElementById("breakdown-img-bar");

  const videoSizeEl = document.getElementById("breakdown-video-size");
  const videoBarEl = document.getElementById("breakdown-video-bar");

  const audioSizeEl = document.getElementById("breakdown-audio-size");
  const audioBarEl = document.getElementById("breakdown-audio-bar");

  const otherSizeEl = document.getElementById("breakdown-other-size");
  const otherBarEl = document.getElementById("breakdown-other-bar");

  async function loadStorageAnalytics() {
    try {
      const [storageData, files] = await Promise.all([
        apiGet("/files/storage").catch(() => null),
        apiGet("/files/").catch(() => [])
      ]);

      const totalFiles = storageData ? storageData.total_files : files.length;
      const usedBytes = storageData ? storageData.total_storage_bytes : files.reduce((a, b) => a + (b.file_size || 0), 0);
      
      const capacityBytes = 15 * 1024 * 1024 * 1024; // 15 GB Limit
      const remainingBytes = Math.max(0, capacityBytes - usedBytes);
      const usedPercent = Math.min(100, ((usedBytes / capacityBytes) * 100)).toFixed(1);

      if (storageTotal) storageTotal.textContent = "15 GB";
      if (storageUsed) storageUsed.textContent = formatFileSize(usedBytes);
      if (storageRemaining) storageRemaining.textContent = formatFileSize(remainingBytes);
      if (storagePercentage) storagePercentage.textContent = `${usedPercent}%`;
      if (storageProgress) storageProgress.style.width = `${usedPercent}%`;
      if (storageFileCount) storageFileCount.textContent = totalFiles;

      // File Type Category breakdown
      let docsBytes = 0, imgBytes = 0, videoBytes = 0, audioBytes = 0, otherBytes = 0;

      files.forEach(f => {
        const type = (f.file_type || '').toLowerCase();
        const name = (f.original_name || '').toLowerCase();
        const size = f.file_size || 0;

        if (type.includes('pdf') || type.includes('word') || type.includes('text') || type.includes('csv') || /\.(pdf|docx|txt|csv|json|md)$/.test(name)) {
          docsBytes += size;
        } else if (type.includes('image') || /\.(jpg|jpeg|png|webp|gif)$/.test(name)) {
          imgBytes += size;
        } else if (type.includes('video') || /\.(mp4|mov|avi|mkv)$/.test(name)) {
          videoBytes += size;
        } else if (type.includes('audio') || /\.(mp3|wav|m4a|flac)$/.test(name)) {
          audioBytes += size;
        } else {
          otherBytes += size;
        }
      });

      const maxBytes = usedBytes || 1; // Prevent div by 0

      if (docSizeEl) docSizeEl.textContent = formatFileSize(docsBytes);
      if (docBarEl) docBarEl.style.width = `${((docsBytes / maxBytes) * 100).toFixed(1)}%`;

      if (imgSizeEl) imgSizeEl.textContent = formatFileSize(imgBytes);
      if (imgBarEl) imgBarEl.style.width = `${((imgBytes / maxBytes) * 100).toFixed(1)}%`;

      if (videoSizeEl) videoSizeEl.textContent = formatFileSize(videoBytes);
      if (videoBarEl) videoBarEl.style.width = `${((videoBytes / maxBytes) * 100).toFixed(1)}%`;

      if (audioSizeEl) audioSizeEl.textContent = formatFileSize(audioBytes);
      if (audioBarEl) audioBarEl.style.width = `${((audioBytes / maxBytes) * 100).toFixed(1)}%`;

      if (otherSizeEl) otherSizeEl.textContent = formatFileSize(otherBytes);
      if (otherBarEl) otherBarEl.style.width = `${((otherBytes / maxBytes) * 100).toFixed(1)}%`;

    } catch (e) {
      showToast("Error loading storage details: " + e.message, "error");
    }
  }

  loadStorageAnalytics();
});
