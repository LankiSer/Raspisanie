<template>
  <div
    v-if="show"
    class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50"
    @click="handleBackdropClick"
  >
    <div class="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
      <div class="mt-3">
        <!-- Header -->
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-medium text-gray-900">
            {{ isEditing ? 'Редактировать занятие' : 'Создать занятие' }}
          </h3>
          <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">
            <XMarkIcon class="h-6 w-6" />
          </button>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-6">
          <!-- Error message -->
          <div v-if="error" class="rounded-md bg-red-50 p-4">
            <div class="text-sm text-red-700">{{ error }}</div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Date -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Дата *
              </label>
              <input
                v-model="form.date"
                type="date"
                required
                class="form-input"
                :min="minDate"
              />
            </div>

            <!-- Time slot -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Временной слот *
              </label>
              <select v-model="form.slot_id" required class="form-select">
                <option value="">Выберите время</option>
                <option
                  v-for="slot in timeSlots"
                  :key="slot.slot_id"
                  :value="slot.slot_id"
                >
                  {{ slot.start_time }} - {{ slot.end_time }}
                  {{ slot.label ? `(${slot.label})` : '' }}
                </option>
              </select>
            </div>

            <!-- Group -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Группа *
              </label>
              <select
                v-model="form.group_id"
                @change="loadEnrollments"
                required
                class="form-select"
              >
                <option value="">Выберите группу</option>
                <option
                  v-for="group in groups"
                  :key="group.group_id"
                  :value="group.group_id"
                >
                  {{ group.name }} ({{ group.size }} чел.)
                </option>
              </select>
            </div>

            <!-- Subject & Teacher (Enrollment) -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Предмет и преподаватель *
              </label>
              <select v-model="form.enrollment_id" required class="form-select">
                <option value="">Выберите предмет</option>
                <option
                  v-for="enrollment in availableEnrollments"
                  :key="enrollment.enrollment_id"
                  :value="enrollment.enrollment_id"
                >
                  {{ getEnrollmentDisplayName(enrollment) }}
                </option>
              </select>
            </div>

            <!-- Room -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Аудитория
              </label>
              <select v-model="form.room_id" class="form-select">
                <option value="">Без аудитории</option>
                <option
                  v-for="room in availableRooms"
                  :key="room.room_id"
                  :value="room.room_id"
                >
                  {{ room.number }}
                  ({{ room.capacity }} мест)
                  {{ room.kind ? `- ${room.kind}` : '' }}
                </option>
              </select>
            </div>

            <!-- Status (for editing) -->
            <div v-if="isEditing">
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Статус
              </label>
              <select v-model="form.status" class="form-select">
                <option value="planned">Запланировано</option>
                <option value="confirmed">Подтверждено</option>
                <option value="completed">Завершено</option>
                <option value="cancelled">Отменено</option>
                <option value="moved">Перенесено</option>
                <option value="skipped">Пропущено</option>
              </select>
            </div>
          </div>

          <!-- Reason (for cancellation, etc.) -->
          <div v-if="isEditing && ['cancelled', 'moved', 'skipped'].includes(form.status)">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Причина
            </label>
            <textarea
              v-model="form.reason"
              rows="3"
              class="form-input"
              placeholder="Укажите причину..."
            ></textarea>
          </div>

          <!-- Conflicts warning -->
          <div v-if="conflicts.length > 0" class="rounded-md bg-yellow-50 p-4">
            <div class="flex">
              <ExclamationTriangleIcon class="h-5 w-5 text-yellow-400 mt-0.5 mr-3" />
              <div class="text-sm text-yellow-700">
                <p class="font-medium">Обнаружены конфликты:</p>
                <ul class="mt-2 list-disc list-inside">
                  <li v-for="conflict in conflicts" :key="conflict">{{ conflict }}</li>
                </ul>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex justify-end space-x-3 pt-6 border-t">
            <button
              type="button"
              @click="$emit('close')"
              class="btn-secondary"
            >
              Отмена
            </button>
            <button
              type="button"
              v-if="!isEditing"
              @click="checkConflicts"
              class="btn-secondary"
              :disabled="!canCheckConflicts"
            >
              Проверить конфликты
            </button>
            <button
              type="submit"
              class="btn-primary"
              :disabled="loading"
            >
              <span v-if="loading">
                {{ isEditing ? 'Сохраняем...' : 'Создаем...' }}
              </span>
              <span v-else>
                {{ isEditing ? 'Сохранить' : 'Создать' }}
              </span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { XMarkIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
import { lessonsAPI, catalogAPI } from '@/services/api'
import { format, addDays } from 'date-fns'

export default {
  name: 'LessonModal',
  components: {
    XMarkIcon,
    ExclamationTriangleIcon
  },
  props: {
    show: {
      type: Boolean,
      default: false
    },
    lesson: {
      type: Object,
      default: null
    },
    initialDate: {
      type: String,
      default: ''
    },
    initialSlotId: {
      type: [Number, String],
      default: null
    }
  },
  emits: ['close', 'saved'],
  setup(props, { emit }) {
    const loading = ref(false)
    const error = ref('')
    const conflicts = ref([])
    
    // Catalog data
    const timeSlots = ref([])
    const groups = ref([])
    const rooms = ref([])
    const enrollments = ref([])
    const courses = ref([])
    const teachers = ref([])
    const courseAssignments = ref([])
    
    // Form
    const form = ref({
      date: '',
      slot_id: '',
      group_id: '',
      enrollment_id: '',
      room_id: '',
      status: 'planned',
      reason: '',
      version: 1
    })

    // Computed
    const isEditing = computed(() => !!props.lesson)
    
    const minDate = computed(() => {
      return format(new Date(), 'yyyy-MM-dd')
    })

    const availableEnrollments = computed(() => {
      return enrollments.value.filter(e => e.group_id === form.value.group_id)
    })

    const availableRooms = computed(() => {
      if (!form.value.group_id) return rooms.value
      
      const selectedGroup = groups.value.find(g => g.group_id === form.value.group_id)
      if (!selectedGroup) return rooms.value
      
      // Filter rooms by capacity
      return rooms.value.filter(room => room.capacity >= selectedGroup.size)
    })

    const canCheckConflicts = computed(() => {
      return form.value.date && form.value.slot_id && form.value.enrollment_id
    })

    const getEnrollmentDisplayName = (enrollment) => {
      // Find course and teacher from course assignments
      const courseAssignment = courseAssignments.value.find(a => a.assignment_id === enrollment.assignment_id)
      if (!courseAssignment) return `Enrollment ${enrollment.enrollment_id}`
      
      const course = courses.value.find(c => c.course_id === courseAssignment.course_id)
      const teacher = teachers.value.find(t => t.teacher_id === courseAssignment.teacher_id)
      
      const courseName = course ? course.name : `Course ${courseAssignment.course_id}`
      const teacherName = teacher ? `${teacher.first_name} ${teacher.last_name}` : `Teacher ${courseAssignment.teacher_id}`
      
      return `${courseName} - ${teacherName}`
    }

    // Methods
    const resetForm = () => {
      form.value = {
        date: props.initialDate || format(new Date(), 'yyyy-MM-dd'),
        slot_id: props.initialSlotId || '',
        group_id: '',
        enrollment_id: '',
        room_id: '',
        status: 'planned',
        reason: '',
        version: 1
      }
      conflicts.value = []
      error.value = ''
    }

    const loadCatalogData = async () => {
      try {
        const [slotsRes, groupsRes, roomsRes, enrollmentsRes, coursesRes, teachersRes, assignmentsRes] = await Promise.all([
          catalogAPI.getTimeSlots(),
          catalogAPI.getGroups(),
          catalogAPI.getRooms(),
          catalogAPI.getEnrollments(),
          catalogAPI.getCourses(),
          catalogAPI.getTeachers(),
          catalogAPI.getCourseAssignments()
        ])
        
        timeSlots.value = slotsRes.data || []
        groups.value = groupsRes.data || []
        rooms.value = roomsRes.data || []
        enrollments.value = enrollmentsRes.data || []
        courses.value = coursesRes.data || []
        teachers.value = teachersRes.data || []
        courseAssignments.value = assignmentsRes.data || []
      } catch (err) {
        console.error('Error loading catalog data:', err)
      }
    }

    const loadEnrollments = async () => {
      if (!form.value.group_id) return
      
      try {
        const response = await catalogAPI.getEnrollments({
          group_id: form.value.group_id
        })
        // Update only enrollments for selected group
        enrollments.value = response.data || []
      } catch (err) {
        console.error('Error loading enrollments:', err)
      }
    }

    const checkConflicts = async () => {
      if (!canCheckConflicts.value) return
      
      try {
        const response = await lessonsAPI.checkConflicts({
          date: form.value.date,
          slot_id: parseInt(form.value.slot_id),
          enrollment_id: parseInt(form.value.enrollment_id),
          room_id: form.value.room_id ? parseInt(form.value.room_id) : null,
          org_id: 1 // TODO: get from auth store
        })
        
        conflicts.value = response.data?.conflicts || []
      } catch (err) {
        console.error('Error checking conflicts:', err)
        conflicts.value = ['Ошибка при проверке конфликтов']
      }
    }

    const handleSubmit = async () => {
      loading.value = true
      error.value = ''
      
      try {
        const data = {
          date: form.value.date,
          slot_id: parseInt(form.value.slot_id),
          enrollment_id: parseInt(form.value.enrollment_id),
          room_id: form.value.room_id ? parseInt(form.value.room_id) : null,
          org_id: 1, // TODO: get from auth store
          term_id: 1 // TODO: get current term
        }
        
        if (isEditing.value) {
          // Update lesson
          data.status = form.value.status
          data.reason = form.value.reason || null
          data.version = form.value.version
          
          await lessonsAPI.update(props.lesson.lesson_id, data)
        } else {
          // Create lesson
          await lessonsAPI.create(data)
        }
        
        emit('saved')
      } catch (err) {
        console.error('Error saving lesson:', err)
        
        if (err.response?.status === 409) {
          if (err.response.data?.conflicts) {
            conflicts.value = err.response.data.conflicts
            error.value = 'Обнаружены конфликты. Проверьте данные и попробуйте снова.'
          } else {
            error.value = 'Занятие было изменено другим пользователем. Перезагрузите страницу.'
          }
        } else {
          error.value = err.response?.data?.detail || err.message || 'Ошибка при сохранении'
        }
      } finally {
        loading.value = false
      }
    }

    const handleBackdropClick = (event) => {
      if (event.target === event.currentTarget) {
        emit('close')
      }
    }

    // Watchers
    watch(() => props.show, async (newShow) => {
      if (newShow) {
        // Load catalog data first
        await loadCatalogData()
        
        if (props.lesson) {
          // Edit mode - populate form
          // Find group_id from enrollment_id
          const enrollment = enrollments.value.find(e => e.enrollment_id === props.lesson.enrollment_id)
          const groupId = enrollment ? enrollment.group_id : ''
          
          form.value = {
            date: props.lesson.date,
            slot_id: props.lesson.slot_id,
            group_id: groupId,
            enrollment_id: props.lesson.enrollment_id,
            room_id: props.lesson.room_id || '',
            status: props.lesson.status || 'planned',
            reason: props.lesson.reason || '',
            version: props.lesson.version || 1
          }
        } else {
          // Create mode - reset form
          resetForm()
        }
        
        conflicts.value = []
        error.value = ''
      }
    })

    watch(() => form.value.group_id, (newGroupId) => {
      if (newGroupId) {
        form.value.enrollment_id = ''
        loadEnrollments()
      }
    })

    onMounted(() => {
      loadCatalogData()
    })

    return {
      loading,
      error,
      conflicts,
      timeSlots,
      groups,
      rooms,
      enrollments,
      courses,
      teachers,
      courseAssignments,
      form,
      isEditing,
      minDate,
      availableEnrollments,
      availableRooms,
      canCheckConflicts,
      getEnrollmentDisplayName,
      loadEnrollments,
      checkConflicts,
      handleSubmit,
      handleBackdropClick
    }
  }
}
</script>
