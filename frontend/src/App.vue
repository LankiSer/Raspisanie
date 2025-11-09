<template>
  <div id="app" class="min-h-screen bg-gray-50">
    <!-- Navigation -->
    <nav v-if="authStore.isAuthenticated" class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <!-- Logo & Main Navigation -->
          <div class="flex">
            <div class="flex-shrink-0 flex items-center">
              <router-link to="/dashboard" class="text-xl font-semibold text-blue-600">
                Schedule
              </router-link>
            </div>
            <div class="hidden md:ml-6 md:flex md:space-x-8 md:items-center">
              <router-link
                to="/dashboard"
                class="border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm"
                active-class="border-blue-500 text-gray-900"
              >
                Дашборд
              </router-link>
              <router-link
                to="/schedule"
                class="border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm"
                active-class="border-blue-500 text-gray-900"
              >
                Расписание
              </router-link>
              <div class="relative" @mouseenter="showCatalogMenu = true" @mouseleave="showCatalogMenu = false">
                <button
                  class="border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm inline-flex items-center"
                >
                  Справочники
                  <ChevronDownIcon class="ml-1 h-4 w-4" />
                </button>
                <div
                  v-show="showCatalogMenu"
                  class="absolute z-10 left-0 mt-1 w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5"
                >
                  <div class="py-1">
                    <router-link to="/catalog/groups" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                      Группы
                    </router-link>
                    <router-link to="/catalog/teachers" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                      Преподаватели
                    </router-link>
                    <router-link to="/catalog/courses" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                      Предметы
                    </router-link>
                    <router-link to="/catalog/rooms" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                      Аудитории
                    </router-link>
                    <router-link to="/catalog/slots" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                      Временные слоты
                    </router-link>
                    <router-link to="/catalog/enrollments" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                      Связи предметов с группами
                    </router-link>
                    <router-link to="/catalog/teacher-availability" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                      Доступность преподавателей
                    </router-link>
                  </div>
                </div>
              </div>
              <router-link
                to="/generation"
                class="border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm"
                active-class="border-blue-500 text-gray-900"
              >
                Генерация
              </router-link>
              <router-link
                to="/reports"
                class="border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm"
                active-class="border-blue-500 text-gray-900"
              >
                Отчеты
              </router-link>
            </div>
          </div>

          <!-- User menu -->
          <div class="flex items-center">
            <div class="relative ml-3">
              <div class="flex items-center space-x-4">
                <span class="text-sm text-gray-700">{{ authStore.user?.email }}</span>
                <button
                  @click="logout"
                  class="text-gray-400 hover:text-gray-500 transition-colors duration-200"
                >
                  Выход
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="flex-1">
      <router-view />
    </main>

    <!-- Toast notifications -->
    <div
      v-if="notifications.length > 0"
      class="fixed top-4 right-4 space-y-2 z-50"
    >
      <div
        v-for="notification in notifications"
        :key="notification.id"
        :class="{
          'bg-green-500': notification.type === 'success',
          'bg-red-500': notification.type === 'error',
          'bg-blue-500': notification.type === 'info',
          'bg-yellow-500': notification.type === 'warning'
        }"
        class="max-w-sm w-full text-white p-4 rounded-lg shadow-lg flex items-center justify-between"
      >
        <span>{{ notification.message }}</span>
        <button
          @click="removeNotification(notification.id)"
          class="ml-4 text-white hover:text-gray-200"
        >
          ×
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronDownIcon } from '@heroicons/vue/24/outline'
import { useAuthStore } from './stores/auth'

export default {
  name: 'App',
  components: {
    ChevronDownIcon
  },
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    const showCatalogMenu = ref(false)
    const notifications = ref([])

    // Auto-hide notifications
    const addNotification = (message, type = 'info') => {
      const id = Date.now()
      notifications.value.push({ id, message, type })
      
      setTimeout(() => {
        removeNotification(id)
      }, 5000)
    }

    const removeNotification = (id) => {
      const index = notifications.value.findIndex(n => n.id === id)
      if (index > -1) {
        notifications.value.splice(index, 1)
      }
    }

    const logout = async () => {
      try {
        await authStore.logout()
        router.push('/login')
      } catch (error) {
        console.error('Logout error:', error)
      }
    }

    // Global error handler for API calls
    window.addEventListener('unhandledrejection', (event) => {
      if (event.reason?.response?.status === 401) {
        authStore.logout()
        router.push('/login')
      }
    })

    return {
      authStore,
      showCatalogMenu,
      notifications,
      addNotification,
      removeNotification,
      logout
    }
  }
}
</script>