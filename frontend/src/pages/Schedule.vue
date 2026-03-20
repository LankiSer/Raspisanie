<template>
  <div class="page-container">
    <!-- Header -->
    <div class="page-header mb-4">
      <div>
        <h1>Расписание</h1>
        <p class="text-gray-500 text-sm mt-0.5">Управление расписанием занятий</p>
      </div>
        <div v-if="authStore.canManageSchedule" class="flex flex-wrap gap-3">
          <button
            @click="showCreateLessonModal = true"
            class="btn-primary flex items-center gap-2"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
            </svg>
            Добавить занятие
          </button>
          <router-link
            v-if="authStore.isMethodist"
            to="/generation"
            class="btn-secondary flex items-center gap-2"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
            </svg>
            Генерация расписания
          </router-link>
          <button
            @click="refreshData"
            class="btn-outline flex items-center gap-2"
            :disabled="loading"
          >
            <svg class="w-5 h-5" :class="{ 'animate-spin': loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            Обновить
          </button>
        </div>
    </div>

    <!-- Filters -->
    <div class="bg-white p-4 rounded-lg shadow mb-6">
      <div class="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Период
          </label>
          <select v-model="filters.viewType" @change="loadScheduleData" class="form-select">
            <option value="week">Неделя</option>
            <option value="groups">По группам</option>
            <option value="all-groups">Все группы</option>
            <option value="month">Месяц</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Дата
          </label>
          <input
            v-model="filters.date"
            type="date"
            @change="loadScheduleData"
            class="form-input"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Группа
          </label>
          <select v-model="filters.groupId" @change="loadScheduleData" class="form-select">
            <option value="">Все группы</option>
            <option v-for="group in groups" :key="group.group_id" :value="group.group_id">
              {{ group.name }}
            </option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Преподаватель
          </label>
          <select v-model="filters.teacherId" @change="loadScheduleData" class="form-select">
            <option value="">Все преподаватели</option>
            <option v-for="teacher in teachers" :key="teacher.teacher_id" :value="teacher.teacher_id">
              {{ teacher.first_name }} {{ teacher.last_name }}
            </option>
          </select>
        </div>
        <div class="flex items-end">
          <button
            @click="resetFilters"
            class="btn-secondary w-full"
          >
            Сбросить фильтры
          </button>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
      <p class="mt-2 text-gray-600">Загружаем расписание...</p>
    </div>

    <!-- Schedule Grid -->
    <div v-else class="bg-white rounded-lg shadow overflow-hidden">
      <!-- Week view -->
      <div v-if="filters.viewType === 'week'">
        <div class="space-y-6 p-4">
          <div
            v-for="day in weekDaysWork"
            :key="day.date"
            class="border rounded-lg overflow-hidden bg-white shadow-sm"
          >
            <div class="bg-gray-50 border-b px-4 py-3">
              <div class="font-semibold text-gray-900">{{ day.name }}</div>
              <div class="text-xs text-gray-500">{{ formatDate(day.date) }}</div>
            </div>

            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200 table-fixed">
                <thead class="bg-gray-50 sticky top-0 z-10">
                  <tr>
                    <th
                      class="w-32 px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b"
                    >
                      Время
                    </th>
                    <th
                      v-for="group in filteredGroups"
                      :key="group.group_id"
                      class="px-2 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-b"
                      style="min-width: 210px;"
                    >
                      <div class="truncate">{{ group.name }}</div>
                      <div class="text-xs text-gray-400">{{ group.size }} ст.</div>
                    </th>
                  </tr>
                </thead>

                <tbody class="divide-y divide-gray-200">
                  <tr v-for="slot in timeSlots" :key="slot.slot_id">
                    <td class="px-4 py-2 border-b text-sm font-medium text-gray-700 bg-gray-50 align-top">
                      <div>{{ formatSlotTime(slot.start_time) }} – {{ formatSlotTime(slot.end_time) }}</div>
                      <div v-if="slot.label" class="text-xs text-gray-500">{{ slot.label }}</div>
                    </td>
                    <td
                      v-for="group in filteredGroups"
                      :key="`${group.group_id}-${slot.slot_id}`"
                      class="border-b p-0"
                    >
                      <div class="relative h-20">
                        <ScheduleCell
                          :date="day.date"
                          :slot="slot"
                          :lessons="getLessonsForCellWithGroup(day.date, slot.slot_id, group.name)"
                          :can-edit="authStore.canManageSchedule"
                          @lesson-click="handleLessonClick"
                          @cell-click="(date, slotId) => handleCellClick(date, slotId, group.group_id)"
                          @lesson-drop="(lesson, targetDate, targetSlotId) => handleLessonDrop(lesson, targetDate, targetSlotId, group.name)"
                        />
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Day view -->
      <div v-else-if="filters.viewType === 'day'" class="divide-y">
        <div
          v-for="slot in timeSlots"
          :key="slot.slot_id"
          class="flex hover:bg-gray-50"
        >
          <!-- Time column -->
          <div class="w-32 p-4 bg-gray-50 text-sm font-medium text-gray-700 border-r">
            <div>{{ formatSlotTime(slot.start_time) }} – {{ formatSlotTime(slot.end_time) }}</div>
            <div v-if="slot.label" class="text-xs text-gray-500">{{ slot.label }}</div>
          </div>

          <!-- Lesson content -->
          <div class="flex-1 relative h-20">
            <ScheduleCell
              :date="filters.date"
              :slot="slot"
              :lessons="getLessonsForCell(filters.date, slot.slot_id)"
              :can-edit="authStore.canManageSchedule"
              @lesson-click="handleLessonClick"
              @cell-click="handleCellClick"
              @lesson-drop="handleLessonDrop"
            />
          </div>
        </div>
      </div>

      <!-- Month view -->
      <div v-else-if="filters.viewType === 'month'" class="space-y-6 p-4">
        <div
          v-for="day in monthDays"
          :key="day.date"
          class="border rounded-lg overflow-hidden bg-white shadow-sm"
        >
          <div class="bg-gray-50 border-b px-4 py-3">
            <div class="font-semibold text-gray-900">{{ day.name }}</div>
            <div class="text-xs text-gray-500">{{ formatDate(day.date) }}</div>
          </div>

          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200 table-fixed">
              <thead class="bg-gray-50 sticky top-0 z-10">
                <tr>
                  <th
                    class="w-32 px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b"
                  >
                    Время
                  </th>
                  <th
                    v-for="group in filteredGroups"
                    :key="group.group_id"
                    class="px-2 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-b"
                    style="min-width: 210px;"
                  >
                    <div class="truncate">{{ group.name }}</div>
                    <div class="text-xs text-gray-400">{{ group.size }} ст.</div>
                  </th>
                </tr>
              </thead>

              <tbody class="divide-y divide-gray-200">
                <tr v-for="slot in timeSlots" :key="slot.slot_id">
                  <td class="px-4 py-2 border-b text-sm font-medium text-gray-700 bg-gray-50 align-top">
                    <div>{{ formatSlotTime(slot.start_time) }} – {{ formatSlotTime(slot.end_time) }}</div>
                    <div v-if="slot.label" class="text-xs text-gray-500">{{ slot.label }}</div>
                  </td>
                  <td
                    v-for="group in filteredGroups"
                    :key="`${group.group_id}-${slot.slot_id}`"
                    class="border-b p-0"
                  >
                    <div class="relative h-20">
                      <ScheduleCell
                        :date="day.date"
                        :slot="slot"
                        :lessons="getLessonsForCellWithGroup(day.date, slot.slot_id, group.name)"
                        :can-edit="authStore.canManageSchedule"
                        @lesson-click="handleLessonClick"
                        @cell-click="(date, slotId) => handleCellClick(date, slotId, group.group_id)"
                        @lesson-drop="(lesson, targetDate, targetSlotId) => handleLessonDrop(lesson, targetDate, targetSlotId, group.name)"
                      />
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Groups view -->
      <div v-else-if="filters.viewType === 'groups'" class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Группа
              </th>
              <th
                v-for="day in weekDays"
                :key="day.date"
                class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                <div>{{ day.name }}</div>
                <div class="text-xs text-gray-400">{{ formatDate(day.date) }}</div>
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="group in filteredGroups" :key="group.group_id" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{{ group.name }}</div>
                <div class="text-sm text-gray-500">{{ group.size }} студентов</div>
              </td>
              <td
                v-for="day in weekDays"
                :key="`${group.group_id}-${day.date}`"
                class="px-6 py-4 text-center"
              >
                <div v-if="getGroupLessonsForDay(group.group_id, day.date).length > 0" class="space-y-1">
                  <div
                    v-for="lesson in getGroupLessonsForDay(group.group_id, day.date)"
                    :key="lesson.lesson_id"
                    class="bg-gov-50 border border-gov-200 text-gov-900 text-xs px-2 py-1 rounded cursor-pointer hover:bg-gov-100"
                    @click="handleLessonClick(lesson, $event)"
                  >
                    <div class="font-medium">{{ lesson.course_name }}</div>
                    <div class="text-xs">{{ lesson.teacher_name }}</div>
                    <div class="text-xs">{{ lesson.room_number }}</div>
                    <div class="text-xs">{{ lesson.start_time }}</div>
                  </div>
                </div>
                <div v-else class="text-gray-400 text-xs">—</div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- All Groups view -->
      <div v-else-if="filters.viewType === 'all-groups'">
        <!-- Header -->
        <div class="grid grid-cols-8 bg-gray-50 border-b">
          <div class="p-4 font-medium text-gray-900 border-r">Время</div>
          <div
            v-for="day in weekDays"
            :key="day.date"
            class="p-4 font-medium text-gray-900 border-r text-center"
          >
            <div>{{ day.name }}</div>
            <div class="text-sm text-gray-500">{{ formatDate(day.date) }}</div>
          </div>
        </div>

        <!-- Time slots -->
        <div
          v-for="slot in timeSlots"
          :key="slot.slot_id"
          class="grid grid-cols-8 border-b hover:bg-gray-50"
        >
          <!-- Time column -->
          <div class="p-4 border-r bg-gray-50 text-sm font-medium text-gray-700">
            <div>{{ formatSlotTime(slot.start_time) }} – {{ formatSlotTime(slot.end_time) }}</div>
            <div v-if="slot.label" class="text-xs text-gray-500">{{ slot.label }}</div>
          </div>

          <!-- Day cells -->
          <div
            v-for="day in weekDays"
            :key="`${slot.slot_id}-${day.date}`"
            class="relative border-r h-20"
          >
            <ScheduleCell
              :date="day.date"
              :slot="slot"
              :lessons="getLessonsForCell(day.date, slot.slot_id)"
              :can-edit="authStore.canManageSchedule"
              @lesson-click="handleLessonClick"
              @cell-click="handleCellClick"
              @lesson-drop="handleLessonDrop"
            />
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="!loading && lessons.length === 0" class="text-center py-12">
        <CalendarIcon class="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900 mb-2">Расписание пусто</h3>
        <p class="text-gray-600 mb-4">На выбранный период занятия не запланированы</p>
        <button
          v-if="authStore.canManageSchedule"
          @click="showCreateLessonModal = true"
          class="btn-primary"
        >
          Добавить занятие
        </button>
      </div>
    </div>

    <!-- Create/Edit Lesson Modal -->
    <LessonModal
      :show="showCreateLessonModal || !!editingLesson"
      :lesson="editingLesson"
      :initial-date="modalInitialDate"
      :initial-slot-id="modalInitialSlotId"
      :initial-group-id="modalInitialGroupId"
      @close="closeLessonModal"
      @saved="handleLessonSaved"
    />

    <!-- Context Menu -->
    <ContextMenu
      :show="showContextMenu"
      :x="contextMenuX"
      :y="contextMenuY"
      :lesson="contextMenuLesson"
      @close="showContextMenu = false"
      @edit="handleEditLesson"
      @move="handleMoveLesson"
      @cancel="handleCancelLesson"
      @delete="handleDeleteLesson"
      @status-changed="loadSchedule"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import { CalendarIcon } from '@heroicons/vue/24/outline'
