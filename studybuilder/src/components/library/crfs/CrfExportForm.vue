<template>
  <v-card>
    <v-card-title>
      {{ $t('OdmViewer.export') + item.name }}
    </v-card-title>
    <v-card-text>
      <v-form ref="observer">
        <v-row>
          <v-col cols="4">
            <v-select
              v-model="format"
              class="mt-5"
              :label="$t('OdmViewer.format')"
              :items="formats"
              density="compact"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
          <v-col cols="2">
            <v-switch
              v-model="draft"
              color="primary"
              class="mt-6"
              :label="$t('_global.draft')"
            />
          </v-col>
          <v-col cols="4">
            <label>{{ $t('OdmViewer.stylesheet') }}</label>
            <v-radio-group v-model="exportParams.stylesheet">
              <v-radio
                :label="$t('OdmViewer.crf_with_annotations')"
                value="sdtm"
              />
              <v-radio :label="$t('OdmViewer.blank')" value="blank" />
            </v-radio-group>
          </v-col>
        </v-row>
      </v-form>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn class="primary" :loading="loading" @click="exportElement()">
        {{ $t('_global.export') }}
      </v-btn>
      <v-btn class="secondary-btn" color="white" @click="close()">
        {{ $t('_global.close') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import crfs from '@/api/crfs'
import exportLoader from '@/utils/exportLoader'
import { DateTime } from 'luxon'
import statuses from '@/constants/statuses'

export default {
  inject: ['formRules'],
  props: {
    open: Boolean,
    item: {
      type: Object,
      default: null,
    },
    type: {
      type: String,
      default: null,
    },
  },
  emits: ['close'],
  data() {
    return {
      formats: ['PDF', 'HTML', 'XML'],
      draft: false,
      format: null,
      exportParams: {
        target_type: '',
        stylesheet: 'sdtm',
        export_to: 'v1',
        target_uid: '',
        status: '',
      },
      loading: false,
    }
  },
  methods: {
    async exportElement() {
      const { valid } = await this.$refs.observer.validate()
      if (!valid) return
      this.loading = true
      this.setExportParams(this.item)
      switch (this.format) {
        case 'PDF':
          this.exportPdf()
          break
        case 'HTML':
          this.exportHtml()
          break
        case 'XML':
          this.exportXml()
      }
    },
    exportPdf() {
      crfs.getPdf(this.exportParams).then(
        (resp) => {
          exportLoader.downloadFile(
            resp.data,
            'application/pdf',
            this.getDownloadFileName()
          )
          this.loading = false
          this.close()
        },
        () => {
          this.loading = false
        }
      )
    },
    exportHtml() {
      crfs.getXml(this.exportParams).then(
        async (resp) => {
          const parser = new DOMParser()
          const xml = parser.parseFromString(resp.data, 'application/xml')
          const xsltProcessor = new XSLTProcessor()
          crfs.getXsl(this.exportParams.stylesheet).then((resp) => {
            const xmlDoc = parser.parseFromString(resp.data, 'text/xml')
            xsltProcessor.importStylesheet(xmlDoc)
            exportLoader.downloadFile(
              new XMLSerializer().serializeToString(
                xsltProcessor.transformToDocument(xml)
              ),
              'text/html',
              this.getDownloadFileName()
            )
            this.loading = false
            this.close()
          })
        },
        () => {
          this.loading = false
        }
      )
    },
    exportXml() {
      crfs.getXml(this.exportParams).then(
        (resp) => {
          exportLoader.downloadFile(
            resp.data,
            'text/xml',
            this.getDownloadFileName()
          )
          this.loading = false
          this.close()
        },
        () => {
          this.loading = false
        }
      )
    },
    setExportParams() {
      this.exportParams.target_uid = this.item.uid
      this.exportParams.target_type = this.type
      this.exportParams.status = this.draft
        ? `${statuses.FINAL}&status=${statuses.DRAFT}`.toLowerCase()
        : statuses.FINAL.toLowerCase()
    },
    getDownloadFileName() {
      const stylesheet = this.type === 'sdtm' ? '_sdtm_crf_' : '_blank_crf_'
      const templateName = this.item.name
      return `${templateName + stylesheet + DateTime.local().toFormat('yyyy-MM-dd HH:mm')}`
    },
    close() {
      this.$emit('close')
    },
  },
}
</script>
