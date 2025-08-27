<template>
  <SimpleFormDialog
    :title="$t('StudyActivityUpdateForms.update_to_activity')"
    max-width="600px"
    no-default-actions
    top-right-cancel
    :open="open"
    @close="close"
  >
    <template #body>
      <v-form ref="observer">
        <div class="label mb-2">
          {{ $t('StudyActivityUpdateForms.instance_name') }}
        </div>
        <v-row>
          <v-col cols="12">
            <span
              v-if="
                checkIfDifferent(
                  activity.activity_instance.name,
                  activity.latest_activity_instance.name
                )
              "
            >
              <v-chip color="red" class="crossed-out">
                <div class="text-nnTrueBlue">
                  {{ activity.activity_instance.name }}
                </div>
              </v-chip>
              &#8594;
            </span>
            <v-chip color="green">
              <div class="text-nnTrueBlue">
                {{ activity.latest_activity_instance.name }}
              </div>
            </v-chip>
          </v-col>
        </v-row>
        <div class="label my-2">
          {{ $t('StudyActivityUpdateForms.instance_class') }}
        </div>
        <v-row>
          <v-col cols="12">
            <span
              v-if="
                checkIfDifferent(
                  activity.activity_instance.activity_instance_class.uid,
                  activity.latest_activity_instance.activity_instance_class.uid
                )
              "
            >
              <v-chip color="red" class="crossed-out">
                <div class="text-nnTrueBlue">
                  {{ activity.activity_instance.activity_instance_class.name }}
                </div>
              </v-chip>
              &#8594;
            </span>
            <v-chip color="green">
              <div class="text-nnTrueBlue">
                {{
                  activity.latest_activity_instance.activity_instance_class.name
                }}
              </div>
            </v-chip>
          </v-col>
        </v-row>
        <div class="label my-2">
          {{ $t('StudyActivityUpdateForms.topic_code') }}
        </div>
        <v-row>
          <v-col cols="12">
            <span
              v-if="
                checkIfDifferent(
                  activity.activity_instance.topic_code,
                  activity.latest_activity_instance.topic_code
                )
              "
            >
              <v-chip color="red" class="crossed-out">
                <div class="text-nnTrueBlue">
                  {{ activity.activity_instance.topic_code }}
                </div>
              </v-chip>
              &#8594;
            </span>
            <v-chip color="green">
              <div class="text-nnTrueBlue">
                {{ activity.latest_activity_instance.topic_code }}
              </div>
            </v-chip>
          </v-col>
        </v-row>
        <div class="label my-2">
          {{ $t('StudyActivityUpdateForms.accept_change') }}
        </div>
      </v-form>
    </template>
    <template #actions="">
      <v-btn
        v-if="!props.activity.keep_old_version"
        color="nnGoldenSun200"
        variant="flat"
        rounded
        class="mr-2"
        :loading="loading"
        @click="declineAndKeep()"
      >
        <v-icon> mdi-close </v-icon>
        {{ $t('StudyActivityUpdateForms.decline_keep') }}
      </v-btn>
      <v-btn
        color="red"
        variant="flat"
        rounded
        class="mr-2"
        :loading="loading"
        @click="declineAndRemove()"
      >
        <v-icon> mdi-close </v-icon>
        {{ $t('StudyActivityUpdateForms.decline_remove') }}
      </v-btn>
      <v-btn
        color="nnBaseBlue"
        variant="flat"
        rounded
        :loading="loading"
        @click="submit()"
      >
        <v-icon> mdi-check </v-icon>
        {{ $t('StudyActivityUpdateForms.accept') }}
      </v-btn>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import { useI18n } from 'vue-i18n'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { inject, ref } from 'vue'
import study from '@/api/study'

const studiesGeneralStore = useStudiesGeneralStore()
const emit = defineEmits(['close'])
const { t } = useI18n()
const eventBusEmit = inject('eventBusEmit')

const props = defineProps({
  activity: {
    type: Object,
    default: null,
  },
  open: Boolean,
})

const observer = ref()
const loading = ref(false)

async function submit() {
  loading.value = true
  study
    .updateStudyActivityInstanceToLatest(
      studiesGeneralStore.selectedStudy.uid,
      props.activity.study_activity_instance_uid
    )
    .then(() => {
      loading.value = false
      eventBusEmit('notification', {
        type: 'success',
        msg: t('StudyActivityUpdateForms.update_success'),
      })
      close()
    })
}

function close() {
  emit('close')
}

async function declineAndRemove() {
  loading.value = true
  const data = {
    activity_instance_uid: null,
    study_activity_uid: props.activity.study_activity_uid,
    show_activity_instance_in_protocol_flowchart:
      props.activity.show_activity_instance_in_protocol_flowchart,
  }
  study
    .updateStudyActivityInstance(
      studiesGeneralStore.selectedStudy.uid,
      props.activity.study_activity_instance_uid,
      data
    )
    .then(() => {
      eventBusEmit('notification', {
        msg: t('StudyActivityInstances.instance_deleted'),
        type: 'success',
      })
      close()
    })
}

async function declineAndKeep() {
  loading.value = true
  const payload = JSON.parse(JSON.stringify(props.activity))
  payload.keep_old_version = true
  study
    .updateStudyActivityInstance(
      studiesGeneralStore.selectedStudy.uid,
      props.activity.study_activity_instance_uid,
      payload
    )
    .then(() => {
      loading.value = false
      eventBusEmit('notification', {
        type: 'success',
        msg: t('StudyActivityUpdateForms.decline_success'),
      })
      close()
    })
}

function checkIfDifferent(valA, valB) {
  return valA !== valB
}
</script>
<style scoped>
.crossed-out {
  text-decoration: line-through;
}
.label {
  font-weight: 700;
  font-size: 18px;
  line-height: 24px;
  letter-spacing: -0.02em;
  color: rgb(var(--v-theme-nnTrueBlue));
  min-height: 24px;
}
</style>
