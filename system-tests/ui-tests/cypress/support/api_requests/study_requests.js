const studiesInfoUrl = '/studies?include_sections=study_description&sort_by[current_metadata.identification_metadata.study_id]=true&page_size=0'
const studiesListUrl = '/studies/list'

Cypress.Commands.add('getStudyUid', (study_number) => {
  cy.sendGetRequest(studiesInfoUrl).then((response) => {
            return response.body.items
                .find(study => study.current_metadata.identification_metadata.study_number == study_number)
                .uid
  })
})

Cypress.Commands.add('getStudyUidById', (study_id) => {
  cy.sendGetRequest(studiesListUrl).then((response) => {
            return response.body.find(study => study.id == study_id).uid
  })
})


Cypress.Commands.add('createAndSetMainTestStudy', (study_number) => {
  cy.sendGetRequest(studiesInfoUrl).then((response) => {
    let test_study_id = response.body.items.find(study => study.current_metadata.identification_metadata.study_number == study_number)
    if (test_study_id == undefined) {
      cy.request('POST', Cypress.env('API') + '/studies', {
        project_number: "CDISC DEV",
        study_acronym: "E2E Main Test Study",
        study_number: study_number,
      })
      cy.createAndSetMainTestStudy(study_number)
    } else {
      Cypress.env('TEST_STUDY_UID', test_study_id.uid)
    }
    
  })
})

Cypress.Commands.add('nullRegistryIdentifiersForStudy', () => {
  cy.request({
    method: 'PATCH',
    url: Cypress.env('API') + '/studies/Study_000001',
    body: {
      current_metadata: {
        identification_metadata: {
          registry_identifiers: {
            ct_gov_id: '',
            ct_gov_id_null_value_code: null,
            eudract_id: '',
            eudract_id_null_value_code: null,
            universal_trial_number_utn: '',
            universal_trial_number_utn_null_value_code: null,
            japanese_trial_registry_id_japic: '',
            japanese_trial_registry_id_japic_null_value_code: null,
            investigational_new_drug_application_number_ind: '',
            investigational_new_drug_application_number_ind_null_value_code: null,
          },
        },
      },
    },
  })
})