<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div>
        <h1 class="text-3xl font-bold text-gray-900">Связи предметов с группами</h1>
        <p class="text-gray-600 mt-1">Управление привязкой предметов к группам и преподавателям</p>
      </div>
      <button 
        @click="openCreateModal"
        class="btn-primary flex items-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
        </svg>
        Добавить связь
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
            placeholder="Поиск по группе, предмету или преподавателю..."
            class="form-input pl-10"
          />
        </div>
        
        <select v-model="filters.group" class="form-select">
          <option value="">Все группы</option>
          <option v-for="group in groups" :key="group.group_id" :value="group.group_id">
            {{ group.name }}
          </option>
        </select>

        <select v-model="filters.course" class="form-select">
          <option value="">Все предметы</option>
          <option v-for="course in courses" :key="course.course_id" :value="course.course_id">
            {{ course.name }}
          </option>
        </select>
      </div>
    </div>

    <!-- Enrollments Table -->
    <div class="bg-white shadow rounded-lg overflow-hidden">
      <div v-if="loading" class="p-8 text-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p class="mt-2 text-gray-600">Загрузка...</p>
      </div>
      
      <div v-else-if="filteredEnrollments.length === 0" class="p-8 text-center">
        <LinkIcon class="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900 mb-2">
          {{ searchQuery ? 'Связи не найдены' : 'Нет связей' }}
        </h3>
        <p class="text-gray-600">
          {{ searchQuery ? 'Попробуйте изменить поисковый запрос' : 'Создайте первую связь' }}
        </p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Группа
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Предмет
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Преподаватель
              </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Часов в семестр
                  </th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Действия
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="enrollment in paginatedEnrollments" :key="enrollment.enrollment_id" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{{ getGroupName(enrollment.group_id) }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{{ getCourseName(enrollment.assignment_id) }}</div>
                <div class="text-sm text-gray-500">{{ getCourseCode(enrollment.assignment_id) }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ getTeacherName(enrollment.assignment_id) }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ enrollment.planned_hours }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <div class="flex items-center justify-end gap-2">
                  <button
                    @click="openEditModal(enrollment)"
                    class="text-indigo-600 hover:text-indigo-900"
                    title="Редактировать"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                    </svg>
                  </button>
                  <button
                    @click="deleteEnrollment(enrollment)"
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
              <span class="font-medium">{{ Math.min(currentPage * itemsPerPage, filteredEnrollments.length) }}</span>
              из
              <span class="font-medium">{{ filteredEnrollments.length }}</span>
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
              {{ editingEnrollment ? 'Редактировать связь' : 'Добавить связь' }}
            </h3>
            <button @click="closeModal" class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>

          <form @submit.prevent="saveEnrollment" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Группа *
              </label>
              <select v-model="form.group_id" required class="form-select">
                <option value="">Выберите группу</option>
                <option v-for="group in groups" :key="group.group_id" :value="group.group_id">
                  {{ group.name }}
                </option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Предмет *
              </label>
              <select v-model="form.course_id" required class="form-select">
                <option value="">Выберите предмет</option>
                <option v-for="course in courses" :key="course.course_id" :value="course.course_id">
                  {{ course.name }} ({{ course.code }})
                </option>
              </select>
            </div>

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
                Часов в семестр *
              </label>
              <input
                v-model.number="form.planned_hours_per_semester"
                type="number"
                min="30"
                max="120"
                required
                class="form-input"
                placeholder="60"
              />
              <p class="text-xs text-gray-500 mt-1">
                Общее количество часов на весь семестр (обычно 60-90 часов)
              </p>
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
                <span v-else>{{ editingEnrollment ? 'Сохранить' : 'Создать' }}</span>
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
import { LinkIcon } from '@heroicons/vue/24/outline'
import { catalogAPI } from '@/services/api'

