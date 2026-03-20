<template>
  <div class="page-container">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1>Отчёты</h1>
        <p class="text-gray-500 text-sm mt-0.5">Нагрузка, конфликты и экспорт PDF</p>
      </div>
    </div>

    <!-- Date range filter -->
    <div class="card mb-6">
      <div class="card-body">
        <div class="flex flex-wrap items-end gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Начало периода</label>
            <input v-model="startDate" type="date" class="form-input" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Конец периода</label>
            <input v-model="endDate" type="date" class="form-input" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Группа (для PDF)</label>
            <select v-model="selectedGroupId" class="form-select">
              <option :value="null">Все группы</option>
              <option v-for="g in groups" :key="g.group_id" :value="g.group_id">{{ g.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Преподаватель (для PDF)</label>
            <select v-model="selectedTeacherId" class="form-select">
              <option :value="null">Все преподаватели</option>
              <option v-for="t in teachers" :key="t.teacher_id" :value="t.teacher_id">
                {{ t.first_name }} {{ t.last_name }}
              </option>
            </select>
          </div>
          <button @click="loadAll" :disabled="loading" class="btn-primary">
            <span v-if="loading">Загрузка…</span>
            <span v-else>Загрузить отчёты</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="alert-error mb-4">{{ error }}</div>

    <!-- PDF export card -->
    <div class="card mb-6">
      <div class="card-header">
        <h2>Экспорт расписания в PDF</h2>
      </div>
      <div class="card-body">
        <p class="text-sm text-gray-500 mb-4">
          Скачайте расписание за выбранный период с применёнными фильтрами группы / преподавателя.
        </p>
        <button @click="downloadPdf" :disabled="pdfLoading" class="btn-primary gap-2">
          <ArrowDownTrayIcon class="w-4 h-4" />
          <span v-if="pdfLoading">Формирование PDF…</span>
          <span v-else>Скачать PDF</span>
        </button>
      </div>
    </div>

    <!-- Teacher workload -->
    <div class="card mb-6">
      <div class="card-header">
        <h2>Нагрузка преподавателей</h2>
        <span class="badge-blue">{{ teacherWorkload.length }} чел.</span>
      </div>
      <div class="table-wrapper">
        <table class="gov-table">
          <thead>
            <tr>
              <th>Преподаватель</th>
              <th class="text-right">Занятий</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!teacherWorkload.length">
              <td colspan="2" class="text-center text-gray-400 py-6">
                Нет данных — выберите период и нажмите «Загрузить»
              </td>
            </tr>
            <tr v-for="row in teacherWorkload" :key="row.teacher_name">
              <td>{{ row.teacher_name }}</td>
              <td class="text-right font-medium">{{ row.lesson_count }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Group workload -->
    <div class="card mb-6">
      <div class="card-header">
        <h2>Нагрузка групп</h2>
        <span class="badge-blue">{{ groupWorkload.length }} групп</span>
      </div>
      <div class="table-wrapper">
        <table class="gov-table">
          <thead>
            <tr>
              <th>Группа</th>
              <th class="text-right">Занятий</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!groupWorkload.length">
              <td colspan="2" class="text-center text-gray-400 py-6">
                Нет данных — выберите период и нажмите «Загрузить»
              </td>
            </tr>
            <tr v-for="row in groupWorkload" :key="row.group_name">
              <td>{{ row.group_name }}</td>
              <td class="text-right font-medium">{{ row.lesson_count }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Conflicts -->
    <div class="card mb-6">
      <div class="card-header">
        <h2>Конфликты расписания</h2>
        <span :class="conflicts.length ? 'badge-red' : 'badge-green'">
          {{ conflicts.length ? conflicts.length + ' конфл.' : 'Конфликтов нет' }}
        </span>
      </div>
      <div class="table-wrapper">
        <table class="gov-table">
          <thead>
            <tr>
              <th>Дата</th>
              <th>Слот</th>
              <th>Аудитория</th>
              <th class="text-right">Занятий</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!conflicts.length">
              <td colspan="4" class="text-center text-gray-400 py-6">
                Конфликтов не обнаружено
              </td>
            </tr>
            <tr v-for="c in conflicts" :key="`${c.date}-${c.slot_id}-${c.room_id}`" class="bg-red-50">
              <td>{{ c.date }}</td>
              <td>Слот #{{ c.slot_id }}</td>
              <td>Аудитория #{{ c.room_id }}</td>
              <td class="text-right font-bold text-red-600">{{ c.count }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Hours log -->
    <div class="card">
      <div class="card-header">
        <div>
          <h2>Журнал списания часов</h2>
          <p class="text-xs text-gray-500 mt-0.5">За какие пары и у кого списаны/возвращены академические часы</p>
        </div>
        <div class="flex items-center gap-2">
          <span v-if="hoursLog.entries.length" class="badge-blue">{{ hoursLog.entries.length }} записей</span>
          <button @click="loadHoursLog" :disabled="logLoading" class="btn-secondary text-sm">
            <span v-if="logLoading">Загрузка…</span>
            <span v-else>Обновить</span>
          </button>
        </div>
      </div>

      <!-- filters for hours log -->
      <div class="card-body border-b border-gray-100 pb-4">
        <div class="flex flex-wrap items-end gap-4">
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">Группа</label>
            <select v-model="logGroupId" class="form-select text-sm">
              <option :value="null">Все группы</option>
              <option v-for="g in groups" :key="g.group_id" :value="g.group_id">{{ g.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">Преподаватель</label>
            <select v-model="logTeacherId" class="form-select text-sm">
              <option :value="null">Все преподаватели</option>
              <option v-for="t in teachers" :key="t.teacher_id" :value="t.teacher_id">
                {{ t.first_name }} {{ t.last_name }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">Показать</label>
            <select v-model="logStatusFilter" class="form-select text-sm">
              <option value="all">Все записи</option>
              <option value="charged">Только списания</option>
              <option value="returned">Только возвраты</option>
            </select>
          </div>
          <button @click="loadHoursLog" :disabled="logLoading" class="btn-primary text-sm">
            Применить
          </button>
        </div>
      </div>

      <!-- summary strip -->
      <div v-if="hoursLog.entries.length" class="card-body border-b border-gray-100 py-3">
        <div class="flex flex-wrap gap-6 text-sm">
          <div>
            <span class="text-gray-500">Списано:</span>
            <span class="font-semibold text-green-700 ml-1">{{ hoursLog.total_charged }} ч</span>
          </div>
          <div>
            <span class="text-gray-500">Возвращено:</span>
            <span class="font-semibold text-red-600 ml-1">{{ hoursLog.total_returned }} ч</span>
          </div>
          <div>
            <span class="text-gray-500">Итого (нетто):</span>
            <span class="font-semibold text-gov-700 ml-1">{{ hoursLog.net_hours }} ч</span>
          </div>
        </div>
      </div>

      <div class="table-wrapper">
        <table class="gov-table">
          <thead>
            <tr>
              <th>Дата</th>
              <th>Время</th>
              <th>Группа</th>
              <th>Дисциплина</th>
              <th>Преподаватель</th>
              <th>Ауд.</th>
              <th class="text-right">Часы</th>
              <th>Статус</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!filteredLogEntries.length">
              <td colspan="8" class="text-center text-gray-400 py-8">
                <span v-if="logLoading">Загрузка…</span>
                <span v-else>Нет данных — нажмите «Обновить» или выберите период и загрузите отчёты</span>
              </td>
            </tr>
            <tr
              v-for="e in filteredLogEntries"
              :key="e.lesson_id"
              :class="{
                'bg-red-50 hover:bg-red-100': e.hours < 0,
                'bg-green-50 hover:bg-green-100': e.hours > 0 && e.status === 'completed',
              }"
            >
              <td class="whitespace-nowrap">{{ formatLogDate(e.date) }}</td>
              <td class="whitespace-nowrap text-gray-500">{{ e.start_time }}–{{ e.end_time }}</td>
              <td class="font-medium">{{ e.group_name }}</td>
              <td>{{ e.course_name }}</td>
              <td class="text-gray-600">{{ e.teacher_name }}</td>
              <td class="text-gray-500">{{ e.room_number }}</td>
              <td class="text-right font-semibold" :class="e.hours < 0 ? 'text-red-600' : e.hours === 0 ? 'text-gray-400' : 'text-green-700'">
                {{ e.hours > 0 ? '+' : '' }}{{ e.hours }}
              </td>
              <td>
                <span :class="statusBadge(e.status)">{{ e.note }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { ArrowDownTrayIcon } from '@heroicons/vue/24/outline'
import { reportsAPI, catalogAPI } from '@/services/api'
import api from '@/services/api'

export default {
  name: 'Reports',
  components: { ArrowDownTrayIcon },
  setup() {
    const today = new Date()
    const weekAgo = new Date(today)
    weekAgo.setDate(weekAgo.getDate() - 7)

    const startDate = ref(weekAgo.toISOString().split('T')[0])
    const endDate   = ref(today.toISOString().split('T')[0])
    const selectedGroupId   = ref(null)
    const selectedTeacherId = ref(null)

    const loading    = ref(false)
    const pdfLoading = ref(false)
    const error      = ref('')

    const groups          = ref([])
    const teachers        = ref([])
    const teacherWorkload = ref([])
    const groupWorkload   = ref([])
    const conflicts       = ref([])

    // Hours log
    const logLoading      = ref(false)
    const logGroupId      = ref(null)
    const logTeacherId    = ref(null)
    const logStatusFilter = ref('all')
    const hoursLog        = ref({ entries: [], total_charged: 0, total_returned: 0, net_hours: 0 })

    const filteredLogEntries = computed(() => {
      const entries = hoursLog.value.entries ?? []
      if (logStatusFilter.value === 'charged')  return entries.filter(e => e.hours > 0)
      if (logStatusFilter.value === 'returned') return entries.filter(e => e.hours < 0)
      return entries
    })

    const statusBadge = (status) => {
      const map = {
        planned:   'badge-blue',
        confirmed: 'badge-green',
        completed: 'badge-green',
        cancelled: 'badge-red',
        skipped:   'badge-red',
        moved:     'badge-yellow',
      }
      return map[status] ?? 'badge-blue'
    }

    const formatLogDate = (dateStr) => {
      const [y, m, d] = String(dateStr).split('-').map(Number)
      return new Date(y, m - 1, d).toLocaleDateString('ru-RU', {
        day: '2-digit', month: '2-digit', year: 'numeric',
      })
    }

    const loadCatalog = async () => {
      try {
        const [gRes, tRes] = await Promise.all([
          catalogAPI.getGroups(),
          catalogAPI.getTeachers(),
        ])
        groups.value   = gRes.data
        teachers.value = tRes.data
      } catch (e) {
        console.error('Failed to load catalog', e)
      }
    }

    const loadAll = async () => {
      loading.value = true
      error.value   = ''
      try {
        const params = { start_date: startDate.value, end_date: endDate.value }
        const [twRes, gwRes, cfRes] = await Promise.all([
          reportsAPI.getTeacherWorkload(params),
          reportsAPI.getGroupWorkload(params),
          reportsAPI.getConflicts(params),
        ])
        teacherWorkload.value = twRes.data.workload ?? []
        groupWorkload.value   = gwRes.data.workload ?? []
        conflicts.value       = cfRes.data.conflicts ?? []
      } catch (e) {
        error.value = e.response?.data?.detail || e.message || 'Ошибка загрузки'
      } finally {
        loading.value = false
      }
      // Also refresh hours log with the same date range
      await loadHoursLog()
    }

    const loadHoursLog = async () => {
      logLoading.value = true
      try {
        const params = { start_date: startDate.value, end_date: endDate.value }
        if (logGroupId.value)   params.group_id   = logGroupId.value
        if (logTeacherId.value) params.teacher_id = logTeacherId.value
        const res = await reportsAPI.getHoursLog(params)
        hoursLog.value = res.data
      } catch (e) {
        console.error('Hours log error', e)
      } finally {
        logLoading.value = false
      }
    }

    const downloadPdf = async () => {
      pdfLoading.value = true
      error.value = ''
      try {
        const params = new URLSearchParams({
          start_date: startDate.value,
          end_date:   endDate.value,
        })
        if (selectedGroupId.value)   params.set('group_id',   selectedGroupId.value)
        if (selectedTeacherId.value) params.set('teacher_id', selectedTeacherId.value)

        const response = await api.get(`/reports/pdf/schedule?${params.toString()}`, {
          responseType: 'blob',
        })

        const url  = URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
        const link = document.createElement('a')
        link.href  = url
        link.download = `schedule_${startDate.value}_${endDate.value}.pdf`
        link.click()
        URL.revokeObjectURL(url)
      } catch (e) {
        error.value = 'Ошибка генерации PDF: ' + (e.response?.data?.detail || e.message)
      } finally {
        pdfLoading.value = false
      }
    }

    onMounted(() => {
      loadCatalog()
    })

    return {
      startDate, endDate, selectedGroupId, selectedTeacherId,
      loading, pdfLoading, error,
      groups, teachers,
      teacherWorkload, groupWorkload, conflicts,
      loadAll, downloadPdf,
      logLoading, logGroupId, logTeacherId, logStatusFilter,
      hoursLog, filteredLogEntries,
      loadHoursLog, statusBadge, formatLogDate,
    }
  },
}
</script>
