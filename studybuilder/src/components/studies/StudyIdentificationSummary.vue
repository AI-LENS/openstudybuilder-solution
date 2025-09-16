<template>
  <StudyMetadataSummary
    :metadata="identification"
    :params="params"
    :first-col-label="$t('StudyIdentificationSummary.core_attribute')"
    :fullscreen-form="false"
    form-max-width="1000px"
    component="identification_metadata"
    :with-reason-for-missing="false"
  >
    <template #topActions>
      <v-btn
        v-if="canDeleteSelectedStudy()"
        size="small"
        color="red"
        :title="$t('_global.delete')"
        icon="mdi-delete-outline"
        :disabled="!accessGuard.checkPermission($roles.STUDY_WRITE)"
        @click.stop="deleteStudy"
      />
    </template>
    <template #form="{ closeHandler, openHandler, formKey }">
      <StudyForm
        :key="formKey"
        :open="openHandler"
        :edited-study="study"
        @close="close(closeHandler)"
        @updated="onIdentificationUpdated"
      />
    </template>
  </StudyMetadataSummary>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script setup>
import { inject, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import api from '@/api/study'
import StudyForm from './StudyForm.vue'
import StudyMetadataSummary from './StudyMetadataSummary.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const { t } = useI18n()
const router = useRouter()
const eventBusEmit = inject('eventBusEmit')
const studiesGeneralStore = useStudiesGeneralStore()
const accessGuard = useAccessGuard()

const identification = ref({})

const params = [
  {
    label: t('Study.clinical_programme'),
    name: 'clinical_programme_name',
  },
  {
    label: t('Study.project_number'),
    name: 'project_number',
  },
  {
    label: t('Study.project_name'),
    name: 'project_name',
  },
  {
    label: t('Study.study_id'),
    name: 'study_id',
  },
  {
    label: t('Study.study_number'),
    name: 'study_number',
  },
  {
    label: t('Study.study_acronym'),
    name: 'study_acronym',
  },
]
const study = ref(null)
const confirm = ref()

onMounted(() => {
  api.getStudy(studiesGeneralStore.selectedStudy.uid).then((resp) => {
    study.value = resp.data
    identification.value = resp.data.current_metadata.identification_metadata
  })
})

function canDeleteSelectedStudy() {
  return (
    study.value &&
    study.value.possible_actions.find((action) => action === 'delete')
  )
}
async function deleteStudy() {
  const options = { type: 'warning' }
  const studyId = study.value.current_metadata.identification_metadata.study_id
  if (
    await confirm.value.open(
      t('StudyStatusTable.confirm_delete', { studyId }),
      options
    )
  ) {
    await api.deleteStudy(studiesGeneralStore.selectedStudy.uid)
    eventBusEmit('notification', {
      msg: t('StudyStatusTable.delete_success'),
      type: 'success',
    })
    studiesGeneralStore.unselectStudy()
    router.push({ name: 'SelectOrAddStudy' })
  }
}
function close(closeHandler) {
  closeHandler()
}
function onIdentificationUpdated(data) {
  study.value = data
  identification.value = data.current_metadata.identification_metadata
}
</script>
