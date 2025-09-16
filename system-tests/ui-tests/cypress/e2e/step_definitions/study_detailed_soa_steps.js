import { activityName } from "./library_activities_steps";
import { activity_activity } from "./study_activities_steps";

const {Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { closeSync } = require("fs");

let groupName, subgroupName
let current_activity
let new_activity_name
let first_in_order
let last_in_order

When('At least {string} activites are present in the selected study', (number_of_activities) => {
    prepareActivites(number_of_activities, `${Cypress.env('TEST_STUDY_UID')}`)
})

Given('At least {string} activities are present in the same {string} flowchart subgroup and {string} group in the selected study', (number_of_activities, group, subgroup) => {
    prepareActivitesInSameGroup(number_of_activities, subgroup, group)
})

When('The user click on {string} action for an Activity', (action) => {
    cy.request(`api/studies/${Cypress.env('TEST_STUDY_UID')}/study-activities?total_count=true`).then((req) => {
        current_activity = req.body.items[0].activity.name.substring(0, 40)
        cy.wait(1000)
        cy.contains('.v-selection-control', 'Expand table').click()
        cy.contains('table tbody tr.bg-white', current_activity).within(() => cy.clickButton('table-item-action-button'))
        cy.clickButton(action)
    })
})

When('The user goes through selection from library form', () => {
    cy.clickFormActionButton('continue')
    cy.get('[data-cy="select-activity"]').not('.v-selection-control--disabled').parentsUntil('tr').siblings().eq(4).invoke('text').then((activity_name) => {
        new_activity_name = activity_name.substring(0, 40)
    })
    cy.get('[data-cy="select-activity"]').not('.v-selection-control--disabled').first().click()
    cy.get('[data-cy="flowchart-group"]').not('.v-input--disabled').first().click()
    cy.get('.v-list-item').filter(':visible').first().click()
    cy.clickFormActionButton('save')
})

Then('The newly selected activity replaces previous activity in study', () => {
    cy.reload()
    cy.contains('.v-selection-control', 'Expand table').click()
    cy.contains('table tbody tr.bg-white', new RegExp(`^(${current_activity})$`, "g")).should('not.exist')
    cy.contains('table tbody tr.bg-white', new RegExp(`^(${new_activity_name})$`, "g")).should('exist')
})

Then('The newly created activity is present in SoA', () => {
    cy.reload()
    cy.contains('.v-selection-control', 'Expand table').click()
    cy.contains(new_activity_name).should('exist')

})

When('The user confirms the deletion pop-up', () => {
    cy.clickButton('continue-popup')
})

Then('The Activity is no longer visible in the SoA', () => {
    cy.reload()
    cy.contains('.v-selection-control', 'Expand table').click()
    cy.contains(current_activity).should('not.exist')
})

Then('The Activity is visible in the SoA', () => {
    cy.contains('.v-selection-control', 'Expand table').click()
    cy.contains(activity_activity.substring(0, 40)).should('be.visible')
})

When('The user selects rows in SoA table', () => {
    cy.request(`api/studies/${Cypress.env('TEST_STUDY_UID')}/study-activities?total_count=true`).then((req) => {
        current_activity = req.body.items[0].activity.name.substring(0, 40)
        cy.wait(1000)
        cy.contains('.v-selection-control', 'Expand table').click()
        cy.contains('.bg-white', current_activity).within(() => {
            cy.get('[id^="checkbox"]').first().click()
        })
    })
})

When('The user clicks on Bulk Edit action on SoA table options', () => {
    cy.get('[title="Bulk actions"]').click()
    cy.contains('.v-list-item', 'Bulk Edit Activities').click()
})

Then('The bulk edit view is presented to user allowing to update Activity Group and Visits for selected activities', () => {
    cy.elementContain('form-body', 'Batch edit study activities')
    cy.elementContain('form-body', 'Note: The entire row of existing selections will be overwritten with the selection(s) done here')
    cy.elementContain('form-body', 'Batch editing will overwrite existing choices. Only activities expected to have same schedule should be batch-edited together.')
    cy.elementContain('form-body', 'Batch edit study activities')
    cy.elementContain('form-body', current_activity)
})

When('The user edits activities in bulk', () => {
    cy.slectFirstVSelect('bulk-edit-soa-group')
    cy.slectFirstVSelect('bulk-edit-visit')
    cy.intercept('**/soa-edits/batch').as('editRequest')
    cy.clickButton('save-button')

})

Then('The data for bulk edited activities is updated', () => {
    cy.wait('@editRequest').its('response.statusCode').should('equal', 207)

})

When('The user edits activities in bulk without selecting Activity Group and Visit', () => {
    bulkAction('Bulk Edit Activities')
    cy.clickButton('save-button')

})

Then('The validation appears for Activity Group field in bulk edit form', () => {
    cy.get('[data-cy="form-body"]').within(()=> {
        cy.get('.v-input').eq(2).should('contain', 'This field is required')
    })
})

When('The user delete activities in bulk', ()=> {
    bulkAction('Bulk Remove Activities')
    cy.intercept('**/study-activities/batch').as('deleteRequest')
    cy.clickButton('continue-popup')
    
})

Then('The activities are removed from the study', () => {
    cy.wait('@deleteRequest').its('response.statusCode').should('equal', 207)

})

When('The user enables the Reorder Activities function for acitivities in the same {string} flowchart subgroup and {string} group', (subgroup, group) => {
    cy.contains('tr.flowchart', group).find('.mdi-chevron-right').click()
    cy.get('.group .mdi-chevron-right').click()
    cy.get('.subgroup .mdi-chevron-right').click()
    cy.contains('tr[class="bg-white"]', subgroup).within(() => cy.clickButton('table-item-action-button'))
    cy.clickButton('Reorder')
})

When('The user updates the order of activities', () => {
    cy.intercept('**/order').as('orderRequest')
    cy.wait(1500)
    cy.get('.mdi-sort').first().parentsUntil('td').invoke('text').then((text) => {last_in_order = text})
    cy.get('.mdi-sort').last().parentsUntil('td').invoke('text').then((text) => {first_in_order = text})

    cy.get('.mdi-sort').last().parentsUntil('td').drag('tr.bg-white', {
        source: { x: 0, y: -50 }, // applies to the element being dragged
        target: { position: 'left' }, // applies to the drop target
        force: true, // applied to both the source and target element)
    })
    cy.wait(1000)
    cy.contains('.v-btn', 'Finish reordering').click()
    cy.wait('@orderRequest')
})

Then('The new order of activites is visible', () => {
    cy.wait(2000)
    cy.get('tr.bg-white').first().should('contain', first_in_order)
})

Then('Text about no added visits and activities is displayed', () => cy.get('.v-empty-state__title').should('have.text', 'No activities & visits added yet'))

Then('User can click Add visit button', () => cy.contains('button', 'Add visit').click())

Then('User can click Add study activity button', () => cy.contains('button', 'Add study activity').click())

Then('No activities are found', () => cy.get('table[aria-label="SoA table"] .bg-white').should('not.exist'))

Then('Activity is found in table', () => cy.contains('table[aria-label="SoA table"] .bg-white', activityName).should('exist'))

When('User search for non-existing activity', () => cy.contains('.v-input__control', 'Search Activities').type('xxx'))

When('User search newly added activity', () => cy.contains('.v-input__control', 'Search Activities').type(activityName))

When('User search newly added activity in lowercase', () => cy.contains('.v-input__control', 'Search Activities').type(activityName.toLowerCase()))

When('User search newly added activity by partial name', () => cy.contains('.v-input__control', 'Search Activities').type(activityName.slice(-3)))

When('User search search activity by subgroup', () => cy.contains('.v-input__control', 'Search Activities').type('API_SubGroup'))

When('User search search activity by group', () => cy.contains('.v-input__control', 'Search Activities').type('API_Group'))

When('User expand table', () => cy.contains('.v-selection-control', 'Expand table').click())

When('User selects visits {string}', (visitList) => {
    const visitListArray = visitList.split(',')
    visitListArray.forEach(visit => cy.contains('table thead th', visit.trim()).find('input').check())
})

When('Button for collapsing visits is clicked', () => cy.get('button[title="Group selected visits together"]').click())

When('Button for collapsing visits is not available', () => cy.get('button[title="Group selected visits together"]').should('not.be.visible'))

When('Option for collapsing in {string} is selected', (value) => cy.get(`input[value="${value}"]`).check({force: true}))

Then('Visits are no longer collapsed in detailed SoA view', () => {
    cy.get('table thead tr').should('not.contain', 'V2-V4')
    cy.get('table thead tr').should('not.contain', 'V2,V3,V4')
})

Then('Visits study weeks are no longer collapsed in detailed SoA view', () => {
    cy.get('table thead tr').should('not.contain', '1-4')
    cy.get('table thead tr').should('not.contain', '1,2,4')
})

Then('Visits are collapsed as {string} in detailed SoA view', (visitsGroup) => cy.contains('table thead tr', visitsGroup))

Then('Visits study weeks are collapsed as {string} in detailed SoA view', (weeksGroup) => cy.contains('table thead tr', weeksGroup))

Then('Visit group delete button is clicked', () => cy.get('button[title="Delete this group"]').click())

Then('Error message is displayed for collapsing visits with different epochs', () => cy.checkSnackbarMessage("Given Visits can't be collapsed as they exist in different Epochs"))

Then('Footnotes table is available with options', (options) => {
    options.rows().forEach((option) => {
        cy.contains('.page-title', 'Footnotes').parent().within(() => {
            const locator = option == 'search-field' ? `[data-cy="${option}"]` : `[title="${option}"]`
            cy.get(locator).should('be.visible')
        })
    })
})

Then('SoA table is available with Bulk actions, Export and Show version history', () => {
    cy.get('button[title="Bulk actions"]').should('be.visible')
        .siblings('button[title="Export"]').should('be.visible')
            .siblings('button[title="Show version history"]').should('be.visible')
})

Then('Search is available in SoA table', () => cy.contains('.v-label', 'Search Activities').parent().within(() => cy.get('input').should('exist')))

Then('Button for Expanding SoA table is available', () => cy.contains('.v-selection-control', 'Expand table').should('be.visible'))

Then('SoA table is visible with following headers', (options) => {
    options.rows().forEach(option => cy.contains('table tr th.header.zindex25', `${option}`).should('be.visible'))
})

Then('Group and subgroup names are fetch to be used in SoA', () => {
    cy.getGroupNameByUid().then(name => groupName = name)
    cy.getSubGroupNameByUid().then(name => subgroupName = name)
})

Then('Group is visible in the protocol SoA', () => cy.contains('th.group', groupName).should('be.visible'))

Then('Subgroup is visible in the protocol SoA', () => cy.contains('th.subGroup', subgroupName).should('be.visible'))

Then('Activity is visible in the protocol SoA', () => cy.contains('th.activity', activityName).should('be.visible'))

Then('Group is not visible in the protocol SoA', () => cy.contains('th.group', groupName).should('not.exist'))

Then('Subgroup is not visible in the protocol SoA', () => cy.contains('th.subGroup', subgroupName).should('not.exist'))

Then('Activity is not visible in the protocol SoA', () => cy.contains('th.activity', activityName).should('not.exist'))

When('User switches to the {string} view', (view) => cy.get(`button[value="${view}"]`).click())

When('User clicks eye icon on SoA group level for {string}', (flowchart) => cy.contains('tr.flowchart', flowchart).find('[title^="Show/hide SoA"]').click())

When('User clicks eye icon on group level', () => cy.contains('tr.group', groupName).find('[title^="Show/hide SoA"]').click())

When('User clicks eye icon on subgroup level', () => cy.contains('tr.subgroup', subgroupName).find('[title^="Show/hide SoA"]').click())

When('User clicks eye icon on activity level', () => cy.contains('tr[id*="StudyActivity_"]', activityName).find('[title^="Show/hide SoA"]').click())

When('User waits for the protocol SoA table to load', () => cy.get('[id="protocolFlowchart"]').should('be.visible'))

Then('Activity SoA group, group, subgroup and name are visible in the detailed view', () => verifySoATable('table[aria-label="SoA table"] tbody tr'))

Then('Epoch {string} and epoch {string} are visible in the detailed view', (epoch1, epoch2) => {
    cy.contains('table[aria-label="SoA table"] thead tr th', 'Epoch').should('be.visible')
        .next().should('contain.text', epoch1).should('be.visible')
            .next().next().should('contain.text', epoch2).should('be.visible')
})

Then('Visits {string}, {string}, {string} are visible in the detailed view', (visit1, visit2, visit3) => {
    verifySoATableHeaders('table[aria-label="SoA table"] thead tr th', 'Visit', visit1, visit2, visit3)
})

Then('Study weeks {int}, {int}, {int} are visible in the detailed view', (week1, week2, week3) => {
    verifySoATableHeaders('table[aria-label="SoA table"] thead tr th', 'Study week', week1, week2, week3)
})

Then('Study visit windows {string}, {string}, {string} are visible in the detailed view', (window1, window2, window3) => {
    verifySoATableHeaders('table[aria-label="SoA table"] thead tr th', 'Visit window (days)', window1, window2, window3)
})

Then('Activity SoA group, group, subgroup and name are visible in the protocol view', () => verifySoATable('[id="protocolFlowchart"] table tbody tr'))

Then('Epoch {string} and epoch {string} are visible in the protocol view', (epoch1, epoch2) => {
    cy.contains('[id="protocolFlowchart"] table thead tr th', 'Procedure').should('be.visible')
        .next().should('contain.text', epoch1).should('be.visible')
            .next().should('contain.text', epoch2).should('be.visible')
})

Then('Visits {string}, {string}, {string} are visible in the protocol view', (visit1, visit2, visit3) => {
    verifySoATableHeaders('[id="protocolFlowchart"] table thead tr th', 'Visit short name', visit1, visit2, visit3)
})

Then('Study weeks {int}, {int}, {int} are visible in the protocol view', (week1, week2, week3) => {
    verifySoATableHeaders('[id="protocolFlowchart"] table thead tr th', 'Study week', week1, week2, week3)
})

Then('Study visit windows {string}, {string}, {string} are visible in the protocol view', (window1, window2, window3) => {
    verifySoATableHeaders('[id="protocolFlowchart"] table thead tr th', 'Visit window (days)', window1, window2, window3)
})

function bulkAction(action) {
    cy.request(`api/studies/${Cypress.env('TEST_STUDY_UID')}/study-activities?total_count=true`).then((req) => {
        current_activity = req.body.items[0].activity.name.substring(0, 40)
        cy.wait(1000)
        cy.contains('.v-selection-control', 'Expand table').click()
        cy.contains('.bg-white', current_activity).within(() => {
            cy.get('[id^="checkbox"]').first().click()
        })
    })
    cy.get('[title="Bulk actions"]').click()
    cy.contains('.v-list-item', action).click()
}

function prepareActivites(number_of_activities, study_id) {
    cy.request('api/studies/' + study_id + '/study-activities?total_count=true').then((req) => {
        if (req.body.total < parseInt(number_of_activities)) {
            cy.log('No activity')
            cy.visit('studies/' + study_id + '/activities/list')
            cy.clickButton('add-study-activity')
            cy.clickFormActionButton('continue')
            cy.get('[data-cy="select-activity"]').not('.v-selection-control--disabled').first().click()
            cy.get('[data-cy="flowchart-group"]').not('.v-input--disabled').first().click()
            cy.get('.v-list-item').filter(':visible').first().click()
            cy.clickFormActionButton('save')
            prepareActivites(number_of_activities, study_id)
        } else {
            cy.log('Skipping activity creation')
        }
    })
}

function prepareActivitesInSameGroup(number_of_activities, subgroup, group) {
    let group_subgroup_count = 0
    cy.sendGetRequest(`/studies/${Cypress.env('TEST_STUDY_UID')}/study-activities?page_size=100`).then(response => {
        response.body.items.forEach(item => {
            let subgroupName = item.activity.activity_groupings[0].activity_subgroup_name
            let soaName = item.study_soa_group.soa_group_term_name
            if (subgroupName == group && soaName == subgroup) group_subgroup_count++
        })
    }).then(() => {
        if (group_subgroup_count < parseInt(number_of_activities)) {
            cy.visit(`studies/${Cypress.env('TEST_STUDY_UID')}/activities/list`)
            cy.clickButton('add-study-activity')
            cy.clickFormActionButton('continue')
            cy.contains('Use the same SoA group for all').click()
            cy.searchForInPopUp(group)
            cy.get('input[aria-label="Use the same SoA group for all"]').check()
            cy.get('.v-card-title [role="combobox"] input').click()
            cy.contains('.v-list-item__content', subgroup).click()
            while (group_subgroup_count != parseInt(number_of_activities)) {
                cy.get('.v-data-table__td--select-row input').not(':disabled').not('[checked]').first().check();
                group_subgroup_count++;
            }
            cy.clickFormActionButton('save')
        } else {
            cy.log('Skipping activity creation')
        }
    })

}

function verifySoATable(tableLocator) {
    cy.contains(`${tableLocator}`, 'INFORMED CONSENT').should('be.visible')
        .next().should('contain.text', groupName).should('be.visible')
            .next().should('contain.text', subgroupName).should('be.visible')
                .next().should('contain.text', activityName).should('be.visible')
}

function verifySoATableHeaders(tableLocator, key, v1, v2, v3) {
    cy.contains(tableLocator, key).should('be.visible')
        .next().should('contain.text', v1).should('be.visible')
            .next().should('contain.text', v2).should('be.visible')
                    .next().should('contain.text', v3).should('be.visible')
}