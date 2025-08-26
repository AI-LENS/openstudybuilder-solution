<template>
  <div class="subgroup-overview-container">
    <BaseActivityOverview
      ref="overview"
      :source="'activity-sub-groups'"
      :item-uid="props.itemUid"
      :transform-func="transformItem"
      :navigate-to-version="changeVersion"
      :history-headers="historyHeaders"
      :yaml-version="props.yamlVersion"
      :cosmos-version="props.cosmosVersion"
      v-bind="$attrs"
    >
      <template #htmlContent>
        <!-- Subgroup Details using ActivitySummary -->
        <div class="summary-section">
          <v-skeleton-loader
            v-if="!props.itemOverview?.activity_subgroup"
            type="card"
            class="subgroup-activity-summary"
          />
          <ActivitySummary
            v-else
            :activity="props.itemOverview.activity_subgroup"
            :all-versions="allVersions(props.itemOverview)"
            :show-library="true"
            :show-nci-concept-id="false"
            :show-data-collection="false"
            :show-abbreviation="false"
            :show-author="true"
            class="subgroup-activity-summary"
            @version-change="
              (value) =>
                changeVersion(props.itemOverview.activity_subgroup, value)
            "
          />
        </div>

        <!-- Activity Groups Section -->
        <div v-if="isLoadingGroups" class="my-5">
          <div class="section-header mb-1">
            <h3 class="text-h6 font-weight-bold text-primary">
              {{ $t('ActivityOverview.activity_group') }}
            </h3>
          </div>
          <v-skeleton-loader type="table" />
        </div>
        <div v-else class="my-5">
          <div class="section-header mb-1">
            <h3 class="text-h6 font-weight-bold text-primary">
              {{ $t('ActivityOverview.activity_group') }}
            </h3>
          </div>
          <NNTable
            :headers="groupsHeaders"
            :items="groups"
            :items-length="groupsTotal"
            :items-per-page="tableOptions.itemsPerPage"
            :hide-export-button="false"
            :hide-default-switches="true"
            :disable-filtering="true"
            :hide-search-field="false"
            :modifiable-table="true"
            :use-cached-filtering="false"
            :no-padding="true"
            elevation="0"
            class="groups-table"
            item-value="uid"
            :initial-sort="initialSort"
            :disable-sort="false"
            :loading="false"
            :export-data-url="`concepts/activities/activity-sub-groups/${props.itemUid}/activity-groups`"
            export-object-label="Activity Groups"
            @filter="
              (filters, options) => handleFilter(filters, options, 'groups')
            "
            @update:options="updateTableOptions"
          >
            <template #[`item.name`]="{ item }">
              <router-link
                :to="{
                  name: 'GroupOverview',
                  params: { id: item.uid, version: item.version },
                }"
              >
                {{ item.name }}
              </router-link>
            </template>
            <template #[`item.status`]="{ item }">
              <StatusChip :status="item.status" />
            </template>
            <template #no-data>
              <div class="text-center py-4">
                <span class="text-body-1 text-grey-darken-1">
                  {{ $t('SubgroupOverview.noItemsAvailable') }}
                </span>
              </div>
            </template>
          </NNTable>
        </div>

        <!-- Activities Section -->
        <div v-if="isLoadingActivities" class="my-5">
          <div class="section-header mb-1">
            <h3 class="text-h6 font-weight-bold text-primary">
              {{ $t('ActivityOverview.activities') }}
            </h3>
          </div>
          <v-skeleton-loader type="table" />
        </div>
        <div v-else class="my-5">
          <div class="section-header mb-1">
            <h3 class="text-h6 font-weight-bold text-primary">
              {{ $t('ActivityOverview.activities') }}
            </h3>
          </div>
          <NNTable
            :headers="activitiesHeaders"
            :items="activitiesList"
            :items-length="activitiesTotal"
            :items-per-page="activitiesPagination.itemsPerPage"
            :page="activitiesPagination.page"
            :hide-export-button="false"
            :export-data-url="`concepts/activities/activity-sub-groups/${props.itemUid}/activities`"
            export-object-label="Activities"
            :hide-default-switches="true"
            :disable-filtering="true"
            :hide-search-field="false"
            :modifiable-table="true"
            :no-padding="true"
            elevation="0"
            class="activities-table"
            item-value="uid"
            :initial-sort="initialSort"
            :disable-sort="false"
            :loading="false"
            @filter="
              (filters, options) => handleFilter(filters, options, 'activities')
            "
            @update:options="updateActivitiesOptions"
          >
            <template #[`item.name`]="{ item }">
              <router-link
                :to="{
                  name: 'ActivityOverview',
                  params: { id: item.uid, version: item.version },
                }"
              >
                {{ item.name }}
              </router-link>
            </template>
            <template #[`item.status`]="{ item }">
              <StatusChip :status="item.status" />
            </template>
            <template #no-data>
              <div class="text-center py-4">
                <span class="text-body-1 text-grey-darken-1">
                  {{ $t('SubgroupOverview.noItemsAvailable') }}
                </span>
              </div>
            </template>
          </NNTable>
        </div>
      </template>

      <template #itemForm="{ show, item, close }">
        <v-dialog
          :model-value="show"
          persistent
          max-width="800px"
          content-class="top-dialog"
        >
          <ActivitiesGroupsForm
            ref="groupFormRef"
            :open="show"
            :subgroup="true"
            :edited-group-or-subgroup="item"
            @close="close"
          />
        </v-dialog>
      </template>
    </BaseActivityOverview>
  </div>
