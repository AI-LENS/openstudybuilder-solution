import { activityName } from "./library_activities_steps";
import { getCurrentStudyId } from "./../../support/helper_functions";
const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

export let activity_activity
let activity_placeholder_name, activity_library, activity_soa_group, activity_group, activity_sub_group, edit_placeholder_name, current_study

When('Study activity add button is clicked', () => cy.clickButton('add-study-activity'))

Then('The Study Activity is found', () => cy.searchAndCheckPresence(activity_activity, true))

When('Activity placeholder is found', () => cy.searchAndCheckPresence(activity_placeholder_name, true))

Then('The Study Activity Placeholder is no longer available', () => cy.searchAndCheckPresence(activity_placeholder_name, false))

When('Activity placeholder is searched for', () => cy.searchForInPopUp(activity_placeholder_name))

Given('Study activities for selected study are loaded', () => {
    cy.intercept(`/api/studies/${Cypress.env('TEST_STUDY_UID')}/study-activities?*`).as('getData')
    cy.wait('@getData', { timeout: 30000 })
})

Given('The activity exists in the library', () => {
    cy.log('Handled by import script')
})

When('User tries to add Activity in Draft status', () => {
    cy.searchForInPopUp(activityName)
    cy.waitForTable()
})

When('User search and select activity created via API', () => addLibraryActivityByName())

When('User selects first available activity', () => selectActivityAndGetItsData())

When('User selects first available activity and SoA group', () => selectActivityAndGetItsData('INFORMED CONSENT'))

When('Study with id value {string} is selected', (value) => cy.selectVSelect('select-study-for-activity-by-id', value))

When('Study with acronym value {string} is selected', (value) => cy.selectVSelect('select-study-for-activity-by-acronym', value))

Then('The Study Activity is visible in table', () => checkIfTableContainsActivity())

Then('The Activity in Draft status is not found', () => cy.contains('.v-sheet table tbody tr', 'No data available'))

When('Activity placeholder data is filled in', () => fillPlaceholderData())

When('Selected study id is saved', () => current_study = getCurrentStudyId())

When('Data collection flag is unchecked', () => cy.get('input[aria-label="Data collection"]').uncheck())

When('Data collection flag is checked', () => cy.get('input[aria-label="Data collection"]').check())

Then('The Study Activity placeholder is visible within the Study Activities table', () => {
    cy.tableContains('Requested')
    cy.tableContains('INFORMED CONSENT')
    cy.tableContains('General')
    cy.tableContains(activity_placeholder_name)
})

Then('The edited Study Activity data is reflected within the Study Activity table', () => cy.tableContains('EFFICACY'))

When('Activity from studies is selected', () => cy.get('[data-cy="select-from-studies"] input').check())

When('Activity from library is selected', () => cy.get('[data-cy="select-from-library"] input').check({force: true}))

When('Activity from placeholder is selected', () => cy.get('[data-cy="create-placeholder"] input').check())

When('Study by id is selected', () => cy.selectVSelect('select-study-for-activity-by-id', current_study))

Then('The validation appears and Create Activity form stays on Study Selection', () => {
    cy.elementContain('select-study-for-activity-by-acronym', 'This field is required')
    cy.elementContain('select-study-for-activity-by-id', 'This field is required')
})

When('The user tries to go further without SoA group chosen', () => {
    cy.get('.v-data-table__td--select-row input').not('[aria-disabled="true"]').eq(0).check()
})

When('The user tries to go further in activity placeholder creation without SoA group chosen', () => {
    cy.contains('.choice .text', 'Create a placeholder activity without submitting for approval').click()
    cy.fillInput('instance-name', `Placeholder Instance Name ${Date.now()}`)
    cy.fillInput('activity-rationale', 'Placeholder Test Rationale')
})

Then('The validation appears and Create Activity form stays on SoA group selection', () => {
    cy.get('.v-snackbar__content').should('contain', 'Every selected Activity needs SoA Group')
    cy.get('[data-cy="flowchart-group"]').should('be.visible')
})

Then('The validation appears under empty SoA group selection', () => {
    cy.get('[data-cy="flowchart-group"]').find('.v-messages').should('contain', 'This field is required')
})

Then('The SoA group can be changed', () => {
    cy.wait(1000)
    cy.selectAutoComplete('flowchart-group', 'EFFICACY')
})

Then('The study activity table is displaying updated value for data collection', () => {
    cy.getCellValue(0, 'Data collection').then(value => cy.wrap(value).should('equal', 'Yes'))
})

