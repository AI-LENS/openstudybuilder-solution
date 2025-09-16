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
              v-model="form.arm_type_uid"
              :label="$t('StudyArmsForm.arm_type')"
              :items="armTypes"
              item-title="name.sponsor_preferred_name"
              item-value="term_uid"
              data-cy="arm-type"
              clearable
              density="compact"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.name"
              :label="$t('StudyArmsForm.arm_name')"
              data-cy="arm-name"
              :rules="[formRules.required, formRules.max(form.name, 200)]"
              clearable
              density="compact"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.short_name"
              :label="$t('StudyArmsForm.arm_short_name')"
              data-cy="arm-short-name"
              :rules="[formRules.required, formRules.max(form.short_name, 20)]"
              clearable
              density="compact"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.randomization_group"
              :label="$t('StudyArmsForm.randomisation_group')"
              data-cy="arm-randomisation-group"
              clearable
              density="compact"
              @blur="enableArmCode"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.code"
              :label="$t('StudyArmsForm.arm_code')"
              data-cy="arm-code"
              :rules="[formRules.max(form.code, 20)]"
              clearable
              density="compact"
              :disabled="!armCodeEnable && !isEdit()"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.number_of_subjects"
              :label="$t('StudyArmsForm.planned_number')"
              data-cy="arm-planned-number-of-subjects"
              :rules="[formRules.min_value(form.number_of_subjects, 1)]"
              type="number"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.description"
              :label="$t('StudyArmsForm.description')"
              data-cy="arm-description"
              clearable
              density="compact"
            />
          </v-col>
        </v-row>
        <v-text-field
          v-if="isEdit()"
          v-model="branches"
          :label="$t('StudyArmsForm.connected_branches')"
          data-cy="arm-connected-branches"
          clearable
          readonly
          density="compact"
        />
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script>
import arms from '@/api/arms'
import codelists from '@/api/controlledTerminology/terms'
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
    editedArm: {
      type: Object,
      default: undefined,
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
      helpItems: [
        'StudyArmsForm.arm_type',
        'StudyArmsForm.arm_name',
        'StudyArmsForm.arm_short_name',
        'StudyArmsForm.randomisation_group',
        'StudyArmsForm.arm_code',
        'StudyArmsForm.planned_number',
        'StudyArmsForm.description',
      ],
      armTypes: [],
      editMode: false,
      armCodeEnable: false,
      branches: [],
      codeRules: '',
    }
  },
  computed: {
    title() {
      return Object.keys(this.editedArm).length !== 0
        ? this.$t('StudyArmsForm.edit_arm')
        : this.$t('StudyArmsForm.add_arm')
    },
  },
  watch: {
    editedArm(value) {
      if (Object.keys(value).length !== 0) {
        arms.getStudyArm(this.selectedStudy.uid, value.arm_uid).then((resp) => {
          this.form = JSON.parse(JSON.stringify(resp.data))
          if (this.form.arm_connected_branch_arms) {
            this.branches = this.form.arm_connected_branch_arms.map(
              (el) => el.name
            )
            delete this.form.arm_connected_branch_arms
          }
          this.form.arm_type_uid = value.arm_type.term_uid
          this.formStore.save(this.form)
        })
      }
    },
  },
  mounted() {
    codelists.getByCodelist('armTypes').then((resp) => {
      this.armTypes = resp.data.items
    })
    if (Object.keys(this.editedArm).length !== 0) {
      this.form = JSON.parse(JSON.stringify(this.editedArm))
      if (this.form.arm_connected_branch_arms) {
        this.branches = this.form.arm_connected_branch_arms.map((el) => el.name)
        delete this.form.arm_connected_branch_arms
      }
      this.form.arm_type_uid = this.editedArm.arm_type.term_uid
      this.formStore.save(this.form)
    }
  },
  methods: {
    enableArmCode() {
      if (!this.armCodeEnable) {
        this.form.code = this.form.randomization_group
        this.armCodeEnable = true
      }
    },
    isEdit() {
      return Object.keys(this.editedArm).length !== 0
    },
    async submit() {
      if (Object.keys(this.editedArm).length !== 0) {
        this.edit()
      } else {
        this.create()
      }
    },
    create() {
      arms.create(this.selectedStudy.uid, this.form).then(
        () => {
          this.eventBusEmit('notification', {
            msg: this.$t('StudyArmsForm.arm_created'),
          })
          this.close()
        },
        () => {
          this.$refs.form.working = false
        }
      )
    },
    edit() {
      arms.edit(this.selectedStudy.uid, this.form, this.editedArm.arm_uid).then(
        () => {
          this.eventBusEmit('notification', {
            msg: this.$t('StudyArmsForm.arm_updated'),
          })
          this.close()
        },
        () => {
          this.$refs.form.working = false
        }
      )
    },
    close() {
      this.form = {}
      this.armCodeEnable = false
      this.$refs.observer.reset()
      this.$emit('close')
      this.formStore.reset()
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
  },
}
</script>
