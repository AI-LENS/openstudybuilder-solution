<template>
  <SimpleFormDialog
    ref="form"
    :title="title"
    :help-items="helpItems"
    :help-text="$t('_help.StudyDefineForm.general')"
    :open="open"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.code"
              :label="$t('StudyElements.el_type')"
              :items="elementTypes"
              item-title="type_name"
              item-value="type"
              clearable
              density="compact"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.element_subtype_uid"
              :label="$t('StudyElements.el_sub_type')"
              item-title="subtype_name"
              item-value="subtype"
              :items="elementSubTypes"
              :rules="[formRules.required]"
              clearable
              class="required"
              density="compact"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.name"
              :label="$t('StudyElements.el_name')"
              :rules="[formRules.required, formRules.max(form.name, 200)]"
              clearable
              class="required"
              density="compact"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.short_name"
              :label="$t('StudyElements.el_short_name')"
              :rules="[formRules.required, formRules.max(form.short_name, 20)]"
              clearable
              class="required"
              density="compact"
            />
          </v-col>
        </v-row>
        <div class="label ml-1">
          {{ $t('StudyElements.planned_duration_time') }}
          <DurationField v-model="form.planned_duration" />
        </div>
        <v-row>
          <v-col>
            <v-textarea
              id="startRule"
              v-model="form.start_rule"
              :label="$t('StudyElements.el_start_rule')"
              rows="1"
              auto-grow
              density="compact"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-textarea
              id="endRule"
              v-model="form.end_rule"
              :label="$t('StudyElements.el_end_rule')"
              rows="1"
              auto-grow
              density="compact"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.description"
              :label="$t('_global.description')"
              clearable
              density="compact"
            />
          </v-col>
        </v-row>
        <div class="mt-4">
          <label class="v-label">{{ $t('StudyEpochForm.color') }}</label>
          <v-color-picker
            v-model="colorHash"
            data-cy="epoch-color-picker"
            clearable
            show-swatches
            hide-canvas
            hide-sliders
            swatches-max-height="300px"
          />
        </div>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script>
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import arms from '@/api/arms'
import DurationField from '@/components/tools/DurationField.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useFormStore } from '@/stores/form'

export default {
  components: {
    SimpleFormDialog,
    DurationField,
  },
  inject: ['eventBusEmit', 'formRules'],
  props: {
    metadata: {
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
      form: {
        planned_duration: {},
      },
      helpItems: [
        'StudyElements.el_name',
        'StudyElements.el_short_name',
        'StudyElements.el_sub_type',
        'StudyElements.el_type',
      ],
      data: [],
      allowedConfigs: [],
      colorHash: null,
    }
  },
  computed: {
    title() {
      return this.metadata
        ? this.$t('StudyElements.edit_el')
        : this.$t('StudyElements.add_element')
    },
    elementTypes() {
      if (!this.form.element_subtype_uid) {
        return [
          ...new Map(this.allowedConfigs.map((v) => [v.type_name, v])).values(),
        ]
      } else {
        return this.allowedConfigs.filter(
          (element) => element.subtype === this.form.element_subtype_uid
        )
      }
    },
    elementSubTypes() {
      if (!this.form.code) {
        return this.allowedConfigs
      } else {
        return this.allowedConfigs.filter(
          (element) => element.type === this.form.code
        )
      }
    },
  },
  watch: {
    metadata(value) {
      if (value) {
        arms
          .getStudyElement(this.selectedStudy.uid, value.element_uid)
          .then((resp) => {
            this.form = resp.data
            if (this.form.element_colour) {
              this.colorHash = this.form.element_colour
            }
            if (!this.form.planned_duration) {
              this.form.planned_duration = {}
            }
            if (resp.data.element_subtype) {
              this.form.element_subtype_uid = resp.data.element_subtype.term_uid
            }
            this.formStore.save(this.form)
          })
      }
    },
  },
  mounted() {
    arms.getStudyElementsAllowedConfigs().then((resp) => {
      this.allowedConfigs = resp.data
    })
    if (this.metadata) {
      this.form = this.metadata
      if (this.form.element_colour) {
        this.colorHash = this.form.element_colour
      }
      if (!this.form.planned_duration) {
        this.form.planned_duration = {}
      }
      if (this.metadata.element_subtype) {
        this.form.element_subtype_uid = this.metadata.element_subtype.term_uid
      }
      this.formStore.save(this.form)
    }
  },
  methods: {
    close() {
      // Reset form data
      this.form = {
        planned_duration: {},
      }
      this.$emit('close')
      this.colorHash = null

      // Reset form validation and working state
      if (this.$refs.observer) {
        this.$refs.observer.reset()
      }
      if (this.$refs.form) {
        this.$refs.form.working = false
      }

      this.formStore.reset()
    },
    async cancel() {
      if (this.formStore.isEmpty || this.formStore.isEqual(this.form)) {
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
          this.data = {}
          this.data = this.metadata
          this.close()
        }
      }
    },
    async submit() {
      if (!this.form.planned_duration.duration_value) {
        this.form.planned_duration = null
      }
      if (this.colorHash) {
        this.form.element_colour =
          this.colorHash.hexa !== undefined
            ? this.colorHash.hexa
            : this.colorHash
      } else {
        this.form.element_colour = '#BDBDBD'
      }
      if (this.metadata) {
        arms
          .editStudyElement(
            this.selectedStudy.uid,
            this.metadata.element_uid,
            this.form
          )
          .then(
            () => {
              this.eventBusEmit('notification', {
                msg: this.$t('StudyElements.el_edited'),
              })
              this.$refs.form.working = false
              this.close()
            },
            () => {
              this.$refs.form.working = false
            }
          )
      } else {
        arms.addStudyElement(this.selectedStudy.uid, this.form).then(
          () => {
            this.eventBusEmit('notification', {
              msg: this.$t('StudyElements.el_created'),
            })
            this.$refs.form.working = false
            this.close()
          },
          () => {
            this.$refs.form.working = false
          }
        )
      }
    },
  },
}
</script>
<style lang="css" scoped>
.label {
  font-weight: 500;
  font-size: 14px;
  line-height: 24px;
  letter-spacing: -0.02em;
  min-height: 24px;
}
</style>
