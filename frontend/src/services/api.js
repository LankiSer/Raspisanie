import axios from 'axios'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // Handle common errors
    if (error.response) {
      const { status, data } = error.response
      
      // Handle authentication errors
      if (status === 401) {
        // Token expired or invalid
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user')
        window.location.href = '/login'
        return Promise.reject(error)
      }
      
      // Handle validation errors
      if (status === 422 && data.detail) {
        const message = Array.isArray(data.detail) 
          ? data.detail.map(err => err.msg).join(', ')
          : data.detail
        error.message = message
      }
      
      // Handle other HTTP errors
      if (data?.error?.message) {
        error.message = data.error.message
      }
    } else if (error.request) {
      // Network error
      error.message = 'Ошибка сети. Проверьте подключение к интернету.'
    }
    
    return Promise.reject(error)
  }
)

// API methods
export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
  refresh: () => api.post('/auth/refresh'),
}

export const lessonsAPI = {
  getByDay: (date, params = {}) => api.get(`/lessons/by-date/${date}`, { params }),
  getByTerm: (params) => api.get('/lessons/term', { params }),
  create: (data) => api.post('/lessons', data),
  update: (id, data) => api.patch(`/lessons/${id}`, data),
  delete: (id) => api.delete(`/lessons/${id}`),
  checkConflicts: (data) => api.post('/lessons/check-conflicts', data),
  bulkUpdate: (data) => api.post('/lessons/bulk', data),
}

export const generationAPI = {
  preview: (data) => api.post('/generation/preview', data),
  run: (data) => api.post('/generation/run', data),
  getStats: () => api.get('/generation/stats'),
  getJobs: (params = {}) => api.get('/generation/jobs', { params }),
  getJob: (jobId) => api.get(`/generation/jobs/${jobId}`),
  applyJob: (jobId) => api.post(`/generation/jobs/${jobId}/apply`),
  cancelJob: (jobId) => api.delete(`/generation/jobs/${jobId}`),
}

export const catalogAPI = {
  // Groups
  getGroups: (params = {}) => api.get('/educational/groups', { params }),
  createGroup: (data) => api.post('/educational/groups', data),
  updateGroup: (id, data) => api.patch(`/educational/groups/${id}`, data),
  deleteGroup: (id) => api.delete(`/educational/groups/${id}`),
  
  // Teachers
  getTeachers: (params = {}) => api.get('/educational/teachers', { params }),
  createTeacher: (data) => api.post('/educational/teachers', data),
  updateTeacher: (id, data) => api.patch(`/educational/teachers/${id}`, data),
  deleteTeacher: (id) => api.delete(`/educational/teachers/${id}`),
  
  // Teacher availability
  getTeacherAvailability: (teacherId) => api.get(`/facilities/teacher-availability?teacher_id=${teacherId}`),
  updateTeacherAvailability: (teacherId, data) => api.post(`/facilities/teacher-availability`, { teacher_id: teacherId, ...data }),
  
  // Courses
  getCourses: (params = {}) => api.get('/educational/courses', { params }),
  createCourse: (data) => api.post('/educational/courses', data),
  updateCourse: (id, data) => api.patch(`/educational/courses/${id}`, data),
  deleteCourse: (id) => api.delete(`/educational/courses/${id}`),
  
  // Course assignments
  getCourseAssignments: (params = {}) => api.get('/educational/course-assignments', { params }),
  createCourseAssignment: (data) => api.post('/educational/course-assignments', data),
  deleteCourseAssignment: (id) => api.delete(`/educational/course-assignments/${id}`),
  
  // Enrollments
  getEnrollments: (params = {}) => api.get('/educational/enrollments', { params }),
  createEnrollment: (data) => api.post('/educational/enrollments/from-frontend', data),
  updateEnrollment: (id, data) => api.patch(`/educational/enrollments/${id}/from-frontend`, data),
  deleteEnrollment: (id) => api.delete(`/educational/enrollments/${id}`),
  
  // Rooms
  getRooms: (params = {}) => api.get('/facilities/rooms', { params }),
  createRoom: (data) => api.post('/facilities/rooms', data),
  updateRoom: (id, data) => api.patch(`/facilities/rooms/${id}`, data),
  deleteRoom: (id) => api.delete(`/facilities/rooms/${id}`),
  
  // Time slots
  getTimeSlots: (params = {}) => api.get('/facilities/slots', { params }),
  createTimeSlot: (data) => api.post('/facilities/slots', data),
  updateTimeSlot: (id, data) => api.patch(`/facilities/slots/${id}`, data),
  deleteTimeSlot: (id) => api.delete(`/facilities/slots/${id}`),
  
  // Terms
  getTerms: (params = {}) => api.get('/academic/terms', { params }),
  createTerm: (data) => api.post('/academic/terms', data),
  updateTerm: (id, data) => api.patch(`/academic/terms/${id}`, data),
  deleteTerm: (id) => api.delete(`/academic/terms/${id}`),
  
  // Holidays
  getHolidays: (params = {}) => api.get('/facilities/holidays', { params }),
  createHoliday: (data) => api.post('/facilities/holidays', data),
  deleteHoliday: (id) => api.delete(`/facilities/holidays/${id}`),
  
  // Teacher availability
  getTeacherAvailability: (params = {}) => api.get('/facilities/teacher-availability', { params }),
  createTeacherAvailability: (data) => api.post('/facilities/teacher-availability', data),
  updateTeacherAvailability: (id, data) => api.patch(`/facilities/teacher-availability/${id}`, data),
  deleteTeacherAvailability: (id) => api.delete(`/facilities/teacher-availability/${id}`),
}

export const reportsAPI = {
  getTeacherWorkload: (params) => api.get('/reports/workload/teacher', { params }),
  getGroupWorkload: (params) => api.get('/reports/workload/group', { params }),
  getConflicts: (params) => api.get('/reports/conflicts', { params }),
  exportIcal: (params) => api.get('/exports/ical', { params, responseType: 'blob' }),
}

// All APIs now use real backend

export default api
