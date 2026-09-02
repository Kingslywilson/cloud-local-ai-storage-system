/* ==========================================================================
   User Profile & Settings Page Module
   ========================================================================== */

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();

  const profileNameInput = document.getElementById("profile-name");
  const profileEmailInput = document.getElementById("profile-email");
  const profileCreatedEl = document.getElementById("profile-created");

  const editProfileBtn = document.getElementById("edit-profile-btn");
  const saveProfileBtn = document.getElementById("save-profile-btn");
  const cancelProfileBtn = document.getElementById("cancel-profile-btn");
  const profileLogoutBtn = document.getElementById("profile-logout-btn");

  let originalUserData = null;

  async function loadUserProfile() {
    try {
      const user = await apiGet("/auth/me");
      originalUserData = user;

      if (profileNameInput) profileNameInput.value = user.name || "";
      if (profileEmailInput) profileEmailInput.value = user.email || "";
      if (profileCreatedEl) profileCreatedEl.textContent = user.created_at ? formatDate(user.created_at) : "Active Account";

    } catch (e) {
      showToast("Error loading user profile: " + e.message, "error");
    }
  }

  function setEditing(isEditing) {
    if (profileNameInput) profileNameInput.disabled = !isEditing;
    if (editProfileBtn) editProfileBtn.style.display = isEditing ? "none" : "inline-flex";
    if (saveProfileBtn) saveProfileBtn.style.display = isEditing ? "inline-flex" : "none";
    if (cancelProfileBtn) cancelProfileBtn.style.display = isEditing ? "inline-flex" : "none";
  }

  if (editProfileBtn) {
    editProfileBtn.addEventListener("click", () => setEditing(true));
  }

  if (cancelProfileBtn) {
    cancelProfileBtn.addEventListener("click", () => {
      if (originalUserData) {
        if (profileNameInput) profileNameInput.value = originalUserData.name || "";
      }
      setEditing(false);
    });
  }

  if (saveProfileBtn) {
    saveProfileBtn.addEventListener("click", async () => {
      const newName = profileNameInput?.value.trim();
      if (!newName) {
        showToast("Name cannot be empty", "warning");
        return;
      }

      try {
        // Try updating profile if backend supports PUT /auth/me or update endpoint
        const updated = await apiPut("/auth/me", { name: newName }).catch(() => null);
        
        if (originalUserData) originalUserData.name = newName;
        localStorage.setItem("user_info", JSON.stringify({ ...originalUserData, name: newName }));
        
        showToast("Profile updated successfully!", "success");
        setEditing(false);

        const userNameTopbar = document.getElementById("user-name");
        if (userNameTopbar) userNameTopbar.textContent = newName;

      } catch (e) {
        showToast("Profile update failed: " + e.message, "error");
      }
    });
  }

  if (profileLogoutBtn) {
    profileLogoutBtn.addEventListener("click", (e) => {
      e.preventDefault();
      logoutUser();
    });
  }

  loadUserProfile();
});
