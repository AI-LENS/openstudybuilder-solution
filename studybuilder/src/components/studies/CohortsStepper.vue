<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="title"
    :steps="steps"
    :help-items="helpItems"
    :form-observer-getter="getObserver"
    help-text=""
    :reset-loading="resetLoading"
    custom-actions
    @close="close"
  >
    <template #[`step.creationMode`]>
      <div class="label mb-4">{{ $t('CohortsStepper.select_class') }}</div>
      <v-radio-group v-model="creationMode" color="primary">
        <v-radio
          :label="$t('CohortsStepper.full_stepper')"
          :value="cohortConstants.FULL"
          data-cy="full-design-study"
        />
        <v-radio
          :label="$t('CohortsStepper.arms_only_stepper')"
          :value="cohortConstants.MANUAL"
          data-cy="manual-study"
        />
      </v-radio-group>
    </template>
    <template #[`step.arms`]>
      <v-form ref="armsForm">
        <div class="label mb-4">
          {{ $t('CohortsStepper.set_arms_for_study') }}
        </div>
        <v-sheet
          v-for="(arm, index) in arms"
          :key="index"
          color="nnLightBlue100"
          rounded="xl"
          style="max-width: 80%"
          class="mb-4 px-4 py-4"
          border="sm"
        >
          <v-row>
            <v-col cols="4">
              <v-autocomplete
                v-model="arm.arm_type_uid"
                data-cy="arm-type"
                :label="$t('CohortsStepper.study_arm_type')"
                :rules="[formRules.required]"
                :items="armTypes"
                variant="outlined"
                bg-color="white"
                open-on-clear
                color="nnBaseBlue"
                base-color="nnBaseBlue"
                rounded="lg"
                item-title="name.sponsor_preferred_name"
                item-value="term_uid"
                clearable
                density="compact"
              />
            </v-col>
            <v-col cols="4">
              <v-text-field
                v-model="arm.name"
                data-cy="arm-name"
                :label="$t('CohortsStepper.arm_name')"
                :rules="[formRules.required, formRules.max(arm.name, 200)]"
                variant="outlined"
                bg-color="white"
                color="nnBaseBlue"
                base-color="nnBaseBlue"
                rounded="lg"
                clearable
                density="compact"
                class="smallfont"
              />
            </v-col>
            <v-col cols="3">
              <v-text-field
                v-model="arm.short_name"
                data-cy="arm-short-name"
                :label="$t('CohortsStepper.arm_short_name')"
                :rules="[formRules.required, formRules.max(arm.short_name, 20)]"
                variant="outlined"
                bg-color="white"
                color="nnBaseBlue"
                base-color="nnBaseBlue"
                rounded="lg"
                clearable
                density="compact"
              />
            </v-col>
            <v-col cols="1">
              <v-btn
                color="error"
                data-cy="remove-arm"
                class="text-none"
                variant="flat"
                @click="removeArm(arm, index)"
              >
                {{ $t('_global.remove') }}
              </v-btn>
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="4">
              <div style="display: flex">
                <v-text-field
                  v-if="creationMode === cohortConstants.MANUAL"
                  v-model="arm.number_of_subjects"
                  data-cy="number-of-subjects"
                  :label="$t('CohortsStepper.no_participants')"
                  class="mr-1"
                  variant="outlined"
                  bg-color="white"
                  color="nnBaseBlue"
                  base-color="nnBaseBlue"
                  rounded="lg"
                  clearable
                  density="compact"
                />
                <v-text-field
                  v-model="arm.randomization_group"
                  data-cy="randomization-group"
                  :label="$t('CohortsStepper.rand_group_optional')"
                  class="mr-1"
                  variant="outlined"
                  bg-color="white"
                  color="nnBaseBlue"
                  base-color="nnBaseBlue"
                  rounded="lg"
                  clearable
                  density="compact"
                />
                <v-text-field
                  v-if="creationMode !== cohortConstants.MANUAL"
                  v-model="arm.code"
                  data-cy="arm-code"
                  :label="$t('CohortsStepper.arm_code_optional')"
                  :rules="[formRules.max(arm.code, 20)]"
                  class="ml-1"
                  variant="outlined"
                  bg-color="white"
                  color="nnBaseBlue"
                  base-color="nnBaseBlue"
                  rounded="lg"
                  clearable
                  density="compact"
                />
              </div>
            </v-col>
            <v-col cols="4">
              <v-text-field
                v-model="arm.description"
                data-cy="arm-description"
                :label="$t('CohortsStepper.desc')"
                variant="outlined"
                bg-color="white"
                color="nnBaseBlue"
                base-color="nnBaseBlue"
                rounded="lg"
                clearable
                density="compact"
              />
            </v-col>
            <!-- Hidden for now, will be used later 
            <v-col v-if="creationMode !== cohortConstants.MANUAL" cols="3">
              <v-switch
                v-model="arm.merge_branch_for_this_arm_for_sdtm_adam"
                inset
                hide-details
                class="mt-n2"
                color="nnBaseBlue"
              >
                <template #label>
                  <div style="font-size: 14px; color: #454b5c">
                    {{ $t('CohortsStepper.merge_branch') }}
                  </div>
                </template>
              </v-switch>
            </v-col> -->
            <v-col v-if="creationMode === cohortConstants.MANUAL" cols="3">
              <v-text-field
                v-model="arm.code"
                data-cy="arm-code"
                :label="$t('CohortsStepper.arm_code_optional')"
                :rules="[formRules.max(arm.code, 20)]"
                class="ml-1"
                variant="outlined"
                bg-color="white"
                color="nnBaseBlue"
                base-color="nnBaseBlue"
                rounded="lg"
                clearable
                density="compact"
              />
            </v-col>
          </v-row>
        </v-sheet>
        <v-btn
          class="secondary-btn text-none"
          data-cy="arm-push"
          variant="outlined"
          prepend-icon="mdi-plus"
          width="120px"
          rounded="xl"
          @click="arms.push({})"
        >
          {{ $t('CohortsStepper.add_arm') }}
        </v-btn>
      </v-form>
    </template>
    <template #[`step.cohorts`]>
      <v-form ref="cohortsForm">
        <div class="label mb-4">
          {{ $t('CohortsStepper.set_cohorts_for_study') }}
        </div>
        <v-row>
          <v-col cols="3">
            <v-autocomplete
              v-model="sourceVariable.source_variable"
              data-cy="source-variable"
              :label="$t('CohortsStepper.source_var_optional')"
              :items="sourceVariables"
              variant="outlined"
              bg-color="white"
              open-on-clear
              color="nnBaseBlue"
              base-color="nnBaseBlue"
              rounded="lg"
              clearable
              density="compact"
            />
          </v-col>
          <v-col cols="3">
            <v-text-field
              v-model="sourceVariable.source_variable_description"
              data-cy="source-variable-description"
              :label="$t('CohortsStepper.source_var_desc')"
              variant="outlined"
              bg-color="white"
              color="nnBaseBlue"
              base-color="nnBaseBlue"
              rounded="lg"
              clearable
              density="compact"
            />
          </v-col>
        </v-row>
        <v-sheet
          v-for="(cohort, index) in cohorts"
          :key="index"
          color="nnLightBlue100"
          rounded="xl"
          style="max-width: 80%"
          class="mb-4 px-4 py-4"
          border="xs"
        >
          <v-row>
            <v-col cols="2">
              <v-text-field
                v-model="cohort.code"
                data-cy="cohort-code"
                :label="$t('CohortsStepper.cohort_code')"
                :rules="[formRules.required]"
                variant="outlined"
                bg-color="white"
                color="nnBaseBlue"
                base-color="nnBaseBlue"
                rounded="lg"
                clearable
                density="compact"
              />
            </v-col>
            <v-col cols="4">
              <v-text-field
                v-model="cohort.name"
                data-cy="cohort-name"
                :label="$t('CohortsStepper.cohort_name')"
                :rules="[formRules.required, formRules.max(cohort.name, 200)]"
                variant="outlined"
                bg-color="white"
                color="nnBaseBlue"
                base-color="nnBaseBlue"
                rounded="lg"
                clearable
                density="compact"
              />
            </v-col>
            <v-col cols="4">
              <v-text-field
                v-model="cohort.short_name"
                data-cy="cohort-short-name"
                :label="$t('CohortsStepper.cohort_short_name')"
                :rules="[
                  formRules.required,
                  formRules.max(cohort.short_name, 20),
                ]"
                variant="outlined"
                bg-color="white"
                color="nnBaseBlue"
                base-color="nnBaseBlue"
                rounded="lg"
                clearable
                density="compact"
              />
            </v-col>
            <v-col cols="2">
              <v-btn
                color="error"
                class="text-none"
                variant="flat"
                data-cy="remove-cohort"
                @click="removeCohort(cohort, index)"
              >
                {{ $t('_global.remove') }}
              </v-btn>
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="10">
              <v-text-field
                v-model="cohort.description"
                data-cy="cohort-description"
                :label="$t('CohortsStepper.desc')"
                variant="outlined"
                bg-color="white"
                color="nnBaseBlue"
                base-color="nnBaseBlue"
                rounded="lg"
                clearable
                density="compact"
              />
            </v-col>
          </v-row>
        </v-sheet>
        <v-btn
          class="secondary-btn text-none"
          variant="outlined"
          prepend-icon="mdi-plus"
          data-cy="cohort-push"
          rounded="xl"
          @click="cohorts.push({})"
        >
          {{ $t('CohortsStepper.add_cohort') }}
        </v-btn>
      </v-form>
    </template>
    <template #[`step.linking`]>
      <v-form ref="linkingForm">
        <div class="label mb-4">
          {{ $t('CohortsStepper.link_arms_cohorts') }}
        </div>
        <v-alert
          color="nnLightBlue200"
          style="width: 75vw"
          class="mb-2 text-nnTrueBlue"
          type="info"
          rounded="lg"
          :text="$t('CohortsStepper.link_info')"
        />
        <div style="display: flex">
          <div style="display: grid">
            <v-sheet
              rounded="lg"
              width="300px"
              height="110px"
              class="mr-2 pt-2"
              style="justify-items: center; align-content: center"
            >
              <div style="color: grey">
                {{ $t('CohortsStepper.total_amount') }}
              </div>
              <v-text-field
                v-model="totalParticipants"
                data-cy="total-participants"
                prepend-inner-icon="mdi-account"
                width="110px"
                variant="outlined"
                bg-color="white"
                color="nnBaseBlue"
                rounded
                clearable
                disabled
                density="compact"
              />
            </v-sheet>
            <v-sheet
              v-for="cohort in cohorts"
              :key="cohort.name"
              data-cy="cohort-name"
              rounded="lg"
              border
              width="300px"
              height="100px"
              color="nnLightBlue100"
              class="mr-2 ps-4"
            >
              <v-row class="mt-1">
                <v-col class="text-nnTrueBlue">
                  <div class="text-body-2">
                    {{ $t('CohortsStepper.cohort_name') }}
                  </div>
                  <div
                    class="text-subtitle-1 font-weight-bold"
                    style="line-height: 1.25"
                  >
                    {{ cohort.name }}
                  </div>
                </v-col>
                <v-col style="display: flex">
                  <div
                    class="mt-4 ml-n4"
                    style="color: grey; font-size: 0.9rem"
                  >
                    {{ $t('CohortsStepper.total') }}
                  </div>
                  <v-text-field
                    v-model="cohort.number_of_subjects"
                    prepend-inner-icon="mdi-account"
                    data-cy="number-of-subjects"
                    label="0"
                    single-line
                    width="85px"
                    variant="outlined"
                    bg-color="white"
                    color="nnBaseBlue"
                    rounded
                    clearable
                    disabled
                    density="compact"
                    class="mt-1"
                    style="scale: 80%; height: 60px"
                  />
                </v-col>
              </v-row>
            </v-sheet>
          </div>
          <div
            v-for="(arm, armIndex) in branches"
            :key="arm.name"
            style="display: grid"
          >
            <v-sheet
              rounded="lg"
              width="300px"
              height="100px"
              border
              color="nnLightBlue100"
              class="mb-2 mr-2 ps-4"
            >
              <v-row class="mt-1">
                <v-col class="text-nnTrueBlue">
                  <div class="text-body-2">
                    {{ $t('CohortsStepper.arm_name') }}
                  </div>
                  <div
                    class="text-subtitle-1 font-weight-bold"
                    style="line-height: 1.25"
                  >
                    {{ arm.name }}
                  </div>
                </v-col>
                <v-col style="display: flex">
                  <div
                    class="mt-4 ml-n5"
                    style="color: grey; font-size: 0.9rem"
                  >
                    {{ $t('CohortsStepper.total') }}
                  </div>
                  <v-text-field
                    v-model="arm.number_of_subjects"
                    data-cy="number-of-subjects"
                    prepend-inner-icon="mdi-account"
                    width="85px"
                    variant="outlined"
                    bg-color="white"
                    color="nnBaseBlue"
                    rounded
                    clearable
                    disabled
                    density="compact"
                    class="mt-1"
                    style="scale: 80%; height: 60px"
                  />
                </v-col>
              </v-row>
            </v-sheet>
            <div
              v-for="(cohort, index) in arm.study_cohorts"
              :key="cohort.name"
              style="display: flex"
            >
              <v-sheet
                rounded="lg"
                width="300px"
                height="100px"
                border
                :class="
                  cohort.study_branch_arms[0].number_of_subjects > 0
                    ? 'mb-2 mr-2 tile pa-2'
                    : 'mb-2 mr-2 tile pa-2 bg-greyBackground'
                "
                style="justify-content: center"
              >
                <div class="mb-2 text-nnTrueBlue">
                  <p class="text-body-2 ml-3" style="height: 40px">
                    {{ cohort.study_branch_arms[0].name }}
                  </p>
                  <div style="display: flex" class="mb-5">
                    <v-number-input
                      :key="cohort.study_branch_arms[0].name"
                      v-model="cohort.study_branch_arms[0].number_of_subjects"
                      data-cy="number-of-subjects-single-arm"
                      :reverse="false"
                      control-variant="split"
                      density="compact"
                      :min="0"
                      inset
                      variant="outlined"
                      style="width: 160px"
                      @update:model-value="
                        (value) => updateParticipants(value, index, armIndex)
                      "
                    ></v-number-input>
                    <v-btn
                      class="mt-1 ml-2"
                      size="x-small"
                      variant="outlined"
                      color="nnBaseBlue"
                      icon="mdi-pencil"
                      data-cy="edit-branch"
                      @click="openBranchEditForm(cohort.study_branch_arms[0])"
                    />
                  </div>
                </div>
              </v-sheet>
              <v-btn
                v-if="index === 0 && armIndex === arms.length - 1"
                class="secondary-btn ml-2 mt-4"
                variant="outlined"
                rounded="xl"
                data-cy="copy-branches"
                :loading="loading"
                @click="copyBranches"
              >
                {{ $t('CohortsStepper.copy_row') }}
              </v-btn>
            </div>
          </div>
        </div>
      </v-form>
    </template>
    <template #customActions>
      <v-btn
        class="secondary-btn my-2 ml-2"
        variant="outlined"
        width="120px"
        rounded="xl"
        data-cy="cancel-stepper"
        :loading="loading"
        @click="cancel"
      >
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-btn
        v-if="stepper.currentStep !== 1"
        class="secondary-btn"
        variant="outlined"
        width="120px"
        rounded="xl"
        data-cy="save-close-stepper"
        :loading="loading"
        @click="saveAndClose"
      >
        {{ $t('_global.save_exit') }}
      </v-btn>
      <v-spacer />
      <v-btn
        v-if="stepper.currentStep > 1"
        class="secondary-btn"
        variant="outlined"
        width="120px"
        rounded="xl"
        :loading="loading"
        data-cy="previous-stepper"
        @click="previousStep()"
      >
        {{ $t('_global.previous') }}
      </v-btn>
      <v-btn
        class="mr-2"
        color="secondary"
        variant="flat"
        rounded="xl"
        data-cy="continue-stepper"
        :loading="loading"
        :disabled="checkContinueDisabled"
        @click="saveAndContinue()"
      >
        {{ continueLabel }}
      </v-btn>
    </template>
  </HorizontalStepperForm>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  <BranchEditForm
    :branch="editBranch"
    :open="showBranchEditForm"
    @save="applyBranchChanges"
    @close="closeBranchEditForm"
  />
