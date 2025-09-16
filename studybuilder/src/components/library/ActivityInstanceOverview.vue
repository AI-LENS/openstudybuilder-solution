<template>
  <div class="activity-instance-overview-container">
    <BaseActivityOverview
      ref="overview"
      :transform-func="transformItem"
      :navigate-to-version="changeVersion"
      :history-headers="historyHeaders"
      v-bind="$attrs"
      @refresh="refreshData"
    >
      <template #htmlContent="{ itemOverview }">
        <div v-if="itemOverview">
          <!-- Activity Instance Summary -->
          <ActivitySummary
            v-if="itemOverview.activity_instance"
            :activity="
              adaptActivityInstanceForSummary(
                itemOverview.activity_instance,
                activityGroupings
              )
            "
            :all-versions="allVersions(itemOverview)"
            :activity-groupings="activityGroupings"
            :show-data-collection="false"
            class="activity-summary"
            @version-change="(value) => manualChangeVersion(value)"
          />

          <!-- Activity Groupings section -->
          <div class="activity-section">
            <div class="section-header mb-1">
              <h3 class="text-h6 font-weight-bold text-primary">
                {{ $t('ActivityInstanceOverview.activity_groupings') }}
              </h3>
            </div>
            <div>
              <NNTable
                :headers="groupingsHeaders"
                :items="displayedGroupings"
                :items-length="
                  activityGroupings.length
                    ? convertActivityGroupingsToTableItems(
                        activityGroupings.value
                      ).length
                    : 0
                "
                :items-per-page="10"
                :hide-export-button="false"
                :hide-default-switches="true"
                :disable-filtering="false"
                :hide-search-field="false"
                :modifiable-table="true"
                :no-padding="true"
                elevation="0"
                class="groupings-table"
                item-value="uid"
                :disable-sort="false"
                :loading="loadingGroupings"
                :items-per-page-options="[10, 25, 50, 100]"
                :server-items-length="
                  activityGroupings.length
                    ? convertActivityGroupingsToTableItems(
                        activityGroupings.value
                      ).length
                    : 0
                "
                :export-data-url="`concepts/activities/activity-instances/${route.params.id}/activity-groupings`"
                export-object-label="Activity Groupings"
                @filter="handleGroupingsFilter"
                @update:options="handleGroupingsFilter"
              >
                <template #[`item.activity_group_name`]="{ item }">
                  <router-link
                    v-if="item.activity_group_id"
                    :to="{
                      name: 'GroupOverview',
                      params: {
                        id: item.activity_group_id,
                        version: item.activity_group_version,
                      },
                    }"
                    class="d-block"
                  >
                    {{ item.activity_group_name }}
                  </router-link>
                  <div class="text-caption text-grey-darken-1">
                    {{ $t('_global.version') }}
                    {{ item.activity_group_version }}
                    <span v-if="item.activity_group_status" class="ml-2"
                      >- {{ item.activity_group_status }}</span
                    >
                  </div>
                </template>
                <template #[`item.activity_subgroup_name`]="{ item }">
                  <router-link
                    v-if="item.activity_subgroup_id"
                    :to="{
                      name: 'SubgroupOverview',
                      params: {
                        id: item.activity_subgroup_id,
                        version: item.activity_subgroup_version,
                      },
                    }"
                    class="d-block"
                  >
                    {{ item.activity_subgroup_name }}
                  </router-link>
                  <div class="text-caption text-grey-darken-1">
                    {{ $t('_global.version') }}
                    {{ item.activity_subgroup_version }}
                    <span v-if="item.activity_subgroup_status" class="ml-2"
                      >- {{ item.activity_subgroup_status }}</span
                    >
                  </div>
                </template>
                <template #[`item.activity_name`]="{ item }">
                  <router-link
                    v-if="item.activity_id"
                    :to="{
                      name: 'ActivityOverview',
                      params: {
                        id: item.activity_id,
                        version: item.activity_version,
                      },
                    }"
                    class="d-block"
                  >
                    {{ item.activity_name }}
                  </router-link>
                  <div class="text-caption text-grey-darken-1">
                    {{ $t('_global.version') }} {{ item.activity_version }}
                    <span v-if="item.activity_status" class="ml-2"
                      >- {{ item.activity_status }}</span
                    >
                  </div>
                </template>
              </NNTable>
            </div>
          </div>

          <!-- Activity Items section -->
          <div class="activity-section mt-8">
            <ActivityItemsTable
              :activity-instance-id="route.params.id"
              :version="route.params.version"
            />
          </div>
        </div>
        <div v-else class="d-flex justify-center align-center pa-8">
          <v-progress-circular
            indeterminate
            color="primary"
          ></v-progress-circular>
        </div>
      </template>
      <template #itemForm="{ show, item, close }">
        <v-dialog
          :model-value="show"
          persistent
          fullscreen
          content-class="top-dialog"
        >
          <ActivitiesInstantiationsForm
            :edited-activity="item"
            @close="close"
          />
        </v-dialog>
      </template>
    </BaseActivityOverview>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import BaseActivityOverview from './BaseActivityOverview.vue'
