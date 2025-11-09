<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div>
        <h1 class="text-3xl font-bold text-gray-900">Преподаватели</h1>
        <p class="text-gray-600 mt-1">Управление преподавателями и их доступностью</p>
      </div>
      <button 
        @click="openCreateModal"
        class="btn-primary flex items-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
        </svg>
        Добавить преподавателя
      </button>
    </div>

    <!-- Search and Filters -->
    <div class="bg-white shadow rounded-lg p-4 mb-6">
      <div class="flex flex-col sm:flex-row gap-4">
        <div class="flex-1">
          <div class="relative">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
              </svg>
            </div>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Поиск по имени или email..."
              class="form-input pl-10"
            />
          </div>
        </div>
        <div class="flex gap-2">
          <select v-model="filters.status" class="form-select">
            <option value="">Все статусы</option>
            <option value="active">Активные</option>
            <option value="inactive">Неактивные</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Teachers Table -->
    <div class="bg-white shadow rounded-lg overflow-hidden">
      <div v-if="loading" class="p-8 text-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p class="mt-2 text-gray-600">Загрузка...</p>
      </div>
      
      <div v-else-if="filteredTeachers.length === 0" class="p-8 text-center">
        <AcademicCapIcon class="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900 mb-2">
          {{ searchQuery ? 'Преподаватели не найдены' : 'Нет преподавателей' }}
        </h3>
        <p class="text-gray-600">
          {{ searchQuery ? 'Попробуйте изменить поисковый запрос' : 'Добавьте первого преподавателя' }}
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
                Email
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Телефон
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
            <tr v-for="teacher in paginatedTeachers" :key="teacher.teacher_id" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                  <div class="flex-shrink-0 h-10 w-10">
                    <div class="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                      <span class="text-sm font-medium text-indigo-600">
                        {{ teacher.first_name[0] }}{{ teacher.last_name[0] }}
                      </span>
                    </div>
                  </div>
                  <div class="ml-4">
                    <div class="text-sm font-medium text-gray-900">
                      {{ teacher.first_name }} {{ teacher.last_name }}
                    </div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ teacher.email }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ teacher.phone || '—' }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span :class="teacher.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'" 
                      class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">
                  {{ teacher.is_active ? 'Активен' : 'Неактивен' }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <div class="flex items-center justify-end gap-2">
                  <button
                    @click="openEditModal(teacher)"
                    class="text-indigo-600 hover:text-indigo-900"
                    title="Редактировать"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                    </svg>
                  </button>
                  <button
                    @click="toggleTeacherStatus(teacher)"
                    :class="teacher.is_active ? 'text-yellow-600 hover:text-yellow-900' : 'text-green-600 hover:text-green-900'"
                    :title="teacher.is_active ? 'Деактивировать' : 'Активировать'"
                  >
                    <svg v-if="teacher.is_active" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636M5.636 18.364l12.728-12.728"></path>
                    </svg>
                    <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                  </button>
                  <button
                    @click="deleteTeacher(teacher)"
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
            class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          >
            Предыдущая
          </button>
          <button
            @click="currentPage = Math.min(totalPages, currentPage + 1)"
            :disabled="currentPage === totalPages"
            class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          >
            Следующая
          </button>
        </div>
        <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
          <div>
            <p class="text-sm text-gray-700">
              Показано <span class="font-medium">{{ (currentPage - 1) * itemsPerPage + 1 }}</span>
              - <span class="font-medium">{{ Math.min(currentPage * itemsPerPage, filteredTeachers.length) }}</span>
              из <span class="font-medium">{{ filteredTeachers.length }}</span> преподавателей
            </p>
          </div>
          <div>
            <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
              <button
                v-for="page in visiblePages"
                :key="page"
                @click="currentPage = page"
                :class="page === currentPage ? 'bg-indigo-50 border-indigo-500 text-indigo-600' : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'"
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
              {{ editingTeacher ? 'Редактировать преподавателя' : 'Добавить преподавателя' }}
            </h3>
            <button @click="closeModal" class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
          
          <form @submit.prevent="saveTeacher" class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Имя *
                </label>
                <input
                  v-model="form.firstName"
                  type="text"
                  required
                  class="form-input"
                  placeholder="Имя"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Фамилия *
                </label>
                <input
                  v-model="form.lastName"
                  type="text"
                  required
                  class="form-input"
                  placeholder="Фамилия"
                />
              </div>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Email *
              </label>
              <input
                v-model="form.email"
                type="email"
                required
                class="form-input"
                placeholder="email@university.edu"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Телефон
              </label>
              <input
                v-model="form.phone"
                type="tel"
                class="form-input"
                placeholder="+7-499-123-45-67"
              />
            </div>
            
            <div class="flex items-center">
              <input
                v-model="form.isActive"
                type="checkbox"
                class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <label class="ml-2 block text-sm text-gray-900">
                Активный преподаватель
              </label>
            </div>
            
            <div class="flex justify-end gap-3 pt-4">
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
                <span v-else>{{ editingTeacher ? 'Сохранить' : 'Создать' }}</span>
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
import { AcademicCapIcon } from '@heroicons/vue/24/outline'
import { catalogAPI } from '@/services/api'

export default {
  name: 'Teachers',
  components: {
    AcademicCapIcon
  },
  setup() {
    // State
    const teachers = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const showModal = ref(false)
    const editingTeacher = ref(null)
    const searchQuery = ref('')
    const currentPage = ref(1)
    const itemsPerPage = 10

    // Filters
    const filters = ref({
      status: ''
    })

    // Form
    const form = ref({
      firstName: '',
      lastName: '',
      email: '',
      phone: '',
      isActive: true
    })

    // Computed
    const filteredTeachers = computed(() => {
      let filtered = teachers.value

      // Search filter
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        filtered = filtered.filter(teacher => 
          teacher.first_name.toLowerCase().includes(query) ||
          teacher.last_name.toLowerCase().includes(query) ||
          teacher.email.toLowerCase().includes(query)
        )
      }

      // Status filter
      if (filters.value.status) {
        const isActive = filters.value.status === 'active'
        filtered = filtered.filter(teacher => teacher.is_active === isActive)
      }

      return filtered
    })

    const totalPages = computed(() => 
      Math.ceil(filteredTeachers.value.length / itemsPerPage)
    )

    const paginatedTeachers = computed(() => {
      const start = (currentPage.value - 1) * itemsPerPage
      const end = start + itemsPerPage
      return filteredTeachers.value.slice(start, end)
    })

    const visiblePages = computed(() => {
      const pages = []
      const total = totalPages.value
      const current = currentPage.value
      
      if (total <= 7) {
        for (let i = 1; i <= total; i++) {
          pages.push(i)
        }
      } else {
        if (current <= 4) {
          for (let i = 1; i <= 5; i++) {
            pages.push(i)
          }
          pages.push('...')
          pages.push(total)
        } else if (current >= total - 3) {
          pages.push(1)
          pages.push('...')
          for (let i = total - 4; i <= total; i++) {
            pages.push(i)
          }
        } else {
          pages.push(1)
          pages.push('...')
          for (let i = current - 1; i <= current + 1; i++) {
            pages.push(i)
          }
          pages.push('...')
          pages.push(total)
        }
      }
      
      return pages
    })

    // Methods
    const loadTeachers = async () => {
      loading.value = true
      try {
        const response = await catalogAPI.getTeachers()
        teachers.value = response.data || []
      } catch (error) {
        console.error('Error loading teachers:', error)
        teachers.value = []
      } finally {
        loading.value = false
      }
    }

    const openCreateModal = () => {
      editingTeacher.value = null
      form.value = {
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        isActive: true
      }
      showModal.value = true
    }

    const openEditModal = (teacher) => {
      editingTeacher.value = teacher
      form.value = {
        firstName: teacher.first_name,
        lastName: teacher.last_name,
        email: teacher.email,
        phone: teacher.phone || '',
        isActive: teacher.is_active
      }
      showModal.value = true
    }

    const closeModal = () => {
      showModal.value = false
      editingTeacher.value = null
      form.value = {
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        isActive: true
      }
    }

    const saveTeacher = async () => {
      saving.value = true
      try {
        const teacherData = {
          first_name: form.value.firstName,
          last_name: form.value.lastName,
          email: form.value.email,
          phone: form.value.phone || null,
          is_active: form.value.isActive
        }

        if (editingTeacher.value) {
          // Update existing teacher
          await catalogAPI.updateTeacher(editingTeacher.value.teacher_id, teacherData)
          const index = teachers.value.findIndex(t => t.teacher_id === editingTeacher.value.teacher_id)
          if (index !== -1) {
            teachers.value[index] = { ...editingTeacher.value, ...teacherData }
          }
        } else {
          // Create new teacher
          const response = await catalogAPI.createTeacher(teacherData)
          teachers.value.unshift(response.data)
        }

        closeModal()
      } catch (error) {
        console.error('Error saving teacher:', error)
        alert('Ошибка при сохранении преподавателя')
      } finally {
        saving.value = false
      }
    }

    const toggleTeacherStatus = async (teacher) => {
      try {
        const newStatus = !teacher.is_active
        await catalogAPI.updateTeacher(teacher.teacher_id, { is_active: newStatus })
        teacher.is_active = newStatus
      } catch (error) {
        console.error('Error toggling teacher status:', error)
        alert('Ошибка при изменении статуса преподавателя')
      }
    }

    const deleteTeacher = async (teacher) => {
      if (!confirm(`Вы уверены, что хотите удалить преподавателя "${teacher.first_name} ${teacher.last_name}"?`)) {
        return
      }

      try {
        await catalogAPI.deleteTeacher(teacher.teacher_id)
        const index = teachers.value.findIndex(t => t.teacher_id === teacher.teacher_id)
        if (index !== -1) {
          teachers.value.splice(index, 1)
        }
      } catch (error) {
        console.error('Error deleting teacher:', error)
        alert('Ошибка при удалении преподавателя')
      }
    }

    // Watchers
    watch([searchQuery, filters], () => {
      currentPage.value = 1
    })

    // Lifecycle
    onMounted(() => {
      loadTeachers()
    })

    return {
      // State
      teachers,
      loading,
      saving,
      showModal,
      editingTeacher,
      searchQuery,
      currentPage,
      itemsPerPage,
      filters,
      form,
      
      // Computed
      filteredTeachers,
      totalPages,
      paginatedTeachers,
      visiblePages,
      
      // Methods
      loadTeachers,
      openCreateModal,
      openEditModal,
      closeModal,
      saveTeacher,
      toggleTeacherStatus,
      deleteTeacher
    }
  }
}
</script>
