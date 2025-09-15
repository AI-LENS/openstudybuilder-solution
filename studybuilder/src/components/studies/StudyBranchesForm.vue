<template>
  <SimpleFormDialog
    ref="form"
    :title="title"
    :help-items="helpItems"
    :open="open"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col cols="12">
            <v-autocomplete
              v-model="form.arm_uid"
              :label="$t('StudyBranchArms.study_arm')"
              data-cy="study-arm"
              :items="arms"
              item-title="name"
              item-value="arm_uid"
              :rules="[formRules.required]"
              clearable
              :disabled="Object.keys(editedBranchArm).length !== 0"
              class="required"
              density="compact"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.name"
              :label="$t('StudyBranchArms.branch_arm_name')"
              data-cy="study-branch-arm-name"
              :rules="[formRules.required, formRules.max(form.name, 200)]"
              clearable
              class="required"
              density="compact"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.short_name"
              :label="$t('StudyBranchArms.branch_arm_short_name')"
              data-cy="study-branch-arm-short-name"
              :rules="[formRules.required, formRules.max(form.short_name, 20)]"
              clearable
              class="required"
              density="compact"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.randomization_group"
              :label="$t('StudyBranchArms.randomisation_group')"
              data-cy="study-branch-arm-randomisation-group"
              clearable
              :rules="[formRules.max(form.randomization_group, 20)]"
              density="compact"
              @blur="enableBranchCode"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.code"
              :label="$t('StudyBranchArms.code')"
              data-cy="study-branch-arm-code"
              :rules="codeRules"
              clearable
              :disabled="!branchCodeEnable && !isEdit()"
              density="compact"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.number_of_subjects"
              :disabled="!form.arm_uid"
              :label="$t('StudyBranchArms.nuber_of_subjects')"
              data-cy="study-branch-arm-planned-number-of-subjects"
              :rules="[
                formRules.min_value(form.number_of_subjects, 1),
                numberOfSubjectsMaxValueRule(
                  form.number_of_subjects,
                  findMaxNuberOfSubjects()
                ),
              ]"
              type="number"
              clearable
              density="compact"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.description"
              :label="$t('_global.description')"
              data-cy="study-branch-arm-description"
              clearable
              density="compact"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script>
import arms from '@/api/arms'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import _isEqual from 'lodash/isEqual'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useFormStore } from '@/stores/form'