Then('Warning that {string} {string} can not be added to the study is displayed', (status, item) => {
    cy.get('.v-snackbar__content').should('contain', `has status ${status}. Only Final ${item} can be added to a study.`)
})

When('The existing activity request is selected', () => cy.get('[data-cy="select-activity"] input').check())

When('The study activity request is edited', () => {
    edit_placeholder_name = `Edit name ${Date.now()}`
    cy.fillInput('instance-name', edit_placeholder_name)
})

When('The study activity request SoA group field is edited', () => {
    cy.get('[data-cy="flowchart-group"]').click()
    cy.contains('.v-list-item', 'HIDDEN').click()
})

When('The study activity request data collection field is edited', () => {
    cy.get('[aria-label="Data collection"]').click()
})

When('The study activity request rationale for activity field is edited', () => {
    cy.fillInput('activity-rationale', "TEST OF UPDATE REDBELL")
})

Then('The updated notification icon and update option are not present', () => {
    cy.get('.v-badge__badge').should('not.exist')
})

When('The user is presented with the changes to request', () => {
    cy.get('[data-cy="form-body"]').should('contain', edit_placeholder_name)
})

Then('The activity request changes are applied', () => {
    cy.searchAndCheckPresence(edit_placeholder_name, true)
    cy.searchAndCheckPresence(activity_placeholder_name, false)
})

Then('The activity request changes not applied', () => {
    cy.searchAndCheckPresence(activity_placeholder_name, true)
})

Then('The activity request is removed from the study', () => {
    cy.searchAndCheckPresence(edit_placeholder_name, false)
    cy.searchAndCheckPresence(activity_placeholder_name, false)
})

Then('[API] All Activities are deleted from study', () => {
    cy.getExistingStudyActivities(Cypress.env('TEST_STUDY_UID')).then(uids => uids.forEach(uid => cy.deleteActivityFromStudy(Cypress.env('TEST_STUDY_UID'), uid)))
})

function getActivityData(rowIndex, getSoAGroupValue) {
    cy.getCellValueInPopUp(rowIndex, 'Library').then((text) => activity_library = text)
    if (getSoAGroupValue) cy.getCellValueInPopUp(rowIndex, 'SoA group').then((text) => activity_soa_group = text)
    cy.getCellValueInPopUp(rowIndex, 'Activity group').then((text) => activity_group = text)
    cy.getCellValueInPopUp(rowIndex, 'Activity subgroup').then((text) => activity_sub_group = text)
    cy.getCellValueInPopUp(rowIndex, 'Activity').then((text) => activity_activity = text.slice(0, 50))
}

function checkIfTableContainsActivity() {
    cy.wait(1000)
    cy.tableContains(activity_library)
    cy.tableContains(activity_soa_group)
    cy.tableContains(activity_group)
    cy.tableContains(activity_sub_group)
    cy.tableContains(activity_activity)
}

function addLibraryActivityByName() {
    activity_activity = activityName
    cy.waitForTable()
    cy.searchForInPopUp(activity_activity)
    cy.waitForTable()
    cy.get('[data-cy="select-activity"] input').check()
    cy.selectVSelect('flowchart-group', 'INFORMED CONSENT')
}

function selectActivityAndGetItsData(activity_soa_group = null) {
    if (activity_soa_group) activity_soa_group = 'INFORMED CONSENT'
    cy.get('.v-data-table__td--select-row input').each((el, index) => {
        if (el.is(':enabled')) {
            cy.wrap(el).check()
            if (activity_soa_group) {
                cy.get('[data-cy="flowchart-group"]').eq(index).click()
                cy.contains('.v-overlay .v-list-item-title', activity_soa_group).click({ force: true })
            }
            getActivityData(index, !activity_soa_group)
            return false
        }
    })
}

function fillPlaceholderData() {
    activity_placeholder_name = `Placeholder Instance Name ${Date.now()}`
    cy.contains('.choice .text', 'Create a placeholder activity without submitting for approval').click()
    cy.selectVSelect('flowchart-group', 'INFORMED CONSENT')
    cy.get('[data-cy="activity-group"] input').type('General')
    cy.selectFirstVSelect('activity-group')
    cy.selectFirstVSelect('activity-subgroup')
    cy.fillInput('instance-name', activity_placeholder_name)
    cy.fillInput('activity-rationale', 'Placeholder Test Rationale')
}