export default {
  name: 'Enrollments',
  components: {
    LinkIcon
  },
  setup() {
    // State
    const enrollments = ref([])
    const groups = ref([])
    const courses = ref([])
    const teachers = ref([])
    const courseAssignments = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const showModal = ref(false)
    const editingEnrollment = ref(null)
    const searchQuery = ref('')
    const currentPage = ref(1)
    const itemsPerPage = 10

    // Filters
    const filters = ref({
      group: '',
      course: ''
    })

    // Form
    const form = ref({
      group_id: '',
      course_id: '',
      teacher_id: '',
      planned_hours_per_semester: 60
    })

    // Computed properties for filtering and pagination
    const filteredEnrollments = computed(() => {
      let filtered = enrollments.value

      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        filtered = filtered.filter(e => 
          getGroupName(e.group_id).toLowerCase().includes(query) ||
          getCourseName(e.course_id).toLowerCase().includes(query) ||
          getTeacherName(e.teacher_id).toLowerCase().includes(query)
        )
      }

      if (filters.value.group) {
        filtered = filtered.filter(e => e.group_id === parseInt(filters.value.group))
      }

      if (filters.value.course) {
        filtered = filtered.filter(e => e.course_id === parseInt(filters.value.course))
      }

      return filtered
    })

    const totalPages = computed(() => Math.ceil(filteredEnrollments.value.length / itemsPerPage))
    
    const paginatedEnrollments = computed(() => {
      const start = (currentPage.value - 1) * itemsPerPage
      const end = start + itemsPerPage
      return filteredEnrollments.value.slice(start, end)
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
    const getGroupName = (groupId) => {
      const group = groups.value.find(g => g.group_id === groupId)
      return group ? group.name : `Группа ${groupId}`
    }

    const getCourseName = (assignmentId) => {
      // Find course assignment and get course name
      const assignment = courseAssignments.value.find(a => a.assignment_id === assignmentId)
      if (assignment) {
        const course = courses.value.find(c => c.course_id === assignment.course_id)
        return course ? course.name : `Предмет ${assignment.course_id}`
      }
      return `Предмет ${assignmentId}`
    }

    const getCourseCode = (assignmentId) => {
      // Find course assignment and get course code
      const assignment = courseAssignments.value.find(a => a.assignment_id === assignmentId)
      if (assignment) {
        const course = courses.value.find(c => c.course_id === assignment.course_id)
        return course ? course.code : ''
      }
      return ''
    }

    const getTeacherName = (assignmentId) => {
      // Find course assignment and get teacher name
      const assignment = courseAssignments.value.find(a => a.assignment_id === assignmentId)
      if (assignment) {
        const teacher = teachers.value.find(t => t.teacher_id === assignment.teacher_id)
        return teacher ? `${teacher.first_name} ${teacher.last_name}` : `Преподаватель ${assignment.teacher_id}`
      }
      return `Преподаватель ${assignmentId}`
    }

    // Methods
    const loadData = async () => {
      loading.value = true
      try {
        const [enrollmentsRes, groupsRes, coursesRes, teachersRes, assignmentsRes] = await Promise.all([
          catalogAPI.getEnrollments(),
          catalogAPI.getGroups(),
          catalogAPI.getCourses(),
          catalogAPI.getTeachers(),
          catalogAPI.getCourseAssignments()
        ])
        
        enrollments.value = enrollmentsRes.data || []
        groups.value = groupsRes.data || []
        courses.value = coursesRes.data || []
        teachers.value = teachersRes.data || []
        courseAssignments.value = assignmentsRes.data || []
      } catch (error) {
        console.error('Error loading data:', error)
        alert('Ошибка при загрузке данных')
      } finally {
        loading.value = false
      }
    }

    const openCreateModal = () => {
      editingEnrollment.value = null
      form.value = {
        group_id: '',
        course_id: '',
        teacher_id: '',
        planned_hours_per_semester: 60
      }
      showModal.value = true
    }

    const openEditModal = (enrollment) => {
      editingEnrollment.value = enrollment
      form.value = {
        group_id: enrollment.group_id,
        course_id: enrollment.course_id,
        teacher_id: enrollment.teacher_id,
        planned_hours_per_semester: enrollment.planned_hours_per_semester
      }
      showModal.value = true
    }

    const closeModal = () => {
      showModal.value = false
      editingEnrollment.value = null
    }

    const saveEnrollment = async () => {
      saving.value = true
      try {
        const enrollmentData = {
          org_id: 1, // Demo organization ID
          group_id: parseInt(form.value.group_id),
          course_id: parseInt(form.value.course_id),
          teacher_id: parseInt(form.value.teacher_id),
          planned_hours_per_semester: form.value.planned_hours_per_semester
        }

        if (editingEnrollment.value) {
          // Update existing enrollment
          const updateData = {
            group_id: parseInt(form.value.group_id),
            course_id: parseInt(form.value.course_id),
            teacher_id: parseInt(form.value.teacher_id),
            planned_hours_per_semester: form.value.planned_hours_per_semester
          }
          await catalogAPI.updateEnrollment(editingEnrollment.value.enrollment_id, updateData)
          const index = enrollments.value.findIndex(e => e.enrollment_id === editingEnrollment.value.enrollment_id)
          if (index !== -1) {
            enrollments.value[index] = { ...editingEnrollment.value, ...updateData }
          }
        } else {
          // Create new enrollment
          const response = await catalogAPI.createEnrollment(enrollmentData)
          enrollments.value.unshift(response.data)
        }

        closeModal()
      } catch (error) {
        console.error('Error saving enrollment:', error)
        alert('Ошибка при сохранении связи')
      } finally {
        saving.value = false
      }
    }

    const deleteEnrollment = async (enrollment) => {
      if (!confirm(`Вы уверены, что хотите удалить связь "${getGroupName(enrollment.group_id)}" - "${getCourseName(enrollment.course_id)}"?`)) {
        return
      }

      try {
        await catalogAPI.deleteEnrollment(enrollment.enrollment_id)
        const index = enrollments.value.findIndex(e => e.enrollment_id === enrollment.enrollment_id)
        if (index !== -1) {
          enrollments.value.splice(index, 1)
        }
      } catch (error) {
        console.error('Error deleting enrollment:', error)
        alert('Ошибка при удалении связи')
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
      enrollments, groups, courses, teachers, courseAssignments, loading, saving, showModal, editingEnrollment, searchQuery, currentPage, itemsPerPage, filters, form,
      // Computed
      filteredEnrollments, totalPages, paginatedEnrollments, visiblePages,
      // Methods
      loadData, openCreateModal, openEditModal, closeModal, saveEnrollment, deleteEnrollment,
      getGroupName, getCourseName, getCourseCode, getTeacherName
    }
  }
}
</script>