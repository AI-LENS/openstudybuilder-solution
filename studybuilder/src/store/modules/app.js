import Vue from 'vue'
import i18n from '../../plugins/i18n'
import generalUtils from '@/utils/generalUtils'

const studyId = getStudyUid()

const state = {
  drawer: true,
  section: '',
  breadcrumbs: [],
  helpPath: '',
  userData: {},
  studyUid: 'none',
  menuItems: {
    Library: {
      url: '/library',
      items: [
        {
          title: i18n.t('Sidebar.library.about'),
          url: { name: 'Library' },
          icon: 'mdi-information-outline'
        },
        {
          id: 'process_overview_tile',
          title: i18n.t('Sidebar.library.process_overview'),
          icon: 'mdi-arrow-right-bold-outline',
          url: { name: 'ProcessOverview' },
          description: i18n.t('Library.process_overview_description')
        },
        {
          id: 'codelists_tile',
          title: i18n.t('Sidebar.library.code_lists'),
          icon: 'mdi-folder-text-outline',
          description: i18n.t('Library.codelist_description'),
          children: [
            {
              title: i18n.t('Sidebar.dashboard'),
              url: { name: 'CTDashboard' }
            },
            {
              title: i18n.t('Sidebar.library.ct_catalogues'),
              url: { name: 'CtCatalogues' }
            },
            {
              title: i18n.t('Sidebar.library.ct_packages'),

              url: { name: 'CtPackages' }
            },
            {
              title: i18n.t('Sidebar.library.cdisc'),
              url: { name: 'CDISC' }
            },
            {
              title: i18n.t('Sidebar.library.sponsor'),
              url: { name: 'Sponsor' }
            }
          ]
        },
        {
          id: 'dictionaries_tile',
          title: i18n.t('Sidebar.library.dictionaries'),
          icon: 'mdi-book-open-outline',
          description: i18n.t('Library.dictionaries_description'),
          children: [
            {
              title: i18n.t('Sidebar.library.snomed'),
              url: { name: 'Snomed' }
            },
            {
              title: i18n.t('Sidebar.library.meddra'),
              url: { name: 'MedDra' }
            },
            {
              title: i18n.t('Sidebar.library.medrt'),
              url: { name: 'MedRt' }
            },
            {
              title: i18n.t('Sidebar.library.unii'),
              url: { name: 'Unii' }
            },
            {
              title: i18n.t('Sidebar.library.loinc'),
              url: { name: 'Loinc' }
            },
            {
              title: i18n.t('Sidebar.library.ucum'),
              url: { name: 'Ucum' }
            }
          ]
        },
        {
          id: 'concepts_tile',
          title: i18n.t('Sidebar.library.concepts'),
          icon: 'mdi-car-shift-pattern',
          description: i18n.t('Library.concepts_description'),
          children: [
            {
              title: i18n.t('Sidebar.library.activities'),
              url: { name: 'Activities' }
            },
            {
              title: i18n.t('Sidebar.library.units'),
              url: { name: 'Units' }
            },
            {
              title: i18n.t('Sidebar.library.crfs'),
              url: { name: 'Crfs' }
            },
            {
              title: i18n.t('Sidebar.library.compounds'),
              url: { name: 'Compounds' }
            }
          ]
        },
        {
          id: 'syntax_templates_tile',
          title: i18n.t('Sidebar.library.syntax_templates'),
          icon: 'mdi-folder-star-outline',
          description: i18n.t('Library.syntax_templates_description'),
          children: [
            {
              title: i18n.t('Sidebar.library.objective_templates'),
              url: { name: 'ObjectiveTemplates' }
            },
            {
              title: i18n.t('Sidebar.library.endpoint_templates'),
              url: { name: 'EndpointTemplates' }
            },
            {
              title: i18n.t('Sidebar.library.timeframe_templates'),
              url: { name: 'TimeframeTemplates' }
            },
            {
              title: i18n.t('Sidebar.library.criteria_templates'),
              url: { name: 'CriteriaTemplates' }
            },
            {
              title: i18n.t('Sidebar.library.activity_templates'),
              url: { name: 'ActivityTemplates' }
            },
            {
              title: i18n.t('Sidebar.library.footnote_templates'),
              url: { name: 'FootnoteTemplates' }
            }
          ]
        },
        {
          id: 'template_instantiations_tile',
          title: i18n.t('Sidebar.library.template_instantiations'),
          icon: 'mdi-folder-account-outline',
          description: i18n.t('Library.template_instantiations_description'),
          children: [
            {
              title: i18n.t('Sidebar.library.objective_instances'),
              url: { name: 'Objectives' }
            },
            {
              title: i18n.t('Sidebar.library.endpoint_instances'),
              url: { name: 'Endpoints' }
            },
            {
              title: i18n.t('Sidebar.library.timeframe_instances'),
              url: { name: 'Timeframes' }
            },
            {
              title: i18n.t('Sidebar.library.activity_instruction_instances'),
              url: { name: 'ActivityInstructions' }
            },
            {
              title: i18n.t('Sidebar.library.criteria_instances'),
              url: { name: 'CriteriaInstances' }
            },
            {
              title: i18n.t('Sidebar.library.footnote_instances'),
              url: { name: 'FootnoteInstances' }
            }
          ]
        },
        {
          id: 'template_collections_tile',
          title: i18n.t('Sidebar.library.template_collections'),
          icon: 'mdi-folder-star-multiple-outline',
          description: i18n.t('Library.template_collections_description'),
          children: [
            {
              title: i18n.t('Sidebar.library.project_templates'),
              url: { name: 'ProjectTemplates' }
            },
            {
              title: i18n.t('Sidebar.library.shared_templates'),
              url: { name: 'SharedTemplates' }
            },
            {
              title: i18n.t('Sidebar.library.supporting_templates'),
              url: { name: 'SupportingTemplates' }
            }
          ]
        },
        {
          id: 'data_exchange_std_tile',
          title: i18n.t('Sidebar.library.data_exchange_std'),
          icon: 'mdi-arrow-decision-outline',
          description: i18n.t('Library.data_exchange_standards_description'),
          children: [
            {
              title: i18n.t('Sidebar.library.cdash'),
              url: { name: 'Cdash' }
            },
            {
              title: i18n.t('Sidebar.library.sdtm'),
              url: { name: 'Sdtm' }
            },
            {
              title: i18n.t('Sidebar.library.adam'),
              url: { name: 'Adam' }
            }
          ]
        },
        {
          id: 'list_tile',
          title: i18n.t('Sidebar.library.list'),
          icon: 'mdi-format-list-bulleted-square',
          description: i18n.t('Library.list_description'),
          children: [
            {
              title: i18n.t('Sidebar.library.gen_clinical_metadata'),
              url: { name: 'GeneralClinicalMetadata' }
            },
            {
              title: i18n.t('Sidebar.library.cdash_std'),
              url: { name: 'CdashStandards' }
            },
            {
              title: i18n.t('Sidebar.library.sdtm_std_cst'),
              url: { name: 'SdtmStdCst' }
            },
            {
              title: i18n.t('Sidebar.library.sdtm_std_dmw'),
              url: { name: 'SdtmStdDmw' }
            },
            {
              title: i18n.t('Sidebar.library.adam_std_cst'),
              url: { name: 'AdamStdCst' }
            },
            {
              title: i18n.t('Sidebar.library.adam_std_new'),
              url: { name: 'AdamStdNew' }
            }
          ]
        }
      ]
    },
    Studies: {
      url: '/study',
      items: [
        {
          title: i18n.t('Sidebar.study.about'),
          url: { name: 'Studies' },
          icon: 'mdi-information-outline'
        },
        {
          id: 'process_overview_tile',
          title: i18n.t('Sidebar.study.process_overview'),
          icon: 'mdi-arrow-right-bold-outline',
          children: [
            {
              title: i18n.t('Sidebar.study.protocol_process'),
              url: { name: 'ProtocolProcess' }
            }
          ],
          description: i18n.t('Studies.process_overview_description')
        },
        {
          title: i18n.t('Sidebar.study.select'),
          url: { name: 'SelectOrAddStudy' },
          icon: 'mdi-view-list'
        },
        {
          title: i18n.t('Sidebar.study.manage'),
          icon: 'mdi-wrench-outline',
          description: i18n.t('Studies.manage_description'),
          children: [
            {
              title: i18n.t('Sidebar.study.study_status'),
              url: { name: 'StudyStatus', params: { study_id: studyId } },
              studyRequired: true
            }
          ]
        },
        {
          title: i18n.t('Sidebar.study.define'),
          icon: 'mdi-note-edit-outline',
          description: i18n.t('Studies.define_description'),
          children: [
            {
              title: i18n.t('Sidebar.study.specification_overview'),
              url: { name: 'SpecificationDashboard', params: { study_id: studyId } },
              studyRequired: true,
              hidden: true
            },
            {
              title: i18n.t('Sidebar.study.study_title'),
              url: { name: 'StudyTitle', params: { study_id: studyId } },
              studyRequired: true
            },
            {
              title: i18n.t('Sidebar.study.registry_ids'),
              url: { name: 'StudyRegistryIdentifiers', params: { study_id: studyId } },
              studyRequired: true
            },
            {
              title: i18n.t('Sidebar.study.study_properties'),
              url: { name: 'StudyProperties', params: { study_id: studyId } },
              studyRequired: true
            },
            {
              title: i18n.t('Sidebar.study.study_structure'),
              url: { name: 'StudyStructure', params: { study_id: studyId } },
              studyRequired: true
            },
            {
              title: i18n.t('Sidebar.study.population'),
              url: { name: 'StudyPopulation', params: { study_id: studyId } },
              studyRequired: true
            },
            {
              title: i18n.t('Sidebar.study.study_criteria'),
              url: { name: 'StudySelectionCriteria', params: { study_id: studyId } },
              studyRequired: true
            },
            {
              title: i18n.t('Sidebar.study.study_interventions'),
              url: { name: 'StudyInterventions', params: { study_id: studyId } },
              studyRequired: true
            },
            {
              title: i18n.t('Sidebar.study.purpose'),
              url: { name: 'StudyPurpose', params: { study_id: studyId } },
              studyRequired: true
            },
            {
              title: i18n.t('Sidebar.study.activities'),
              url: { name: 'StudyActivities', params: { study_id: studyId } },
              studyRequired: true
            },
            {
              title: i18n.t('Sidebar.study.terminology'),
              url: { name: 'StudyTerminology', params: { study_id: studyId } },
              hidden: true
            }
          ]
        },
        {
          title: i18n.t('Sidebar.study.build'),
          icon: 'mdi-apps',
          url: { name: 'Build' },
          description: i18n.t('Studies.build_description'),
          children: [
            {
              title: i18n.t('Sidebar.study.standarisation_plan'),
              url: { name: 'StandardisationPlan' },
              hidden: true
            },
            {
              title: i18n.t('Sidebar.study.protocol_elements'),
              url: { name: 'ProtocolElements', params: { study_id: studyId } },
              studyRequired: true
            },
            {
              title: i18n.t('Sidebar.study.crf_specifications'),
              url: { name: 'CrfSpecifications' },
              hidden: true
            },
            {
              title: i18n.t('Sidebar.study.study_disclosure'),
              url: { name: 'StudyDisclosure' },
              hidden: true
            },
            {
              title: i18n.t('Sidebar.study.trial_supplies_spec'),
              url: { name: 'TrialSuppliesSpecifications' },
              hidden: true
            },
            {
              title: i18n.t('Sidebar.study.odm_specification'),
              url: { name: 'OdmSpecification' },
              hidden: true
            },
            {
              title: i18n.t('Sidebar.study.ctr_odm_xml'),
              url: { name: 'CtrOdmXml' },
              hidden: true
            },
            {
              title: i18n.t('Sidebar.study.sdtm_specification'),
              url: { name: 'SdtmSpecification' },
              hidden: true
            },
            {
              title: i18n.t('Sidebar.study.sdtm_study'),
              url: { name: 'SdtmStudyDesignDatasets' }
            },
            {
              title: i18n.t('Sidebar.study.adam_spec'),
              url: { name: 'AdamSpecification' },
              hidden: true
            }
          ]
        },
        {
          title: i18n.t('Sidebar.study.list'),
          icon: 'mdi-format-list-bulleted-square',
          description: i18n.t('Studies.list_description'),
          children: [
            {
              title: i18n.t('Sidebar.study.mma_trial_metadata'),
              url: { name: 'MmaTrialMetadata' },
              hidden: true
            },
            {
              title: i18n.t('Sidebar.study.sdtm_define_p21'),
              url: { name: 'SdtmDefineP21' },
              hidden: true
            },
            {
              title: i18n.t('Sidebar.study.sdtm_define_cst'),
              url: { name: 'SdtmDefineCst' },
              hidden: true
            },
            {
              title: i18n.t('Sidebar.study.dmw_additional_metadata'),
              url: { name: 'DmwAdditionalMetadata' },
              hidden: true
            },
            {
              title: i18n.t('Sidebar.study.sdtm_additional_metadata'),
              url: { name: 'SdtmAdditionalMetadata' },
              hidden: true
            },
            {
              title: i18n.t('Sidebar.study.adam_define_p21'),
              url: { name: 'AdamDefineP21' },
              hidden: true
            },
            {
              title: i18n.t('Sidebar.study.adam_define_cst'),
              url: { name: 'AdamDefineCst' },
              hidden: true
            },
            {
              title: i18n.t('Sidebar.study.analysis_study_metadata_new'),
              url: { name: 'AnalysisStudyMetadataNew' }
            }
          ]
        }
      ]
    },
    Admin: {},
    Help: {}
  }
}

