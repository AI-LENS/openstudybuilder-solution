<template>
  <v-select
    v-model="model"
    :label="props.label"
    :items="allowedValues"
    item-value="term_uid"
    bg-color="white"
    variant="outlined"
    density="compact"
    hide-details
    :loading="loading"
  >
    <template #prepend-item>
      <v-row @keydown.stop>
        <v-text-field
          v-model="search"
          class="pl-6"
          :placeholder="$t('_global.search')"
        />
        <v-btn
          variant="text"
          size="small"
          icon="mdi-close"
          class="mr-3 mt-3"
          @click="reset"
        />
      </v-row>
    </template>
  </v-select>
</template>

<script setup>
import { ref, watch } from 'vue'
import { i18n } from '@/plugins/i18n'
import activityItemClassesApi from '@/api/activityItemClasses'
import termsApi from '@/api/controlledTerminology/terms'
import _debounce from 'lodash/debounce'

const props = defineProps({
  activityItemClass: {
    type: Object,
    default: null,
  },
  dataDomain: {
    type: String,
    default: null,
  },
  label: {
    type: String,
    default: () => i18n.t('ActivityInstanceForm.value'),
  },
})
const model = defineModel({ type: String })
const search = defineModel('search', { type: String })

const allowedValues = ref([])
const loading = ref(false)

const fetchTerms = _debounce(function () {
  loading.value = true
  const filters = { '*': { v: [search.value] } }
  if (props.activityItemClass.name === 'unit_dimension') {
    termsApi.getNamesByCodelist('unitDimensions', { filters }).then((resp) => {
      allowedValues.value = []
      const present = resp.data.items.find(
        (item) => item.term_uid === model.value
      )
      if (!present) {
        model.value = null
      }
      allowedValues.value = resp.data.items.map((item) => {
        return { term_uid: item.term_uid, name: item.sponsor_preferred_name }
      })
      loading.value = false
    })
  } else {
    activityItemClassesApi
      .getDatasetTerms(props.activityItemClass.uid, props.dataDomain, {
        filters,
        page_size: 50,
      })
      .then((resp) => {
        allowedValues.value = []
        const present = resp.data.items.find(
          (item) => item.term_uid === model.value
        )
        if (!present) {
          model.value = null
        }
        allowedValues.value = resp.data.items
        loading.value = false
      })
  }
}, 800)

const reset = () => {
  if (search.value && search.value !== '') {
    model.value = null
    allowedValues.value = []
    search.value = ''
  }
}

watch(search, () => {
  fetchTerms()
})
watch(
  () => props.activityItemClass,
  (value) => {
    if (value) {
      fetchTerms()
    }
  },
  { immediate: true }
)

watch(
  () => props.dataDomain,
  (value) => {
    if (value) {
      fetchTerms()
    }
  }
)

defineExpose({
  allowedValues,
})
</script>
