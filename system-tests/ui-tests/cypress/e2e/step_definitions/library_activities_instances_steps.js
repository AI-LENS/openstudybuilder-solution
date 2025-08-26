import { apiActivityName } from "./api_library_steps";
const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let activityInstance, topicCode = `Topic${Date.now()}`
let nciconceptid = "NCI-ID", nciname = 'NCI-name', adamcode = "Adam-code"

When('The Add Activity Instance button is clicked', () => startActivityCreation())

When('All activity instance data is filled in', () => addInstanceAllData())

When('The activity instance mandatory data is filled in and custom activity is selected', () => addInstanceMandatoryData(`Topic${Date.now()}`, apiActivityName))

When('The activity instance mandatory data is filled in', () => addInstanceMandatoryData())

When('Second activity instance data is created with the same topic code', () => addInstanceMandatoryData(topicCode))

Then('Activity Instance is searched for and not found', () => cy.searchAndCheckPresence(activityInstance, false))

Then('Activity Instance is searched for and found', () => cy.searchAndCheckPresence(activityInstance, true))

Then('The newly added Activity Instance item is added in the table by default', () => {
    cy.checkRowByIndex(0, 'Activity Instance', activityInstance)
    cy.checkRowByIndex(0, 'NCI Concept ID', nciconceptid)
    cy.checkRowByIndex(0, 'Topic code', topicCode)
    cy.checkRowByIndex(0, 'ADaM parameter code', adamcode)
    cy.checkRowByIndex(0, 'Required for activity', "Yes")
    cy.checkRowByIndex(0, 'Default selected for activity', "No")
    cy.checkRowByIndex(0, 'Data sharing', "No")
    cy.checkRowByIndex(0, 'Legacy usage', "No")
})

Then('The validation message appears for Activity field', () => cy.checkIfValidationAppears('instanceform-activity-class'))

Then('The validation message appears for class field', () => cy.checkIfValidationAppears('instanceform-instanceclass-class'))

Then('The validation error for {string} activity in not allowed state is displayed', (status) => {
    const validationMessage = `Selected activity is in ${status.toUpperCase()} state. Please move the activity to FINAL state before creating the Activity Instance.`
    cy.get('.v-alert__content').should('have.text', validationMessage)
})

Then('The message of {string} displayed in all the above mandatory fields', (message) => {
    cy.get('.v-messages__message').should('contain', message)
}) 

When('The Activity instance activity is selected', () => cy.selectFirstVSelect('instanceform-activity-dropdown'))

When('The Activity instance group data is filled in', () => fillInstanceActivityGroupData())

When('The Activity instance class data is filled in', () => fillInstanceClassData())

When('The Activity created through API is selected', () => fillInstanceActivityGroupData(apiActivityName))

When('The user enters a value for Activity instance name', () => cy.fillInput('instanceform-instancename-field', "TEST"))

Then('The field for Sentence case name will be defaulted to the lower case value of the Activity instance name', () => {      
    cy.get('[data-cy="sentence-case-name-field"]').within(() => cy.get('input').invoke('val').should('contain', "test"))
})

When('The user define a value for Sentence case name and it is not identical to the value of Activity instance name', () => {
    cy.fillInput('instanceform-instancename-field', "TEST")
    cy.fillInput('sentence-case-name-field', "TEST2")
})

Then('The user is not able to save', () => cy.get('[data-cy="save-button"]').should('be.visible'))

Then('The user is not able to continue', () => cy.get('[data-cy="continue-button"]').should('be.visible'))

When('The activity instance edition form is filled with data', () => editActivityInstance())

Then('Activity instance cannot be saved', () => cy.get('.v-overlay .v-window').should('be.visible'))

When('[API] Activity Instance in status Final with Final group, subgroup and activity linked exists', () => {
    if (!activityInstance) createAndApproveActivityInstanceViaApi()
    cy.getActivityInstanceNameByUid().then(name => activityInstance = name)
})

Then('The edit form displays text {string}', (message) => cy.get('.v-alert').should('contain', message))

