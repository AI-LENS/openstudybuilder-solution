<template>
  <div>
    <NNTable
      ref="table"
      :headers="headers"
      :items="items"
      item-value="uid"
      :items-length="total"
      column-data-resource="concepts/odms/items"
      export-data-url="concepts/odms/items"
      export-object-label="CRFItems"
      @filter="getItems"
    >
      <template #actions="">
        <v-btn
          class="ml-2"
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          :title="$t('CRFItems.add_title')"
          data-cy="add-crf-item"
          :disabled="!checkPermission($roles.LIBRARY_WRITE)"
          icon="mdi-plus"
          @click.stop="showForm = true"
        />
      </template>
      <template #[`item.name`]="{ item }">
        <v-tooltip bottom>
          <template #activator="{ props }">
            <div v-bind="props">
              <NNParameterHighlighter
                :name="
                  item.name.length > 40
                    ? item.name.substring(0, 40) + '...'
                    : item.name
                "
                :show-prefix-and-postfix="false"
              />
            </div>
          </template>
          <span>{{ item.name }}</span>
        </v-tooltip>
      </template>
      <template #[`item.description`]="{ item }">
        <v-tooltip bottom>
          <template #activator="{ props }">
            <div
              v-bind="props"
              v-html="sanitizeHTMLHandler(getDescription(item, true))"
            />
          </template>
          <span>{{ getDescription(item, false) }}</span>
        </v-tooltip>
      </template>
      <template #[`item.notes`]="{ item }">
        <v-tooltip bottom>
          <template #activator="{ props }">
            <div
              v-bind="props"
              v-html="sanitizeHTMLHandler(getNotes(item, true))"
            />
          </template>
          <span>{{ getNotes(item, false) }}</span>
        </v-tooltip>
      </template>
      <template #[`item.activities`]="{ item }">
        <v-tooltip v-if="item.activity" bottom>
          <template #activator="{ props }">
            <div v-bind="props">
              {{
                item.activity.name.length > 40
                  ? item.activity.name.substring(0, 40) + '...'
                  : item.activity.name
              }}
            </div>
          </template>
          <span>{{ item.activity.name }}</span>
        </v-tooltip>
      </template>
      <template #[`item.status`]="{ item }">
        <StatusChip :status="item.status" />
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
    </NNTable>
    <v-dialog v-model="showForm" persistent content-class="fullscreen-dialog">
      <CrfItemForm
        :selected-item="selectedItem"
        :read-only-prop="
          selectedItem && selectedItem.status === constants.FINAL
        "
        @close="closeForm"
        @new-version="newVersion"
        @approve="approve"
      />
    </v-dialog>
    <v-dialog
      v-model="showItemHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeItemHistory"
    >
      <HistoryTable
        :title="itemHistoryTitle"
        :headers="headers"
        :items="itemHistoryItems"
        @close="closeItemHistory"
      />
    </v-dialog>
    <CrfActivitiesModelsLinkForm
      :open="linkForm"
      :item-to-link="selectedItem"
      item-type="item"
      @close="closeLinkForm"
    />
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  </div>
</template>

<script>
import NNTable from '@/components/tools/NNTable.vue'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import crfs from '@/api/crfs'
import CrfItemForm from '@/components/library/crfs/CrfItemForm.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import CrfActivitiesModelsLinkForm from '@/components/library/crfs/CrfActivitiesModelsLinkForm.vue'
import constants from '@/constants/statuses'
import filteringParameters from '@/utils/filteringParameters'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import crfTypes from '@/constants/crfTypes'
import parameters from '@/constants/parameters'
import dataFormating from '@/utils/dataFormating'
import { useAccessGuard } from '@/composables/accessGuard'
import { useCrfsStore } from '@/stores/crfs'
import { computed } from 'vue'
import { sanitizeHTML } from '@/utils/sanitize'

