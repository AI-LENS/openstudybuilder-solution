import { apiGroupName } from "./api_library_steps"
const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

export let activityName, synonym =`Synonym${Date.now()}`
const nciconceptid = "NCIID", nciconceptname = "NCINAME", abbreviation = "ABB", definition = "DEF"

When('The Add activity button is clicked', () => cy.clickButton('add-activity'))

Then('Activity is searched for and not found', () => cy.searchAndCheckPresence(activityName, false))

Then('Activity is searched for and found', () => cy.searchAndCheckPresence(activityName, true))

Then('Activity is created and confirmation message is shown', () => waitForActivityToBeCreated())

Then('The activity form is filled with only mandatory data', () => fillNewActivityData())

Then('The activity form is filled in using group and subgroup created through API', () => fillNewActivityData(false, apiGroupName))

When('The activity form is filled with all data', () => fillNewActivityData(true))

Then('Validation error for GroupingHierarchy is displayed', () => cy.checkSnackbarMessage('1 validation error for ActivityGroupingHierarchySimpleModel'))

Then('The user adds already existing synonym', () => cy.fillInputNew('activityform-synonyms-field', synonym))

Given('Custom group name is typed and selected in activity form', () => {
    cy.get('[data-cy="activityform-activity-group-dropdown"] input').type(apiGroupName)
    cy.selectFirstVSelect('activityform-activity-group-dropdown')
})

When('Drafted subgroup is not available during activity creation', () => {
    cy.get('[data-cy="activityform-activity-subgroup-dropdown"]').click()
    cy.checkNoDataAvailable()
})

Then('The user is not able to save activity with already existing synonym and error message is displayed', () => {
    cy.get('div[data-cy="form-body"]').should('be.visible');          
    cy.get('.v-snackbar__content').should('be.visible').should('contain.text', 'Following Activities already have the provided synonyms'); 
})

Then('The newly added activity is added in the table', () => {  
    cy.checkRowByIndex(0, 'Activity name', activityName)
    cy.checkRowByIndex(0, 'Sentence case name', activityName.toLowerCase())
    cy.checkRowByIndex(0, 'Synonyms', synonym)
    cy.checkRowByIndex(0, 'NCI Concept ID', nciconceptid)
    cy.checkRowByIndex(0, 'NCI Concept Name', nciconceptname)
    cy.checkRowByIndex(0, 'Abbreviation', abbreviation)
    cy.checkRowByIndex(0, 'Data collection', "Yes")
})

Then('The user is not able to save the acitivity', () => {   
    cy.get('div[data-cy="form-body"]').should('be.visible');          
    cy.get('span.dialog-title').should('be.visible').should('have.text', 'Add activity'); 
})

Then('The validation message appears for activity group', () => cy.checkIfValidationAppears('activityform-activity-group-class'))

Then('The validation message appears for activity name', () => cy.checkIfValidationAppears('activityform-activity-name-class'))

Then('The validation message appears for activity subgroup', () => cy.checkIfValidationAppears('activityform-activity-subgroup-class'))

Then('The validation message appears for sentance case name that it is not identical to name', () => cy.checkIfValidationAppears('sentence-case-name-class', 'Sentence case name value must be identical to name value'))

When('Select a value for Activity group field', () => cy.selectFirstVSelect('activityform-activity-group-dropdown'))

Then('The default value for Data collection must be checked', () => {      
    cy.get('[data-cy="activityform-datacollection-checkbox"]').within(() => {
        cy.get('.mdi-checkbox-marked').should('exist');
    })
})

When('The user enters a value for Activity name', () => {
    cy.fillInput('activityform-activity-name-field', "TEST")
})

Then('The field for Sentence case name will be defaulted to the lower case value of the Activity name', () => {      
    cy.get('[data-cy$="activity-name-field"] input').then(($input) => {
        cy.get('[data-cy="sentence-case-name-field"] input').should('have.value', $input.val().toLowerCase())
    })
})

When('The user define a value for Sentence case name and it is not identical to the value of Activity name', () => {
    cy.fillInput('activityform-activity-name-field', "TEST")
    cy.fillInput('sentence-case-name-field', "TEST2")
})

When('The activity edition form is filled with data', () => editActivity())

When('[API] Activity in status Final with Final group and subgroub exists', () => {
    if (!activityName) createActivityViaApi(true)
})

Then('[API] Study Activity is created and group is drafted', () => {
    createAndChangeStatusOfLinkedItemViaApi(() => cy.groupNewVersion())
})

Then('[API] Study Activity is created and group is inactivated', () => {
    createAndChangeStatusOfLinkedItemViaApi(() => cy.inactivateGroup())
})