</template>

<script setup>
import { inject, onMounted, ref, watch, computed } from 'vue'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import codelists from '@/api/controlledTerminology/terms'
import cohortsApi from '@/api/cohorts'
import armsApi from '@/api/arms'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import BranchEditForm from './BranchEditForm.vue'
import _isEmpty from 'lodash/isEmpty'
import { useI18n } from 'vue-i18n'
import cohortConstants from '@/constants/cohorts'

const { t } = useI18n()
const formRules = inject('formRules')
const studiesGeneralStore = useStudiesGeneralStore()
const emit = defineEmits(['close'])

const stepper = ref()
const confirm = ref()

const props = defineProps({
  designClass: {
    type: String,
    default: null,
  },
  initialStep: {
    type: Number,
    default: 0,
  },
})

const fullStepperSteps = [
  { name: 'creationMode', title: t('CohortsStepper.select_class') },
  { name: 'arms', title: t('CohortsStepper.set_arms') },
  { name: 'cohorts', title: t('CohortsStepper.set_cohorts') },
  { name: 'linking', title: t('CohortsStepper.linking') },
]

const manuallyDefinedSteps = [
  { name: 'creationMode', title: t('CohortsStepper.select_class') },
  { name: 'arms', title: t('CohortsStepper.set_arms') },
]
const steps = ref([])
const creationMode = ref(cohortConstants.FULL)
const resetLoading = ref(0)
const armsForm = ref()
const cohortsForm = ref()
const linkingForm = ref()
const arms = ref([{}])
const armTypes = ref([])
const cohorts = ref([{}])
const branches = ref([])
const totalParticipants = ref(0)
const loading = ref(false)
const editableDesignClass = ref(true)
const showBranchEditForm = ref(false)
const editBranch = ref(null)
const sourceVariable = ref({})
const sourceVariables = [
  t('CohortsStepper.cohort'),
  t('CohortsStepper.subgroup'),
  t('CohortsStepper.stratum'),
]
const currentDesignClass = ref('')
const helpItems = ref([
  'CohortsStepper.select_class',
  'CohortsStepper.set_arms_for_study',
  'CohortsStepper.study_arm_type',
  'CohortsStepper.arm_name',
  'CohortsStepper.arm_short_name',
  'CohortsStepper.rand_group',
  'CohortsStepper.arm_code',
  'CohortsStepper.set_cohorts_for_study',
  'CohortsStepper.source_var',
  'CohortsStepper.cohort_code',
  'CohortsStepper.cohort_name',
  'CohortsStepper.cohort_short_name',
  'CohortsStepper.link_arms_cohorts',
])