const getters = {
  drawer: state => state.drawer,
  section: state => state.section,
  studyUid: state => state.studyUid,
  breadcrumbs: state => state.breadcrumbs,
  getBreadcrumbsLevel: state => level => {
    if (state.breadcrumbs.length > level) {
      return state.breadcrumbs[level]
    }
    return undefined
  },
  helpUrl: state => {
    const baseUrl = Vue.prototype.$config.DOC_BASE_URL.replace(/\/+$/, '')
    if (state.helpPath) {
      return `${baseUrl}/guides/${state.helpPath}`
    }
    return `${baseUrl}/guides/userguide/userguides_introduction.html`
  },
  userData: state => state.userData,
  menuItems: state => state.menuItems,
  libraryMenu: state => state.menuItems.Library,
  studiesMenu: state => state.menuItems.Studies,
  findMenuItemPath: state => (section, routeName) => {
    let result
    let subResult
    state.menuItems[section].items.forEach(item => {
      if (item.url && item.url.name === routeName) {
        result = item
      } else if (item.children && item.children.length) {
        item.children.forEach(subItem => {
          if (subItem.url.name === routeName) {
            result = item
            subResult = subItem
          }
        })
      }
    })
    return [result, subResult]
  }
}

const mutations = {
  SET_DRAWER (state, value) {
    state.drawer = value
  },
  SET_SECTION (state, section) {
    state.section = section
    localStorage.setItem('section', section)
    if (section) {
      state.breadcrumbs = [
        {
          text: section, disabled: true, to: { name: section }, exact: true
        }
      ]
    }
  },
  RESET_BREADCRUMBS (state) {
    state.breadcrumbs = []
    localStorage.removeItem('section')
    localStorage.removeItem('breadcrumbs')
  },
  SET_BREADCRUMBS (state, breadcrumbs) {
    state.breadcrumbs = breadcrumbs
  },
  ADD_BREADCRUMBS_LEVEL (state, { item, pos, replace }) {
    function appendToBreadcrumbs () {
      for (const level of state.breadcrumbs) {
        Vue.set(level, 'disabled', false)
      }
      item.disabled = true
      state.breadcrumbs.push(item)
    }
    const lastIndex = state.breadcrumbs.length - 1
    if (state.breadcrumbs.length && pos === lastIndex && state.breadcrumbs[lastIndex].text === item.text) {
      return
    }
    if (pos !== undefined) {
      if (!replace) {
        state.breadcrumbs = state.breadcrumbs.slice(0, pos)
        appendToBreadcrumbs()
      } else {
        item.disabled = pos === state.breadcrumbs.length - 1
        Vue.set(state.breadcrumbs, pos, item)
        state.breadcrumbs = state.breadcrumbs.slice(0, pos + 1)
      }
    } else {
      appendToBreadcrumbs()
    }
    localStorage.setItem('breadcrumbs', JSON.stringify(state.breadcrumbs))
  },
  TRUNCATE_BREADCRUMBS_FROM_LEVEL (state, pos) {
    state.breadcrumbs = state.breadcrumbs.slice(0, pos)
    localStorage.setItem('breadcrumbs', JSON.stringify(state.breadcrumbs))
  },
  SET_HELP_PATH (state, value) {
    state.helpPath = value
  },
  SET_USER_DATA (state, value) {
    state.userData = value
    if (state.userData.studyNumberLength === undefined) {
      state.userData.studyNumberLength = 4
    }
    localStorage.setItem('userData', JSON.stringify(value))
  }
}

