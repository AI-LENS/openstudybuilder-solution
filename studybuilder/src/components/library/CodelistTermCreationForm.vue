<template>
  <StepperForm
    ref="stepper"
    data-cy="form-body"
    :title="$t('CodelistTermCreationForm.title')"
    :steps="steps"
    :form-observer-getter="getObserver"
    :help-items="helpItems"
    :edit-data="form"
    @close="close"
    @save="submit"
  >
    <template #[`step.creation_mode`]>
      <v-row>
        <v-col>
          <v-radio-group v-model="createNewTerm">
            <v-radio
              data-cy="select-exitsing-term"
              :label="$t('CodelistTermCreationForm.select_mode')"
              :value="false"
            />
            <v-radio
              data-cy="create-new-term"
              :label="$t('CodelistTermCreationForm.create_mode')"
              :value="true"
            />
          </v-radio-group>
        </v-col>
      </v-row>
    </template>
    <template #[`step.select`]>
      <v-row>
        <v-col>
          <NNTable
            v-model="selection"
            :headers="termHeaders"
            :items="terms"
            :items-length="total"
            :items-per-page-options="itemsPerPage"
            item-value="term_uid"
            class="mt-4"
            hide-export-button
            column-data-resource="ct/terms"
            :loading="loading"
            show-select
            :codelist-uid="null"
            @filter="scheduleFilterTerms"
          />
        </v-col>
      </v-row>
    </template>
    <template #[`step.names`]>
      <v-form ref="namesForm">
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.sponsor_preferred_name"
              data-cy="term-sponsor-preferred-name"
              :label="$t('CodelistTermCreationForm.sponsor_pref_name')"
              :rules="[formRules.required]"
              density="compact"
              clearable
              @update:model-value="setSentenceCase"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.sponsor_preferred_name_sentence_case"
              data-cy="term-sentence-case-name"
              :label="$t('CodelistTermCreationForm.sponsor_sentence_case_name')"
              :rules="[
                formRules.required,
                (value) => formRules.sameAs(value, form.sponsor_preferred_name),
              ]"
              density="compact"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.order"
              data-cy="term-order"
              :label="$t('CodelistTermCreationForm.order')"
              :rules="[formRules.required]"
              density="compact"
              clearable
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.attributes`]>
      <v-form ref="attributesForm">
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.name_submission_value"
              data-cy="term-name"
              :label="$t('CodelistTermCreationForm.name_submission_value')"
              :rules="[formRules.required]"
              density="compact"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.code_submission_value"
              data-cy="term-submission-value"
              :label="$t('CodelistTermCreationForm.code_submission_value')"
              :rules="[formRules.required]"
              density="compact"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.nci_preferred_name"
              data-cy="term-nci-preffered-name"
              :label="$t('CodelistTermCreationForm.nci_pref_name')"
              density="compact"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-textarea
              v-model="form.definition"
              data-cy="term-definition"
              :label="$t('CodelistTermCreationForm.definition')"
              :rules="[formRules.required]"
              density="compact"
              clearable
              auto-grow
              rows="1"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </StepperForm>
</template>

<script setup>
import { inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import constants from '@/constants/libraries.js'
import controlledTerminology from '@/api/controlledTerminology'
import termsApi from '@/api/controlledTerminology/terms'
import StepperForm from '@/components/tools/StepperForm.vue'
import NNTable from '@/components/tools/NNTable.vue'
import filteringParameters from '@/utils/filteringParameters'

const { t } = useI18n()
const eventBusEmit = inject('eventBusEmit')
const formRules = inject('formRules')
const props = defineProps({
  catalogueName: {
    type: String,
    default: null,
  },
  codelistUid: {
    type: String,
    default: null,
  },
})
const emit = defineEmits(['close', 'created'])

const itemsPerPage = [
  {
    value: 5,
    title: '5',
  },
  {
    value: 10,
    title: '10',
  },
  {
    value: 15,
    title: '15',
  },
  {
    value: 25,
    title: '25',
  },
  {
    value: 50,
    title: '50',
  },
  {
    value: 100,
    title: '100',
  },
]
const createNewTerm = ref(false)
const form = ref({})
const alternateSteps = [
  {
    name: 'creation_mode',
    title: t('CodelistTermCreationForm.creation_mode_label'),
  },
  {
    name: 'names',
    title: t('CodelistTermCreationForm.create_sponsor_name'),
  },
  {
    name: 'attributes',
    title: t('CodelistTermCreationForm.create_term_attributes'),
  },
]
const helpItems = [
  'CodelistTermCreationForm.sponsor_pref_name',
  'CodelistTermCreationForm.sponsor_sentence_case_name',
  'CodelistTermCreationForm.name_submission_value',
  'CodelistTermCreationForm.code_submission_value',
  'CodelistTermCreationForm.nci_pref_name',
  'CodelistTermCreationForm.definition',
]
const selection = ref([])
const steps = ref(getInitialSteps())
const termHeaders = [
  {
    title: t('CodelistTermCreationForm.concept_id'),
    key: 'attributes.concept_id',
  },
  {
    title: t('CodelistTermCreationForm.submission_value'),
    key: 'attributes.name_submission_value',
  },
  {
    title: t('CodelistTermCreationForm.sponsor_name'),
    key: 'name.sponsor_preferred_name',
  },
  {
    title: t('CodelistTermCreationForm.nci_pref_name'),
    key: 'attributes.nci_preferred_name',
  },
  { title: t('_global.definition'), key: 'attributes.definition' },
]
const terms = ref([])
let timer = null
const total = ref(0)
const loading = ref(false)
const stepper = ref()
const namesForm = ref()
const attributesForm = ref()

watch(createNewTerm, (value) => {
  steps.value = value ? alternateSteps : getInitialSteps()
})

onMounted(() => {
  termsApi.getAll({ page_size: 10, total_count: true }).then((resp) => {
    terms.value = resp.data.items
    total.value = resp.data.total
  })
})

function close() {
  emit('close')
  createNewTerm.value = true
  form.value = {}
  stepper.value.reset()
}
function getInitialSteps() {
  return [
    {
      name: 'creation_mode',
      title: t('CodelistTermCreationForm.creation_mode_label'),
    },
    {
      name: 'select',
      title: t('CodelistTermCreationForm.select_term_label'),
    },
  ]
}
function getObserver(step) {
  if (step === 2) {
    return namesForm.value
  }
  if (step === 3) {
    return attributesForm.value
  }
  return undefined
}
async function submit() {
  if (createNewTerm.value) {
    const data = {
      ...form.value,
      catalogue_name: props.catalogueName,
      codelist_uid: props.codelistUid,
      library_name: constants.LIBRARY_SPONSOR,
    }
    try {
      const resp = await controlledTerminology.createCodelistTerm(data)
      eventBusEmit('notification', {
        msg: t('CodelistTermCreationForm.add_success'),
      })
      emit('created', resp.data)
      close()
    } finally {
      stepper.value.loading = false
    }
  } else {
    if (!selection.value.length) {
      eventBusEmit('notification', {
        msg: t('CodelistTermCreationForm.no_selection'),
        type: 'error',
      })
      return
    }
    const codelistUid = props.codelistUid
    for (const term of selection.value) {
      await controlledTerminology.addTermToCodelist(codelistUid, term.term_uid)
    }
    eventBusEmit('notification', {
      msg: t('CodelistTermCreationForm.add_success'),
    })
    close()
  }
}
function setSentenceCase(value) {
  if (value) {
    form.value.sponsor_preferred_name_sentence_case = value.toLowerCase()
  }
}
function filterTerms(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  termsApi.getAll(params).then((resp) => {
    terms.value = resp.data.items
    total.value = resp.data.total
    loading.value = false
  })
}
/*
 ** Avoid sending too many request to the API
 */
function scheduleFilterTerms(filters, options, filtersUpdated) {
  loading.value = true
  if (timer) {
    clearTimeout(timer)
    timer = null
  }
  timer = setTimeout(filterTerms(filters, options, filtersUpdated), 300)
}
</script>
