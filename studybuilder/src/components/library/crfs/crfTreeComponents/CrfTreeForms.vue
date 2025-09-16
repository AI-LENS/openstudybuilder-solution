<template>
  <td :colspan="columns.length" class="pa-0">
    <v-data-table
      id="forms"
      v-model:expanded="expanded"
      :initial-sort-by="[{ key: 'order_number', order: 'asc' }]"
      :headers="columns"
      :items="forms"
      item-value="name"
      light
      :loading="loading"
      :items-per-page="-1"
    >
      <template #headers="{ columns }">
        <tr>
          <template v-for="column in columns" :key="column.key">
            <td>
              <span>{{ column.title }}</span>
            </td>
          </template>
        </tr>
      </template>
      <template #bottom />
      <template #item="{ item, internalItem, toggleExpand, isExpanded, index }">
        <tr style="background-color: rgb(var(--v-theme-dfltBackgroundLight2))">
          <td width="45%" :class="'font-weight-bold'">
            <v-row class="align-center">
              <v-btn
                v-if="isExpanded(internalItem)"
                icon="mdi-chevron-down"
                variant="text"
                class="ml-4"
                @click="toggleExpand(internalItem)"
              />
              <v-btn
                v-else-if="item.item_groups && item.item_groups.length > 0"
                icon="mdi-chevron-right"
                variant="text"
                class="ml-4"
                @click="toggleExpand(internalItem)"
              />
              <v-btn v-else variant="text" class="ml-4 hide" icon />
              <v-btn
                v-if="sortMode"
                size="small"
                variant="text"
                icon="mdi-arrow-up-thin"
                @click="orderUp(item, index)"
              />
              <v-btn
                v-if="sortMode"
                size="small"
                variant="text"
                icon="mdi-arrow-down-thin"
                @click="orderDown(item, index)"
              />
              <ActionsMenu :actions="actions" :item="item" />
              <span class="ml-2">
                <v-icon color="crfForm"> mdi-alpha-f-circle-outline </v-icon>
                {{ item.name }}
              </span>
            </v-row>
          </td>
          <td width="10%">
            <CrfTreeTooltipsHandler :item="item" value="mandatory" />
            <CrfTreeTooltipsHandler :item="item" value="locked" />
          </td>
          <td width="10%">
            <CrfTreeTooltipsHandler :item="item" value="repeating" />
          </td>
          <td width="10%">
            <StatusChip :status="item.status" />
          </td>
          <td width="10%">
            {{ item.version }}
          </td>
          <td width="15%">
            <v-menu v-if="item.status !== statuses.FINAL" offset-y>
              <template #activator="{ props }">
                <div>
                  <v-btn
                    v-show="item.status !== statuses.FINAL"
                    width="150px"
                    size="small"
                    rounded
                    v-bind="props"
                    color="crfGroup"
                    :title="$t('CrfTree.link_item_groups')"
                  >
                    <v-icon icon="mdi-plus" />
                    {{ $t('CrfTree.item_groups') }}
                  </v-btn>
                </div>
              </template>
              <v-list>
                <v-list-item @click="openLinkForm(item)">
                  <template #prepend>
                    <v-icon icon="mdi-plus" />
                  </template>
                  <v-list-item-title>
                    {{ $t('CrfTree.link_existing') }}
                  </v-list-item-title>
                </v-list-item>
                <v-list-item @click="openCreateAndAddForm(item)">
                  <template #prepend>
                    <v-icon icon="mdi-pencil-outline" />
                  </template>
                  <v-list-item-title>
                    {{ $t('CrfTree.create_and_link') }}
                  </v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>
            <v-btn v-else width="150px" rounded size="small" class="hide" />
          </td>
        </tr>
      </template>
      <template #expanded-row="{ columns, item }">
        <CrfTreeItemGroups
          :sort-mode="sortMode"
          :parent-form="item"
          :columns="columns"
          :refresh-item-groups="refreshItemGroups"
          :expand-groups-for-form="expandGroupsForForm"
        />
      </template>
    </v-data-table>
  </td>
  <v-dialog v-model="showFormForm" persistent content-class="fullscreen-dialog">
    <CrfFormForm
      :selected-form="selectedForm"
      :read-only-prop="selectedForm && selectedForm.status === statuses.FINAL"
      class="fullscreen-dialog"
      @close="closeDefinition"
      @link-form="linkForm"
    />
  </v-dialog>
  <CrfLinkForm
    :open="showLinkForm"
    :item-to-link="selectedForm"
    items-type="item-groups"
    @close="closeLinkForm"
  />
  <v-dialog
    v-model="showExportForm"
    max-width="800px"
    persistent
    @keydown.esc="closeExportForm"
  >
    <CrfExportForm :item="selectedForm" type="form" @close="closeExportForm" />
  </v-dialog>
  <CrfReferencesForm
    :open="showAttributesForm"
    :parent="parentTemplate"
    :element="selectedForm"
    :read-only="selectedForm.status === statuses.FINAL"
    @close="closeAttributesForm"
  />
  <v-dialog
    v-model="showCreateForm"
    persistent
    content-class="fullscreen-dialog"
  >
    <CrfItemGroupForm
      class="fullscreen-dialog"
      @close="closeCreateAndAddForm"
      @link-group="linkItemGroup"
    />
  </v-dialog>
