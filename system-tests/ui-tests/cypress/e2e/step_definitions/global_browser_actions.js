const { Given, Then } = require("@badeball/cypress-cucumber-preprocessor");


Then('The current URL is {string}', (url) => {
    cy.url().should('contain', url)
})

Given('The test study {string} page is opened', (url) => {
    let test_study_uid = Cypress.env('TEST_STUDY_UID')
    cy.visit(`studies/${test_study_uid}${url}`)
    cy.waitForPage()
})

Given('The {string} page is opened', (url) => {
    cy.visit(url)
    cy.waitForPage()
})

Given('The homepage is opened', () => {
    cy.visit('/')
})

Given('The studies page is opened', () => {
    cy.visit('/studies')
})