import { useAuthStore } from '@/stores/auth'
import { lessonsAPI, catalogAPI } from '@/services/api'
import { format, addDays, startOfWeek, parseISO, startOfMonth, endOfMonth } from 'date-fns'
import { ru } from 'date-fns/locale'
import ScheduleCell from '@/components/ScheduleCell.vue'
import LessonModal from '@/components/LessonModal.vue'
import ContextMenu from '@/components/ContextMenu.vue'

export default {
  name: 'Schedule',
  components: {
    CalendarIcon,
    ScheduleCell,
    LessonModal,
    ContextMenu
  },
  setup() {
    const authStore = useAuthStore()
    
    const loading = ref(false)
    const lessons = ref([])
    const timeSlots = ref([])
    const groups = ref([])
    const teachers = ref([])
    
    // Filters
    const filters = ref({
      viewType: 'week',
      date: format(new Date(), 'yyyy-MM-dd'),
      groupId: '',
      teacherId: ''
    })
    
    // Modals
    const showCreateLessonModal = ref(false)
    const editingLesson = ref(null)
    const modalInitialDate = ref('')
    const modalInitialSlotId = ref(null)
    const modalInitialGroupId = ref(null)
    
    // Context menu
    const showContextMenu = ref(false)
    const contextMenuX = ref(0)
    const contextMenuY = ref(0)
    const contextMenuLesson = ref(null)

    // Computed
    const weekDays = computed(() => {
      const startDate = startOfWeek(parseISO(filters.value.date), { weekStartsOn: 1 }) // Monday
      return Array.from({ length: 7 }, (_, i) => {
        const date = addDays(startDate, i)
        return {
          date: format(date, 'yyyy-MM-dd'),
          name: format(date, 'EEEE', { locale: ru })
        }
      })
    })

    const weekDaysWork = computed(() => {
      // Show only Mon-Fri like in the reference screenshot.
      return weekDays.value.filter((d) => {
        const wd = parseISO(d.date).getDay() // 0=Sun..6=Sat
        return wd >= 1 && wd <= 5
      })
    })

    const monthDays = computed(() => {
      const baseDate = parseISO(filters.value.date)
      const startDate = startOfMonth(baseDate)
      const endDate = endOfMonth(baseDate)

      const days = []
      let cur = startDate
      while (cur <= endDate) {
        // 0 = Sunday, 6 = Saturday
        if (cur.getDay() !== 0 && cur.getDay() !== 6) {
          days.push({
            date: format(cur, 'yyyy-MM-dd'),
            name: format(cur, 'EEEE', { locale: ru })
          })
        }
        cur = addDays(cur, 1)
      }
      return days
    })

    const filteredGroups = computed(() => {
      if (filters.value.groupId) {
        return groups.value.filter(group => group.group_id === parseInt(filters.value.groupId))
      }
      return groups.value
    })

    // Methods
    const formatDate = (dateStr) => {
      return format(parseISO(dateStr), 'dd.MM')
    }

    /** Нормализация времени слота (без сдвига TZ, только HH:MM) */
    const formatSlotTime = (t) => {
      if (t == null || t === '') return ''
      const s = String(t)
      if (/^\d{1,2}:\d{2}/.test(s)) return s.slice(0, 5)
      return s
    }

    const getLessonsForCell = (date, slotId) => {
      const key = `${date}|${slotId}`
      return lessonsByDateSlot.value.get(key) || []
    }

    const getLessonsForCellWithGroup = (date, slotId, groupName) => {
      const key = `${date}|${slotId}|${String(groupName ?? '').trim()}`
      return lessonsByDateSlotGroup.value.get(key) || []
    }

    const getGroupLessonsForSlot = (groupId, slotId, date) => {
      return lessons.value.filter(lesson => 
        lesson.group_id === groupId && 
        lesson.slot_id === slotId && 
        lesson.date === date
      )
    }

    const getGroupLessonsForDay = (groupId, date) => {
      // Find group name by group_id
      const group = groups.value.find(g => g.group_id === groupId)
      if (!group) return []
      
      return lessons.value.filter(lesson =>
        lesson.group_name?.trim() === group.name?.trim() &&
        lesson.date === date
      )
    }

    const loadScheduleData = async () => {
      loading.value = true
      
      try {
        const baseDate = parseISO(filters.value.date)

        // Load data by view type
        let startDate
        let endDate
        if (filters.value.viewType === 'day') {
          startDate = baseDate
          endDate = baseDate
        } else if (filters.value.viewType === 'month') {
          startDate = startOfMonth(baseDate)
          endDate = endOfMonth(baseDate)
        } else {
          // week/groups/all-groups => keep existing "calendar week" behavior
          startDate = startOfWeek(baseDate, { weekStartsOn: 1 })
          endDate = addDays(startDate, 6)
        }
        
        const params = {
          start_date: format(startDate, 'yyyy-MM-dd'),
          end_date: format(endDate, 'yyyy-MM-dd')
        }
        
        // Add filters if selected
        if (filters.value.groupId) {
          params.group_id = parseInt(filters.value.groupId)
        }
        if (filters.value.teacherId) {
          params.teacher_id = parseInt(filters.value.teacherId)
        }
        
        const lessonsResponse = await lessonsAPI.getByTerm(params)
        
        lessons.value = lessonsResponse.data || []
      } catch (error) {
        console.error('Error loading lessons:', error)
        lessons.value = []
      } finally {
        loading.value = false
      }
    }

    // Index lessons by `date|slot_id` to avoid O(N) filtering on every cell render.
    const lessonsByDateSlot = computed(() => {
      const map = new Map()
      for (const lesson of lessons.value) {
        const key = `${lesson.date}|${lesson.slot_id}`
        const cur = map.get(key)
        if (cur) {
          cur.push(lesson)
        } else {
          map.set(key, [lesson])
        }
      }
      return map
    })

    const lessonsByDateSlotGroup = computed(() => {
      const map = new Map()
      for (const lesson of lessons.value) {
        const key = `${lesson.date}|${lesson.slot_id}|${String(lesson.group_name ?? '').trim()}`
        const cur = map.get(key)
        if (cur) {
          cur.push(lesson)
        } else {
          map.set(key, [lesson])
        }
      }
      return map
    })

    const refreshData = async () => {
      await loadScheduleData()
    }

    const loadCatalogData = async () => {
      try {
        // Load time slots
        const slotsResponse = await catalogAPI.getTimeSlots()
        const raw = slotsResponse.data || []
        const hourOf = (s) => {
          const st = String(s.start_time || '0')
          const m = st.match(/^(\d{1,2})/)
          return m ? parseInt(m[1], 10) : 99
        }
        timeSlots.value = [...raw]
          .filter((s) => {
            const h = hourOf(s)
            return h >= 6 && h <= 22
          })
          .sort((a, b) => String(a.start_time).localeCompare(String(b.start_time)))
        
        // Load groups
        const groupsResponse = await catalogAPI.getGroups()
        groups.value = groupsResponse.data || []
        
        // Load teachers
        const teachersResponse = await catalogAPI.getTeachers()
        teachers.value = teachersResponse.data || []
        
      } catch (error) {
        console.error('Error loading catalog data:', error)
      }
    }

    const resetFilters = () => {
      filters.value = {
        viewType: 'week',
        date: format(new Date(), 'yyyy-MM-dd'),
        groupId: '',
        teacherId: ''
      }
      loadScheduleData()
    }

    const handleLessonClick = (lesson, event) => {
      if (event.button === 2) { // Right click
        event.preventDefault()
        contextMenuLesson.value = lesson
        contextMenuX.value = event.pageX
        contextMenuY.value = event.pageY
        showContextMenu.value = true
      } else {
        editingLesson.value = lesson
      }
    }

    const handleCellClick = (date, slotId, targetGroupId = null) => {
      if (authStore.canManageSchedule) {
        modalInitialDate.value = date
        modalInitialSlotId.value = slotId
        modalInitialGroupId.value = targetGroupId
        showCreateLessonModal.value = true
      }
    }

    const handleLessonDrop = async (lesson, targetDate, targetSlotId, targetGroupName = null) => {
      if (!authStore.canManageSchedule) return
      const sid = Number(targetSlotId)
      if (!Number.isFinite(sid) || sid < 1) {
        console.warn('Invalid target slot for drag-drop')
        return
      }

      // Prevent moving lesson into a different group column visually.
      if (targetGroupName != null) {
        const fromGroup = String(lesson.group_name ?? '').trim()
        const toGroup = String(targetGroupName ?? '').trim()
        if (fromGroup && toGroup && fromGroup !== toGroup) {
          console.warn('Drop blocked: lesson belongs to another group')
          return
        }
      }

      try {
        await lessonsAPI.update(lesson.lesson_id, {
          date: targetDate,
          slot_id: sid,
          version: lesson.version
        })
        
        await loadScheduleData()
      } catch (error) {
        console.error('Error moving lesson:', error)
        // Show error message
      }
    }

    const closeLessonModal = () => {
      showCreateLessonModal.value = false
      editingLesson.value = null
      modalInitialDate.value = ''
      modalInitialSlotId.value = null
      modalInitialGroupId.value = null
    }

    const handleLessonSaved = () => {
      closeLessonModal()
      loadScheduleData()
    }

    const handleEditLesson = (lesson) => {
      editingLesson.value = lesson
      showContextMenu.value = false
    }

    const handleMoveLesson = (lesson) => {
      // TODO: Implement move lesson functionality
      showContextMenu.value = false
    }

    const handleCancelLesson = async (lesson) => {
      try {
        await lessonsAPI.update(lesson.lesson_id, {
          status: 'cancelled',
          version: lesson.version
        })
        
        await loadScheduleData()
      } catch (error) {
        console.error('Error cancelling lesson:', error)
      }
      
      showContextMenu.value = false
    }

    const handleDeleteLesson = async (lesson) => {
      if (confirm('Вы уверены, что хотите удалить это занятие?')) {
        try {
          await lessonsAPI.delete(lesson.lesson_id)
          await loadScheduleData()
        } catch (error) {
          console.error('Error deleting lesson:', error)
        }
      }
      
      showContextMenu.value = false
    }

    // Close context menu when clicking outside
    const handleDocumentClick = (event) => {
      if (!event.target.closest('.context-menu')) {
        showContextMenu.value = false
      }
    }

    onMounted(async () => {
      document.addEventListener('click', handleDocumentClick)
      await loadCatalogData()
      await loadScheduleData()
    })

    // Watch filters
    watch(() => filters.value.date, loadScheduleData)
    watch(() => filters.value.viewType, loadScheduleData)
    watch(() => filters.value.groupId, loadScheduleData)
    watch(() => filters.value.teacherId, loadScheduleData)

    return {
      authStore,
      loading,
      lessons,
      timeSlots,
      groups,
      teachers,
      filters,
      weekDays,
      weekDaysWork,
      monthDays,
      filteredGroups,
      showCreateLessonModal,
      editingLesson,
      modalInitialDate,
      modalInitialSlotId,
      modalInitialGroupId,
      showContextMenu,
      contextMenuX,
      contextMenuY,
      contextMenuLesson,
      formatDate,
      formatSlotTime,
      getLessonsForCell,
      getLessonsForCellWithGroup,
      getGroupLessonsForSlot,
      getGroupLessonsForDay,
      loadScheduleData,
      refreshData,
      resetFilters,
      handleLessonClick,
      handleCellClick,
      handleLessonDrop,
      closeLessonModal,
      handleLessonSaved,
      handleEditLesson,
      handleMoveLesson,
      handleCancelLesson,
      handleDeleteLesson
    }
  }
}
</script>