import ActivitySummary from './ActivitySummary.vue'
import NNTable from '@/components/tools/NNTable.vue'
import ActivitiesInstantiationsForm from './ActivitiesInstantiationsForm.vue'
import ActivityItemsTable from './ActivityItemsTable.vue'
import activities from '@/api/activities'

const { t } = useI18n()
const appStore = useAppStore()
const route = useRoute()
const router = useRouter()

const overview = ref(null)
// Separate data sources for the new endpoints
const activityGroupings = ref([])
const loadingGroupings = ref(false)

const emit = defineEmits(['refresh'])

// Table headers
const groupingsHeaders = [
  {
    title: 'Activity group',
    key: 'activity_group_name',
    sortable: true,
    width: '40%',
  },
  {
    title: 'Activity subgroup',
    key: 'activity_subgroup_name',
    sortable: true,
    width: '40%',
  },
  {
    title: 'Activity',
    key: 'activity_name',
    sortable: true,
    width: '20%',
  },
]

// Methods for ActivitySummary component
function refreshData() {
  // Refresh the activity groupings
  fetchActivityGroupings()
  emit('refresh')
}

// Fetch activity groupings from new endpoint
async function fetchActivityGroupings() {
  try {
    loadingGroupings.value = true
    const activityInstanceId = route.params.id
    const version = route.params.version

    if (activityInstanceId) {
      const response = await activities.getActivityInstanceGroupings(
        activityInstanceId,
        version
      )
      activityGroupings.value = response.data || []
      // Initialize filtered groupings
      filteredGroupings.value = convertActivityGroupingsToTableItems(
        activityGroupings.value
      )
    }
  } catch (error) {
    console.error('Error fetching activity groupings:', error)
    activityGroupings.value = []
    filteredGroupings.value = []
  } finally {
    loadingGroupings.value = false
  }
}

// Convert activity instance to format expected by ActivitySummary
function adaptActivityInstanceForSummary(
  activityInstance,
  activityGroupings = []
) {
  if (!activityInstance) return {}

  // Extract activity name from activity groupings
  let activityName = activityInstance.activity_name
  if (!activityName && activityGroupings && activityGroupings.length > 0) {
    activityName = activityGroupings[0]?.activity?.name
  }

  return {
    name: activityInstance.name,
    name_sentence_case: activityInstance.name_sentence_case,
    version: activityInstance.version,
    start_date: activityInstance.start_date,
    end_date: activityInstance.end_date,
    status: activityInstance.status,
    definition: activityInstance.definition,
    abbreviation: activityInstance.abbreviation,
    library_name: activityInstance.library_name,
    nci_concept_id: activityInstance.nci_concept_id,
    adam_param_code: activityInstance.adam_param_code,
    activity_instance_class:
      activityInstance.activity_instance_class?.name ||
      activityInstance.activity_instance_class,
    is_required_for_activity: activityInstance.is_required_for_activity,
    is_default_selected_for_activity:
      activityInstance.is_default_selected_for_activity,
    is_data_sharing: activityInstance.is_data_sharing,
    is_legacy_usage: activityInstance.is_legacy_usage,
    topic_code: activityInstance.topic_code,
    activity_name: activityName,
  }
}

// Get all versions for the version selector
function allVersions(item) {
  if (!item || !item.all_versions) return []
  return item.all_versions
}

// Handle manual version changes
async function manualChangeVersion(version) {
  if (!version || !overview.value || !overview.value.itemOverview) return

  try {
    const activityInstance = overview.value.itemOverview.activity_instance
    await router.push({
      name: 'ActivityInstanceOverview',
      params: { id: activityInstance.uid, version: version },
    })
    emit('refresh')
  } catch (error) {
    console.error('Error navigating to new version:', error)
  }
}

