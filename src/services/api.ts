// Use environment variable or default to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

class ApiService {
  private getAuthToken(): string | null {
    return sessionStorage.getItem('token');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const token = this.getAuthToken();
    const url = `${API_BASE_URL}${endpoint}`;

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          detail: `HTTP ${response.status}: ${response.statusText}`,
        }));
        return {
          error: errorData.detail || errorData.message || 'An error occurred',
        };
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      return {
        error:
          error instanceof Error
            ? error.message
            : 'Network error occurred',
      };
    }
  }

  // Dashboard APIs
  async getDashboardStats(period: 'today' | 'week' | 'month' = 'today') {
    return this.request(`/dashboard/stats?period=${period}`);
  }

  async getActivityData(period: 'today' | 'week' | 'month' = 'today') {
    return this.request(`/dashboard/activity?period=${period}`);
  }

  async getRecentIncidents(limit: number = 5) {
    return this.request(`/dashboard/recent-incidents?limit=${limit}`);
  }

  // Incidents APIs
  async getIncidents(params?: {
    severity?: string;
    status?: string;
    page?: number;
    limit?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.severity) queryParams.append('severity', params.severity);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const query = queryParams.toString();
    return this.request(`/incidents${query ? `?${query}` : ''}`);
  }

  async getIncidentById(incidentId: string) {
    return this.request(`/incidents/${incidentId}`);
  }

  async updateIncidentStatus(
    incidentId: string,
    status: 'investigating' | 'resolved' | 'dismissed',
    notes?: string
  ) {
    return this.request(`/incidents/${incidentId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status, notes }),
    });
  }

  // Monitoring APIs
  async getMonitoringFeeds(examId?: string) {
    const query = examId ? `?exam_id=${examId}` : '';
    return this.request(`/monitoring/feeds${query}`);
  }

  async getCameraStatus(cameraId: string) {
    return this.request(`/monitoring/cameras/${cameraId}/status`);
  }

  // Reports APIs
  async generateIncidentReport(data: {
    incident_ids: string[];
    format: 'pdf' | 'csv' | 'json';
    include_video_links: boolean;
  }) {
    return this.request('/reports/incidents', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async generateExamReport(
    examId: string,
    data: {
      format: 'pdf' | 'csv' | 'json';
      include_statistics: boolean;
    }
  ) {
    return this.request(`/reports/exams/${examId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getReportHistory(params?: { page?: number; limit?: number }) {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const query = queryParams.toString();
    return this.request(`/reports${query ? `?${query}` : ''}`);
  }

  // User Management APIs
  async getUsers(params?: {
    role?: string;
    page?: number;
    limit?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.role) queryParams.append('role', params.role);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const query = queryParams.toString();
    return this.request(`/users${query ? `?${query}` : ''}`);
  }

  async getUserById(userId: string) {
    return this.request(`/users/${userId}`);
  }

  async updateUser(
    userId: string,
    data: {
      name?: string;
      email?: string;
      user_type?: string;
      status?: 'active' | 'suspended' | 'inactive';
    }
  ) {
    return this.request(`/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteUser(userId: string) {
    return this.request(`/users/${userId}`, {
      method: 'DELETE',
    });
  }

  async createUser(data: {
    name: string;
    email: string;
    user_type: 'admin' | 'investigator' | 'invigilator' | 'student';
    password: string;
    status?: 'active' | 'suspended' | 'inactive';
    username?: string; // For admin
    roll_number?: string; // For student
    designation?: string; // For investigator
    photo_url?: string; // For invigilator/student
  }) {
    return this.request('/users', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getCurrentUser() {
    return this.request('/users/me');
  }

  // Exam Management APIs
  async getExams(params?: {
    status?: string;
    page?: number;
    limit?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append('status', params.status);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const query = queryParams.toString();
    return this.request(`/exams${query ? `?${query}` : ''}`);
  }

  async getExamById(examId: string) {
    return this.request(`/exams/${examId}`);
  }

  async createExam(data: {
    name: string;
    course_code: string;
    instructor_id: string;
    scheduled_date: string;
    duration_minutes: number;
    seating_plan_id: string;
    description?: string;
  }) {
    return this.request('/exams', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateExam(examId: string, data: Partial<{
    name: string;
    course_code: string;
    scheduled_date: string;
    duration_minutes: number;
    status: string;
  }>) {
    return this.request(`/exams/${examId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteExam(examId: string) {
    return this.request(`/exams/${examId}`, {
      method: 'DELETE',
    });
  }

  async getActiveExams() {
    return this.request('/exams/active');
  }

  // Seating Plan APIs
  async getSeatingPlans(params?: {
    page?: number;
    limit?: number;
    status?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.status) queryParams.append('status', params.status);

    const query = queryParams.toString();
    return this.request(`/seating-plans${query ? `?${query}` : ''}`);
  }

  async getSeatingPlanById(planId: string) {
    return this.request(`/seating-plans/${planId}`);
  }

  async assignStudentToSeat(
    planId: string,
    data: {
      student_id: string;
      room_id: string;
      seat_number: string;
    }
  ) {
    return this.request(`/seating-plans/${planId}/assign`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async deleteSeatingPlan(planId: string) {
    return this.request(`/seating-plans/${planId}`, {
      method: 'DELETE',
    });
  }

  // Notifications APIs
  async getNotifications(params?: {
    unread_only?: boolean;
    page?: number;
    limit?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.unread_only) queryParams.append('unread_only', 'true');
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const query = queryParams.toString();
    return this.request(`/notifications${query ? `?${query}` : ''}`);
  }

  async markNotificationAsRead(notificationId: string) {
    return this.request(`/notifications/${notificationId}/read`, {
      method: 'PUT',
    });
  }

  async markAllNotificationsAsRead() {
    return this.request('/notifications/read-all', {
      method: 'PUT',
    });
  }

  // Investigator-specific APIs
  async getViolations(params?: {
    status?: string;
    severity?: number;
    type?: string;
    page?: number;
    limit?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append('status', params.status);
    if (params?.severity) queryParams.append('severity', params.severity.toString());
    if (params?.type) queryParams.append('type', params.type);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const query = queryParams.toString();
    return this.request(`/violations${query ? `?${query}` : ''}`);
  }

  async getViolationById(violationId: string) {
    return this.request(`/violations/${violationId}`);
  }

  async confirmViolation(violationId: string, notes?: string) {
    return this.request(`/violations/${violationId}`, {
      method: 'PUT',
      body: JSON.stringify({ status: 'confirmed', notes }),
    });
  }

  async dismissViolation(violationId: string, notes?: string) {
    return this.request(`/violations/${violationId}`, {
      method: 'PUT',
      body: JSON.stringify({ status: 'dismissed', notes }),
    });
  }

  async getStudentActivities(params?: {
    student_id?: string;
    exam_id?: string;
    severity?: string;
    type?: string;
    page?: number;
    limit?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.student_id) queryParams.append('student_id', params.student_id);
    if (params?.exam_id) queryParams.append('exam_id', params.exam_id);
    if (params?.severity) queryParams.append('severity', params.severity);
    if (params?.type) queryParams.append('type', params.type);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const query = queryParams.toString();
    return this.request(`/student-activities${query ? `?${query}` : ''}`);
  }

  async getStudentActivityById(activityId: string) {
    return this.request(`/student-activities/${activityId}`);
  }

  async getInvigilatorActivities(params?: {
    invigilator_id?: string;
    room_id?: string;
    type?: string;
    page?: number;
    limit?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.invigilator_id) queryParams.append('invigilator_id', params.invigilator_id);
    if (params?.room_id) queryParams.append('room_id', params.room_id);
    if (params?.type) queryParams.append('type', params.type);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const query = queryParams.toString();
    return this.request(`/invigilator-activities${query ? `?${query}` : ''}`);
  }

  async getInvigilatorActivityById(activityId: string) {
    return this.request(`/invigilator-activities/${activityId}`);
  }

  async getReports(params?: {
    page?: number;
    limit?: number;
    type?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.type) queryParams.append('type', params.type);

    const query = queryParams.toString();
    return this.request(`/reports${query ? `?${query}` : ''}`);
  }

  async getReportById(reportId: string) {
    return this.request(`/reports/${reportId}`);
  }

  async downloadReport(reportId: string) {
    return this.request(`/reports/${reportId}/download`);
  }

  async getInvestigatorProfile() {
    return this.request('/investigators/me');
  }

  async updateInvestigatorProfile(data: {
    name?: string;
    email?: string;
    designation?: string;
  }) {
    return this.request('/investigators/me', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async changePassword(data: {
    current_password: string;
    new_password: string;
  }) {
    return this.request('/investigators/change-password', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Phone Monitoring APIs
  async startPhoneMonitoring(data: {
    stream_url: string;
    exam_id?: string;
    room_id?: string;
    duration_seconds?: number;
    process_every_n_frames?: number;
  }) {
    return this.request('/phone-monitoring/start', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Video Processing APIs
  async uploadVideo(formData: FormData) {
    const token = this.getAuthToken();
    const url = `${API_BASE_URL}/api/video-streams/upload`;

    return new Promise<ApiResponse<any>>((resolve) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          // Progress can be handled via callback if needed
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText);
            resolve({ data });
          } catch {
            resolve({ data: { success: true } });
          }
        } else {
          try {
            const errorData = JSON.parse(xhr.responseText);
            resolve({
              error: errorData.detail || errorData.message || 'Upload failed',
            });
          } catch {
            resolve({
              error: `HTTP ${xhr.status}: ${xhr.statusText}`,
            });
          }
        }
      });

      xhr.addEventListener('error', () => {
        resolve({
          error: 'Network error occurred',
        });
      });

      xhr.open('POST', url);
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      }
      xhr.send(formData);
    });
  }

  async getVideoStreams(examId?: string, roomId?: string) {
    if (examId) {
      return this.request(`/api/video-streams/exam/${examId}/streams`);
    }
    if (roomId) {
      return this.request(`/api/video-streams/room/${roomId}/streams`);
    }
    return this.request('/api/video-streams/all');
  }

  async getVideoProcessingStatus(streamId: string) {
    return this.request(`/api/video-streams/${streamId}/status`);
  }

  async getVideoProcessingResults(streamId: string) {
    return this.request(`/api/video-streams/${streamId}/results`);
  }

  // Rooms API
  async getRooms() {
    return this.request('/rooms');
  }

  async getRoomById(roomId: string) {
    return this.request(`/rooms/${roomId}`);
  }

  async stopPhoneMonitoring(sessionId: string) {
    return this.request(`/phone-monitoring/stop/${sessionId}`, {
      method: 'POST',
    });
  }

  async getMonitoringStatus(sessionId: string) {
    return this.request(`/phone-monitoring/status/${sessionId}`);
  }

  async getActiveMonitoring() {
    return this.request('/phone-monitoring/active');
  }

  async getLatestFrame(sessionId: string): Promise<string> {
    // Fetch frame as blob for image display
    const token = this.getAuthToken();
    const url = `${API_BASE_URL}/phone-monitoring/latest-frame/${sessionId}`;
    
    const headers: HeadersInit = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    try {
      const response = await fetch(url, { headers });
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('No frames found yet');
        }
        throw new Error(`Failed to fetch frame: ${response.status} ${response.statusText}`);
      }
      
      // Check if response is actually an image
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.startsWith('image/')) {
        console.warn('Unexpected content type:', contentType);
      }
      
      const blob = await response.blob();
      if (blob.size === 0) {
        throw new Error('Received empty frame');
      }
      
      return URL.createObjectURL(blob);
    } catch (error) {
      console.error('Error fetching latest frame:', error);
      throw error;
    }
  }
}

export const apiService = new ApiService();

