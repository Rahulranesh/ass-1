/**
 * APIClient.js — Base class for all service communication
 *
 * OOP Concepts:
 *  - ENCAPSULATION: baseUrl and default headers are private (#)
 *  - ABSTRACTION: Subclasses call _get(), _post(), _put() without
 *    knowing fetch internals, token injection, or error handling.
 */

export class APIClient {
  // Private fields (Encapsulation — ES2022 private class fields)
  #baseUrl;
  #defaultHeaders;

  constructor(baseUrl = process.env.NEXT_PUBLIC_API_URL) {
    this.#baseUrl = baseUrl ?? "";
    this.#defaultHeaders = {
      "Content-Type": "application/json",
    };
  }

  // -----------------------------------------------------------------------
  // Private helpers (Encapsulation)
  // -----------------------------------------------------------------------

  /**
   * Retrieve the stored JWT access token (encapsulated storage logic).
   * @returns {string|null}
   */
  #getToken() {
    if (typeof window === "undefined") return null;
    return sessionStorage.getItem("access_token");
  }

  /**
   * Build the full request headers, injecting JWT if available.
   * @param {Object} extra - Additional headers to merge.
   * @returns {Object}
   */
  #buildHeaders(extra = {}) {
    const headers = { ...this.#defaultHeaders, ...extra };
    const token = this.#getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  }

  /**
   * Core fetch wrapper — handles JSON parse and error normalisation.
   * Encapsulated: subclasses never call fetch() directly.
   */
  async #request(method, path, body = null, extraHeaders = {}) {
    const url = `${this.#baseUrl}${path}`;
    const options = {
      method,
      headers: this.#buildHeaders(extraHeaders),
    };
    if (body !== null) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);
    let data;
    try {
      data = await response.json();
    } catch {
      data = { message: response.statusText };
    }

    if (!response.ok) {
      const message =
        data?.error || data?.message || `HTTP ${response.status}: ${response.statusText}`;
      const err = new Error(message);
      err.statusCode = response.status;
      err.data = data;
      throw err;
    }

    return data;
  }

  // -----------------------------------------------------------------------
  // Protected HTTP methods (Abstraction — for subclass use only)
  // -----------------------------------------------------------------------

  /** @protected */
  async _get(path, extraHeaders = {}) {
    return this.#request("GET", path, null, extraHeaders);
  }

  /** @protected */
  async _post(path, body, extraHeaders = {}) {
    return this.#request("POST", path, body, extraHeaders);
  }

  /** @protected */
  async _put(path, body, extraHeaders = {}) {
    return this.#request("PUT", path, body, extraHeaders);
  }

  /** @protected */
  async _delete(path, extraHeaders = {}) {
    return this.#request("DELETE", path, null, extraHeaders);
  }

  // -----------------------------------------------------------------------
  // Token management (public — called by AuthService after login)
  // -----------------------------------------------------------------------

  /**
   * Store tokens in sessionStorage after successful login.
   * @param {Object} tokens
   */
  storeTokens({ access_token, id_token, refresh_token }) {
    if (typeof window === "undefined") return;
    sessionStorage.setItem("access_token", access_token);
    sessionStorage.setItem("id_token", id_token);
    sessionStorage.setItem("refresh_token", refresh_token);
  }

  /**
   * Clear all stored tokens (logout).
   */
  clearTokens() {
    if (typeof window === "undefined") return;
    ["access_token", "id_token", "refresh_token"].forEach((key) =>
      sessionStorage.removeItem(key)
    );
  }

  /**
   * Check if the user is currently authenticated.
   * @returns {boolean}
   */
  isAuthenticated() {
    return !!this.#getToken();
  }
}