</template>

<script>
import crfs from '@/api/crfs'
import CrfTreeItemGroups from '@/components/library/crfs/crfTreeComponents/CrfTreeItemGroups.vue'
import CrfTreeTooltipsHandler from '@/components/library/crfs/CrfTreeTooltipsHandler.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import statuses from '@/constants/statuses'
import CrfLinkForm from '@/components/library/crfs/CrfLinkForm.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import CrfFormForm from '@/components/library/crfs/CrfFormForm.vue'
import _isEmpty from 'lodash/isEmpty'
import CrfExportForm from '@/components/library/crfs/CrfExportForm.vue'
import CrfReferencesForm from '@/components/library/crfs/CrfReferencesForm.vue'
import crfTypes from '@/constants/crfTypes'
import CrfItemGroupForm from '@/components/library/crfs/CrfItemGroupForm.vue'

export default {
  components: {
    CrfTreeItemGroups,
    CrfTreeTooltipsHandler,
    StatusChip,
    CrfLinkForm,
    ActionsMenu,
    CrfFormForm,
    CrfExportForm,
    CrfReferencesForm,
    CrfItemGroupForm,
  },
  props: {
    parentTemplate: {
      type: Object,
      default: null,
    },
    columns: {
      type: Array,
      default: null,
    },
    refreshForms: {
      type: Number,
      default: null,
    },
    expandFormsForTemplate: {
      type: String,
      default: null,
    },
    sortMode: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      forms: [],
      loading: false,
      showFormForm: false,
      showLinkForm: false,
      selectedForm: {},
      refreshItemGroups: 0,
      actions: [
        {
          label: this.$t('CrfTree.open_def'),
          icon: 'mdi-arrow-left',
          click: this.openDefinition,
        },
        {
          label: this.$t('CrfTree.edit_reference'),
          icon: 'mdi-pencil-outline',
          click: this.editAttributes,
          condition: (item) => item.status === statuses.DRAFT,
          accessRole: this.$roles.LIBRARY_WRITE,
        },
        {
          label: this.$t('CrfTree.preview_odm'),
          icon: 'mdi-file-xml-box',
          click: this.previewODM,
        },
        {
          label: this.$t('_global.export'),
          icon: 'mdi-download-outline',
          click: this.openExportForm,
        },
        {
          label: this.$t('CrfTree.expand'),
          icon: 'mdi-arrow-expand-down',
          condition: (item) => item.item_groups.length > 0,
          click: this.expandAll,
        },
      ],
      expanded: [],
      expandGroupsForForm: [],
      showExportForm: false,
      showAttributesForm: false,
      showCreateForm: false,
    }
  },
  watch: {
    refreshForms() {
      this.fetchForms()
    },
    expandFormsForTemplate(value) {
      if (!_isEmpty(value) && value === this.parentTemplate.uid) {
        this.expanded = this.forms
          .map((form) => (form.item_groups.length > 0 ? form.name : null))
          .filter(function (val) {
            return val !== null
          })
        this.expandGroupsForForm = this.forms
          .map((form) => (form.item_groups.length > 0 ? form.uid : null))
          .filter(function (val) {
            return val !== null
          })
      }
    },
  },
  created() {
    this.statuses = statuses
  },
  mounted() {
    this.fetchForms()
  },
  methods: {
    openCreateAndAddForm(item) {
      this.selectedForm = item
      this.showCreateForm = true
    },
    closeCreateAndAddForm() {
      this.showCreateForm = false
      this.selectedForm = {}
    },
    linkItemGroup(group) {
      const payload = [
        {
          uid: group.data.uid,
          order_number: this.selectedForm.item_groups.length,
          mandatory: 'No',
          collection_exception_condition_oid: null,
          vendor: { attributes: [] },
        },
      ]
      crfs
        .addItemGroupsToForm(payload, this.selectedForm.uid, false)
        .then(() => {
          this.fetchForms()
        })
    },
    async fetchForms() {
      this.loading = true
      const params = {
        total_count: true,
        filters: JSON.stringify({
          uid: { v: this.parentTemplate.forms.map((form) => form.uid) },
        }),
        page_size: 0,
      }
      await crfs.get('forms', { params }).then((resp) => {
        this.forms = []
        this.parentTemplate.forms.forEach((form) => {
          this.forms.push({
            ...form,
            ...resp.data.items.find((a) => a.uid === form.uid),
          })
        })
        this.refreshItemGroups += 1
        this.loading = false
        if (
          !_isEmpty(this.expandFormsForTemplate) &&
          this.expandFormsForTemplate === this.parentTemplate.uid
        ) {
          this.expanded = this.forms
            .map((form) => (form.item_groups.length > 0 ? form.name : null))
            .filter(function (val) {
              return val !== null
            })
          this.expandGroupsForForm = this.forms
            .map((form) => (form.item_groups.length > 0 ? form.uid : null))
            .filter(function (val) {
              return val !== null
            })
        }
      })
    },
    openDefinition(item) {
      this.selectedForm = item
      this.showFormForm = true
    },
    closeDefinition() {
      this.selectedForm = {}
      this.showFormForm = false
      this.fetchForms()
    },
    openLinkForm(item) {
      this.selectedForm = item
      this.showLinkForm = true
    },
    closeLinkForm() {
      this.showLinkForm = false
      this.selectedForm = {}
      this.fetchForms()
    },
    async expandAll(item) {
      await this.expanded.push(item.name)
      this.expandGroupsForForm = [item.uid]
    },
    openExportForm(item) {
      this.selectedForm = item
      this.showExportForm = true
    },
    closeExportForm() {
      this.selectedForm = {}
      this.showExportForm = false
    },
    editAttributes(item) {
      this.selectedForm = item
      this.showAttributesForm = true
    },
    closeAttributesForm() {
      this.selectedForm = {}
      this.showAttributesForm = false
    },
    previewODM(item) {
      this.$router.push({
        name: 'Crfs',
        params: {
          tab: 'odm-viewer',
          uid: item.uid,
          type: crfTypes.FORM,
        },
      })
    },
    orderUp(item, index) {
      if (index === 0) {
        return
      } else {
        this.forms[index].order_number--
        this.forms[index - 1].order_number++
        this.forms.sort((a, b) => {
          return a.order_number - b.order_number
        })
        crfs.addFormsToTemplate(this.forms, this.parentTemplate.uid, true)
      }
    },
    orderDown(item, index) {
      if (index === this.forms.length - 1) {
        return
      } else {
        this.forms[index].order_number++
        this.forms[index + 1].order_number--
        this.forms.sort((a, b) => {
          return a.order_number - b.order_number
        })
        crfs.addFormsToTemplate(this.forms, this.parentTemplate.uid, true)
      }
    },
  },
}
</script>
<style scoped>
#forms .v-table__wrapper > table > thead > tr {
  visibility: collapse;
}
</style>