export default {
  components: {
    NNTable,
    NNParameterHighlighter,
    StatusChip,
    ActionsMenu,
    CrfItemForm,
    HistoryTable,
    CrfActivitiesModelsLinkForm,
    ConfirmDialog,
  },
  props: {
    elementProp: {
      type: Object,
      default: null,
    },
  },
  emits: ['updateItem'],
  setup() {
    const crfsStore = useCrfsStore()

    return {
      fetchItems: crfsStore.fetchItems,
      total: computed(() => crfsStore.totalItems),
      items: computed(() => crfsStore.items),
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
          click: this.approve,
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
          label: this.$t('_global.view'),
          icon: 'mdi-eye-outline',
          iconColor: 'primary',
          condition: (item) => item.status === constants.FINAL,
          click: this.view,
        },
        {
          label: this.$t('_global.new_version'),
          icon: 'mdi-plus-circle-outline',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'new_version'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.newVersion,
        },
        {
          label: this.$t('_global.inactivate'),
          icon: 'mdi-close-octagon-outline',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'inactivate'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.inactivate,
        },
        {
          label: this.$t('_global.reactivate'),
          icon: 'mdi-undo-variant',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'reactivate'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.reactivate,
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete-outline',
          iconColor: 'error',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'delete'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.delete,
        },
        {
          label: this.$t('CrfLinikingForm.link_activities'),
          icon: 'mdi-plus',
          iconColor: 'primary',
          condition: (item) => item.status === constants.DRAFT,
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.openLinkForm,
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openItemHistory,
        },
      ],
      headers: [
        { title: '', key: 'actions', width: '1%' },
        { title: this.$t('CRFItems.oid'), key: 'oid' },
        { title: this.$t('_global.name'), key: 'name' },
        {
          title: this.$t('_global.description'),
          key: 'description',
          filteringName: 'descriptions.description',
        },
        {
          title: this.$t('CRFItems.impl_notes'),
          key: 'notes',
          filteringName: 'descriptions.sponsor_instruction',
        },
        { title: this.$t('CRFItems.type'), key: 'datatype', width: '1%' },
        { title: this.$t('CRFItems.length'), key: 'length', width: '1%' },
        { title: this.$t('CRFItems.sds_name'), key: 'sds_var_name' },
        { title: this.$t('_global.links'), key: 'activity.name' },
        { title: this.$t('_global.version'), key: 'version', width: '1%' },
        { title: this.$t('_global.status'), key: 'status', width: '1%' },
      ],
      showForm: false,
      filters: '',
      selectedItem: null,
      showItemHistory: false,
      linkForm: false,
      itemHistoryItems: [],
    }
  },
  computed: {
    itemHistoryTitle() {
      if (this.selectedItem) {
        return this.$t('CRFItems.item_history_title', {
          itemUid: this.selectedItem.uid,
        })
      }
      return ''
    },
  },
  watch: {
    elementProp(value) {
      if (value.tab === 'items' && value.type === crfTypes.ITEM && value.uid) {
        this.edit(value)
      }
    },
  },
  mounted() {
    if (
      this.elementProp.tab === 'items' &&
      this.elementProp.type === crfTypes.ITEM &&
      this.elementProp.uid
    ) {
      this.edit(this.elementProp)
    }
  },
  created() {
    this.constants = constants
  },
  methods: {
    sanitizeHTMLHandler(html) {
      return sanitizeHTML(html)
    },
    getDescription(item, short) {
      const engDesc = item.descriptions.find(
        (el) => el.language === parameters.ENG
      )
      if (engDesc && engDesc.description) {
        return short
          ? engDesc.description.length > 40
            ? engDesc.description.substring(0, 40) + '...'
            : engDesc.description
          : engDesc.description
      }
      return ''
    },
    getNotes(item, short) {
      const engDesc = item.descriptions.find(
        (el) => el.language === parameters.ENG
      )
      if (engDesc && engDesc.sponsor_instruction) {
        return short
          ? engDesc.sponsor_instruction.length > 40
            ? engDesc.sponsor_instruction.substring(0, 40) + '...'
            : engDesc.sponsor_instruction
          : engDesc.sponsor_instruction
      }
      return ''
    },
    openForm() {
      this.showForm = true
    },
    closeForm() {
      this.showForm = false
      this.selectedItem = null
      this.$refs.table.filterTable()
    },
    approve(item) {
      crfs.approve('items', item.uid).then((resp) => {
        this.$emit('updateItem', { type: crfTypes.ITEM, element: resp.data })
        this.$refs.table.filterTable()
      })
    },
    async delete(item) {
      let relationships = 0
      await crfs.getRelationships(item.uid, 'items').then((resp) => {
        if (resp.data.OdmItemGroup && resp.data.OdmItemGroup.length > 0) {
          relationships = resp.data.OdmItemGroup.length
        }
      })
      const options = {
        type: 'warning',
        cancelLabel: this.$t('_global.cancel'),
        agreeLabel: this.$t('_global.continue'),
      }
      if (
        relationships > 0 &&
        (await this.$refs.confirm.open(
          `${this.$t('CRFItems.delete_warning_1')} ${relationships} ${this.$t('CRFItems.delete_warning_2')}`,
          options
        ))
      ) {
        crfs.delete('items', item.uid).then(() => {
          this.$refs.table.filterTable()
        })
      } else if (relationships === 0) {
        crfs.delete('items', item.uid).then(() => {
          this.$refs.table.filterTable()
        })
      }
    },
    inactivate(item) {
      crfs.inactivate('items', item.uid).then((resp) => {
        this.$emit('updateItem', { type: crfTypes.ITEM, element: resp.data })
        this.$refs.table.filterTable()
      })
    },
    reactivate(item) {
      crfs.reactivate('items', item.uid).then((resp) => {
        this.$emit('updateItem', { type: crfTypes.ITEM, element: resp.data })
        this.$refs.table.filterTable()
      })
    },
    async newVersion(item) {
      let relationships = 0
      await crfs.getRelationships(item.uid, 'items').then((resp) => {
        if (resp.data.OdmItemGroup && resp.data.OdmItemGroup.length > 0) {
          relationships = resp.data.OdmItemGroup.length
        }
      })
      const options = {
        type: 'warning',
        cancelLabel: this.$t('_global.cancel'),
        agreeLabel: this.$t('_global.continue'),
      }
      if (
        relationships > 1 &&
        (await this.$refs.confirm.open(
          `${this.$t('CRFForms.new_version_warning')}`,
          options
        ))
      ) {
        crfs.newVersion('items', item.uid).then((resp) => {
          this.$emit('updateItem', { type: crfTypes.ITEM, element: resp.data })
          this.$refs.table.filterTable()
        })
      } else if (relationships <= 1) {
        crfs.newVersion('items', item.uid).then((resp) => {
          this.$emit('updateItem', { type: crfTypes.ITEM, element: resp.data })
          this.$refs.table.filterTable()
        })
      }
    },
    edit(item) {
      crfs.getItem(item.uid).then((resp) => {
        this.selectedItem = resp.data
        this.showForm = true
      })
    },
    view(item) {
      crfs.getItem(item.uid).then((resp) => {
        this.selectedItem = resp.data
        this.showForm = true
      })
    },
    async openItemHistory(item) {
      this.selectedItem = item
      const resp = await crfs.getItemAuditTrail(item.uid)
      this.itemHistoryItems = this.transformItems(resp.data)
      this.showItemHistory = true
    },
    closeItemHistory() {
      this.selectedItem = null
      this.showItemHistory = false
    },
    transformItems(items) {
      const result = []
      for (const item of items) {
        const newItem = { ...item }
        if (newItem.activities) {
          newItem.activities = dataFormating.names(newItem.activities)
        } else {
          newItem.activities = ''
        }
        result.push(newItem)
      }
      return result
    },
    openLinkForm(item) {
      this.selectedItem = item
      this.linkForm = true
    },
    closeLinkForm() {
      this.linkForm = false
      this.selectedItem = null
      this.$refs.table.filterTable()
    },
    getItems(filters, options, filtersUpdated) {
      if (filters) {
        this.filters = filters
      }
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      this.fetchItems(params)
    },
  },
}
</script>