onMounted(async () => {
  currentDesignClass.value = JSON.parse(JSON.stringify(props.designClass))
  cohortsApi
    .checkDesignClassEditable(studiesGeneralStore.selectedStudy.uid)
    .then((resp) => {
      editableDesignClass.value = !resp.data
    })
  codelists.getByCodelist('armTypes').then((resp) => {
    armTypes.value = resp.data.items
  })
  stepper.value.currentStep = props.initialStep
  if (stepper.value.currentStep === 2) {
    getArms()
  } else if (stepper.value.currentStep === 3) {
    await getArms()
    await getCohorts()
    cohortsApi
      .getSourceVariable(studiesGeneralStore.selectedStudy.uid)
      .then((resp) => {
        if (resp.data) {
          sourceVariable.value = resp.data
        }
      })
  } else if (stepper.value.currentStep === 4) {
    await getArms()
    await getCohorts()
    cohortsApi
      .getSourceVariable(studiesGeneralStore.selectedStudy.uid)
      .then((resp) => {
        if (resp.data) {
          sourceVariable.value = resp.data
        }
      })
    cohorts.value.forEach((cohort) => {
      if (!cohort.branch_arm_roots) {
        cohort.branch_arm_roots = []
        arms.value.forEach(() => {
          cohort.branch_arm_roots.push({ number_of_subjects: 0 })
        })
      }
    })
    getBranches()
  }
})

