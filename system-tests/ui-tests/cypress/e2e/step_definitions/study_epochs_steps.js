const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let epochDescription = `Epoch ${Date.now()}`

When('User waits for epochs to load', () => {
    cy.intercept(`**/study-epochs?page_size=0`).as('getEpochs')
    cy.wait('@getEpochs').its('response.statusCode').should('eq', 200)
})

When('Study Epoch is found', () => cy.searchAndCheckPresence(epochDescription, true))

When('Study Epoch is not available', () => cy.searchAndCheckPresence(epochDescription, false))

When('A new Study Epoch is added', () => {
    cy.waitForData('study-epochs')
    cy.clickButton('create-epoch')
    cy.selectAutoComplete('epoch-type', 'Post Treatment')
    cy.selectAutoComplete('epoch-subtype', 'Elimination')
    fillRulesAndDecscription('D10', 'D99')
    save()
})

Then('The new Study Epoch is available within the table', () => {
    cy.checkRowByIndex(0, 'Epoch name', 'Elimination')
    cy.checkRowByIndex(0, 'Epoch type', 'Post Treatment')
    cy.checkRowByIndex(0, 'Epoch subtype', 'Elimination')
    cy.checkRowByIndex(0, 'Start rule', 'D10')
    cy.checkRowByIndex(0, 'End rule', 'D99')
    cy.checkRowByIndex(0, 'Description', epochDescription)
})

When('The Study Epoch is edited', () => {
    epochDescription = `Edited epoch ${Date.now()}`
    cy.wait(1000)
    fillRulesAndDecscription('D22', 'D33')
    save()
})

Then('The Type and Subtype fields are disabled', () => {
    cy.checkIfInputDisabled('epoch-type')
    cy.checkIfInputDisabled('epoch-subtype')
})

Then('The edited Study Epoch with updated values is available within the table', () => {
    cy.checkRowByIndex(0, 'Description', epochDescription)
    cy.checkRowByIndex(0, 'Start rule', 'D22')
    cy.checkRowByIndex(0, 'End rule', 'D33')
})

function save() {
    cy.clickButton('save-button')
    cy.waitForFormSave()
    cy.waitForData('study-epochs')
}

function fillRulesAndDecscription(startRule, endRule) {
    cy.fillInput('description', epochDescription)
    cy.fillInput('epoch-start-rule', startRule)
    cy.fillInput('epoch-end-rule', endRule)
}