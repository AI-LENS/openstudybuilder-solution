const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let activityGroupName, abbreviation = "ABB", definition = "DEF"

When('The add activity group button is clicked', () => cy.clickButton('add-activity'))

When('Activity group is searched for and found', () => cy.searchAndCheckPresence(activityGroupName, true))

When('Activity group is searched for and not found', () => cy.searchAndCheckPresence(activityGroupName, false))

Given('Activity group is saved and snackbar message says it is {string}', (action) => saveGroup(action))

When('The test activity group container is filled with data', () => fillGroupData())

When('The activity group is edited', () => editGroup())

Then('The newly added activity group is visible in the the table', () => {
    cy.checkRowByIndex(0, 'Activity group', activityGroupName)
    cy.checkRowByIndex(0,'Sentence case name', activityGroupName.toLowerCase())
    cy.checkRowByIndex(0, 'Abbreviation', abbreviation)
    cy.checkRowByIndex(0, 'Definition', definition)
})

When('The Group name and Sentence case name and Definition fields are not filled with data', () => {
    cy.fillInput('groupform-activity-group-field', 'Test')
    cy.clearInput('groupform-activity-group-field')
    cy.clearInput('sentence-case-name-field')
})

Then('The user is not able to save the acitivity group', () => {   
    cy.get('div[data-cy="form-body"]').should('be.visible');          
    cy.get('span.dialog-title').should('be.visible').should('have.text', 'Add activity group'); 
})

Then('The message is displayed as {string} in the mandatory fields', (message) => {   
    cy.get('[data-cy="groupform-activity-group-field"]').contains('.v-messages__message', message).should('be.visible'); 
    cy.get('[data-cy="sentence-case-name-field"]').contains('.v-messages__message', message).should('be.visible');
    cy.get('[data-cy="groupform-definition-field"]').contains('.v-messages__message', message).should('be.visible');
})

When('The user enters a value for Activity group name', () => cy.fillInput('groupform-activity-group-field', "TEST"))

Then('The field for Sentence case name will be defaulted to the lower case value of the Activity group name', () => {      
    cy.get('[data-cy="sentence-case-name-field"] input').should('have.value', 'test')
})

When('The user define a value for Sentence case name and it is not identical to the value of Activity group name', () => {
    cy.fillInput('groupform-activity-group-field', "TEST")
    cy.fillInput('sentence-case-name-field', "TEST2")
})

When('The activity group edition form is filled with data', () => editGroup())

When('[API] Activity group in status Draft exists', () => createGroupViaApi())

When('[API] Activity group is approved', () => cy.approveGroup())

When('[API] Activity group is inactivated', () => cy.inactivateGroup())

When('[API] Activity group is reactivated', () => cy.reactivateGroup())

When('[API] Activity group gets new version', () => cy.groupNewVersion())

Given('[API] First activity group for search test is created', () => createGroupViaApi(`SearchTest${Date.now()}`))

Given('[API] Second activity group for search test is created', () => cy.createGroup(`SearchTest${Date.now()}`))

function fillGroupData() {
    activityGroupName = `Group${Date.now()}`
    cy.fillInput('groupform-activity-group-field', activityGroupName)
    cy.fillInput('groupform-abbreviation-field', abbreviation)
    cy.fillInput('groupform-definition-field', definition)
}

function saveGroup(action = 'created') {
    cy.intercept('/api/concepts/activities/activity-groups?page_number=1&*').as('getData')
    cy.clickButton('save-button')
    cy.get('.v-snackbar__content').contains(`Group ${action}`).should('be.visible');
    cy.wait('@getData', {timeout: 20000})
}

function editGroup() {
    activityGroupName = `${activityGroupName}Edited`
    cy.fillInput('groupform-activity-group-field', activityGroupName)
    cy.fillInput('groupform-change-description-field', "e2e test")
}

function createGroupViaApi(customName = '') {
    cy.createGroup(customName)
    cy.getGroupNameByUid().then(name => activityGroupName = name)
}