watch(creationMode, (value) => {
  if (value === cohortConstants.MANUAL) {
    steps.value = manuallyDefinedSteps
  } else {
    steps.value = fullStepperSteps
  }
})

watch(
  () => props.designClass,
  (value) => {
    if (value === cohortConstants.MANUAL) {
      creationMode.value = cohortConstants.MANUAL
    } else {
      creationMode.value = cohortConstants.FULL
    }
  },
  { immediate: true }
)

const title = computed(() => {
  return arms.value.length > 0 || cohorts.value.length > 0
    ? t('CohortsStepper.update_structure')
    : t('CohortsStepper.create_stucture')
})

const continueLabel = computed(() => {
  if (stepper.value.currentStep === 1) {
    return t('_global.continue')
  } else if (
    creationMode.value === cohortConstants.FULL &&
    stepper.value.currentStep === 4
  ) {
    return t('CohortsStepper.create_stucture')
  } else if (
    creationMode.value === cohortConstants.MANUAL &&
    stepper.value.currentStep === 2
  ) {
    return t('CohortsStepper.create_arms')
  }
  return t('_global.save_continue')
})

const checkContinueDisabled = computed(() => {
  if (
    stepper.value.currentStep === 3 &&
    (arms.value.length === 0 || cohorts.value.length === 0)
  ) {
    return true
  }
  return false
})

