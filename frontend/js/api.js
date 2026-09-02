/* ==========================================================================
   Central API Request Helper Module
   ========================================================================== */

/**
 * Perform generic API fetch request
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;
  const token = getToken();

  // Set up default headers
  const headers = options.headers || {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Set JSON content-type if body is provided and not FormData
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const config = {
    ...options,
    headers: headers
  };

  try {
    const response = await fetch(url, config);

    // Handle 401 Unauthorized globally
    if (response.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user_info");
      window.location.href = "index.html";
      throw new Error("Session expired. Please login again.");
    }

    // Check if response is ok
    if (!response.ok) {
      let errorMessage = `HTTP Error ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData && errorData.detail) {
          errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
        }
      } catch (e) {}
      throw new Error(errorMessage);
    }

    // Handle file blob responses vs json
    const contentType = response.headers.get("content-type");
    if (contentType && (contentType.includes("application/json") || contentType.includes("json"))) {
      return await response.json();
    } else if (contentType && (contentType.includes("octet-stream") || contentType.includes("pdf") || contentType.includes("image") || contentType.includes("audio") || contentType.includes("video"))) {
      return await response.blob();
    }

    // Fallback: try text or json
    const text = await response.text();
    try {
      return JSON.parse(text);
    } catch (e) {
      return text;
    }
  } catch (err) {
    console.error(`API Error [${endpoint}]:`, err);
    throw err;
  }
}

/**
 * HTTP GET Helper
 */
async function apiGet(endpoint) {
  return apiRequest(endpoint, { method: "GET" });
}

/**
 * HTTP POST Helper
 */
async function apiPost(endpoint, data = {}) {
  return apiRequest(endpoint, {
    method: "POST",
    body: JSON.stringify(data)
  });
}

/**
 * HTTP PUT Helper
 */
async function apiPut(endpoint, data = {}) {
  return apiRequest(endpoint, {
    method: "PUT",
    body: JSON.stringify(data)
  });
}

/**
 * HTTP DELETE Helper
 */
async function apiDelete(endpoint) {
  return apiRequest(endpoint, { method: "DELETE" });
}

/**
 * HTTP Multipart Upload Helper (DO NOT manually set Content-Type)
 */
async function apiUpload(endpoint, formData) {
  return apiRequest(endpoint, {
    method: "POST",
    body: formData
  });
}