Then('[API] Study Activity is created and subgroup is drafted', () => {
    createAndChangeStatusOfLinkedItemViaApi(() => cy.subGroupNewVersion())
})

Then('[API] Study Activity is created and subgroup is inactivated', () => {
    createAndChangeStatusOfLinkedItemViaApi(() => cy.inactivateSubGroup())
})

Then('[API] Study Activity is created and approved', () => createActivityViaApi(true))

Then('[API] Study Activity is created and not approved', () => createActivityViaApi(false))

Then('[API] Study Activity is created', () => getGroupAndSubgroupAndCreateActivity())

When('[API] Activity in status Draft exists', () => createActivityViaApiSimplified())

When('[API] Activity is approved', () => cy.approveActivity())

When('[API] Activity is inactivated', () => cy.inactivateActivity())

When('[API] Activity is reactivated', () => cy.reactivateActivity())

When('[API] Activity new version is created', () => cy.activityNewVersion())

Given('[API] First activity for search test is created', () => createActivityViaApiSimplified(`SearchTest${Date.now()}`))

Given('[API] Second activity for search test is created', () => cy.createActivity(`SearchTest${Date.now()}`))

When('The user opens version history of activity subgroup', () => {
    cy.intercept('**versions').as('version_history_data')
    cy.tableRowActions(0, 'History')
})

Then('The version history displays correct data for activity subgroup', () => {
    cy.wait('@version_history_data').then((req) => {
        let data = req.response.body[0]
        cy.getCellValue(0, 'Activity group', data.activity_groups[0].name)
        cy.getCellValue(0, 'Activity subgroup', data.name)
        cy.getCellValue(0, 'Sentence case name', data.name_sentence_case)
        cy.getCellValue(0, 'Status', data.status)
        cy.getCellValue(0, 'Version', data.version)
        cy.getCellValue(0, 'User', data.author_username)

    })
})

function fillNewActivityData(fillOptionalData = false, customGroup = '') {
    cy.intercept('/api/concepts/activities/activities?page_number=1&page_size=0&total_count=true&sort_by=%7B%22name%22:true%7D&filters=%7B%7D').as('getData')
    activityName = `Activity${Date.now()}`
    if (customGroup) cy.get('[data-cy="activityform-activity-group-dropdown"] input').type(customGroup)
    cy.selectFirstVSelect('activityform-activity-group-dropdown')
    cy.selectFirstVSelect('activityform-activity-subgroup-dropdown')
    cy.fillInput('activityform-activity-name-field', activityName)
    if (fillOptionalData) {
        cy.fillInputNew('activityform-synonyms-field', synonym)
        cy.fillInput('activityform-nci-concept-id-field', nciconceptid)
        cy.fillInput('activityform-nci-concept-name-field', nciconceptname)
        cy.fillInput('activityform-abbreviation-field', abbreviation)
        cy.fillInput('activityform-definition-field', definition)
    }
}

function waitForActivityToBeCreated() {
    cy.checkSnackbarMessage('Activity created')
    cy.wait('@getData', {timeout: 20000})
    cy.get('.dialog-title').should('not.exist')
}

function editActivity() {
    activityName = `Update ${activityName}`
    cy.fillInput('activityform-activity-name-field', activityName)
    cy.contains('.v-label', 'Reason for change').parent().find('[value]').type('Test update')
}

function createActivityViaApi(approve) {
    createAndApproveViaApi(() => cy.createGroup(), () => cy.approveGroup())
    createAndApproveViaApi(() => cy.createSubGroup(), () => cy.approveSubGroup())
    approve ? createAndApproveViaApi(() => cy.createActivity(), () => cy.approveActivity()) : cy.createActivity()
    cy.getActivityNameByUid().then(name => activityName = name)
}

function createActivityViaApiSimplified(customName = '') {
    cy.intercept('/api/concepts/activities/activities?page_number=1&*').as('getData')
    getGroupAndSubgroupAndCreateActivity(customName)
    cy.getActivityNameByUid().then(name => activityName = name)
    cy.getActivitySynonymByUid().then(apiSynonym => synonym = apiSynonym)
    cy.wait('@getData', {timeout: 20000})
}

function getGroupAndSubgroupAndCreateActivity(customName) {
    cy.getFinalGroupUid()
    cy.getFinalSubGroupUid()
    cy.createActivity(customName)
}

function createAndChangeStatusOfLinkedItemViaApi(action) {
    createActivityViaApi(true)
    action()
}

function createAndApproveViaApi(createFunction, approveFunction) {
    createFunction()
    approveFunction()
}