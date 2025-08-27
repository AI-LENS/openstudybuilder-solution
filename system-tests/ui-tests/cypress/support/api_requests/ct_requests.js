Cypress.Commands.add('createAndOpenCodelist', () => {
  let number = Date.now()
  cy.request('POST', Cypress.env('API') + '/ct/codelists', {
    catalogue_name: 'SEND CT',
    definition: `Definition${number}`,
    extensible: true,
    library_name: 'Sponsor',
    name: `Name${number}`,
    nci_preferred_name: `NCI${number}`,
    sponsor_preferred_name: `SponsorName${number}`,
    submission_value: `Submission${number}`,
    template_parameter: false,
    terms: [],
  }).then((created_response) => {
    cy.log('Codelist - created - visiting')
    cy.visit('/library/ct_catalogues/All/' + created_response.body.codelist_uid)
    cy.wait(3000)
  })
})

Cypress.Commands.add('createAndOpenTerm', () => {
  let number = Date.now()
  cy.request('POST', Cypress.env('API') + '/ct/terms', {
    catalogue_name: 'SEND CT',
    code_submission_value: `SubmissionCode${number}`,
    codelist_uid: 'C100129',
    definition: `Definition${number}`,
    library_name: 'Sponsor',
    name_submission_value: `SubmissionName${number}`,
    nci_preferred_name: `NCI${number}`,
    order: '1',
    sponsor_preferred_name: `SponsorName${number}`,
    sponsor_preferred_name_sentence_case: `SentanceName${number}`,
    synonyms: `Synonyms${number}`,
  }).then((created_response) => {
    cy.log('Term - created - visiting')
    cy.visit('/library/ct_catalogues/All/C100129/terms/' + created_response.body.term_uid)
    cy.wait(3000)
  })
})


Cypress.Commands.add('createCTPackage', (packageName) => {
  cy.request({
    url: `${Cypress.env('API')}/ct/packages/sponsor`,
    method: 'POST',
    body: {
      extends_package: `${packageName}`,
      effective_date: `${new Date().toISOString().split('T')[0]}`
    },
    failOnStatusCode: false
  }).then((response) => {
    expect(response.status).to.be.oneOf([201, 409])
    cy.log(`${packageName} exists`)
  })
})