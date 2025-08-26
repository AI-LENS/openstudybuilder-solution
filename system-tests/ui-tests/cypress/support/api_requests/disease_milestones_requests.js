Cypress.Commands.add('createDiseaseMiletone', () => {
    cy.request({
        method: 'POST',
        url: Cypress.env('API') + `/studies/${Cypress.env('TEST_STUDY_UID')}/study-disease-milestones`,
        body: `{"disease_milestone_type":"CTTerm_000215","study_uid":"${Cypress.env('TEST_STUDY_UID')}","repetition_indicator":false}`
    })
    cy.log('Disease milestone created - reloading')
    cy.reload()
})

Cypress.Commands.add('checkAndCreateDiseaseMilestone', () => {
    cy.request(Cypress.env('API') + `/studies/${Cypress.env('TEST_STUDY_UID')}/study-disease-milestones?page_number=1&page_size=10&total_count=true`)
        .then((resp) => {
            if (resp.body.total == 0) {
                cy.log('Disease milestone not found - creating')
                cy.createDiseaseMiletone()
            }
            else {
                cy.log('Disease milestone found - skipping creating')
            }
        })
})