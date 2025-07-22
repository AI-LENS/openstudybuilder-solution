const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('Modal window form is closed by clicking cancel button', () => {
    cy.get('[data-cy="form-body"] [data-cy="cancel-button"]').click()
})

When('Fullscreen wizard is closed by clicking cancel button', () => {
    cy.contains('[data-cy="form-body"].fullscreen-dialog .v-card-actions button', 'Cancel').click()
})

When('Overlay cancel button is clicked', () => cy.get('.v-overlay [data-cy="cancel-button"]').click())

When('Action is confirmed by clicking continue', () => cy.clickButton('continue-popup'))

Then('The form is no longer available', () => cy.get('[data-cy="form-body"]').should('not.exist'))

When('Form save button is clicked', () => cy.clickFormActionButton('save'))

When('Form continue button is clicked', () => cy.clickFormActionButton('continue'))

When('Modal window {string} button is clicked', (value) => cy.contains('.v-card-actions button', value).click())

When('The overlay is not closed', () => cy.get('.v-overlay').should('be.visible'))

When('User goes to Change description step', () => cy.contains('.v-stepper-item', 'Change description', {matchCase: false}).click())