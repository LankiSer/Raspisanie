<template>
  <div class="page-container">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1>Дашборд</h1>
        <p class="text-gray-500 text-sm mt-0.5">Добро пожаловать в систему управления расписанием!</p>
      </div>
      <div class="flex items-center gap-3">
        <span v-if="activeTerm" class="badge-blue text-sm">{{ activeTerm.name }}</span>
        <button
          v-if="authStore.user?.role === 'admin'"
          @click="runSeed"
          :disabled="seedLoading"
          class="btn-secondary text-sm"
          title="Загрузить тестовые данные ВКСИТ в базу"
        >
          <span v-if="seedLoading">Загрузка…</span>
          <span v-else>Загрузить тест. данные</span>
        </button>
      </div>
    </div>
    <div v-if="seedMessage" :class="seedError ? 'alert-error' : 'alert-success'" class="mb-4">
      {{ seedMessage }}
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div class="stat-card">
        <div class="stat-icon">
          <CalendarDaysIcon class="w-6 h-6 text-gov-600" />
        </div>
        <div>
          <div class="text-xs text-gray-500 font-medium">Активный семестр</div>
          <div class="text-lg font-bold text-gray-900 leading-tight">{{ activeTerm?.name || 'Не задан' }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <UsersIcon class="w-6 h-6 text-gov-600" />
        </div>
        <div>
          <div class="text-xs text-gray-500 font-medium">Всего групп</div>
          <div class="text-3xl font-bold text-gray-900">{{ stats.totalGroups }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <AcademicCapIcon class="w-6 h-6 text-gov-600" />
        </div>
        <div>
          <div class="text-xs text-gray-500 font-medium">Преподавателей</div>
          <div class="text-3xl font-bold text-gray-900">{{ stats.totalTeachers }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <ClockIcon class="w-6 h-6 text-gov-600" />
        </div>
        <div>
          <div class="text-xs text-gray-500 font-medium">Пар на этой неделе</div>
          <div class="text-3xl font-bold text-gray-900">{{ stats.lessonsThisWeek }}</div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Quick Actions -->
      <div class="card card-body lg:col-span-1">
        <h2 class="mb-4">Быстрые действия</h2>
        <div class="space-y-2">
          <router-link to="/schedule" class="btn-primary w-full flex items-center gap-2">
            <CalendarDaysIcon class="w-4 h-4" />
            Расписание
          </router-link>
          <router-link v-if="authStore.isMethodist" to="/generation" class="btn-secondary w-full flex items-center gap-2">
            <CogIcon class="w-4 h-4" />
            Генерация расписания
          </router-link>
          <router-link v-if="authStore.isMethodist" to="/catalog/groups" class="btn-secondary w-full flex items-center gap-2">
            <UsersIcon class="w-4 h-4" />
            Управление группами
          </router-link>
          <router-link to="/reports" class="btn-secondary w-full flex items-center gap-2">
            <DocumentTextIcon class="w-4 h-4" />
            Отчёты
          </router-link>
          <router-link to="/tg-admin" class="btn-secondary w-full flex items-center gap-2">
            <ChatBubbleLeftIcon class="w-4 h-4" />
            Telegram-диалоги
          </router-link>
        </div>
      </div>

      <!-- Today & Conflicts -->
      <div class="lg:col-span-2 space-y-4">
        <!-- Conflicts alert -->
        <div v-if="conflicts.length" class="alert-error flex items-start gap-3">
          <ExclamationTriangleIcon class="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          <div>
            <span class="font-medium">Внимание!</span> Обнаружены конфликты в расписании.
            <router-link to="/reports" class="underline font-medium ml-1">Подробнее</router-link>
          </div>
        </div>

        <!-- Today's lessons -->
        <div class="card">
          <div class="card-header">
            <h2>Расписание на сегодня</h2>
            <span class="text-xs text-gray-400">{{ todayFormatted }}</span>
          </div>
          <div class="card-body">
            <div v-if="loading" class="text-center text-gray-400 py-6 text-sm">Загрузка…</div>
            <div v-else-if="!todayLessons.length" class="text-center text-gray-400 py-6 text-sm">
              На сегодня занятий не запланировано
            </div>
            <div v-else class="space-y-2">
              <div
                v-for="lesson in todayLessons"
                :key="lesson.lesson_id"
                class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gov-50 transition-colors"
              >
                <div :class="{
                  'bg-gov-500':   lesson.status === 'planned',
                  'bg-green-500': lesson.status === 'confirmed',
                  'bg-gray-400':  lesson.status === 'completed',
                  'bg-red-500':   lesson.status === 'cancelled',
                  'bg-amber-500': lesson.status === 'moved',
                }" class="w-2 h-2 rounded-full shrink-0"></div>
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-medium text-gray-900 truncate">{{ lesson.course_name }}</div>
                  <div class="text-xs text-gray-500 truncate">
                    {{ lesson.group_name }} · {{ lesson.teacher_name }} · {{ lesson.room_number || 'Аудитория не указана' }}
                  </div>
                </div>
                <div class="text-xs text-gray-500 whitespace-nowrap shrink-0">
                  {{ fmtTime(lesson.start_time) }} – {{ fmtTime(lesson.end_time) }}
                </div>
              </div>
            </div>
            <router-link to="/schedule" class="block mt-3 text-sm text-gov-600 hover:text-gov-700 font-medium">
              Посмотреть полное расписание →
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import {
  CalendarDaysIcon, UsersIcon, AcademicCapIcon, ClockIcon,
  CogIcon, DocumentTextIcon, ExclamationTriangleIcon, ChatBubbleLeftIcon,
} from '@heroicons/vue/24/outline'
import { useAuthStore } from '@/stores/auth'
import { lessonsAPI, catalogAPI, reportsAPI, adminAPI } from '@/services/api'
import { format, startOfWeek, endOfWeek } from 'date-fns'
import { ru } from 'date-fns/locale'

export default {
  name: 'Dashboard',
  components: {
    CalendarDaysIcon, UsersIcon, AcademicCapIcon, ClockIcon,
    CogIcon, DocumentTextIcon, ExclamationTriangleIcon, ChatBubbleLeftIcon,
  },
  setup() {
    const authStore = useAuthStore()
    const loading   = ref(false)
    const stats     = ref({ totalGroups: 0, totalTeachers: 0, lessonsThisWeek: 0 })
    const activeTerm  = ref(null)
    const todayLessons = ref([])
    const conflicts    = ref([])
    const seedLoading = ref(false)
    const seedMessage = ref('')
    const seedError   = ref(false)

    const today = computed(() => format(new Date(), 'yyyy-MM-dd'))
    const todayFormatted = computed(() =>
      format(new Date(), 'd MMMM yyyy, EEEE', { locale: ru })
    )

    const fmtTime = (t) => {
      if (!t) return ''
      // Backend returns "HH:MM:SS" — show only "HH:MM"
      return String(t).slice(0, 5)
    }

    const loadDashboardData = async () => {
      loading.value = true
      try {
        // Today's lessons
        try {
          const res = await lessonsAPI.getByDay(today.value)
          todayLessons.value = res.data || []
        } catch {}

        // Groups & teachers counts
        try {
          const [gRes, tRes] = await Promise.all([
            catalogAPI.getGroups({ limit: 1000 }),
            catalogAPI.getTeachers({ limit: 1000 }),
          ])
          stats.value.totalGroups   = (gRes.data || []).length
          stats.value.totalTeachers = (tRes.data || []).length
        } catch {}

        // Active term
        try {
          const tRes = await catalogAPI.getTerms({ limit: 100 })
          const terms = tRes.data || []
          const now = new Date()
          now.setHours(0, 0, 0, 0)
          activeTerm.value =
            terms.find(t => {
              const s = new Date(t.start_date)
              const e = new Date(t.end_date)
              return now >= s && now <= e
            }) ||
            (terms.length ? [...terms].sort((a, b) => new Date(b.start_date) - new Date(a.start_date))[0] : null)
        } catch {}

        // Lessons this week
        try {
          const now = new Date()
          const weekStart = format(startOfWeek(now, { weekStartsOn: 1 }), 'yyyy-MM-dd')
          const weekEnd   = format(endOfWeek(now,   { weekStartsOn: 1 }), 'yyyy-MM-dd')
          const wRes = await lessonsAPI.getByTerm({ start_date: weekStart, end_date: weekEnd })
          stats.value.lessonsThisWeek = (wRes.data || []).length
        } catch {}

        // Conflicts
        try {
          const cRes = await reportsAPI.getConflicts({})
          conflicts.value = cRes.data?.conflicts || []
        } catch {}

      } finally {
        loading.value = false
      }
    }

    const runSeed = async () => {
      seedLoading.value = true
      seedMessage.value = ''
      seedError.value = false
      try {
        const res = await adminAPI.seed()
        seedMessage.value = res.data?.detail || 'Тестовые данные успешно загружены!'
        await loadDashboardData()
      } catch (e) {
        seedError.value = true
        seedMessage.value = e.response?.data?.error?.message || e.response?.data?.detail || 'Ошибка загрузки данных'
      } finally {
        seedLoading.value = false
        setTimeout(() => { seedMessage.value = '' }, 6000)
      }
    }

    onMounted(loadDashboardData)

    return {
      authStore, loading, stats, activeTerm, todayLessons, conflicts,
      today, todayFormatted, fmtTime,
      seedLoading, seedMessage, seedError, runSeed,
    }
  },
}
</script>
