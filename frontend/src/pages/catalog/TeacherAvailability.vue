<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div>
        <h1 class="text-3xl font-bold text-gray-900">Доступность преподавателей</h1>
        <p class="text-gray-600 mt-1">Настройка расписания работы преподавателей</p>
      </div>
      <button 
        @click="openCreateModal"
        class="btn-primary flex items-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
        </svg>
        Добавить доступность
      </button>
    </div>

    <!-- Search and Filters -->
    <div class="bg-white shadow rounded-lg p-4 mb-6">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="relative">
          <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
          </div>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Поиск по преподавателю..."
            class="form-input pl-10"
          />
        </div>
        
        <select v-model="filters.teacher" class="form-select">
          <option value="">Все преподаватели</option>
          <option v-for="teacher in teachers" :key="teacher.teacher_id" :value="teacher.teacher_id">
            {{ teacher.first_name }} {{ teacher.last_name }}
          </option>
        </select>

        <select v-model="filters.day" class="form-select">
          <option value="">Все дни</option>
          <option value="1">Понедельник</option>
          <option value="2">Вторник</option>
          <option value="3">Среда</option>
          <option value="4">Четверг</option>
          <option value="5">Пятница</option>
        </select>
      </div>
    </div>

    <!-- Availability Table -->
    <div class="bg-white shadow rounded-lg overflow-hidden">
      <div v-if="loading" class="p-8 text-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p class="mt-2 text-gray-600">Загрузка...</p>
      </div>
      
      <div v-else-if="filteredAvailability.length === 0" class="p-8 text-center">
        <ClockIcon class="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900 mb-2">
          {{ searchQuery ? 'Доступность не найдена' : 'Нет настроек доступности' }}
        </h3>
        <p class="text-gray-600">
          {{ searchQuery ? 'Попробуйте изменить поисковый запрос' : 'Добавьте первую настройку доступности' }}
        </p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Преподаватель
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                День недели
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Время работы
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Статус
              </th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Действия
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="availability in paginatedAvailability" :key="availability.availability_id" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{{ getTeacherName(availability.teacher_id) }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ getDayName(availability.weekday) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ availability.start_time }} - {{ availability.end_time }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span 
                  :class="availability.is_available ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
                  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                >
                  {{ availability.is_available ? 'Доступен' : 'Недоступен' }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <div class="flex items-center justify-end gap-2">
                  <button
                    @click="openEditModal(availability)"
                    class="text-indigo-600 hover:text-indigo-900"
                    title="Редактировать"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                    </svg>
                  </button>
                  <button
                    @click="toggleAvailability(availability)"
                    :class="availability.is_available ? 'text-yellow-600 hover:text-yellow-900' : 'text-green-600 hover:text-green-900'"
                    :title="availability.is_available ? 'Сделать недоступным' : 'Сделать доступным'"
                  >
                    <svg v-if="availability.is_available" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636M5.636 18.364l12.728-12.728"></path>
                    </svg>
                    <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                  </button>
                  <button
                    @click="deleteAvailability(availability)"
                    class="text-red-600 hover:text-red-900"
                    title="Удалить"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
        <div class="flex-1 flex justify-between sm:hidden">
          <button
            @click="currentPage = Math.max(1, currentPage - 1)"
            :disabled="currentPage === 1"
            class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Предыдущая
          </button>
          <button
            @click="currentPage = Math.min(totalPages, currentPage + 1)"
            :disabled="currentPage === totalPages"
            class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Следующая
          </button>
        </div>
        <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
          <div>
            <p class="text-sm text-gray-700">
              Показано
              <span class="font-medium">{{ (currentPage - 1) * itemsPerPage + 1 }}</span>
              -
              <span class="font-medium">{{ Math.min(currentPage * itemsPerPage, filteredAvailability.length) }}</span>
              из
              <span class="font-medium">{{ filteredAvailability.length }}</span>
              результатов
            </p>
          </div>
          <div>
            <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
              <button
                v-for="page in visiblePages"
                :key="page"
                @click="currentPage = page"
                :class="page === currentPage ? 'z-10 bg-indigo-50 border-indigo-500 text-indigo-600' : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'"
                class="relative inline-flex items-center px-4 py-2 border text-sm font-medium"
              >
                {{ page }}
              </button>
            </nav>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div class="mt-3">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-medium text-gray-900">
              {{ editingAvailability ? 'Редактировать доступность' : 'Добавить доступность' }}
            </h3>
            <button @click="closeModal" class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>

          <form @submit.prevent="saveAvailability" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Преподаватель *
              </label>
              <select v-model="form.teacher_id" required class="form-select">
                <option value="">Выберите преподавателя</option>
                <option v-for="teacher in teachers" :key="teacher.teacher_id" :value="teacher.teacher_id">
                  {{ teacher.first_name }} {{ teacher.last_name }}
                </option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                День недели *
              </label>
              <select v-model="form.weekday" required class="form-select">
                <option value="">Выберите день</option>
                <option value="1">Понедельник</option>
                <option value="2">Вторник</option>
                <option value="3">Среда</option>
                <option value="4">Четверг</option>
                <option value="5">Пятница</option>
              </select>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Начало работы *
                </label>
                <input
                  v-model="form.start_time"
                  type="time"
                  required
                  class="form-input"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Конец работы *
                </label>
                <input
                  v-model="form.end_time"
                  type="time"
                  required
                  class="form-input"
                />
              </div>
            </div>

            <div class="flex items-center">
              <input
                v-model="form.is_available"
                type="checkbox"
                class="form-checkbox"
              />
              <label class="ml-2 text-sm text-gray-700">
                Доступен в это время
              </label>
            </div>

            <div class="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                @click="closeModal"
                class="btn-secondary"
              >
                Отмена
              </button>
              <button
                type="submit"
                :disabled="saving"
                class="btn-primary"
              >
                <span v-if="saving">Сохранение...</span>
                <span v-else>{{ editingAvailability ? 'Сохранить' : 'Создать' }}</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import { ClockIcon } from '@heroicons/vue/24/outline'
import { catalogAPI } from '@/services/api'

export default {
  name: 'TeacherAvailability',
  components: {
    ClockIcon
  },
  setup() {
    // State
    const availability = ref([])
    const teachers = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const showModal = ref(false)
    const editingAvailability = ref(null)
    const searchQuery = ref('')
    const currentPage = ref(1)
    const itemsPerPage = 10

    // Filters
    const filters = ref({
      teacher: '',
      day: ''
    })

    // Form
    const form = ref({
      teacher_id: '',
      weekday: '',
      start_time: '09:00',
      end_time: '17:00',
      is_available: true
    })

    // Computed properties for filtering and pagination
    const filteredAvailability = computed(() => {
      let filtered = availability.value

      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        filtered = filtered.filter(a => 
          getTeacherName(a.teacher_id).toLowerCase().includes(query)
        )
      }

      if (filters.value.teacher) {
        filtered = filtered.filter(a => a.teacher_id === parseInt(filters.value.teacher))
      }

      if (filters.value.day) {
        filtered = filtered.filter(a => a.weekday === parseInt(filters.value.day))
      }

      return filtered
    })

    const totalPages = computed(() => Math.ceil(filteredAvailability.value.length / itemsPerPage))
    
    const paginatedAvailability = computed(() => {
      const start = (currentPage.value - 1) * itemsPerPage
      const end = start + itemsPerPage
      return filteredAvailability.value.slice(start, end)
    })

    const visiblePages = computed(() => {
      const pages = []
      const start = Math.max(1, currentPage.value - 2)
      const end = Math.min(totalPages.value, currentPage.value + 2)
      
      for (let i = start; i <= end; i++) {
        pages.push(i)
      }
      return pages
    })

    // Helper methods
    const getTeacherName = (teacherId) => {
      const teacher = teachers.value.find(t => t.teacher_id === teacherId)
      return teacher ? `${teacher.first_name} ${teacher.last_name}` : `Преподаватель ${teacherId}`
    }

    const getDayName = (dayOfWeek) => {
      const days = ['', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
      return days[dayOfWeek] || `День ${dayOfWeek}`
    }

    // Methods
    const loadData = async () => {
      loading.value = true
      try {
        const [availabilityRes, teachersRes] = await Promise.all([
          catalogAPI.getTeacherAvailability(),
          catalogAPI.getTeachers()
        ])
        
        availability.value = availabilityRes.data || []
        teachers.value = teachersRes.data || []
      } catch (error) {
        console.error('Error loading data:', error)
        alert('Ошибка при загрузке данных')
      } finally {
        loading.value = false
      }
    }

    const openCreateModal = () => {
      editingAvailability.value = null
      form.value = {
        teacher_id: '',
        weekday: '',
        start_time: '09:00',
        end_time: '17:00',
        is_available: true
      }
      showModal.value = true
    }

    const openEditModal = (availabilityItem) => {
      editingAvailability.value = availabilityItem
      form.value = {
        teacher_id: availabilityItem.teacher_id,
        weekday: availabilityItem.weekday,
        start_time: availabilityItem.start_time,
        end_time: availabilityItem.end_time,
        is_available: availabilityItem.is_available
      }
      showModal.value = true
    }

    const closeModal = () => {
      showModal.value = false
      editingAvailability.value = null
    }

    const saveAvailability = async () => {
      saving.value = true
      try {
        const availabilityData = {
          org_id: 1, // Demo organization ID
          teacher_id: parseInt(form.value.teacher_id),
          weekday: parseInt(form.value.weekday),
          start_time: form.value.start_time,
          end_time: form.value.end_time,
          is_available: form.value.is_available
        }

        if (editingAvailability.value) {
          // Update existing availability
          const updateData = {
            teacher_id: parseInt(form.value.teacher_id),
            weekday: parseInt(form.value.weekday),
            start_time: form.value.start_time,
            end_time: form.value.end_time,
            is_available: form.value.is_available
          }
          await catalogAPI.updateTeacherAvailability(editingAvailability.value.availability_id, updateData)
          const index = availability.value.findIndex(a => a.availability_id === editingAvailability.value.availability_id)
          if (index !== -1) {
            availability.value[index] = { ...editingAvailability.value, ...updateData }
          }
        } else {
          // Create new availability
          const response = await catalogAPI.createTeacherAvailability(availabilityData)
          availability.value.unshift(response.data)
        }

        closeModal()
      } catch (error) {
        console.error('Error saving availability:', error)
        alert('Ошибка при сохранении доступности')
      } finally {
        saving.value = false
      }
    }

    const toggleAvailability = async (availabilityItem) => {
      try {
        const updateData = { is_available: !availabilityItem.is_available }
        await catalogAPI.updateTeacherAvailability(availabilityItem.availability_id, updateData)
        availabilityItem.is_available = !availabilityItem.is_available
      } catch (error) {
        console.error('Error toggling availability:', error)
        alert('Ошибка при изменении статуса доступности')
      }
    }

    const deleteAvailability = async (availabilityItem) => {
      if (!confirm(`Вы уверены, что хотите удалить доступность "${getTeacherName(availabilityItem.teacher_id)}" - "${getDayName(availabilityItem.weekday)}"?`)) {
        return
      }

      try {
        await catalogAPI.deleteTeacherAvailability(availabilityItem.availability_id)
        const index = availability.value.findIndex(a => a.availability_id === availabilityItem.availability_id)
        if (index !== -1) {
          availability.value.splice(index, 1)
        }
      } catch (error) {
        console.error('Error deleting availability:', error)
        alert('Ошибка при удалении доступности')
      }
    }

    // Watchers
    watch([searchQuery, filters], () => {
      currentPage.value = 1
    })

    // Lifecycle
    onMounted(() => {
      loadData()
    })

    return {
      // State
      availability, teachers, loading, saving, showModal, editingAvailability, searchQuery, currentPage, itemsPerPage, filters, form,
      // Computed
      filteredAvailability, totalPages, paginatedAvailability, visiblePages,
      // Methods
      loadData, openCreateModal, openEditModal, closeModal, saveAvailability, toggleAvailability, deleteAvailability,
      getTeacherName, getDayName
    }
  }
}
</script>
