import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref(null)
  const token = ref(localStorage.getItem('auth_token'))
  const loading = ref(false)

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  
  const isAdmin = computed(() => 
    user.value?.role?.toLowerCase() === 'admin' || user.value?.role?.toLowerCase() === 'superadmin'
  )
  
  const isMethodist = computed(() => 
    user.value?.role?.toLowerCase() === 'methodist' || isAdmin.value
  )
  
  const canManageSchedule = computed(() => 
    isMethodist.value || user.value?.role?.toLowerCase() === 'teacher'
  )

  // Actions
  const login = async (email, password) => {
    loading.value = true
    
    try {
      const response = await api.post('/auth/login', {
        email,
        password
      })
      
      const { access_token, user: userData } = response.data
      
      token.value = access_token
      user.value = userData
      
      // Save to localStorage
      localStorage.setItem('auth_token', access_token)
      localStorage.setItem('user', JSON.stringify(userData))
      
      // Set default authorization header
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      
      return userData
    } catch (error) {
      console.error('Login error:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const register = async (organizationName, email, password, locale = 'ru', tz = 'Europe/Moscow') => {
    loading.value = true
    
    try {
      const response = await api.post('/auth/register', {
        organization_name: organizationName,
        email,
        password,
        locale,
        tz
      })
      
      const { access_token, user: userData } = response.data
      
      token.value = access_token
      user.value = userData
      
      // Save to localStorage
      localStorage.setItem('auth_token', access_token)
      localStorage.setItem('user', JSON.stringify(userData))
      
      // Set default authorization header
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      
      return userData
    } catch (error) {
      console.error('Registration error:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const logout = () => {
    token.value = null
    user.value = null
    
    // Clear localStorage
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
    
    // Remove authorization header
    delete api.defaults.headers.common['Authorization']
  }

  const getCurrentUser = async () => {
    if (!token.value) return null
    
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
      return response.data
    } catch (error) {
      // Token might be invalid, logout
      logout()
      throw error
    }
  }

  const refreshToken = async () => {
    if (!token.value) return false
    
    try {
      const response = await api.post('/auth/refresh', {
        refresh_token: token.value
      })
      
      const { access_token } = response.data
      token.value = access_token
      localStorage.setItem('auth_token', access_token)
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      
      return true
    } catch (error) {
      logout()
      return false
    }
  }

    const demoLogin = async () => {
      loading.value = true
      
      try {
        // Call real demo login API
        const response = await api.post('/auth/demo-login')
        const { access_token, user: demoUser } = response.data
        
        token.value = access_token
        user.value = demoUser
        
        // Save to localStorage
        localStorage.setItem('auth_token', access_token)
        localStorage.setItem('user', JSON.stringify(demoUser))
        
        // Set default authorization header
        api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
        
        return demoUser
      } catch (error) {
        console.error('Demo login error:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

  // Initialize store
  const init = async () => {
    const savedToken = localStorage.getItem('auth_token')
    const savedUser = localStorage.getItem('user')
    
    if (savedToken && savedUser) {
      token.value = savedToken
      user.value = JSON.parse(savedUser)
      
      // Set authorization header
      api.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`
      
      // Verify token is still valid
      try {
        await getCurrentUser()
      } catch (error) {
        logout()
      }
    }
  }

  // Call init when store is created
  init()

  return {
    // State
    user,
    token,
    loading,
    
    // Getters
    isAuthenticated,
    isAdmin,
    isMethodist,
    canManageSchedule,
    
    // Actions
    login,
    register,
    logout,
    getCurrentUser,
    refreshToken,
    demoLogin,
    init
  }
})
