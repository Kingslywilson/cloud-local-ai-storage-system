/* ==========================================================================
   Authentication Helper Module
   ========================================================================== */

/**
 * Get JWT Access Token from localStorage
 */
function getToken() {
  return localStorage.getItem("access_token");
}

/**
 * Check if current user is logged in
 */
function isLoggedIn() {
  return !!getToken();
}

/**
 * Redirect to login page if unauthenticated (Call on protected pages)
 */
function requireAuth() {
  if (!isLoggedIn()) {
    window.location.href = "index.html";
  }
}

/**
 * Redirect to dashboard page if already logged in (Call on login/register pages)
 */
function redirectIfLoggedIn() {
  if (isLoggedIn()) {
    window.location.href = "dashboard.html";
  }
}

/**
 * Log out user by clearing local token and redirecting to login page
 */
function logoutUser() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("user_info");
  window.location.href = "index.html";
}

/**
 * Initialize Sidebar and Topbar User Details across all pages
 */
document.addEventListener("DOMContentLoaded", () => {
  // Mobile Sidebar Toggle
  const sidebar = document.getElementById("sidebar");
  const sidebarToggle = document.getElementById("sidebar-toggle");

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", () => {
      sidebar.classList.toggle("active");
    });
  }

  // Bind Global Logout Buttons
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", (e) => {
      e.preventDefault();
      logoutUser();
    });
  }

  const profileLogoutBtn = document.getElementById("profile-logout-btn");
  if (profileLogoutBtn) {
    profileLogoutBtn.addEventListener("click", (e) => {
      e.preventDefault();
      logoutUser();
    });
  }

  // Load User Details into Top Bar if logged in
  if (isLoggedIn()) {
    const userNameEl = document.getElementById("user-name");
    const userAvatarEl = document.querySelector(".user-avatar");
    
    // Check cache
    const storedUser = localStorage.getItem("user_info");
    if (storedUser) {
      try {
        const u = JSON.parse(storedUser);
        if (userNameEl) userNameEl.textContent = u.name || u.email;
        if (userAvatarEl && u.name) userAvatarEl.textContent = u.name.charAt(0).toUpperCase();
      } catch (e) {}
    }

    // Fetch fresh user profile
    if (typeof apiGet === 'function') {
      apiGet("/auth/me")
        .then(user => {
          if (user && user.name) {
            localStorage.setItem("user_info", JSON.stringify(user));
            if (userNameEl) userNameEl.textContent = user.name;
            if (userAvatarEl) userAvatarEl.textContent = user.name.charAt(0).toUpperCase();
          }
        })
        .catch(() => {});
    }
  }
});