steps.value = fullStepperSteps

function updateParticipants(value, cohortIndex, armIndex) {
  try {
    let armCounter = 0
    branches.value[armIndex].study_cohorts.forEach((cohort) => {
      armCounter += cohort.study_branch_arms[0].number_of_subjects
    })
    branches.value[armIndex].number_of_subjects = armCounter

    let cohortCounter = 0
    if (!cohorts.value[cohortIndex].branch_arm_roots[armIndex]) {
      const iterations =
        armIndex + 1 - cohorts.value[cohortIndex].branch_arm_roots.length
      for (let i = iterations; i > 0; i--) {
        cohorts.value[cohortIndex].branch_arm_roots.push({
          number_of_subjects: 0,
        })
      }
    }
    cohorts.value[cohortIndex].branch_arm_roots[armIndex].number_of_subjects =
      value
    cohorts.value[cohortIndex].branch_arm_roots.forEach((branch) => {
      cohortCounter += branch.number_of_subjects
    })
    cohorts.value[cohortIndex].number_of_subjects = cohortCounter
    totalParticipants.value = 0
    cohorts.value.forEach((cohort) => {
      totalParticipants.value += cohort.number_of_subjects
    })
  } catch (error) {
    console.error(error)
  }
}

async function saveAndContinue() {
  if (!(await stepper.value.validateStepObserver(stepper.value.currentStep))) {
    return
  }
  loading.value = true
  if (stepper.value.currentStep === 0) {
    stepper.value.currentStep = 1
  }
  if (stepper.value.currentStep === 1) {
    saveDesignClass()
    getArms()
  } else if (stepper.value.currentStep === 2) {
    saveArms(steps.value.length === 2)
    getCohorts()
    cohortsApi
      .getSourceVariable(studiesGeneralStore.selectedStudy.uid)
      .then((resp) => {
        if (resp.data) {
          sourceVariable.value = resp.data
        }
      })
  } else if (stepper.value.currentStep === 3) {
    saveSourceVariable()
    saveCohorts()
  } else if (stepper.value.currentStep === 4) {
    saveBranches()
  }
}

