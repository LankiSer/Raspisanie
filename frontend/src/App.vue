<template>
  <div id="app" class="min-h-screen flex flex-col bg-gray-50">

    <!-- ── Top bar (gov-style) ───────────────────── -->
    <header v-if="authStore.isAuthenticated" class="bg-gov-700 text-white shadow-md">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16 gap-4">

          <!-- Logo -->
          <router-link to="/dashboard" class="flex items-center gap-3 shrink-0">
            <div class="w-9 h-9 rounded bg-white/20 flex items-center justify-center">
              <CalendarDaysIcon class="w-5 h-5 text-white" />
            </div>
            <div class="hidden sm:block">
              <div class="text-sm font-bold leading-tight tracking-wide">ВКСИТ</div>
              <div class="text-xs text-gov-200 leading-tight">Расписание занятий</div>
            </div>
          </router-link>

          <!-- Nav links -->
          <nav class="hidden md:flex items-center gap-1 flex-1">
            <router-link
              v-for="link in navLinks"
              :key="link.to"
              :to="link.to"
              class="px-3 py-1.5 rounded text-sm font-medium text-gov-100 hover:text-white hover:bg-white/10 transition-colors"
              active-class="bg-white/15 text-white"
            >
              {{ link.label }}
            </router-link>

            <!-- Справочники dropdown -->
            <div class="relative" @mouseenter="handleMenuEnter" @mouseleave="handleMenuLeave">
              <button class="px-3 py-1.5 rounded text-sm font-medium text-gov-100 hover:text-white hover:bg-white/10 transition-colors inline-flex items-center gap-1">
                Справочники
                <ChevronDownIcon class="w-3.5 h-3.5" />
              </button>
              <div
                v-show="showCatalogMenu"
                class="absolute top-full left-0 mt-1 w-56 rounded-lg shadow-lg bg-white border border-gray-200 z-50"
                @mouseenter="handleMenuEnter"
                @mouseleave="handleMenuLeave"
              >
                <div class="py-1">
                  <router-link v-for="item in catalogLinks" :key="item.to" :to="item.to"
                    class="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gov-50 hover:text-gov-700 transition-colors">
                    {{ item.label }}
                  </router-link>
                </div>
              </div>
            </div>
          </nav>

          <!-- User section -->
          <div class="flex items-center gap-3 shrink-0">
            <span class="hidden lg:block text-xs text-gov-200 max-w-[160px] truncate">
              {{ authStore.user?.email }}
            </span>
            <span class="hidden lg:block badge bg-white/20 text-white text-xs">
              {{ roleLabel }}
            </span>
            <button
              @click="logout"
              class="px-3 py-1.5 rounded text-sm text-gov-100 hover:text-white hover:bg-white/10 transition-colors border border-white/20"
            >
              Выйти
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- ── Page content ──────────────────────────── -->
    <main class="flex-1">
      <router-view />
    </main>

    <!-- ── Footer ────────────────────────────────── -->
    <footer v-if="authStore.isAuthenticated" class="border-t border-gray-200 bg-white mt-auto">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between text-xs text-gray-400">
        <span>АПОУ ВО «Вологодский колледж связи и информационных технологий»</span>
        <span>Система управления расписанием</span>
      </div>
    </footer>

    <!-- ── Toast notifications ───────────────────── -->
    <div class="fixed top-20 right-4 space-y-2 z-50 max-w-sm w-full pointer-events-none">
      <div
        v-for="notification in notifications"
        :key="notification.id"
        :class="{
          'bg-green-600 border-green-700': notification.type === 'success',
          'bg-red-600 border-red-700':     notification.type === 'error',
          'bg-gov-600 border-gov-700':     notification.type === 'info',
          'bg-amber-500 border-amber-600': notification.type === 'warning',
        }"
        class="pointer-events-auto flex items-start gap-3 text-white px-4 py-3 rounded-lg shadow-lg border text-sm"
      >
        <span class="flex-1">{{ notification.message }}</span>
        <button @click="removeNotification(notification.id)" class="text-white/70 hover:text-white shrink-0 leading-none text-lg">×</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronDownIcon, CalendarDaysIcon } from '@heroicons/vue/24/outline'
import { useAuthStore } from './stores/auth'

export default {
  name: 'App',
  components: { ChevronDownIcon, CalendarDaysIcon },
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    const showCatalogMenu = ref(false)
    const notifications = ref([])
    let menuCloseTimeout = null

    const navLinks = [
      { to: '/dashboard', label: 'Дашборд' },
      { to: '/schedule',  label: 'Расписание' },
      { to: '/generation', label: 'Генерация' },
      { to: '/reports',   label: 'Отчёты' },
      { to: '/tg-admin',  label: 'Telegram' },
    ]

    const catalogLinks = [
      { to: '/catalog/groups',               label: 'Группы' },
      { to: '/catalog/teachers',             label: 'Преподаватели' },
      { to: '/catalog/courses',              label: 'Предметы' },
      { to: '/catalog/rooms',               label: 'Аудитории' },
      { to: '/catalog/slots',               label: 'Временные слоты' },
      { to: '/catalog/enrollments',         label: 'Связи предметов с группами' },
      { to: '/catalog/teacher-availability', label: 'Доступность преподавателей' },
    ]

    const roleLabel = computed(() => {
      const map = {
        superadmin: 'Суперадмин',
        admin: 'Администратор',
        methodist: 'Методист',
        teacher: 'Преподаватель',
        student: 'Студент',
      }
      return map[authStore.user?.role?.toLowerCase()] ?? authStore.user?.role ?? ''
    })

    const addNotification = (message, type = 'info') => {
      const id = Date.now()
      notifications.value.push({ id, message, type })
      setTimeout(() => removeNotification(id), 5000)
    }

    const removeNotification = (id) => {
      const index = notifications.value.findIndex(n => n.id === id)
      if (index > -1) notifications.value.splice(index, 1)
    }

    const logout = async () => {
      try {
        await authStore.logout()
        router.push('/login')
      } catch (e) {
        console.error('Logout error:', e)
      }
    }

    const handleMenuEnter = () => {
      if (menuCloseTimeout) { clearTimeout(menuCloseTimeout); menuCloseTimeout = null }
      showCatalogMenu.value = true
    }

    const handleMenuLeave = () => {
      menuCloseTimeout = setTimeout(() => {
        showCatalogMenu.value = false
        menuCloseTimeout = null
      }, 300)
    }

    window.addEventListener('unhandledrejection', (event) => {
      if (event.reason?.response?.status === 401) {
        authStore.logout()
        router.push('/login')
      }
    })

    return {
      authStore, showCatalogMenu, notifications,
      navLinks, catalogLinks, roleLabel,
      addNotification, removeNotification,
      logout, handleMenuEnter, handleMenuLeave,
    }
  },
}
</script>