// Change version function used by BaseActivityOverview
async function changeVersion(activityInstance, version) {
  if (!activityInstance || !activityInstance.uid) return

  try {
    await router.push({
      name: 'ActivityInstanceOverview',
      params: { id: activityInstance.uid, version },
    })
    emit('refresh')
  } catch (error) {
    console.error('Error navigating to new version:', error)
  }
}

// Add ref for filtered groupings
const searchTerm = ref('')
const filteredGroupings = ref([])

// Convert activity groupings for NNTable
function convertActivityGroupingsToTableItems(groupings) {
  if (!groupings || !groupings.length) return []

  return groupings.map((grouping) => ({
    activity_group_name: grouping.activity_group.name,
    activity_group_id: grouping.activity_group.uid,
    activity_group_version: grouping.activity_group.version || '1.0',
    activity_group_status: grouping.activity_group.status,
    activity_subgroup_name: grouping.activity_subgroup.name,
    activity_subgroup_id: grouping.activity_subgroup.uid,
    activity_subgroup_version: grouping.activity_subgroup.version || '1.0',
    activity_subgroup_status: grouping.activity_subgroup.status,
    activity_name: grouping.activity.name,
    activity_id: grouping.activity.uid,
    activity_version: grouping.activity.version || '1.0',
    activity_status: grouping.activity.status,
    uid: `${grouping.activity_group.uid}-${grouping.activity_subgroup.uid}-${grouping.activity.uid}`, // Add unique key
  }))
}

// Handle filtering for activity groupings
function handleGroupingsFilter(filters, options) {
  // Handle both @filter and @update:options events
  const searchValue = options?.search || filters?.search || ''

  if (searchValue) {
    searchTerm.value = searchValue.toLowerCase()
    const items = convertActivityGroupingsToTableItems(activityGroupings.value)

    filteredGroupings.value = items.filter((item) => {
      // Create searchable text from all fields including the displayed format
      const searchableFields = [
        item.activity_group_name,
        item.activity_subgroup_name,
        item.activity_name,
        item.activity_group_status,
        item.activity_subgroup_status,
        item.activity_status,
        item.activity_group_version,
        item.activity_subgroup_version,
        item.activity_version,
        // Add the displayed format "Version X.X - Status"
        item.activity_group_version && item.activity_group_status
          ? `Version ${item.activity_group_version} - ${item.activity_group_status}`
          : '',
        item.activity_subgroup_version && item.activity_subgroup_status
          ? `Version ${item.activity_subgroup_version} - ${item.activity_subgroup_status}`
          : '',
        item.activity_version && item.activity_status
          ? `Version ${item.activity_version} - ${item.activity_status}`
          : '',
      ]

      const searchableText = searchableFields
        .filter(Boolean)
        .join(' ')
        .toLowerCase()

      return searchableText.includes(searchTerm.value)
    })
  } else {
    searchTerm.value = ''
    filteredGroupings.value = convertActivityGroupingsToTableItems(
      activityGroupings.value
    )
  }
}

// Computed property for displayed items
const displayedGroupings = computed(() => {
  return searchTerm.value
    ? filteredGroupings.value
    : convertActivityGroupingsToTableItems(activityGroupings.value)
})

// Transform item for BaseActivityOverview
function transformItem(item) {
  if (!item) return

  if (item.activity_groupings && item.activity_groupings.length > 0) {
    const groups = []
    const subgroups = []
    item.activities = [item.activity_groupings[0].activity]
    item.activity = { name: item.activity_groupings[0].activity.name }

    for (const grouping of item.activity_groupings) {
      groups.push(grouping.activity_group.name)
      subgroups.push(grouping.activity_subgroup.name)
    }

    item.activity_group = { name: groups }
    item.activity_subgroup = { name: subgroups }
  } else {
    item.activity_group = { name: [] }
    item.activity_subgroup = { name: [] }
    item.activity = { name: '' }
  }

  item.item_key = item.uid
}