export default {
  components: {
    SimpleFormDialog,
  },
  inject: ['eventBusEmit', 'formRules'],
  props: {
    editedBranchArm: {
      type: Object,
      default: undefined,
    },
    arms: {
      type: Array,
      default: () => [],
    },
    open: Boolean,
  },
  emits: ['close'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    const formStore = useFormStore()
    return {
      selectedStudy: studiesGeneralStore.selectedStudy,
      formStore,
    }
  },
  data() {
    return {
      form: {},
      helpItems: [],
      editMode: false,
      selectedArm: {},
      branchCodeEnable: false,
      codeRules: [],
    }
  },
  computed: {
    title() {
      return Object.keys(this.editedBranchArm).length !== 0
        ? this.$t('StudyBranchArms.edit_branch')
        : this.$t('StudyBranchArms.add_branch')
    },
  },
  watch: {
    editedBranchArm(value) {
      if (Object.keys(value).length !== 0) {
        arms
          .getStudyBranchArm(this.selectedStudy.uid, value.branch_arm_uid)
          .then((resp) => {
            this.form = JSON.parse(JSON.stringify(resp.data))
            this.form.arm_uid = resp.data.arm_root.arm_uid
            this.formStore.save(this.form)
          })
      }
    },
  },
  mounted() {
    if (Object.keys(this.editedBranchArm).length !== 0) {
      this.form = JSON.parse(JSON.stringify(this.editedBranchArm))
      this.form.arm_uid = this.editedBranchArm.arm_root.arm_uid
      this.formStore.save(this.form)
    }
  },
  methods: {
    // This rule is same as max_value generic rule but with custom message
    numberOfSubjectsMaxValueRule(value, max) {
      let result = true
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          result =
            value.length > 0 &&
            value.every((val) => this.formRules.max_value(val, max))
        } else {
          result = Number(value) <= Number(max)
        }
      }
      return result || this.$t('StudyBranchArms.number_of_subjects_exceeds')
    },
    enableBranchCode() {
      if (!this.branchCodeEnable) {
        this.form.code = this.form.randomization_group
        this.branchCodeEnable = true
        this.codeRules = [
          (v) =>
            (v && v.length <= 20) ||
            this.$t('_errors.max_length_reached', { length: '20' }),
        ]
      }
    },
    isEdit() {
      return Object.keys(this.editedBranchArm).length !== 0
    },
    async submit() {
      if (Object.keys(this.editedBranchArm).length !== 0) {
        this.edit()
      } else {
        this.create()
      }
    },
    async create() {
      let armNumberOfSubjects = 0
      ;(
        await arms.getAllBranchesForArm(
          this.selectedStudy.uid,
          this.form.arm_uid
        )
      ).data.forEach((el) => {
        armNumberOfSubjects += el.number_of_subjects
      })
      if (
        this.selectedArm.number_of_subjects <
        parseInt(armNumberOfSubjects, 10) +
          parseInt(this.form.number_of_subjects, 10)
      ) {
        const options = {
          type: 'warning',
          cancelLabel: this.$t('_global.cancel'),
          agreeLabel: this.$t('_global.save_anyway'),
        }
        if (
          await this.$refs.form.confirm(
            this.$t('StudyBranchArms.subjects_exceeded'),
            options
          )
        ) {
          arms.createBranchArm(this.selectedStudy.uid, this.form).then(() => {
            this.eventBusEmit('notification', {
              msg: this.$t('StudyBranchArms.branch_created'),
            })
            this.close()
          })
        }
      } else {
        arms.createBranchArm(this.selectedStudy.uid, this.form).then(() => {
          this.eventBusEmit('notification', {
            msg: this.$t('StudyBranchArms.branch_created'),
          })
          this.close()
        })
      }
      this.$refs.form.working = false
    },
    async edit() {
      let armNumberOfSubjects = 0
      ;(
        await arms.getAllBranchesForArm(
          this.selectedStudy.uid,
          this.form.arm_uid
        )
      ).data.forEach((el) => {
        armNumberOfSubjects +=
          el.branch_arm_uid === this.editedBranchArm.branch_arm_uid
            ? 0
            : el.number_of_subjects
      })
      if (
        this.selectedArm.number_of_subjects <
        parseInt(armNumberOfSubjects, 10) +
          parseInt(this.form.number_of_subjects, 10)
      ) {
        const options = {
          type: 'warning',
          cancelLabel: this.$t('_global.cancel'),
          agreeLabel: this.$t('_global.save_anyway'),
        }
        if (
          await this.$refs.form.confirm(
            this.$t('StudyBranchArms.subjects_exceeded'),
            options
          )
        ) {
          arms
            .editBranchArm(
              this.selectedStudy.uid,
              this.editedBranchArm.branch_arm_uid,
              this.form
            )
            .then(() => {
              this.eventBusEmit('notification', {
                msg: this.$t('StudyBranchArms.branch_updated'),
              })
              this.close()
            })
        }
      } else {
        arms
          .editBranchArm(
            this.selectedStudy.uid,
            this.editedBranchArm.branch_arm_uid,
            this.form
          )
          .then(() => {
            this.eventBusEmit('notification', {
              msg: this.$t('StudyBranchArms.branch_updated'),
            })
            this.close()
          })
      }
      this.$refs.form.working = false
    },
    close() {
      this.form = {}
      this.formStore.reset()
      this.branchCodeEnable = false
      this.$refs.observer.reset()
      this.$emit('close')
    },
    async cancel() {
      if (
        this.storedForm === '' ||
        _isEqual(this.storedForm, JSON.stringify(this.form))
      ) {
        this.close()
      } else {
        const options = {
          type: 'warning',
          cancelLabel: this.$t('_global.cancel'),
          agreeLabel: this.$t('_global.continue'),
        }
        if (
          await this.$refs.form.confirm(
            this.$t('_global.cancel_changes'),
            options
          )
        ) {
          this.close()
        }
      }
    },
    findMaxNuberOfSubjects() {
      this.selectedArm = this.arms.find((e) => e.arm_uid === this.form.arm_uid)
      return this.selectedArm ? this.selectedArm.number_of_subjects : 0
    },
  },
}
</script>