Then('User waits for activity instance to be {string}', (action) => {
    cy.checkSnackbarMessage(`Activity ${action}`)
    cy.wait('@getData', {timeout: 20000})
    cy.wait('@getData2', {timeout: 30000})
})

When('[API] Activity Instance in status Draft exists', () => createActivityInstanceViaApi())

When('[API] Activity Instance is approved', () => cy.approveActivityInstance())

When('[API] Activity Instance is inactivated', () => cy.inactivateActivityInstance())

When('[API] Activity Instance new version is created', () => cy.activityInstanceNewVersion())

Given('[API] First activity instance for search test is created', () => createActivityInstanceViaApi(`SearchTest${Date.now()}`))

Given('[API] Second activity instance for search test is created', () => cy.createActivityInstance(`SearchTest${Date.now()}`))

function addInstanceAllData() {
    addInstanceMandatoryData()
    cy.fillInput('instanceform-nciconceptid-field', nciconceptid)
    cy.fillInput('instanceform-nciconceptname-field', nciname)
    cy.fillInput('instanceform-adamcode-field', adamcode)
    cy.get('[data-cy="instanceform-requiredforactivity-checkbox"] input').check()
}

function addInstanceMandatoryData(code = topicCode, customActivity = '') {
    activityInstance = `Instance${Date.now()}`
    fillInstanceActivityGroupData(customActivity)
    fillInstanceClassData()
    cy.fillInput('instanceform-instancename-field', activityInstance)
    cy.fillInput('instanceform-definition-field', 'DEF')
    cy.fillInput('instanceform-topiccode-field', code) 
}

function startActivityCreation() {
    cy.intercept('/api/concepts/activities/activities?*').as('getData')
    cy.intercept('/api/concepts/activities/activity-instances?*').as('getData2')
    cy.clickButton('add-activity')
    cy.wait(1000)
}

function fillInstanceClassData() {
    cy.selectFirstVSelect('instanceform-instanceclass-dropdown')
    cy.clickFormActionButton('continue')
}

function fillInstanceActivityGroupData(customActivity = '') {
    if (customActivity) cy.get('[data-cy=instanceform-activity-dropdown] input').type(customActivity)
    cy.selectFirstVSelect('instanceform-activity-dropdown')
    cy.get('[data-cy=instanceform-activitygroup-table]').within(() => cy.get('.v-checkbox-btn').first().click())
    cy.clickFormActionButton('continue')
}

function editActivityInstance() {
    activityInstance = `Update ${activityInstance}`
    cy.intercept('/api/concepts/activities/activities?*').as('getData')
    cy.intercept('/api/concepts/activities/activity-instances?*').as('getData2')
    cy.get('.v-card-title').should('contain', 'Edit activity instance')
    cy.wait(1000)
    cy.clickFormActionButton('continue')
    cy.clickFormActionButton('continue')
    cy.fillInput('instanceform-instancename-field', activityInstance)
    cy.fillInput('instanceform-definition-field', "update")
}

function createActivityInstanceViaApi(customName = '') {
    cy.getFinalGroupUid()
    cy.getFinalSubGroupUid()
    cy.getClassUid()
    cy.createActivity()
    cy.approveActivity()
    cy.createActivityInstance(customName)
    cy.getActivityInstanceNameByUid().then(name => activityInstance = name)
    cy.getActivityInstanceTopicCodeByUid().then(code => topicCode = code)
}

function createAndApproveActivityInstanceViaApi() {
    cy.getClassUid()
    createAndApproveViaApi(() => cy.createGroup(), () => cy.approveGroup())
    createAndApproveViaApi(() => cy.createSubGroup(), () => cy.approveSubGroup())
    createAndApproveViaApi(() => cy.createActivity(), () => cy.approveActivity())
    createAndApproveViaApi(() => cy.createActivityInstance(), () => cy.approveActivityInstance())
}

function createAndApproveViaApi(createFunction, approveFunction) {
    createFunction()
    approveFunction()
}