async function saveDesignClass() {
  if (props.designClass) {
    if (currentDesignClass.value === creationMode.value) {
      loading.value = false
      stepper.value.currentStep += 1
      return
    }
    const options = {
      type: 'warning',
      width: 600,
      cancelLabel: t('CohortsStepper.keep_class'),
      agreeLabel: t('CohortsStepper.change_class'),
    }
    if (
      currentDesignClass.value === cohortConstants.MANUAL &&
      creationMode.value !== cohortConstants.MANUAL
    ) {
      if (
        await confirm.value.open(
          t('CohortsStepper.change_class_warning_1'),
          options
        )
      ) {
        cohortsApi
          .changeStudyDesignClass(studiesGeneralStore.selectedStudy.uid, {
            value: creationMode.value,
          })
          .then(() => {
            currentDesignClass.value = creationMode.value
            loading.value = false
            stepper.value.currentStep += 1
            return
          })
          .catch((error) => {
            console.error(t('CohortsStepper.error_update_class'), error)
            loading.value = false
          })
      }
      loading.value = false
      return
    } else if (
      currentDesignClass.value === cohortConstants.FULL &&
      creationMode.value !== cohortConstants.FULL
    ) {
      if (
        await confirm.value.open(
          t('CohortsStepper.change_class_warning_2'),
          options
        )
      ) {
        cohortsApi
          .changeStudyDesignClass(studiesGeneralStore.selectedStudy.uid, {
            value: creationMode.value,
          })
          .then(() => {
            currentDesignClass.value = creationMode.value
            loading.value = false
            stepper.value.currentStep += 1
            return
          })
          .catch((error) => {
            console.error(t('CohortsStepper.error_update_class'), error)
            loading.value = false
          })
      }
    }
    loading.value = false
    return
  } else {
    cohortsApi
      .setStudyDesignClass(studiesGeneralStore.selectedStudy.uid, {
        value: creationMode.value,
      })
      .then(() => {
        currentDesignClass.value = creationMode.value
        loading.value = false
        stepper.value.currentStep += 1
        return
      })
      .catch((error) => {
        console.error(t('CohortsStepper.error_update_class'), error)
        loading.value = false
      })
  }
}

