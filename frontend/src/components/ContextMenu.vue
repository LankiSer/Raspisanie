<template>
  <div
    v-if="show"
    :style="{ top: y + 'px', left: x + 'px' }"
    class="fixed z-50 w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 context-menu"
  >
    <div class="py-1">
      <!-- Edit -->
      <button
        @click="$emit('edit', lesson)"
        class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
      >
        <PencilIcon class="inline h-4 w-4 mr-2" />
        Редактировать
      </button>
      
      <!-- Move -->
      <button
        @click="$emit('move', lesson)"
        class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
      >
        <ArrowRightIcon class="inline h-4 w-4 mr-2" />
        Перенести
      </button>
      
      <div class="border-t border-gray-100"></div>
      
      <!-- Status changes -->
      <button
        v-if="lesson?.status === 'planned'"
        @click="handleStatusChange('confirmed')"
        class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
      >
        <CheckCircleIcon class="inline h-4 w-4 mr-2" />
        Подтвердить
      </button>
      
      <button
        v-if="['planned', 'confirmed'].includes(lesson?.status)"
        @click="handleStatusChange('completed')"
        class="block w-full text-left px-4 py-2 text-gray-700 hover:bg-gray-100 hover:text-gray-900"
      >
        <CheckIcon class="inline h-4 w-4 mr-2" />
        Отметить завершенным
      </button>
      
      <button
        v-if="['planned', 'confirmed'].includes(lesson?.status)"
        @click="$emit('cancel', lesson)"
        class="block w-full text-left px-4 py-2 text-sm text-yellow-700 hover:bg-yellow-50 hover:text-yellow-900"
      >
        <XCircleIcon class="inline h-4 w-4 mr-2" />
        Отменить занятие
      </button>
      
      <div class="border-t border-gray-100"></div>
      
      <!-- Delete -->
      <button
        @click="$emit('delete', lesson)"
        class="block w-full text-left px-4 py-2 text-sm text-red-700 hover:bg-red-50 hover:text-red-900"
      >
        <TrashIcon class="inline h-4 w-4 mr-2" />
        Удалить
      </button>
    </div>
  </div>
</template>

<script>
import {
  PencilIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  CheckIcon,
  XCircleIcon,
  TrashIcon
} from '@heroicons/vue/24/outline'
import { lessonsAPI } from '@/services/api'

export default {
  name: 'ContextMenu',
  components: {
    PencilIcon,
    ArrowRightIcon,
    CheckCircleIcon,
    CheckIcon,
    XCircleIcon,
    TrashIcon
  },
  props: {
    show: {
      type: Boolean,
      default: false
    },
    x: {
      type: Number,
      default: 0
    },
    y: {
      type: Number,
      default: 0
    },
    lesson: {
      type: Object,
      default: null
    }
  },
  emits: ['close', 'edit', 'move', 'cancel', 'delete'],
  setup(props, { emit }) {
    const handleStatusChange = async (newStatus) => {
      if (!props.lesson) return
      
      try {
        await lessonsAPI.update(props.lesson.lesson_id, {
          status: newStatus,
          version: props.lesson.version
        })
        
        emit('close')
        // Optionally emit a refresh event
      } catch (error) {
        console.error('Error updating lesson status:', error)
        // Show error message
      }
    }

    return {
      handleStatusChange
    }
  }
}
</script>
