import { apiGroupName } from "./api_library_steps"
const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let activitysubgroup, abbreviation = "ABB", definition = "DEF"

When('The Add activity subgroup button is clicked', () => cy.clickButton('add-activity'))

When('Activity subgroup is searched for and found', () => cy.searchAndCheckPresence(activitysubgroup, true))

When('Activity subgroup is searched for and not found', () => cy.searchAndCheckPresence(activitysubgroup, false))

Given('Custom group name is typed', () => cy.get('[data-cy="groupform-activity-group-dropdown"] input').type(apiGroupName))

Given('Activity subgroup is saved and snackbar message says it is {string}', (action) => saveSubGroup(action))

When('The activity subgroup edition form is filled with data', () => editSubGroup())

When('The activity subgroup form is filled with data', () => fillSubGroupData())

Then('The newly added activity subgroup is visible in the the table', () => {  
    cy.checkRowByIndex(0, 'Activity subgroup', activitysubgroup)
    cy.checkRowByIndex(0,'Sentence case name', activitysubgroup.toLowerCase())
    cy.checkRowByIndex(0, 'Abbreviation', abbreviation)
    cy.checkRowByIndex(0, 'Definition', definition)
})

When('The Activity groups, Subgroup name, Sentence case name and Definition fields are not filled with data', () => {
    cy.fillInput('groupform-activity-group-field', 'test')
    cy.clearInput('sentence-case-name-field')
    cy.clearInput('groupform-activity-group-field')
})

Then('The user is not able to save the acitivity subgroup', () => {   
    cy.get('div[data-cy="form-body"]').should('be.visible');          
    cy.get('span.dialog-title').should('be.visible').should('have.text', 'Add activity subgroup'); 
})

Then('The validation appears for missing subgroup', () => cy.checkIfValidationAppears('groupform-subgroup-class'))

Then('The validation appears for missing group', () => cy.checkIfValidationAppears('groupform-activity-group-class'))

Then('The validation appears for missing subgroup name', () => cy.checkIfValidationAppears('sentence-case-name-class'))

Then('The validation appears for missing subgroup definition', () => cy.checkIfValidationAppears('groupform-definition-class'))

When('The user enters a value for Activity subgroup name', () => {
    cy.fillInput('groupform-activity-group-field', "TEST")
})

Then('The field for Sentence case name will be defaulted to the lower case value of the Activity subgroup name', () => {      
    cy.get('[data-cy="sentence-case-name-field"] input').should('have.value', 'test')
})

When('The user define a value for Sentence case name and it is not identical to the value of Activity subgroup name', () => {
    cy.fillInput('groupform-activity-group-field', "TEST")
    cy.fillInput('sentence-case-name-field', "TEST2")
})

When('[API] Activity subgroup in status Draft exists', () => createSubGroupViaApi())

When('[API] Activity subgroup is approved', () => cy.approveSubGroup())

When('[API] Activity subgroup is inactivated', () => cy.inactivateSubGroup())

When('[API] Activity subgroup is reactivated', () => cy.reactivateSubGroup())

When('[API] Activity subgroup gets new version', () => cy.subGroupNewVersion())

Given('[API] First activity subgroup for search test is created', () => createSubGroupViaApi(`SearchTest${Date.now()}`))

Given('[API] Second activity subgroup for search test is created', () => cy.createSubGroup(`SearchTest${Date.now()}`))

Given('[API] Activity subgroup is created', () => cy.createSubGroup())

When('Drafted or Retired group is not available during subgroup creation', () => cy.checkNoDataAvailable())

function fillSubGroupData() {
    activitysubgroup = `Subgroup${Date.now()}`
    cy.selectFirstVSelect('groupform-activity-group-dropdown')
    cy.fillInput('groupform-activity-group-field', activitysubgroup)
    cy.fillInput('groupform-abbreviation-field', abbreviation)
    cy.fillInput('groupform-definition-field', definition) 
}

function editSubGroup() {
    activitysubgroup = `${activitysubgroup}Edited`
    cy.fillInput('groupform-activity-group-field', activitysubgroup)
    cy.fillInput('groupform-change-description-field', "e2e test")
}

function saveSubGroup(action = 'created') {
    cy.intercept('/api/concepts/activities/activity-sub-groups?page_number=1&*').as('getData')
    cy.clickButton('save-button')
    cy.get('.v-snackbar__content').contains(`Subgroup ${action}`).should('be.visible')
    cy.wait('@getData', {timeout: 20000}) 
}

function createSubGroupViaApi(customName = '') {
    cy.intercept('/api/concepts/activities/activity-sub-groups?page_number=1&*').as('getData')
    cy.getFinalGroupUid()
    cy.createSubGroup(customName)
    cy.getSubGroupNameByUid().then(name => activitysubgroup = name)
    cy.wait('@getData', {timeout: 20000})
}