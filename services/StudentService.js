/**
 * StudentService.js — Student profile service class
 *
 * OOP Concepts:
 *  - INHERITANCE: Extends APIClient, reusing _get(), _post(), _put()
 *  - ENCAPSULATION: Endpoint path constant is private
 *  - ABSTRACTION: callers use createProfile() / getProfile() without knowing API paths
 */

import { APIClient } from "./APIClient";

export class StudentService extends APIClient {
  // Private constant (Encapsulation)
  #STUDENTS_ENDPOINT = "/students";

  constructor() {
    super();
  }

  /**
   * Create a student profile.
   * Calls POST /students with the authenticated user's JWT.
   *
   * @param {Object} profileData - Student profile fields
   * @returns {Promise<{student_id: string, message: string}>}
   */
  async createProfile(profileData) {
    return this._post(this.#STUDENTS_ENDPOINT, profileData);
  }

  /**
   * Fetch the logged-in student's profile.
   * Calls GET /students/me
   *
   * @returns {Promise<Object>} Student profile data
   */
  async getProfile() {
    return this._get(`${this.#STUDENTS_ENDPOINT}/me`);
  }

  /**
   * Update the logged-in student's profile.
   * Calls PUT /students/me
   *
   * @param {Object} updates - Fields to update
   * @returns {Promise<{message: string}>}
   */
  async updateProfile(updates) {
    return this._put(`${this.#STUDENTS_ENDPOINT}/me`, updates);
  }
}

// Singleton instance
export const studentService = new StudentService();
