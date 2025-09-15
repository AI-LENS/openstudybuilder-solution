<template>
  <StepperForm
    ref="stepper"
    :title="$t('CodelistCreationForm.title')"
    :steps="steps"
    :form-observer-getter="getObserver"
    :help-items="helpItems"
    @close="cancel"
    @save="submit"
  >
    <template #[`step.catalogue`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row>
          <v-col>
            <v-select
              v-model="form.catalogue_name"
              data-cy="catalogue-dropdown"
              :label="$t('CodelistCreationForm.catalogue')"
              :items="catalogues"
              item-title="name"
              item-value="name"
              clearable
              density="compact"
              persistent-hint
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.names`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.sponsor_preferred_name"
              data-cy="sponsor-preffered-name"
              :label="$t('CodelistSponsorValuesForm.pref_name')"
              clearable
              density="compact"
              class="mt-2"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-switch
              v-model="form.template_parameter"
              color="primary"
              :label="$t('CodelistSponsorValuesForm.tpl_parameter')"
              density="compact"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.attributes`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.name"
              data-cy="codelist-name"
              :label="$t('CodelistAttributesForm.name')"
              clearable
              density="compact"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.submission_value"
              data-cy="submission-value"
              :label="$t('CodelistAttributesForm.subm_value')"
              density="compact"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.nci_preferred_name"
              data-cy="nci-preffered-name"
              :label="$t('CodelistAttributesForm.nci_pref_name')"
              density="compact"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-switch
              v-model="form.extensible"
              color="primary"
              data-cy="extensible-toggle"
              :label="$t('CodelistAttributesForm.extensible')"
              density="compact"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-textarea
              v-model="form.definition"
              data-cy="definition"
              :label="$t('CodelistAttributesForm.definition')"
              rows="1"
              clearable
              auto-grow
              density="compact"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </StepperForm>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script setup>
import { computed, inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useCtCataloguesStore } from '@/stores/library-ctcatalogues'
import controlledTerminology from '@/api/controlledTerminology'
import StepperForm from '@/components/tools/StepperForm.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'

const emit = defineEmits(['close', 'created'])

const formRules = inject('formRules')

const ctCataloguesStore = useCtCataloguesStore()
const { t } = useI18n()

const catalogues = computed(() => ctCataloguesStore.catalogues)

const form = ref({
  extensible: false,
  library_name: 'Sponsor',
  template_parameter: false,
})
const confirm = ref()
const observer_1 = ref()
const observer_2 = ref()
const observer_3 = ref()
const stepper = ref()

const helpItems = [
  'CodelistCreationForm.catalogue',
  'CodelistSponsorValuesForm.pref_name',
  'CodelistSponsorValuesForm.tpl_parameter',
  'CodelistAttributesForm.name',
  'CodelistAttributesForm.subm_value',
  'CodelistAttributesForm.nci_pref_name',
  'CodelistAttributesForm.extensible',
  'CodelistAttributesForm.definition',
]
const steps = [
  {
    name: 'catalogue',
    title: t('CodelistCreationForm.step1_title'),
  },
  { name: 'names', title: t('CodelistCreationForm.step2_title') },
  {
    name: 'attributes',
    title: t('CodelistCreationForm.step3_title'),
  },
]

async function cancel() {
  if (form.value.catalogue_name === 'All') {
    close()
  } else {
    const options = {
      type: 'warning',
      cancelLabel: t('_global.cancel'),
      agreeLabel: t('_global.continue'),
    }
    if (await confirm.value.open(t('_global.cancel_changes'), options)) {
      close()
    }
  }
}

function close() {
  emit('close')
  form.value = {}
  stepper.value.reset()
}

function getObserver(step) {
  if (step === 1) {
    return observer_1.value
  }
  if (step === 2) {
    return observer_2.value
  }
  return observer_3.value
}

async function submit() {
  form.value.terms = []
  const data = JSON.parse(JSON.stringify(form.value))
  try {
    const resp = await controlledTerminology.createCodelist(data)
    emit('created', resp.data)
    close()
  } finally {
    stepper.value.loading = false
  }
}
</script>