const actions = {
  initialize ({ commit, dispatch }) {
    const section = localStorage.getItem('section')
    const breadcrumbs = localStorage.getItem('breadcrumbs')
    const userData = localStorage.getItem('userData')
    if (section) {
      commit('SET_SECTION', section)
    }
    if (breadcrumbs) {
      commit('SET_BREADCRUMBS', JSON.parse(breadcrumbs))
    }
    if (userData) {
      commit('SET_USER_DATA', JSON.parse(userData))
    } else {
      commit('SET_USER_DATA', { darkTheme: false, rows: 10, studyNumberLength: 4 })
    }
    dispatch('studiesGeneral/initialize', null, { root: true })
  },
  addBreadcrumbsLevel ({ commit }, { text, to, index, replace }) {
    const item = {
      text,
      to,
      exact: true
    }
    commit('ADD_BREADCRUMBS_LEVEL', { item, pos: index, replace })
  }
}

function getStudyUid () {
  const studyUidFromUrl = generalUtils.extractStudyUidFromUrl(document.location.pathname)
  if (studyUidFromUrl) {
    return studyUidFromUrl
  }
  const selectedStudyFromLocalStorage = JSON.parse(localStorage.getItem('selectedStudy'))
  if (selectedStudyFromLocalStorage) {
    return selectedStudyFromLocalStorage.uid
  }
  return '*'
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}