function saveArms(close = false) {
  const payload = []
  arms.value.forEach((arm) => {
    payload.push({ method: arm.arm_uid ? 'PATCH' : 'POST', content: arm })
  })
  cohortsApi
    .armsBatchActions(studiesGeneralStore.selectedStudy.uid, payload)
    .then((resp) => {
      loading.value = false
      if (close) {
        stepper.value.close()
        return
      }
      arms.value = resp.data.map((arm) => arm.content)
      arms.value.forEach((arm) => (arm.arm_type_uid = arm.arm_type.term_uid))
      stepper.value.currentStep += 1
      return
    })
    .catch((error) => {
      console.error(t('CohortsStepper.error_update_arms'), error)
      loading.value = false
    })
}
function saveSourceVariable() {
  if (sourceVariable.value.start_date) {
    cohortsApi.editSourceVariable(
      studiesGeneralStore.selectedStudy.uid,
      sourceVariable.value
    )
  } else if (!_isEmpty(sourceVariable.value)) {
    cohortsApi.setSourceVariable(
      studiesGeneralStore.selectedStudy.uid,
      sourceVariable.value
    )
  }
}
async function saveCohorts(close = false) {
  const payload = []
  cohorts.value.forEach((cohort) => {
    payload.push({
      method: cohort.cohort_uid ? 'PATCH' : 'POST',
      content: cohort,
    })
  })
  cohortsApi
    .cohortsBatchActions(studiesGeneralStore.selectedStudy.uid, payload)
    .then((resp) => {
      loading.value = false
      if (close) {
        stepper.value.close()
        return
      }
      cohorts.value = resp.data.map((cohort) => cohort.content)
      cohorts.value.forEach((cohort) => {
        if (!cohort.branch_arm_roots) {
          cohort.branch_arm_roots = []
          arms.value.forEach(() => {
            cohort.branch_arm_roots.push({ number_of_subjects: 0 })
          })
        }
      })
      getBranches()
      stepper.value.currentStep += 1
    })
    .catch((error) => {
      console.error(t('CohortsStepper.error_update_cohorts'), error)
      loading.value = false
    })
}
function saveBranches() {
  loading.value = true
  const payload = []
  branches.value.forEach((arm) => {
    arm.study_cohorts.forEach((cohort) => {
      if (cohort.study_branch_arms[0].number_of_subjects > 0) {
        payload.push({
          method: cohort.study_branch_arms[0].branch_arm_uid ? 'PATCH' : 'POST',
          content: cohort.study_branch_arms[0],
        })
      } else if (
        cohort.study_branch_arms[0].branch_arm_uid &&
        !cohort.study_branch_arms[0].number_of_subjects
      ) {
        payload.push({
          method: 'DELETE',
          content: {
            branch_arm_uid: cohort.study_branch_arms[0].branch_arm_uid,
          },
        })
      }
    })
  })
  cohortsApi
    .branchesBatchActions(studiesGeneralStore.selectedStudy.uid, payload)
    .then(() => {
      loading.value = false
      stepper.value.close()
      return
    })
    .catch((error) => {
      console.error(t('CohortsStepper.error_update_branches'), error)
      loading.value = false
    })
}
function copyBranches() {
  try {
    let numbersArray = []
    branches.value.forEach((arm) => {
      numbersArray.push(
        arm.study_cohorts[0].study_branch_arms[0].number_of_subjects
      )
    })
    branches.value.forEach((arm, index) => {
      arm.study_cohorts.forEach((cohort) => {
        arm.number_of_subjects = numbersArray[index] * cohorts.value.length
        cohort.study_branch_arms[0].number_of_subjects = numbersArray[index]
      })
    })
    const numbersCount = numbersArray.reduce((acc, curr) => acc + curr, 0)
    cohorts.value.forEach((cohort) => {
      cohort.number_of_subjects = numbersCount
    })
    totalParticipants.value = numbersCount * cohorts.value.length
  } catch (error) {
    console.error(error)
  }
}
function cancel() {
  stepper.value.cancel()
}
function close() {
  emit('close')
}
async function saveAndClose() {
  if (!(await stepper.value.validateStepObserver(stepper.value.currentStep))) {
    return
  }
  loading.value = true
  if (stepper.value.currentStep === 2) {
    saveArms(true)
  } else if (stepper.value.currentStep === 3) {
    saveSourceVariable()
    saveCohorts(true)
  } else if (stepper.value.currentStep === 4) {
    saveBranches()
  }
}
function previousStep() {
  if (stepper.value.currentStep === 2) {
    cohortsApi
      .checkDesignClassEditable(studiesGeneralStore.selectedStudy.uid)
      .then((resp) => {
        editableDesignClass.value = !resp.data
      })
  }
  stepper.value.currentStep -= 1
}
function createBranchesMatrix(matrix) {
  matrix.forEach((arm) => {
    totalParticipants.value += arm.number_of_subjects
    const armUid = arm.uid
    arm.study_cohorts.forEach((cohort) => {
      const cohortUid = cohort.uid
      if (cohort.study_branch_arms[0]) {
        cohort.study_branch_arms[0].arm_uid = armUid
        cohort.study_branch_arms[0].study_cohort_uid = cohortUid
        cohort.study_branch_arms[0].branch_arm_uid =
          cohort.study_branch_arms[0].uid
        delete cohort.study_branch_arms[0].uid
      } else {
        cohort.study_branch_arms[0] = {
          name: `${arm.name} ${cohort.name}`,
          number_of_subjects: 0,
          short_name: `${arm.short_name} ${cohort.short_name}`,
          code: null,
          randomization_group: null,
          arm_uid: arm.uid,
          study_cohort_uid: cohort.uid,
        }
      }
    })
  })
  branches.value = matrix
}
function getObserver(step) {
  if (step === 2) {
    return armsForm.value
  } else if (step === 3) {
    return cohortsForm.value
  } else if (step === 4) {
    return linkingForm.value
  }
}

