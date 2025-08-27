<template>
  <div>
    <NNTable
      ref="table"
      :headers="headers"
      :items="templates"
      item-value="uid"
      sort-desc
      :items-length="total"
      column-data-resource="concepts/odms/study-events"
      export-data-url="concepts/odms/study-events"
      export-object-label="CRFTemplates"
      @filter="getTemplates"
    >
      <template #actions="">
        <v-btn
          class="ml-2"
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          :title="$t('CrfTemplates.add_template')"
          data-cy="add-crf-template"
          :disabled="!checkPermission($roles.LIBRARY_WRITE)"
          icon="mdi-plus"
          @click.stop="openForm()"
        />
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
      <template #[`item.status`]="{ item }">
        <StatusChip :status="item.status" />
      </template>
      <template #[`item.relations`]="{ item }">
        <v-btn
          size="x-small"
          color="primary"
          icon="mdi-family-tree"
          @click="openRelationsTree(item)"
        />
      </template>
    </NNTable>
    <CrfTemplateForm
      :open="showForm"
      :selected-template="selectedTemplate"
      :read-only-prop="
        selectedTemplate && selectedTemplate.status === statuses.FINAL
      "
      @close="closeForm"
    />
    <v-dialog
      v-model="showTemplateHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeTemplateHistory"
    >
      <HistoryTable
        :title="templateHistoryTitle"
        :headers="headers"
        :items="templateHistoryItems"
        @close="closeTemplateHistory"
      />
    </v-dialog>
  </div>
</template>

<script>
import NNTable from '@/components/tools/NNTable.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import crfs from '@/api/crfs'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import CrfTemplateForm from '@/components/library/crfs/CrfTemplateForm.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import filteringParameters from '@/utils/filteringParameters'
import crfTypes from '@/constants/crfTypes'
import statuses from '@/constants/statuses'
import { useAccessGuard } from '@/composables/accessGuard'
import { useCrfsStore } from '@/stores/crfs'
import { computed } from 'vue'

export default {
  components: {
    NNTable,
    ActionsMenu,
    HistoryTable,
    CrfTemplateForm,
    StatusChip,
  },
  props: {
    elementProp: {
      type: Object,
      default: null,
    },
  },
  setup() {
    const crfsStore = useCrfsStore()

    return {
      fetchTemplates: crfsStore.fetchTemplates,
      total: computed(() => crfsStore.totalTemplates),
      templates: computed(() => crfsStore.templates),
      ...useAccessGuard(),
    }
  },
  data() {
    return {
      actions: [
        {
          label: this.$t('_global.approve'),
          icon: 'mdi-check-decagram',
          iconColor: 'success',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'approve'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.approveTemplate,
        },
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'edit'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.edit,
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete-outline',
          iconColor: 'error',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'delete'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.deleteTemplate,
        },
        {
          label: this.$t('_global.new_version'),
          icon: 'mdi-plus-circle-outline',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'new_version'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.newTemplateVersion,
        },
        {
          label: this.$t('_global.inactivate'),
          icon: 'mdi-close-octagon-outline',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'inactivate'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.inactivateTemplate,
        },
        {
          label: this.$t('_global.reactivate'),
          icon: 'mdi-undo-variant',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'reactivate'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.reactivateTemplate,
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openTemplateHistory,
        },
      ],
      headers: [
        { title: '', key: 'actions', width: '1%' },
        { title: this.$t('CrfTemplates.oid'), key: 'oid' },
        { title: this.$t('_global.name'), key: 'name' },
        {
          title: this.$t('CrfTemplates.effective_date'),
          key: 'effective_date',
        },
        { title: this.$t('CrfTemplates.retired_date'), key: 'retired_date' },
        { title: this.$t('_global.version'), key: 'version' },
        { title: this.$t('_global.status'), key: 'status' },
      ],
      showForm: false,
      showTemplateHistory: false,
      selectedTemplate: null,
      filters: '',
      templateHistoryItems: [],
    }
  },
  computed: {
    templateHistoryTitle() {
      if (this.selectedTemplate) {
        return this.$t('CrfTemplates.template_history_title', {
          templateUid: this.selectedTemplate.uid,
        })
      }
      return ''
    },
  },
  watch: {
    elementProp(value) {
      if (
        value.tab === 'templates' &&
        value.type === crfTypes.TEMPLATE &&
        value.uid
      ) {
        this.edit({ uid: value.uid })
      }
    },
  },
  created() {
    this.statuses = statuses
  },
  mounted() {
    if (
      this.elementProp.tab === 'templates' &&
      this.elementProp.type === crfTypes.TEMPLATE &&
      this.elementProp.uid
    ) {
      crfs.getTemplate(this.elementProp.uid).then((resp) => {
        this.edit(resp.data)
      })
    }
  },
  methods: {
    approveTemplate(item) {
      crfs.approve('study-events', item.uid).then(() => {
        this.$refs.table.filterTable()
      })
    },
    inactivateTemplate(item) {
      crfs.inactivate('study-events', item.uid).then(() => {
        this.$refs.table.filterTable()
      })
    },
    reactivateTemplate(item) {
      crfs.reactivate('study-events', item.uid).then(() => {
        this.$refs.table.filterTable()
      })
    },
    newTemplateVersion(item) {
      crfs.newVersion('study-events', item.uid).then(() => {
        this.$refs.table.filterTable()
      })
    },
    deleteTemplate(item) {
      crfs.delete('study-events', item.uid).then(() => {
        this.$refs.table.filterTable()
      })
    },
    edit(item) {
      crfs.getTemplate(item.uid).then((resp) => {
        this.selectedTemplate = resp.data
        this.showForm = true
      })
    },
    async openTemplateHistory(template) {
      this.selectedTemplate = template
      const resp = await crfs.getTemplateAuditTrail(template.uid)
      this.templateHistoryItems = resp.data
      this.showTemplateHistory = true
    },
    closeTemplateHistory() {
      this.showTemplateHistory = false
      this.selectedTemplate = null
    },
    openForm() {
      this.selectedTemplate = null
      this.showForm = true
    },
    closeForm() {
      this.selectedTemplate = null
      this.showForm = false
      this.$refs.table.filterTable()
    },
    getTemplates(filters, options, filtersUpdated) {
      if (filters) {
        this.filters = filters
      }
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      this.fetchTemplates(params)
    },
  },
}
</script>
