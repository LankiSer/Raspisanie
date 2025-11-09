<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div>
        <h1 class="text-3xl font-bold text-gray-900">Предметы</h1>
        <p class="text-gray-600 mt-1">Управление учебными предметами и их настройками</p>
      </div>
      <button 
        @click="openCreateModal"
        class="btn-primary flex items-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
        </svg>
        Добавить предмет
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
            placeholder="Поиск по названию или коду..."
            class="form-input pl-10"
          />
        </div>
        
        <select v-model="filters.status" class="form-select">
          <option value="">Все статусы</option>
          <option value="active">Активные</option>
          <option value="inactive">Неактивные</option>
        </select>

        <select v-model="filters.credits" class="form-select">
          <option value="">Все кредиты</option>
          <option value="1">1 кредит</option>
          <option value="2">2 кредита</option>
          <option value="3">3 кредита</option>
          <option value="4">4 кредита</option>
          <option value="5">5 кредитов</option>
          <option value="6">6 кредитов</option>
        </select>
      </div>
    </div>

    <!-- Courses Table -->
    <div class="bg-white shadow rounded-lg overflow-hidden">
      <div v-if="loading" class="p-8 text-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p class="mt-2 text-gray-600">Загрузка...</p>
      </div>
      
      <div v-else-if="filteredCourses.length === 0" class="p-8 text-center">
        <BookOpenIcon class="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900 mb-2">
          {{ searchQuery ? 'Предметы не найдены' : 'Нет предметов' }}
        </h3>
        <p class="text-gray-600">
          {{ searchQuery ? 'Попробуйте изменить поисковый запрос' : 'Создайте первый предмет' }}
        </p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Название
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Код
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Кредиты
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
            <tr v-for="course in paginatedCourses" :key="course.course_id" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{{ course.name }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ course.code }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ course.credits }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span 
                  :class="course.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
                  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                >
                  {{ course.is_active ? 'Активный' : 'Неактивный' }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <div class="flex items-center justify-end gap-2">
                  <button
                    @click="openEditModal(course)"
                    class="text-indigo-600 hover:text-indigo-900"
                    title="Редактировать"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                    </svg>
                  </button>
                  <button
                    @click="toggleCourseStatus(course)"
                    :class="course.is_active ? 'text-yellow-600 hover:text-yellow-900' : 'text-green-600 hover:text-green-900'"
                    :title="course.is_active ? 'Деактивировать' : 'Активировать'"
                  >
                    <svg v-if="course.is_active" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636M5.636 18.364l12.728-12.728"></path>
                    </svg>
                    <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                  </button>
                  <button
                    @click="deleteCourse(course)"
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
              <span class="font-medium">{{ Math.min(currentPage * itemsPerPage, filteredCourses.length) }}</span>
              из
              <span class="font-medium">{{ filteredCourses.length }}</span>
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
              {{ editingCourse ? 'Редактировать предмет' : 'Добавить предмет' }}
            </h3>
            <button @click="closeModal" class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>

          <form @submit.prevent="saveCourse" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Название предмета *
              </label>
              <input
                v-model="form.name"
                type="text"
                required
                class="form-input"
                placeholder="Введите название предмета"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Код предмета *
              </label>
              <input
                v-model="form.code"
                type="text"
                required
                class="form-input"
                placeholder="Например: MATH-101"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Количество кредитов *
              </label>
              <input
                v-model.number="form.credits"
                type="number"
                min="1"
                max="10"
                required
                class="form-input"
                placeholder="3"
              />
            </div>

            <div class="flex items-center">
              <input
                v-model="form.isActive"
                type="checkbox"
                class="form-checkbox"
              />
              <label class="ml-2 text-sm text-gray-700">
                Активный предмет
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
                <span v-else>{{ editingCourse ? 'Сохранить' : 'Создать' }}</span>
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
import { BookOpenIcon } from '@heroicons/vue/24/outline'
import { catalogAPI } from '@/services/api'

export default {
  name: 'Courses',
  components: {
    BookOpenIcon
  },
  setup() {
    // State
    const courses = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const showModal = ref(false)
    const editingCourse = ref(null)
    const searchQuery = ref('')
    const currentPage = ref(1)
    const itemsPerPage = 10

    // Filters
    const filters = ref({
      status: '',
      credits: ''
    })

    // Form
    const form = ref({
      name: '',
      code: '',
      credits: 3,
      isActive: true
    })

    // Computed properties for filtering and pagination
    const filteredCourses = computed(() => {
      let filtered = courses.value

      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        filtered = filtered.filter(c => 
          c.name.toLowerCase().includes(query) || 
          c.code.toLowerCase().includes(query)
        )
      }

      if (filters.value.status) {
        const isActive = filters.value.status === 'active'
        filtered = filtered.filter(c => c.is_active === isActive)
      }

      if (filters.value.credits) {
        filtered = filtered.filter(c => c.credits === parseInt(filters.value.credits))
      }

      return filtered
    })

    const totalPages = computed(() => Math.ceil(filteredCourses.value.length / itemsPerPage))
    
    const paginatedCourses = computed(() => {
      const start = (currentPage.value - 1) * itemsPerPage
      const end = start + itemsPerPage
      return filteredCourses.value.slice(start, end)
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

    // Methods
    const loadCourses = async () => {
      loading.value = true
      try {
        const response = await catalogAPI.getCourses()
        courses.value = response.data || []
      } catch (error) {
        console.error('Error loading courses:', error)
        alert('Ошибка при загрузке предметов')
      } finally {
        loading.value = false
      }
    }

    const openCreateModal = () => {
      editingCourse.value = null
      form.value = {
        name: '',
        code: '',
        credits: 3,
        isActive: true
      }
      showModal.value = true
    }

    const openEditModal = (course) => {
      editingCourse.value = course
      form.value = {
        name: course.name,
        code: course.code,
        credits: course.credits,
        isActive: course.is_active
      }
      showModal.value = true
    }

    const closeModal = () => {
      showModal.value = false
      editingCourse.value = null
    }

    const saveCourse = async () => {
      saving.value = true
      try {
        const courseData = {
          org_id: 1, // Demo organization ID
          name: form.value.name,
          code: form.value.code,
          credits: form.value.credits,
          is_active: form.value.isActive
        }

        if (editingCourse.value) {
          // Update existing course
          const updateData = {
            name: form.value.name,
            code: form.value.code,
            credits: form.value.credits,
            is_active: form.value.isActive
          }
          await catalogAPI.updateCourse(editingCourse.value.course_id, updateData)
          const index = courses.value.findIndex(c => c.course_id === editingCourse.value.course_id)
          if (index !== -1) {
            courses.value[index] = { ...editingCourse.value, ...updateData }
          }
        } else {
          // Create new course
          const response = await catalogAPI.createCourse(courseData)
          courses.value.unshift(response.data)
        }

        closeModal()
      } catch (error) {
        console.error('Error saving course:', error)
        alert('Ошибка при сохранении предмета')
      } finally {
        saving.value = false
      }
    }

    const toggleCourseStatus = async (course) => {
      try {
        const updateData = { is_active: !course.is_active }
        await catalogAPI.updateCourse(course.course_id, updateData)
        course.is_active = !course.is_active
      } catch (error) {
        console.error('Error toggling course status:', error)
        alert('Ошибка при изменении статуса предмета')
      }
    }

    const deleteCourse = async (course) => {
      if (!confirm(`Вы уверены, что хотите удалить предмет "${course.name}"?`)) {
        return
      }

      try {
        await catalogAPI.deleteCourse(course.course_id)
        const index = courses.value.findIndex(c => c.course_id === course.course_id)
        if (index !== -1) {
          courses.value.splice(index, 1)
        }
      } catch (error) {
        console.error('Error deleting course:', error)
        alert('Ошибка при удалении предмета')
      }
    }

    // Watchers
    watch([searchQuery, filters], () => {
      currentPage.value = 1
    })

    // Lifecycle
    onMounted(() => {
      loadCourses()
    })

    return {
      // State
      courses, loading, saving, showModal, editingCourse, searchQuery, currentPage, itemsPerPage, filters, form,
      // Computed
      filteredCourses, totalPages, paginatedCourses, visiblePages,
      // Methods
      loadCourses, openCreateModal, openEditModal, closeModal, saveCourse, toggleCourseStatus, deleteCourse
    }
  }
}
</script>