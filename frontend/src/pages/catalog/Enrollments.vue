<template>
  <div class="page-container">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1>Связи предметов с группами</h1>
        <p class="text-gray-500 text-sm mt-0.5">Управление привязкой предметов к группам и преподавателям</p>
      </div>
      <button @click="openCreateModal" class="btn-primary flex items-center gap-2">
        <PlusIcon class="w-4 h-4" />
        Добавить связь
      </button>
    </div>

    <!-- Filters -->
    <div class="card card-body mb-4">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="relative">
          <MagnifyingGlassIcon class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          <input v-model="searchQuery" type="text" placeholder="Поиск по группе, предмету, преподавателю..."
            class="form-input pl-9" />
        </div>
        <select v-model="filters.group_id" class="form-select">
          <option value="">Все группы</option>
          <option v-for="g in groups" :key="g.group_id" :value="g.group_id">{{ g.name }}</option>
        </select>
        <select v-model="filters.course_id" class="form-select">
          <option value="">Все предметы</option>
          <option v-for="c in courses" :key="c.course_id" :value="c.course_id">{{ c.name }}</option>
        </select>
      </div>
    </div>

    <!-- Table -->
    <div class="card overflow-hidden">
      <div v-if="loading" class="p-8 flex flex-col items-center gap-2 text-gray-400">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gov-600"></div>
        <span class="text-sm">Загрузка…</span>
      </div>

      <div v-else-if="!filteredEnrollments.length" class="p-8 text-center text-gray-400">
        <LinkIcon class="w-12 h-12 mx-auto mb-2 opacity-40" />
        <p class="text-sm">{{ searchQuery || filters.group_id || filters.course_id ? 'Ничего не найдено' : 'Нет привязок' }}</p>
      </div>

      <template v-else>
        <div class="table-wrapper">
          <table class="gov-table">
            <thead>
              <tr>
                <th>Группа</th>
                <th>Предмет</th>
                <th>Преподаватель</th>
                <th>Запланировано ч.</th>
                <th>Назначено ч.</th>
                <th class="text-right">Действия</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="e in paginatedEnrollments" :key="e.enrollment_id">
                <td class="font-medium text-gray-900">{{ getGroupName(e.group_id) }}</td>
                <td>
                  <div class="font-medium text-gray-900">{{ getCourseName(e.assignment_id) }}</div>
                  <div class="text-xs text-gray-400">{{ getCourseType(e.assignment_id) }}</div>
                </td>
                <td>{{ getTeacherName(e.assignment_id) }}</td>
                <td>
                  <span class="badge-blue">{{ e.planned_hours }} ч</span>
                </td>
                <td>
                  <span v-if="scheduledHours[e.enrollment_id] !== undefined"
                    :class="scheduledHours[e.enrollment_id] > e.planned_hours ? 'badge-red' : 'badge-green'">
                    {{ scheduledHours[e.enrollment_id] }} ч
                  </span>
                  <span v-else class="text-gray-300 text-xs">—</span>
                </td>
                <td class="text-right">
                  <div class="flex items-center justify-end gap-2">
                    <button @click="openEditModal(e)" class="text-gov-600 hover:text-gov-800 transition-colors" title="Редактировать">
                      <PencilIcon class="w-4 h-4" />
                    </button>
                    <button @click="deleteEnrollment(e)" class="text-red-500 hover:text-red-700 transition-colors" title="Удалить">
                      <TrashIcon class="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="px-4 py-3 border-t border-gray-200 flex items-center justify-between text-sm">
          <span class="text-gray-500">
            {{ (currentPage - 1) * itemsPerPage + 1 }}–{{ Math.min(currentPage * itemsPerPage, filteredEnrollments.length) }}
            из {{ filteredEnrollments.length }}
          </span>
          <div class="flex gap-1">
            <button v-for="page in visiblePages" :key="page" @click="currentPage = page"
              :class="page === currentPage ? 'bg-gov-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-300'"
              class="px-3 py-1 rounded text-sm transition-colors">
              {{ page }}
            </button>
          </div>
        </div>
      </template>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div class="card-header">
          <h3 class="font-semibold text-gray-800">
            {{ editingEnrollment ? 'Редактировать связь' : 'Добавить связь' }}
          </h3>
          <button @click="closeModal" class="text-gray-400 hover:text-gray-600">
            <XMarkIcon class="w-5 h-5" />
          </button>
        </div>
        <form @submit.prevent="saveEnrollment" class="card-body space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Группа *</label>
            <select v-model="form.group_id" required class="form-select">
              <option value="">Выберите группу</option>
              <option v-for="g in groups" :key="g.group_id" :value="g.group_id">{{ g.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Предмет *</label>
            <select v-model="form.course_id" required class="form-select">
              <option value="">Выберите предмет</option>
              <option v-for="c in courses" :key="c.course_id" :value="c.course_id">{{ c.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Преподаватель *</label>
            <select v-model="form.teacher_id" required class="form-select">
              <option value="">Выберите преподавателя</option>
              <option v-for="t in teachers" :key="t.teacher_id" :value="t.teacher_id">
                {{ t.first_name }} {{ t.last_name }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Часов в семестр *</label>
            <input v-model.number="form.planned_hours_per_semester" type="number" min="16" max="216"
              required class="form-input" placeholder="72" />
            <p class="text-xs text-gray-400 mt-0.5">Стандарт: 36–144 ч на предмет в семестре</p>
          </div>
          <div class="flex justify-end gap-2 pt-2">
            <button type="button" @click="closeModal" class="btn-secondary">Отмена</button>
            <button type="submit" :disabled="saving" class="btn-primary">
              {{ saving ? 'Сохранение…' : (editingEnrollment ? 'Сохранить' : 'Создать') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import { LinkIcon, PlusIcon, PencilIcon, TrashIcon, XMarkIcon, MagnifyingGlassIcon } from '@heroicons/vue/24/outline'
import { catalogAPI, lessonsAPI } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { format, startOfYear, endOfYear } from 'date-fns'

export default {
  name: 'Enrollments',
  components: { LinkIcon, PlusIcon, PencilIcon, TrashIcon, XMarkIcon, MagnifyingGlassIcon },
  setup() {
    const authStore = useAuthStore()

    const enrollments     = ref([])
    const groups          = ref([])
    const courses         = ref([])
    const teachers        = ref([])
    const courseAssignments = ref([])
    const scheduledHours  = ref({})   // enrollment_id → scheduled hours count

    const loading     = ref(false)
    const saving      = ref(false)
    const showModal   = ref(false)
    const editingEnrollment = ref(null)
    const searchQuery = ref('')
    const currentPage = ref(1)
    const itemsPerPage = 15

    const filters = ref({ group_id: '', course_id: '' })

    const form = ref({
      group_id: '',
      course_id: '',
      teacher_id: '',
      planned_hours_per_semester: 72,
    })

    // ── Helpers ─────────────────────────────────────────────────────
    const getGroupName = (groupId) =>
      groups.value.find(g => g.group_id === groupId)?.name ?? `Группа ${groupId}`

    const _assignment = (assignmentId) =>
      courseAssignments.value.find(a => a.assignment_id === assignmentId)

    const getCourseName = (assignmentId) => {
      const asgn = _assignment(assignmentId)
      return asgn ? (courses.value.find(c => c.course_id === asgn.course_id)?.name ?? `Предмет ${asgn.course_id}`) : '—'
    }

    const getCourseType = (assignmentId) => {
      const asgn = _assignment(assignmentId)
      return asgn ? (courses.value.find(c => c.course_id === asgn.course_id)?.type ?? '') : ''
    }

    const getTeacherName = (assignmentId) => {
      const asgn = _assignment(assignmentId)
      if (!asgn) return '—'
      const t = teachers.value.find(t => t.teacher_id === asgn.teacher_id)
      return t ? `${t.first_name} ${t.last_name}` : `Преп. ${asgn.teacher_id}`
    }

    // ── Filtering & Pagination ───────────────────────────────────────
    const filteredEnrollments = computed(() => {
      let list = enrollments.value
      if (searchQuery.value) {
        const q = searchQuery.value.toLowerCase()
        list = list.filter(e =>
          getGroupName(e.group_id).toLowerCase().includes(q) ||
          getCourseName(e.assignment_id).toLowerCase().includes(q) ||
          getTeacherName(e.assignment_id).toLowerCase().includes(q)
        )
      }
      if (filters.value.group_id)
        list = list.filter(e => e.group_id === parseInt(filters.value.group_id))
      if (filters.value.course_id) {
        // filter by course_id via courseAssignments
        const matchingAssignments = new Set(
          courseAssignments.value
            .filter(a => a.course_id === parseInt(filters.value.course_id))
            .map(a => a.assignment_id)
        )
        list = list.filter(e => matchingAssignments.has(e.assignment_id))
      }
      return list
    })

    const totalPages = computed(() => Math.ceil(filteredEnrollments.value.length / itemsPerPage))
    const paginatedEnrollments = computed(() => {
      const s = (currentPage.value - 1) * itemsPerPage
      return filteredEnrollments.value.slice(s, s + itemsPerPage)
    })
    const visiblePages = computed(() => {
      const pages = []
      const s = Math.max(1, currentPage.value - 2)
      const e = Math.min(totalPages.value, currentPage.value + 2)
      for (let i = s; i <= e; i++) pages.push(i)
      return pages
    })

    watch([searchQuery, filters], () => { currentPage.value = 1 })

    // ── Load ─────────────────────────────────────────────────────────
    const loadData = async () => {
      loading.value = true
      try {
        const [eRes, gRes, cRes, tRes, aRes] = await Promise.all([
          catalogAPI.getEnrollments(),
          catalogAPI.getGroups(),
          catalogAPI.getCourses(),
          catalogAPI.getTeachers(),
          catalogAPI.getCourseAssignments(),
        ])
        enrollments.value     = eRes.data || []
        groups.value          = gRes.data || []
        courses.value         = cRes.data || []
        teachers.value        = tRes.data || []
        courseAssignments.value = aRes.data || []

        // Load scheduled hours for current academic year
        loadScheduledHours()
      } catch (e) {
        console.error('Error loading enrollments data:', e)
      } finally {
        loading.value = false
      }
    }

    const loadScheduledHours = async () => {
      // Count scheduled (non-cancelled) lessons per enrollment for the current year
      try {
        const now = new Date()
        const res = await lessonsAPI.getByTerm({
          start_date: format(startOfYear(now), 'yyyy-MM-dd'),
          end_date:   format(endOfYear(now), 'yyyy-MM-dd'),
        })
        const lessons = res.data || []
        const map = {}
        for (const l of lessons) {
          if (!l.enrollment_id) continue
          // Each lesson = 1.5 academic hours
          map[l.enrollment_id] = (map[l.enrollment_id] || 0) + 1.5
        }
        scheduledHours.value = map
      } catch {}
    }

    // ── Modal ────────────────────────────────────────────────────────
    const openCreateModal = () => {
      editingEnrollment.value = null
      form.value = { group_id: '', course_id: '', teacher_id: '', planned_hours_per_semester: 72 }
      showModal.value = true
    }

    const openEditModal = (enrollment) => {
      editingEnrollment.value = enrollment
      // Resolve course_id and teacher_id from assignment_id
      const asgn = _assignment(enrollment.assignment_id)
      form.value = {
        group_id:                  enrollment.group_id,
        course_id:                 asgn?.course_id   ?? '',
        teacher_id:                asgn?.teacher_id  ?? '',
        planned_hours_per_semester: enrollment.planned_hours,
      }
      showModal.value = true
    }

    const closeModal = () => { showModal.value = false; editingEnrollment.value = null }

    const saveEnrollment = async () => {
      saving.value = true
      try {
        const payload = {
          group_id:                  parseInt(form.value.group_id),
          course_id:                 parseInt(form.value.course_id),
          teacher_id:                parseInt(form.value.teacher_id),
          planned_hours_per_semester: form.value.planned_hours_per_semester,
        }
        if (editingEnrollment.value) {
          const res = await catalogAPI.updateEnrollment(editingEnrollment.value.enrollment_id, payload)
          const idx = enrollments.value.findIndex(e => e.enrollment_id === editingEnrollment.value.enrollment_id)
          if (idx !== -1) enrollments.value[idx] = res.data
        } else {
          const res = await catalogAPI.createEnrollment(payload)
          enrollments.value.unshift(res.data)
        }
        closeModal()
      } catch (e) {
        console.error('Error saving enrollment:', e)
        alert('Ошибка при сохранении: ' + (e.response?.data?.detail || e.message))
      } finally {
        saving.value = false
      }
    }

    const deleteEnrollment = async (enrollment) => {
      const name = `«${getGroupName(enrollment.group_id)} — ${getCourseName(enrollment.assignment_id)}»`
      if (!confirm(`Удалить связь ${name}?`)) return
      try {
        await catalogAPI.deleteEnrollment(enrollment.enrollment_id)
        enrollments.value = enrollments.value.filter(e => e.enrollment_id !== enrollment.enrollment_id)
      } catch (e) {
        alert('Ошибка при удалении: ' + (e.response?.data?.detail || e.message))
      }
    }

    onMounted(loadData)

    return {
      enrollments, groups, courses, teachers, courseAssignments, scheduledHours,
      loading, saving, showModal, editingEnrollment, searchQuery, currentPage,
      itemsPerPage, filters, form,
      filteredEnrollments, totalPages, paginatedEnrollments, visiblePages,
      getGroupName, getCourseName, getCourseType, getTeacherName,
      openCreateModal, openEditModal, closeModal, saveEnrollment, deleteEnrollment,
    }
  },
}
</script>
