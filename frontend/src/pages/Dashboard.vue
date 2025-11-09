<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-gray-900">Дашборд</h1>
      <p class="text-gray-600">Добро пожаловать в систему управления расписанием!</p>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <!-- Active Term -->
      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <CalendarIcon class="h-6 w-6 text-gray-400" />
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">
                  Активный семестр
                </dt>
                <dd class="text-lg font-medium text-gray-900">
                  {{ activeTerm?.name || 'Не выбран' }}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <!-- Total Groups -->
      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <UsersIcon class="h-6 w-6 text-gray-400" />
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">
                  Всего групп
                </dt>
                <dd class="text-lg font-medium text-gray-900">
                  {{ stats.totalGroups || 0 }}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <!-- Total Teachers -->
      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <AcademicCapIcon class="h-6 w-6 text-gray-400" />
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">
                  Преподавателей
                </dt>
                <dd class="text-lg font-medium text-gray-900">
                  {{ stats.totalTeachers || 0 }}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <!-- Lessons This Week -->
      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <ClockIcon class="h-6 w-6 text-gray-400" />
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">
                  Пар на этой неделе
                </dt>
                <dd class="text-lg font-medium text-gray-900">
                  {{ stats.lessonsThisWeek || 0 }}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Quick Actions -->
      <div class="lg:col-span-1">
        <div class="bg-white shadow rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">
              Быстрые действия
            </h3>
            <div class="space-y-3">
              <router-link
                to="/schedule"
                class="w-full btn-primary text-left inline-flex items-center"
              >
                <CalendarIcon class="h-5 w-5 mr-2" />
                Просмотр расписания
              </router-link>
              
              <router-link
                v-if="authStore.isMethodist"
                to="/generation"
                class="w-full btn-secondary text-left inline-flex items-center"
              >
                <CogIcon class="h-5 w-5 mr-2" />
                Генерация расписания
              </router-link>
              
              <router-link
                v-if="authStore.isMethodist"
                to="/catalog/groups"
                class="w-full btn-secondary text-left inline-flex items-center"
              >
                <UsersIcon class="h-5 w-5 mr-2" />
                Управление группами
              </router-link>
              
              <router-link
                to="/reports"
                class="w-full btn-secondary text-left inline-flex items-center"
              >
                <DocumentTextIcon class="h-5 w-5 mr-2" />
                Отчеты
              </router-link>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Activity & Today's Schedule -->
      <div class="lg:col-span-2 space-y-8">
        <!-- Conflicts Alert -->
        <div v-if="conflicts.length > 0" class="bg-yellow-50 border-l-4 border-yellow-400 p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <ExclamationTriangleIcon class="h-5 w-5 text-yellow-400" />
            </div>
            <div class="ml-3">
              <p class="text-sm text-yellow-700">
                <strong>Внимание!</strong> Обнаружены конфликты в расписании.
                <router-link to="/reports" class="underline font-medium">
                  Просмотреть детали
                </router-link>
              </p>
            </div>
          </div>
        </div>

        <!-- Today's Schedule -->
        <div class="bg-white shadow rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">
              Расписание на сегодня
            </h3>
            
            <div v-if="todayLessons.length === 0" class="text-gray-500 text-center py-8">
              На сегодня занятий не запланировано
            </div>
            
            <div v-else class="space-y-3">
              <div
                v-for="lesson in todayLessons"
                :key="lesson.lesson_id"
                class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div class="flex items-center space-x-3">
                  <div class="flex-shrink-0">
                    <div
                      :class="{
                        'bg-blue-500': lesson.status === 'planned',
                        'bg-green-500': lesson.status === 'confirmed',
                        'bg-gray-500': lesson.status === 'completed',
                        'bg-red-500': lesson.status === 'cancelled',
                        'bg-yellow-500': lesson.status === 'moved'
                      }"
                      class="w-3 h-3 rounded-full"
                    ></div>
                  </div>
                  <div>
                    <div class="text-sm font-medium text-gray-900">
                      {{ lesson.course_name || 'Предмет' }}
                    </div>
                    <div class="text-sm text-gray-500">
                      {{ lesson.group_name || 'Группа' }} • 
                      {{ lesson.teacher_name || 'Преподаватель' }} •
                      {{ lesson.room_number || 'Аудитория не назначена' }}
                    </div>
                  </div>
                </div>
                <div class="text-sm text-gray-500">
                  {{ lesson.start_time }} - {{ lesson.end_time }}
                </div>
              </div>
            </div>
            
            <div class="mt-4">
              <router-link 
                to="/schedule"
                class="text-sm text-blue-600 hover:text-blue-500 font-medium"
              >
                Посмотреть полное расписание →
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { 
  CalendarIcon, 
  UsersIcon, 
  AcademicCapIcon, 
  ClockIcon,
  CogIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon
} from '@heroicons/vue/24/outline'
import { useAuthStore } from '@/stores/auth'
import { lessonsAPI, catalogAPI, reportsAPI } from '@/services/api'
import { format } from 'date-fns'

export default {
  name: 'Dashboard',
  components: {
    CalendarIcon,
    UsersIcon,
    AcademicCapIcon,
    ClockIcon,
    CogIcon,
    DocumentTextIcon,
    ExclamationTriangleIcon
  },
  setup() {
    const authStore = useAuthStore()
    
    const loading = ref(false)
    const stats = ref({
      totalGroups: 0,
      totalTeachers: 0,
      lessonsThisWeek: 0
    })
    const activeTerm = ref(null)
    const todayLessons = ref([])
    const conflicts = ref([])

    const today = computed(() => format(new Date(), 'yyyy-MM-dd'))

    const formatTimeSlot = (timeSlot) => {
      if (!timeSlot) return ''
      return `${timeSlot.start_time} - ${timeSlot.end_time}`
    }

    const loadDashboardData = async () => {
      loading.value = true
      
      try {
        // Load today's lessons
        try {
          const lessonsResponse = await lessonsAPI.getByDay(today.value)
          todayLessons.value = lessonsResponse.data || lessonsResponse || []
        } catch (error) {
          console.warn('Could not load today lessons:', error)
          todayLessons.value = []
        }

        // Load basic stats (simplified)
        try {
          const groupsResponse = await catalogAPI.getGroups({ limit: 1000 })
          const groupsData = groupsResponse.data || groupsResponse
          stats.value.totalGroups = Array.isArray(groupsData) ? groupsData.length : 0
          console.log('Groups loaded:', groupsData)
        } catch (error) {
          console.warn('Could not load groups count:', error)
          stats.value.totalGroups = 0
        }

        try {
          const teachersResponse = await catalogAPI.getTeachers({ limit: 1000 })
          const teachersData = teachersResponse.data || teachersResponse
          stats.value.totalTeachers = Array.isArray(teachersData) ? teachersData.length : 0
          console.log('Teachers loaded:', teachersData)
        } catch (error) {
          console.warn('Could not load teachers count:', error)
          stats.value.totalTeachers = 0
        }

        // Load conflicts (simplified)
        try {
          const conflictsResponse = await reportsAPI.getConflicts({
            org_id: authStore.user?.org_id || 1
          })
          conflicts.value = conflictsResponse.data || []
        } catch (error) {
          console.warn('Could not load conflicts:', error)
          conflicts.value = []
        }

      } catch (error) {
        console.error('Error loading dashboard data:', error)
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      loadDashboardData()
    })

    return {
      authStore,
      loading,
      stats,
      activeTerm,
      todayLessons,
      conflicts,
      today,
      formatTimeSlot
    }
  }
}
</script>