async function getArms() {
  const params = {
    study_uid: studiesGeneralStore.selectedStudy.uid,
  }
  await armsApi
    .getAllForStudy(studiesGeneralStore.selectedStudy.uid, { params })
    .then((resp) => {
      if (resp.data.items.length === 0) {
        return
      }
      arms.value = resp.data.items
      arms.value.forEach((arm) => (arm.arm_type_uid = arm.arm_type.term_uid))
    })
}

async function getCohorts() {
  const params = {
    study_uid: studiesGeneralStore.selectedStudy.uid,
  }
  await armsApi
    .getAllCohorts(studiesGeneralStore.selectedStudy.uid, params)
    .then((resp) => {
      if (resp.data.items.length === 0) {
        return
      }
      cohorts.value = resp.data.items
    })
}

function getBranches() {
  cohortsApi
    .getStudyStructure(studiesGeneralStore.selectedStudy.uid)
    .then((resp) => {
      createBranchesMatrix(resp.data)
    })
}

async function removeArm(arm, index) {
  if (arm.arm_uid) {
    const options = {
      type: 'error',
      cancelLabel: t('CohortsStepper.keep_arm'),
      agreeLabel: t('CohortsStepper.remove_arm'),
    }
    if (
      await confirm.value.open(t('CohortsStepper.remove_arm_warning'), options)
    ) {
      cohortsApi
        .removeArm(studiesGeneralStore.selectedStudy.uid, arm.arm_uid)
        .then(() => {
          arms.value.splice(index, 1)
        })
    }
  } else {
    arms.value.splice(index, 1)
  }
}
async function removeCohort(cohort, index) {
  if (cohort.cohort_uid) {
    const options = {
      type: 'error',
      cancelLabel: t('CohortsStepper.keep_cohort'),
      agreeLabel: t('CohortsStepper.remove_cohort'),
    }
    if (
      await confirm.value.open(
        t('CohortsStepper.remove_cohort_warning'),
        options
      )
    ) {
      cohortsApi
        .removeCohort(
          studiesGeneralStore.selectedStudy.uid,
          cohort.cohort_uid,
          true
        )
        .then(() => {
          cohorts.value.splice(index, 1)
        })
    }
  } else {
    cohorts.value.splice(index, 1)
  }
}
function openBranchEditForm(branch) {
  editBranch.value = branch
  showBranchEditForm.value = true
}
function closeBranchEditForm() {
  editBranch.value = null
  showBranchEditForm.value = false
}
function applyBranchChanges(updatedBranch) {
  branches.value.forEach((arm) => {
    arm.study_cohorts.forEach((cohort) => {
      if (
        cohort.study_branch_arms[0].arm_uid === updatedBranch.arm_uid &&
        cohort.study_branch_arms[0].study_cohort_uid ===
          updatedBranch.study_cohort_uid
      ) {
        cohort.study_branch_arms[0] = updatedBranch
      }
    })
  })
  closeBranchEditForm()
}
</script>
<style scoped>
.label {
  font-weight: 700;
  font-size: 18px;
  line-height: 24px;
  letter-spacing: -0.02em;
  color: var(--semantic-system-brand, #001965);
  min-height: 24px;
}
.tile {
  padding: 20px;
  display: inline-flex;
}
#v-field__field > label.v-label.v-field-label {
  font-size: 10px !important;
}
</style>