</template>

<script setup>
import { onMounted, ref, defineAsyncComponent, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import activitiesApi from '@/api/activities'

import BaseActivityOverview from './BaseActivityOverview.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import ActivitySummary from '@/components/library/ActivitySummary.vue'
import NNTable from '@/components/tools/NNTable.vue'

const ActivitiesGroupsForm = defineAsyncComponent(
  () => import('@/components/library/ActivitiesGroupsForm.vue')
)

const props = defineProps({
  itemOverview: {
    type: Object,
    required: true,
  },
  itemUid: {
    type: String,
    required: true,
  },
  yamlVersion: {
    type: String,
    default: null,
  },
  cosmosVersion: {
    type: String,
    default: null,
  },
})
const emit = defineEmits(['refresh'])

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const appStore = useAppStore()
const overview = ref()
const groupFormRef = ref()

// Table data and loading states
const groups = ref([])
const activitiesList = ref([])
const groupsTotal = ref(0)
const activitiesTotal = ref(0)
const isLoadingGroups = ref(true)
const isLoadingActivities = ref(true)
const isFetchingActivities = ref(false)
let fetchRequestId = 0
const tableOptions = ref({
  search: '',
  sortBy: [],
  sortDesc: [],
  page: 1,
  itemsPerPage: 10,
})

// Separate setting just for activities pagination
const activitiesPagination = ref({
  page: 1,
  itemsPerPage: 10,
})

// Track search term for activities
let lastActivitiesSearchTerm = ''

// Initial sort order for tables
const initialSort = ref([{ key: 'name', order: 'asc' }])

const historyHeaders = [
  { title: t('_global.library'), key: 'library_name' },
  { title: t('_global.name'), key: 'name' },
  { title: t('_global.definition'), key: 'definition' },
  { title: t('_global.version'), key: 'version' },
  { title: t('_global.start_date'), key: 'start_date' },
  { title: t('_global.end_date'), key: 'end_date' },
  { title: t('_global.status'), key: 'status' },
]

// Headers for groups table
const groupsHeaders = [
  { title: t('_global.name'), key: 'name', align: 'start', sortable: true },
  {
    title: t('_global.version'),
    key: 'version',
    align: 'start',
    sortable: true,
  },
  { title: t('_global.status'), key: 'status', align: 'start', sortable: true },
]

// Headers for activities table
const activitiesHeaders = [
  { title: t('_global.name'), key: 'name', align: 'start', sortable: true },
  {
    title: t('_global.version'),
    key: 'version',
    align: 'start',
    sortable: true,
  },
  { title: t('_global.status'), key: 'status', align: 'start', sortable: true },
]

function transformItem(item) {
  item.item_key = item.uid
}

async function changeVersion(subgroup, version) {
  await router.push({
    name: 'SubgroupOverview',
    params: {
      id: subgroup.uid,
      version,
    },
  })
  emit('refresh')
}

function itemMatchesSearch(item, searchTerm) {
  if (!searchTerm || searchTerm === '') return true

  const term = searchTerm.toLowerCase()

  if (item.name?.toLowerCase().includes(term)) return true
  if (item.version && item.version.toString().toLowerCase().includes(term))
    return true
  if (item.status?.toLowerCase().includes(term)) return true

  return false
}

function handleFilter(filters, options, targetTable) {
  tableOptions.value.page = 1

  const searchTerm =
    options && options.search && typeof options.search === 'string'
      ? options.search.toLowerCase()
      : filters && filters.search && typeof filters.search === 'string'
        ? filters.search.toLowerCase()
        : ''

  if (targetTable === 'groups') {
    if (searchTerm) {
      const filteredGroups =
        props.itemOverview.activity_subgroup.activity_groups.filter((group) => {
          return itemMatchesSearch(group, searchTerm)
        })
      groups.value = filteredGroups
      groupsTotal.value = filteredGroups.length
    } else {
      groups.value = [...props.itemOverview.activity_subgroup.activity_groups]
      groupsTotal.value =
        props.itemOverview.activity_subgroup.activity_groups.length
    }
  } else if (targetTable === 'activities') {
    // Skip if search hasn't changed
    if (searchTerm === lastActivitiesSearchTerm) {
      return
    }

    lastActivitiesSearchTerm = searchTerm

    // Reset to page 1 when search changes
    activitiesPagination.value.page = 1

    // Fetch with new search term
    fetchActivities()
  }
}

// Handles pagination for groups table
function updateTableOptions(options) {
  if (!options) return

  // Store sort options separately to prevent losing them
  if (options.sortBy && options.sortBy.length > 0) {
    tableOptions.value.sortBy = [...options.sortBy]
  }

  // Update page and items per page
  tableOptions.value.page = options.page
  tableOptions.value.itemsPerPage = options.itemsPerPage
}

// Handles pagination for activities table
function updateActivitiesOptions(options) {
  if (!options) return

  // Only handle pagination changes
  if (
    options.page !== activitiesPagination.value.page ||
    options.itemsPerPage !== activitiesPagination.value.itemsPerPage
  ) {
    activitiesPagination.value.page = options.page
    activitiesPagination.value.itemsPerPage = options.itemsPerPage

    // Fetch with new pagination
    if (props.itemUid) {
      fetchActivities()
    }
  }
}

async function fetchActivities() {
  // Prevent concurrent fetches
  if (isFetchingActivities.value) {
    return
  }

  const currentRequestId = ++fetchRequestId

  isFetchingActivities.value = true
  isLoadingActivities.value = true

  try {
    const options = {
      version: props.itemOverview?.activity_subgroup?.version,
      total_count: true,
      page_number: activitiesPagination.value.page,
      page_size: activitiesPagination.value.itemsPerPage,
    }

    // Add search parameter if there's a search term
    if (lastActivitiesSearchTerm) {
      options.search_string = lastActivitiesSearchTerm
    }

    const response = await activitiesApi.getSubgroupActivities(
      props.itemUid,
      options
    )

    if (response && response.data) {
      // Check if response has new paginated structure
      if (response.data.items) {
        // Check if this is still the latest request
        if (currentRequestId !== fetchRequestId) {
          return
        }

        // Use server-paginated results directly
        // Use server response directly
        activitiesList.value = response.data.items
        activitiesTotal.value =
          response.data.total || response.data.items.length
      } else {
        // Handle legacy non-paginated response
        if (currentRequestId !== fetchRequestId) {
          return
        }
        // Use server response directly
        activitiesList.value = response.data
        activitiesTotal.value = response.data.length
      }
    } else {
      activitiesList.value = []
      activitiesTotal.value = 0
    }
  } catch (error) {
    activitiesList.value = []
    activitiesTotal.value = 0
  } finally {
    isLoadingActivities.value = false
    isFetchingActivities.value = false
  }
}

function allVersions(item) {
  return [...item.all_versions].sort().reverse()
}

let lastFetchedVersion = null

watch(
  () => props.itemOverview?.activity_subgroup,
  (newSubgroup) => {
    if (newSubgroup && newSubgroup.activity_groups) {
      isLoadingGroups.value = true
      groups.value = [...newSubgroup.activity_groups]
      groupsTotal.value = newSubgroup.activity_groups.length
      isLoadingGroups.value = false

      const currentVersion = newSubgroup.version
      if (lastFetchedVersion !== currentVersion) {
        lastFetchedVersion = currentVersion
        // Reset to page 1 when version changes
        activitiesPagination.value.page = 1
        fetchActivities()
      }
    } else {
      groups.value = []
      groupsTotal.value = 0
    }
  },
  { immediate: true }
)

let hasInitiallyFetchedActivities = false

onMounted(() => {
  if (!hasInitiallyFetchedActivities) {
    hasInitiallyFetchedActivities = true
    fetchActivities()
  }

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
    t('Sidebar.library.activities_subgroups'),
    { name: 'Activities', params: { tab: 'activity-subgroups' } },
    3,
    true
  )

  const subgroupName =
    props.itemOverview?.activity_subgroup?.name || t('_global.loading')

  appStore.addBreadcrumbsLevel(
    subgroupName,
    {
      name: 'SubgroupOverview',
      params: { id: route.params.id },
    },
    4,
    true
  )
})
</script>

