<template>
  <div
    :class="{
      'schedule-cell': true,
      'schedule-cell-occupied': lessons.length > 0
    }"
    @click="handleCellClick"
    @drop="handleDrop"
    @dragover="handleDragOver"
    @dragenter.prevent
    @dragleave="handleDragLeave"
  >
    <!-- Lessons in this cell -->
    <div
      v-for="lesson in lessons"
      :key="lesson.lesson_id"
      :class="getLessonCardClass(lesson)"
      :draggable="canEdit"
      @dragstart="handleDragStart($event, lesson)"
      @click.stop="handleLessonClick(lesson, $event)"
      @contextmenu.prevent="handleLessonClick(lesson, $event)"
      class="lesson-card"
    >
      <!-- Subject name -->
      <div class="font-medium text-xs truncate">
        {{ lesson.course_name || 'Предмет' }}
      </div>
      
      <!-- Teacher & Group -->
      <div class="text-xs text-gray-700 leading-tight">
        <div class="truncate">
          {{ lesson.teacher_name || 'Преподаватель' }}
        </div>
        <div class="truncate">
          {{ lesson.group_name || 'Группа' }}
        </div>
      </div>
      
      <!-- Room -->
      <div class="text-xs text-gray-600 truncate">
        {{ lesson.room_number || 'Ауд. не назначена' }}
      </div>
      
      <!-- Status indicator -->
      <div
        v-if="lesson.status !== 'planned'"
        class="absolute top-1 right-1 w-2 h-2 rounded-full bg-gov-600 ring-1 ring-white"
        :title="getStatusTitle(lesson.status)"
      ></div>
    </div>

    <!-- Drag overlay -->
    <div
      v-show="dragOver"
      class="absolute inset-0 bg-blue-200 bg-opacity-50 border-2 border-blue-400 border-dashed rounded flex items-center justify-center"
    >
      <span class="text-blue-600 text-xs font-medium">Переместить сюда</span>
    </div>

    <!-- Empty cell placeholder -->
    <div
      v-if="lessons.length === 0 && canEdit"
      class="absolute inset-0 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity"
    >
      <PlusIcon class="h-4 w-4 text-gray-400" />
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { PlusIcon } from '@heroicons/vue/24/outline'

export default {
  name: 'ScheduleCell',
  components: {
    PlusIcon
  },
  props: {
    date: {
      type: String,
      required: true
    },
    slot: {
      type: Object,
      required: true
    },
    lessons: {
      type: Array,
      default: () => []
    },
    canEdit: {
      type: Boolean,
      default: false
    }
  },
  emits: ['lesson-click', 'cell-click', 'lesson-drop'],
  setup(props, { emit }) {
    const dragOver = ref(false)

    const getLessonCardClass = (lesson) => {
      const raw = (lesson.status || 'planned').toString().toLowerCase()
      const st = ['planned', 'confirmed', 'completed', 'cancelled', 'moved', 'skipped'].includes(raw)
        ? raw
        : 'planned'
      return `lesson-card lesson-card-${st}`
    }


    const getStatusTitle = (status) => {
      const statusMap = {
        'confirmed': 'Подтверждено',
        'completed': 'Завершено',
        'cancelled': 'Отменено',
        'moved': 'Перенесено',
        'skipped': 'Пропущено'
      }
      return statusMap[status] || status
    }

    const handleCellClick = () => {
      if (props.lessons.length === 0) {
        emit('cell-click', props.date, props.slot.slot_id)
      }
    }

    const handleLessonClick = (lesson, event) => {
      emit('lesson-click', lesson, event)
    }

    const handleDragStart = (event, lesson) => {
      if (!props.canEdit) {
        event.preventDefault()
        return
      }

      // Store the full lesson object so target cell has version for optimistic locking
      event.dataTransfer.setData('text/plain', JSON.stringify({
        lesson,
        source_date: props.date,
        source_slot_id: props.slot.slot_id
      }))
      event.dataTransfer.effectAllowed = 'move'
    }

    const handleDragOver = (event) => {
      if (!props.canEdit) return
      
      event.preventDefault()
      event.dataTransfer.dropEffect = 'move'
      dragOver.value = true
    }

    const handleDragLeave = () => {
      dragOver.value = false
    }

    const handleDrop = (event) => {
      if (!props.canEdit) return
      
      event.preventDefault()
      dragOver.value = false

      try {
        const data = JSON.parse(event.dataTransfer.getData('text/plain'))
        // Full lesson object is always in drag data — includes version for optimistic locking
        emit('lesson-drop', data.lesson, props.date, props.slot.slot_id)
      } catch (error) {
        console.error('Error parsing drag data:', error)
      }
    }

    return {
      dragOver,
      getLessonCardClass,
      getStatusTitle,
      handleCellClick,
      handleLessonClick,
      handleDragStart,
      handleDragOver,
      handleDragLeave,
      handleDrop
    }
  }
}
</script>
