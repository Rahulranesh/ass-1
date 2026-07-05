/**
 * AuthService.js — Authentication service class
 *
 * OOP Concepts:
 *  - INHERITANCE: Extends APIClient, reusing _post(), storeTokens(), clearTokens()
 *  - ENCAPSULATION: Internal state (user, loading) hidden from consumers
 *  - POLYMORPHISM: register() and login() both call _post() but with different
 *    payloads and return shapes
 */

import { APIClient } from "./APIClient";

export class AuthService extends APIClient {
  // Encapsulation: current authenticated user state is private
  #currentUser = null;

  constructor() {
    super(); // Call APIClient constructor (Inheritance)
  }

  // -----------------------------------------------------------------------
  // Public API
  // -----------------------------------------------------------------------

  /**
   * Register a new user account.
   * Polymorphism: calls the same POST /auth endpoint as login() but with
   * action='register' and different required fields.
   *
   * @param {Object} params
   * @param {string} params.email
   * @param {string} params.password
   * @param {string} params.fullName
   * @returns {Promise<{message: string, user_sub: string}>}
   */
  async register({ email, password, fullName }) {
    const data = await this._post("/auth", {
      action: "register",
      email: email.trim().toLowerCase(),
      password,
      full_name: fullName.trim(),
    });
    return data;
  }

  /**
   * Confirm the email address with a verification code.
   *
   * @param {string} email
   * @param {string} code
   * @returns {Promise<{message: string}>}
   */
  async confirmEmail(email, code) {
    return this._post("/auth", {
      action: "confirm",
      email: email.trim().toLowerCase(),
      confirmation_code: code.trim(),
    });
  }

  /**
   * Log in and store JWT tokens in sessionStorage.
   * Polymorphism: same POST endpoint as register(), different action.
   *
   * @param {Object} params
   * @param {string} params.email
   * @param {string} params.password
   * @returns {Promise<void>}
   */
  async login({ email, password }) {
    const data = await this._post("/auth", {
      action: "login",
      email: email.trim().toLowerCase(),
      password,
    });

    // Store tokens (inherited method from APIClient)
    this.storeTokens({
      access_token: data.access_token,
      id_token: data.id_token,
      refresh_token: data.refresh_token,
    });

    // Decode ID token to get user info (encapsulated)
    this.#currentUser = this.#decodeJWT(data.id_token);
    return data;
  }

  /**
   * Log out: clear tokens and reset state.
   */
  logout() {
    this.clearTokens(); // Inherited (Inheritance)
    this.#currentUser = null;
  }

  /**
   * Get the currently authenticated user's basic info.
   * @returns {Object|null}
   */
  getCurrentUser() {
    if (this.#currentUser) return this.#currentUser;

    // Try to restore from stored ID token
    if (typeof window !== "undefined") {
      const idToken = sessionStorage.getItem("id_token");
      if (idToken) {
        this.#currentUser = this.#decodeJWT(idToken);
        return this.#currentUser;
      }
    }
    return null;
  }

  // -----------------------------------------------------------------------
  // Private methods (Encapsulation)
  // -----------------------------------------------------------------------

  /**
   * Decode a JWT payload without verifying the signature.
   * Encapsulation: consumers never deal with base64 or JSON parsing.
   * @param {string} token
   * @returns {Object}
   */
  #decodeJWT(token) {
    try {
      const payload = token.split(".")[1];
      const decoded = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
      return JSON.parse(decoded);
    } catch {
      return {};
    }
  }
}

// Singleton instance — shared across the app
export const authService = new AuthService();