// History headers for BaseActivityOverview
const historyHeaders = [
  { title: t('_global.library'), key: 'library_name' },
  { title: t('_global.name'), key: 'name' },
  { title: t('_global.abbreviation'), key: 'abbreviation' },
  { title: t('_global.type'), key: 'activity_instance_class_name' },
  { title: t('_global.definition'), key: 'definition' },
  {
    title: t('ActivityInstanceOverview.nci_concept_id'),
    key: 'nci_concept_id',
  },
  {
    title: t('ActivityInstanceOverview.nci_concept_name'),
    key: 'nci_concept_name',
  },
  {
    title: t('ActivityInstanceOverview.is_research_lab'),
    key: 'is_research_lab',
  },
  { title: t('ActivityInstanceOverview.topic_code'), key: 'topic_code' },
  { title: t('ActivityInstanceOverview.adam_code'), key: 'adam_param_code' },
  {
    title: t('ActivityInstanceOverview.is_required_for_activity'),
    key: 'is_required_for_activity',
  },
  {
    title: t('ActivityInstanceOverview.is_default_selected_for_activity'),
    key: 'is_default_selected_for_activity',
  },
  {
    title: t('ActivityInstanceOverview.is_data_sharing'),
    key: 'is_data_sharing',
  },
  {
    title: t('ActivityInstanceOverview.is_legacy_usage'),
    key: 'is_legacy_usage',
  },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.status'), key: 'status' },
  { title: t('_global.version'), key: 'version' },
]

// Watch for route parameter changes to refetch data
watch(
  () => [route.params.id, route.params.version],
  () => {
    fetchActivityGroupings()
  },
  { immediate: true }
)

// Setup on mount
onMounted(() => {
  appStore.addBreadcrumbsLevel(
    t('Sidebar.library.concepts'),
    { name: 'Activities' },
    1,
    false
  )

  appStore.addBreadcrumbsLevel(
    t('Sidebar.library.activities'),
    { name: 'Activities' },
    2,
    true
  )

  appStore.addBreadcrumbsLevel(
    t('Sidebar.library.activities_instances'),
    { name: 'Activities', params: { tab: 'activity-instances' } },
    3,
    true
  )

  // Add instance name when available
  if (overview.value?.itemOverview?.activity_instance?.name) {
    appStore.addBreadcrumbsLevel(
      overview.value.itemOverview.activity_instance.name,
      { name: 'ActivityInstanceOverview', params: route.params },
      4,
      true
    )
  }

  // Initial fetch of new endpoint data
  fetchActivityGroupings()
})
</script>

<style scoped>
/* Activity Instance overview container styling */
.activity-instance-overview-container {
  width: 100%;
  background-color: transparent;
}

/* Activity section styling */
.activity-section {
  margin-top: 24px;
}

/* Summary section styling */
.activity-summary {
  margin-bottom: 24px;
}

/* Section header styling */
.section-header {
  margin-top: 16px;
  margin-bottom: 8px;
  padding-left: 0;
}

/* Tables styling */
.groupings-table {
  margin-top: 8px;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: none;
  background-color: transparent;
}

/* Table content styling */
.groupings-table :deep(table) {
  border-collapse: collapse;
  width: 100%;
}

.groupings-table :deep(th) {
  background-color: var(--semantic-system-brand, #001965);
  color: white;
  font-weight: 500;
  padding: 12px 16px;
  text-align: left;
}

.groupings-table :deep(td) {
  padding: 8px 16px;
  border-bottom: 1px solid #e0e0e0;
  background-color: white !important;
}

.groupings-table :deep(.v-card-text) {
  width: 100% !important;
  padding: 0 !important;
}

.groupings-table :deep(.v-table__wrapper) {
  height: auto !important;
}

.groupings-table :deep(.v-card-title) {
  padding: 8px 16px;
  display: flex;
  flex-direction: row;
  justify-content: flex-start;
  align-items: center;
  background-color: transparent;
}

.groupings-table :deep(.v-card__title .v-input) {
  max-width: 300px;
  margin-right: auto;
}

.groupings-table :deep(.v-data-table-footer) {
  border-top: 1px solid #e0e0e0;
  background-color: transparent !important;
}

.activity-instance-overview-container :deep(.v-table),
.groupings-table :deep(.v-table) {
  background: transparent !important;
}

.activity-instance-overview-container :deep(.v-data-table__th),
.groupings-table :deep(.v-data-table__th) {
  background-color: rgb(var(--v-theme-nnTrueBlue)) !important;
}

.activity-instance-overview-container :deep(.v-data-table__tbody tr),
.groupings-table :deep(.v-data-table__tbody tr) {
  background-color: white !important;
}

.activity-instance-overview-container :deep(.v-card),
.activity-instance-overview-container :deep(.v-sheet),
.groupings-table :deep(.v-card),
.groupings-table :deep(.v-sheet) {
  background-color: transparent !important;
  box-shadow: none !important;
}
</style>