<style scoped>
/* Subgroup overview container styling */
.subgroup-overview-container {
  width: 100%;
  background-color: transparent;
}

/* Summary section styling */
.summary-section {
  margin-bottom: 24px;
}

/* Section header styling */
.section-header {
  margin-top: 16px;
  margin-bottom: 8px;
  padding-left: 0;
}

/* Tables styling */
.groups-table,
.activities-table {
  margin-top: 8px;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: none;
  background-color: transparent;
}

/* Table content styling */
.groups-table :deep(table),
.activities-table :deep(table) {
  border-collapse: collapse;
  width: 100%;
}

.groups-table :deep(th),
.activities-table :deep(th) {
  background-color: var(--semantic-system-brand, #001965);
  color: white;
  font-weight: 500;
  padding: 12px 16px;
  text-align: left;
}

.groups-table :deep(td),
.activities-table :deep(td) {
  padding: 8px 16px;
  border-bottom: 1px solid #e0e0e0;
  background-color: white !important;
}

.groups-table :deep(.v-card-text),
.activities-table :deep(.v-card-text) {
  width: 100% !important;
  padding: 0 !important;
}

.groups-table :deep(.v-table__wrapper),
.activities-table :deep(.v-table__wrapper) {
  height: auto !important;
}

.groups-table :deep(.v-card-title),
.activities-table :deep(.v-card-title) {
  padding: 8px 16px;
  display: flex;
  flex-direction: row;
  justify-content: flex-start;
  align-items: center;
  background-color: transparent;
}

.groups-table :deep(.v-card__title .v-input),
.activities-table :deep(.v-card__title .v-input) {
  max-width: 300px;
  margin-right: auto;
}

.groups-table :deep(.v-data-table-footer),
.activities-table :deep(.v-data-table-footer) {
  border-top: 1px solid #e0e0e0;
  background-color: transparent !important;
}

.subgroup-overview-container :deep(.v-table),
.groups-table :deep(.v-table),
.activities-table :deep(.v-table) {
  background: transparent !important;
}

.subgroup-overview-container :deep(.v-data-table__th),
.groups-table :deep(.v-data-table__th),
.activities-table :deep(.v-data-table__th) {
  background-color: rgb(var(--v-theme-nnTrueBlue)) !important;
}

.subgroup-overview-container :deep(.v-data-table__tbody tr),
.groups-table :deep(.v-data-table__tbody tr),
.activities-table :deep(.v-data-table__tbody tr) {
  background-color: white !important;
}

.subgroup-overview-container :deep(.v-card),
.subgroup-overview-container :deep(.v-sheet),
.groups-table :deep(.v-card),
.groups-table :deep(.v-sheet),
.activities-table :deep(.v-card),
.activities-table :deep(.v-sheet) {
  background-color: transparent !important;
  box-shadow: none !important;
}
</style>
