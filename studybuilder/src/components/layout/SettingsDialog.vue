<template>
  <v-card color="greyBackground">
    <v-card-title class="d-flex align-center">
      <span class="headline">{{ $t('Settings.title') }}</span>
      <HelpButtonWithPanels :title="$t('_global.help')" :items="helpItems" />
    </v-card-title>
    <v-card-text>
      <div class="bg-white pa-4">
        <v-select
          v-model="form.rows"
          :label="$t('Settings.rows')"
          :items="tablesConstants.ITEMS_PER_PAGE_OPIONS"
          clearable
        />
        <v-text-field
          v-model="form.studyNumberLength"
          :label="$t('Settings.study_number_length')"
          type="number"
          clearable
        />
        <v-switch
          v-model="form.multilingual"
          color="primary"
          :label="$t('Settings.multilingual_crf')"
          data-cy="settings-multilingual-crf"
          class="mt-4"
        />
      </div>
    </v-card-text>
    <v-card-actions class="pb-4">
      <v-spacer />
      <v-btn class="secondary-btn" color="white" @click="close">
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-btn
        color="secondary"
        data-cy="save-settings-button"
        :loading="working"
        @click="save"
      >
        {{ $t('_global.save') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useAppStore } from '@/stores/app'
import tablesConstants from '@/constants/tables'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'

const emit = defineEmits(['close'])
const appStore = useAppStore()

const helpItems = ['Settings.rows', 'Settings.study_number_length']
const form = ref({})
const working = ref(false)

watch(
  () => appStore.userData,
  (val) => {
    form.value = JSON.parse(JSON.stringify(val))
  },
  { immediate: true }
)

function close() {
  emit('close')
}
function save() {
  working.value = true
  appStore.saveUserData(form.value)
  close()
  working.value = false
}
</script>
