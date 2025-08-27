const { Given, When, Then } = require('@badeball/cypress-cucumber-preprocessor')

let indicationSelected, categorySelected, subCategorySelected, parameterSelected, sequenceNumber

When('The Add template button is clicked', () => cy.clickButton('add-template'))

Then("The validation appears for Indication or Disorder field", () => cy.checkIfValidationAppears('template-indication-dropdown'))

Then('The validation appears for change description field', () => cy.checkIfValidationAppears('template-change-description'))

Then("The validation appears for {string} template category field", (templateType) => cy.checkIfValidationAppears(`template-${templateType}-category`))

Then('The validation appears for {string} template subcategory field', (templateType) => cy.checkIfValidationAppears(`template-${templateType}-sub-category`))

Then('The validation appears for Template name', () => cy.checkIfValidationAppears('template-text-field'))

When('The syntax is verified', () => cy.clickButton('verify-syntax-button'))

When('The Template is added without template text', () => cy.clickFormActionButton('continue'))

When('Template change description is provided', () => cy.fillInput('template-change-description', 'updated for test'))

When('Indexes are set as not applicable', () => cy.checkAllCheckboxes())

Then('Indication or Disorder index is cleared', () => cy.clearField('template-indication-dropdown'))

Then('Category index is cleared for {string} template', (templateType) => cy.clearField(`template-${templateType}-category`))

Then('Subcategory index is cleared for {string} template', (templateType) => cy.clearField(`template-${templateType}-sub-category`))

When('Template indexes are set for {string}', (templateType) => changeIndexesIncludingSubCategory(`${templateType}`, false, false))

When('Template indexes are updated for {string}', (templateType) => changeIndexesIncludingSubCategory(`${templateType}`, true, false))

When('Template indexes are cleared and updated for {string}', (templateType) => changeIndexesIncludingSubCategory(`${templateType}`, true, true))

When('Objective criteria specific indexes are set', () => changeCommonIndexes('objective', false, false))

When('Objective criteria specific indexes are updated', () => changeCommonIndexes('objective', true, false))

When('Objective criteria specific indexes are cleared and updated', () => changeCommonIndexes('objective', true, true))

Then('User goes to Index template step', () => cy.contains('.v-stepper-item', 'Index template').click())

When('The latest sequence number is saved', () => cy.getCellValue(0, 'Sequence number').then(text => sequenceNumber = Number(text.replace(/\D/g,''))))

Then('Sequence number is incremented', () => cy.getCellValue(0, 'Sequence number').then(text => expect(Number(text.replace(/\D/g,''))).greaterThan(sequenceNumber)))

When('The new template name is prepared with a parameters', () => {
  cy.wait(1000)
  cy.fillTextArea('template-text-field', 'Test [Activity] and [Event] template')
})

When('The indication indexes edition is initiated', () => {
  changeIndex('template-indication-dropdown', true)
  cy.getText('[data-cy="template-indication-dropdown"] [class$="selection-text"]').then(text => indicationSelected = text)
})

Then('The indication index is updated', () => checkIndexValue(indicationSelected))

When('The indexes are not updated', () => cy.get('[data-cy="form-body"]').should('not.contain', indicationSelected))

When('Template indexes are verified', () => checkIndexesIncludingSubCategory())

When('Objective indexes are verified', () => checkCommonIndexes())

When('The user hides the parameter in the next step', () => cy.get('[title^="Show/hide parameter"] .v-btn__content').first().click())

When('The user picks the parameter from the dropdown list', () => {
    cy.selectLastVSelect("Activity")
    cy.get('[data-cy="Activity"] span').invoke("text").then(text => parameterSelected = text)
})

When('The template change description is cleared', () => {
  cy.wait(500)
  cy.clearField('template-change-description')
})

Then('The parameter is not visible in the text representation', () => checkParameterValue(false, 'Activity'))

Then('The parameter value is visible in the text representation', () => checkParameterValue(true, parameterSelected.split('...')[0]))

Then('The template has not applicable selected for all indexes', () => {
  cy.get('.v-sheet .v-window [type="checkbox"]').each(checkbox => cy.wrap(checkbox).should('be.checked'))
})

function checkParameterValue(shouldContain, value) {
    let condition = shouldContain ? 'contain' : 'not.contain'
    cy.get('[edit-mode="false"] .template-readonly').should(condition, value)
    cy.get('[edit-mode="false"] .pa-4').should(condition, value)
}

function changeIndexesIncludingSubCategory(templateType, update, clear) {
  cy.wait(1000)
  changeCommonIndexes(templateType, update, clear)
  changeIndex(`template-${templateType}-sub-category`, update, clear)
  cy.getText(`[data-cy="template-${templateType}-sub-category"] [class$="selection-text"]`).then(text => subCategorySelected = text)
}

function changeCommonIndexes(templateType, update, clear) {
  cy.wait(1000)
  changeIndex('template-indication-dropdown', update, clear)
  changeIndex(`template-${templateType}-category`, update, clear)
  cy.getText(`[data-cy="template-indication-dropdown"] [class$="selection-text"]`).then(text => indicationSelected = text)
  cy.getText(`[data-cy="template-${templateType}-category"] [class$="selection-text"]`).then(text => categorySelected = text)
}

function checkIndexesIncludingSubCategory() {
  checkCommonIndexes()
  checkIndexValue(subCategorySelected)
}

function checkCommonIndexes() {
  checkIndexValue(indicationSelected)
  checkIndexValue(categorySelected)
}

function checkIndexValue(expectedValue) {
  expectedValue.split(',').forEach(value => cy.get('[data-cy="form-body"]').should('contain', value.trim()))
}

export function changeIndex(indexLocator, update, clear) {
  let select = update ? (locator) => cy.selectLastMultipleSelect(locator) : (locator) => cy.selectFirstMultipleSelect(locator)
  if (clear) cy.clearField(indexLocator)
  select(indexLocator)
}

export function fillTemplateNameAndContinue(name) {
  cy.wait(1000)
  cy.fillTextArea('template-text-field', name)
  cy.clickFormActionButton('continue')
  cy.clickFormActionButton('continue')
}