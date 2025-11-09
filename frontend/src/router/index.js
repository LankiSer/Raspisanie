import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// Lazy load components
const Login = () => import('@/pages/Login.vue')
const Dashboard = () => import('@/pages/Dashboard.vue')
const Schedule = () => import('@/pages/Schedule.vue')
const Generation = () => import('@/pages/Generation.vue')
const Reports = () => import('@/pages/Reports.vue')

// Catalog pages
const Groups = () => import('@/pages/catalog/Groups.vue')
const Teachers = () => import('@/pages/catalog/Teachers.vue')
const Courses = () => import('@/pages/catalog/Courses.vue')
const Rooms = () => import('@/pages/catalog/Rooms.vue')
const TimeSlots = () => import('@/pages/catalog/TimeSlots.vue')
const Enrollments = () => import('@/pages/catalog/Enrollments.vue')
const TeacherAvailability = () => import('@/pages/catalog/TeacherAvailability.vue')

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { 
      requiresAuth: false,
      title: 'Вход в систему'
    }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { 
      requiresAuth: true,
      title: 'Дашборд'
    }
  },
  {
    path: '/schedule',
    name: 'Schedule',
    component: Schedule,
    meta: { 
      requiresAuth: true,
      title: 'Расписание'
    }
  },
  {
    path: '/generation',
    name: 'Generation',
    component: Generation,
    meta: { 
      requiresAuth: true,
      title: 'Генерация расписания',
      roles: ['admin', 'methodist']
    }
  },
  {
    path: '/reports',
    name: 'Reports',
    component: Reports,
    meta: { 
      requiresAuth: true,
      title: 'Отчеты'
    }
  },
  // Catalog routes
  {
    path: '/catalog',
    redirect: '/catalog/groups'
  },
  {
    path: '/catalog/groups',
    name: 'Groups',
    component: Groups,
    meta: { 
      requiresAuth: true,
      title: 'Группы',
      roles: ['admin', 'methodist']
    }
  },
  {
    path: '/catalog/teachers',
    name: 'Teachers',
    component: Teachers,
    meta: { 
      requiresAuth: true,
      title: 'Преподаватели',
      roles: ['admin', 'methodist']
    }
  },
  {
    path: '/catalog/courses',
    name: 'Courses',
    component: Courses,
    meta: { 
      requiresAuth: true,
      title: 'Предметы',
      roles: ['admin', 'methodist']
    }
  },
  {
    path: '/catalog/rooms',
    name: 'Rooms',
    component: Rooms,
    meta: { 
      requiresAuth: true,
      title: 'Аудитории',
      roles: ['admin', 'methodist']
    }
  },
  {
    path: '/catalog/slots',
    name: 'TimeSlots',
    component: TimeSlots,
    meta: { 
      requiresAuth: true,
      title: 'Временные слоты',
      roles: ['admin', 'methodist']
    }
  },
  {
    path: '/catalog/enrollments',
    name: 'Enrollments',
    component: Enrollments,
    meta: { 
      requiresAuth: true,
      title: 'Связи предметов с группами',
      roles: ['admin', 'methodist']
    }
  },
  {
    path: '/catalog/teacher-availability',
    name: 'TeacherAvailability',
    component: TeacherAvailability,
    meta: { 
      requiresAuth: true,
      title: 'Доступность преподавателей',
      roles: ['admin', 'methodist']
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: '/dashboard'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guards
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  // Set page title
  if (to.meta.title) {
    document.title = `${to.meta.title} - Schedule SaaS`
  }
  
  // Check authentication
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
    return
  }
  
  // Check role access
  if (to.meta.roles && authStore.user) {
    const userRole = authStore.user.role?.toLowerCase()
    if (!to.meta.roles.includes(userRole) && userRole !== 'superadmin') {
      next('/dashboard')
      return
    }
  }
  
  // Redirect authenticated users away from login page
  if (to.name === 'Login' && authStore.isAuthenticated) {
    next('/dashboard')
    return
  }
  
  next()
})

export default router
