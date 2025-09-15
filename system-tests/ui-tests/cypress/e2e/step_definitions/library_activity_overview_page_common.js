const { When, Then, Given } = require("@badeball/cypress-cucumber-preprocessor");

let groupName, subgroupName, secondSubgroup, activityName, instanceName
let trimmedStartDate

When('Group, subgroup, activity and instance names created through API are found', () => {
    cy.getGroupNameByUid().then(text => groupName = text)
    cy.getSubGroupNameByUid().then(text => subgroupName = text)
    cy.getActivityNameByUid().then(text => activityName = text)
    cy.getActivityInstanceNameByUid().then(text => instanceName = text)
})

When('I click {string} button', (title) => cy.get(`button.v-btn[title="${title}"]`).click())

Then('The group overview page can be opened by clicking the group link in overview page', () => clickOnLinkedItem(groupName))

Then('The subgroup overview page can be opened by clicking the subgroup link in overview page', () => clickOnLinkedItem(subgroupName))

Then('The activity overview page can be opened by clicking the activity link in overview page', () => clickOnLinkedItem(activityName))

When('Group created via API is searched for and found', () => cy.searchAndCheckPresence(groupName, true))

When('Subgroup created via API is searched for and found', () => cy.searchAndCheckPresence(subgroupName, true))

When('New Subgroup is searched for and found', () => cy.searchAndCheckPresence(secondSubgroup, true))

When('Activity created via API is searched for and found', () => cy.searchAndCheckPresence(activityName, true))

When('Activity instance created via API is searched for and found', () => cy.searchAndCheckPresence(instanceName, true))

When('User goes to group overview page by clicking its name', () => cy.get('table tbody tr td').contains(groupName).click())

When('User goes to subgroup overview page by clicking its name', () => cy.get('table tbody tr td').contains(subgroupName).click())

When('User goes to activity overview page by clicking its name', () => cy.get('table tbody tr td').contains(activityName).click())

When('User goes to instance overview page by clicking its name', () => cy.get('table tbody tr td').contains(instanceName).click())

Given('Group overview page is opened', () => verifyIfOverviewPageOpened(groupName))

Given('Subgroup overview page is opened', () => verifyIfOverviewPageOpened(subgroupName))

Given('Activity overview page is opened', () => verifyIfOverviewPageOpened(activityName))

Given('Instance overview page is opened', () => verifyIfOverviewPageOpened(instanceName))

Given('The linked group is found in the Groups table with status {string} and version {string}', (status, version) => {
    verifyLinkedItem('Activity group', groupName, status, version)
})

Given('The linked subgroup is found in the Groups table with status {string} and version {string}', (status, version) => {
    verifyLinkedItem('Activity subgroups', subgroupName, status, version)
})

Given('The new linked subgroup is found in the Groups table with status {string} and version {string}', (status, version) => {
    verifyLinkedItem('Activity subgroups', secondSubgroup, status, version)
})

Given('The linked activity is found in the Acivities table with status {string} and version {string}', (status, version) => {
    verifyLinkedItem('Activities', activityName, status, version)
})

Given('The linked activity instance is found in the Acivity Instances table with status {string} and version {string}', (status, version) => {
    verifyLinkedItem('Activity instances', instanceName, status, version)
})

Given('The previous version of linked activity instance is found in the Acivity Instances table with status {string} and version {string}', (status, version) => {
    verifyLinkedItem('Activity instances', instanceName, status, version, 2)
})

Given('User waits for linked {string} table data to load', (tableName) => {
    cy.contains('.section-header', tableName).parent().within(() => {
        cy.contains('tr', 'Loading items...', {timeout: 50000}).should('not.exist');
    })
})

When('Activity instance is expanded by clicking chevron button', () => cy.get('tr button .mdi-chevron-right').click())

Given('Group name is changed', () => {groupName = `Update ${groupName}`, changeGroupingName(groupName)})

Given('Subgroup name is changed', () => {subgroupName = `Update ${subgroupName}`, changeGroupingName(subgroupName)})

When('Activity name is changed', () => {
    cy.fillInput('activityform-activity-name-field', `Update ${activityName}`)
    cy.contains('.v-col', 'Reason for change').find('textarea').not('.v-textarea__sizer').type('Test purpose')
})

When('Instance name is changed', () => cy.fillInput('instanceform-instancename-field',  `Update ${instanceName}`))

Then('The free text search field should be displayed in the {string} table', (tableName) => {
    cy.contains('.section-header', tableName).parent().find('[data-cy="search-field"]').should('be.visible')
})

Then('Activity group, activity subgroup and activity values are available in the table', () => {
    cy.checkRowByIndex(0, 'Activity group', groupName)
    cy.checkRowByIndex(0, 'Activity subgroup', subgroupName) 
    cy.checkRowByIndex(0, 'Activity', activityName)  
})

When('I create a new subgroup and link it to the existing group', () => { 
    secondSubgroup = `Sg${Date.now()}`
    cy.get('[data-cy="groupform-activity-group-dropdown"] input').type(groupName)
    cy.selectFirstVSelect('groupform-activity-group-dropdown')
    cy.fillInput('groupform-activity-group-field', secondSubgroup)
    cy.fillInput('groupform-abbreviation-field', 'abbsg2')
    cy.fillInput('groupform-definition-field', 'defsg2') 
})

Then('The Activity groupings table is empty', () => verifyIfTableIsEmpty('Activity groupings', 'No data available'))

Then('The Activity subgroups table is empty', () => verifyIfTableIsEmpty('Activity subgroup', 'No subgroups available.'))

Then('The Activities groups table is empty', () => verifyIfTableIsEmpty('Activity group', 'No items available'))

Then('The Activities table is empty', () => verifyIfTableIsEmpty('Activities', 'No items available'))

Then('The Activity Items table is empty', () => verifyIfTableIsEmpty('Activity Items', 'No activity items found'))

Then('The Activity Instances table is empty', () => verifyIfTableIsEmpty('Activity instances', 'No activity instances found for this activity.'))

Then('The Activity subgroup created via API is not available in the table', () => {
    cy.contains('.section-header', 'Activity subgroup').parent().within(() => cy.get('table tbody tr').should('not.have.text', subgroupName))
})

Then('The {string} table is displaying correct columns', (tableName, columns) => validateTableColumns(tableName, columns.rows()))

Then('The Activity linked group, subgroup and instance are displayed in the Activity groupings table', () => {
    verifyActivityGroupings('Activity instances', instanceName)
})

Then('The activity instance is not available in Activity groupings table', () => {
    verifyActivityGroupings('Activity instances', 'No activity instances available')
})

Then('The Instance linked group, subgroup and instance are displayed in the Activity groupings table', () => {
    verifyActivityGroupings('Activity', activityName)
})

Then('The Instance linked activity has status {string} and version {string}', (status, version) => {
    cy.contains('.section-header', 'Activity groupings').parent().within(() => {
        cy.checkRowByIndex(0, 'Activity', status)
        cy.checkRowByIndex(0, 'Activity', version)
    })
})

Then('The status displayed on the summary has value {string} and version is {string}', (status, version) => {
    cy.contains('.summary-label', 'Status').parent().within(() => cy.get('.summary-value').should('have.text', status))
    cy.get('.v-select__selection-text').should('contain', version)
})

When('Version {string} is selected from the Version dropdown list', (version) => {
    cy.contains('.summary-label', 'Version').parent().within(() => cy.get('[role="combobox"]').click())
    cy.get('.v-list-item').contains(version).click();
})

Then('The Start date value is saved', () => {
    cy.contains('.summary-label', 'Start date').parent().within(() => {
        cy.get('.summary-value').invoke('text').then(startDate => trimmedStartDate = startDate.trim())
    })
}) 

Then('The correct End date should be displayed', () => {
    cy.contains('.summary-label', 'End date').parent().within(() => {
        cy.get('.summary-value').invoke('text').then(text => cy.wrap(text.trim()).should('equal', trimmedStartDate))
    })
})

When('I click on the COSMoS YAML tab', () => cy.get('button.v-btn.v-tab[value="cosmos"]').click())

Then('The COSMoS YAML page should be opened with Download button and Close button displayed', () => {
    cy.get('button[title="Download YAML content"]').should('be.visible');
    cy.get('button[title="Close YAML viewer"]').should('be.visible');
})

Then('The Download YAML content button is clicked', () => cy.get('button[title="Download YAML content"]').click())

When('I click on the Close button in the COSMoS YAML page', () => cy.get('button[title="Close YAML viewer"]').click())

When('I click on the history button', () => cy.get('button[title="History"]').click())

Then('The history page is opened', () => cy.get(`[data-cy="version-history-window"]`).should('be.visible'))

Then('I verify the definition is {string}', (definition) => cy.contains('.v-col', 'Definition').next().should('have.text', definition))

When('User searches for non-existing item in {string} table', (tableName) => searchForInLinkedItemTable(tableName, 'xxx'))

When('User searches for group by using lowecased name in linked Activity Group table', () => searchForInLinkedItemTable('Activity group', groupName.toLowerCase()))

When('User searches for group by using partial name in linked Activity Group table', () => searchForInLinkedItemTable('Activity group', 'API_Group'))

When('User searches for group in linked Activity Group table', () => searchForInLinkedItemTable('Activity group', groupName))

When('User searches for activity by using lowecased name in linked Activities table', () => searchForInLinkedItemTable('Activities', activityName.toLowerCase()))

When('User searches for activity by using partial name in linked Activities table', () => searchForInLinkedItemTable('Activities', 'API_Activity'))

When('User searches for activity in linked Activities table', () => searchForInLinkedItemTable('Activities', activityName))

When('User searches for subgroup by using lowecased name in linked Subgroups table', () => searchForInLinkedItemTable('Activity subgroups', subgroupName.toLowerCase()))

When('User searches for subgroup by using partial name in linked Subgroups table', () => searchForInLinkedItemTable('Activity subgroups', 'API_Subgroup'))

When('User searches for subgroup in linked Subgroups table', () => searchForInLinkedItemTable('Activity subgroups', subgroupName))

When('User searches for instance by using lowecased name in linked Instances table', () => searchForInLinkedItemTable('Activity instances', instanceName.toLowerCase()))

When('User searches for instance by using partial name in linked Instances table', () => searchForInLinkedItemTable('Activity instances', 'API_ActivityInstance'))

When('User searches for instance in linked Instances table', () => searchForInLinkedItemTable('Activity instances', instanceName))

When('Group name is present in first row of the Activity Group table', () => {
    cy.contains('.section-header', 'Activity group').parent().within(() => cy.get('table tbody tr').should('contain.text', groupName))
})

When('Subgroup name is present in first row of the Activity Subgroup table', () => {
    cy.contains('.section-header', 'Activity subgroup').parent().within(() => cy.get('table tbody tr').should('contain.text', subgroupName))
})

When('Activity name is present in first row of the linked Activity table', () => {
    cy.contains('.section-header', 'Activities').parent().within(() => cy.get('table tbody tr').should('contain.text', activityName))
})

When('Activity Instance name is present in first row of the linked Instances table', () => {
    cy.contains('.section-header', 'Activity instances').parent().within(() => cy.get('table tbody tr').should('contain.text', instanceName))
})

When('Filters for the {string} table are expanded', (tableName) => {
    cy.contains('.section-header', tableName).parent().within(() => cy.clickButton('filters-button'))
})

When('Following filters are available in the table {string}', (tableName, filters) => {
    cy.contains('.section-header', tableName).parent().within(() => {
        filters.rows().forEach(filter => cy.contains('[data-cy="filter-field"] .v-label', filter[0]).should('be.visible'))
    })
})

When('Subgroup name is selected from filters', () => setFilterValue('Activity subgroups', 'Name', subgroupName))

When('Activity Instance name is selected from filters', () => setFilterValue('Activity instances', 'Name', instanceName))

When('{int} result is present in the {string} table', (numberOfResults, tableName) => {
    cy.contains('.section-header', tableName).parent().within(() => cy.get('table tbody tr').should('have.length', numberOfResults))
})

When('[API] A subgroup connected to two to groups is created', () => {
    cy.createTwoGroups(), cy.approveTwoGroups()
    cy.createSubGroupWithTwoGroups(), cy.approveSubGroup()
})

When('[API] A subgroup connected to two activities is created', () => {
    cy.createGroup(), cy.approveGroup()
    cy.createSubGroup(), cy.approveSubGroup()
    cy.createActivity(), cy.approveActivity()
    cy.createActivity(), cy.approveActivity()
})

When('[API] A group connected to two subgroups is created', () => {
    cy.createGroup(), cy.approveGroup()
    cy.createSubGroup(), cy.approveSubGroup()
    cy.createSubGroup(), cy.approveSubGroup()
})

When('[API] An activity connected to two instances is created', () => {
    cy.createGroup(), cy.approveGroup()
    cy.createSubGroup(), cy.approveSubGroup()
    cy.createActivity(), cy.approveActivity()
    cy.createActivityInstance(), cy.approveActivityInstance()
    cy.createActivityInstance(), cy.approveActivityInstance()
})

When('[API] Fetch names of subgroup with two connected groups', () => {
    cy.getGroupNameFromListByUid().then(text => groupName = text)
    cy.getSubGroupNameByUid().then(text => subgroupName = text)
})

When('[API] Fetch names of subgroup with two connected activities', () => {
    cy.getActivityNameByUid().then(text => activityName = text)
    cy.getSubGroupNameByUid().then(text => subgroupName = text)
})

When('[API] Fetch names of group with two connected subgroups', () => {
    cy.getGroupNameByUid().then(text => groupName = text)
    cy.getSubGroupNameByUid().then(text => subgroupName = text)
})

When('[API] Fetch names of activity with two connected instances', () => {
    cy.getActivityNameByUid().then(text => activityName = text)
    cy.getActivityInstanceNameByUid().then(text => instanceName = text)
})

function searchForInLinkedItemTable(tableName, searchFor) {
    cy.contains('.section-header', tableName).parent().within(() => cy.get('[data-cy="search-field"] input').clear().type(searchFor, { force: true }))
}

function verifyIfOverviewPageOpened(name) {
    cy.get('.d-flex.page-title').should('contain.text', name);
    cy.get('button[role="tab"][value="html"]').contains('Overview');
}

function changeGroupingName(name) {
    cy.wait(2000)
    cy.fillInput('groupform-activity-group-field', name)
    cy.fillInput('groupform-change-description-field', "Test purpose")
}

function verifyLinkedItem(tableName, itemName, status, version, rowIndex = 0) {
  cy.contains('.section-header', tableName).parent().within(() => {
    cy.checkRowByIndex(rowIndex, 'Name', itemName)
    cy.checkRowByIndex(rowIndex, 'Status', status)
    cy.checkRowByIndex(rowIndex, 'Version', version)
  })
}

function verifyIfTableIsEmpty(tableName, expectedText) {
    cy.contains('.section-header', tableName).parent().within(() => {
        cy.get('table tbody tr').should('have.text', expectedText)
    })
}

function validateTableColumns(tableName, columns) {
  cy.contains('.section-header', tableName).parent().find('table thead tr').within(() => {
    columns.forEach(column => {
      cy.get('th').eq(columns.indexOf(column)).contains(column[0]).should('exist')
    })
  })
}

function verifyActivityGroupings(activityItemName, expectedActivityItem) {
    cy.contains('.section-header', 'Activity groupings').parent().within(() => {
        cy.checkRowByIndex(0, 'Activity group', groupName)
        cy.checkRowByIndex(0, 'Activity subgroup', subgroupName)
        cy.checkRowByIndex(0, activityItemName, expectedActivityItem)
    })
}

function clickOnLinkedItem(itemName) {
    cy.get('.v-table__wrapper').contains('a', itemName).click();
    verifyIfOverviewPageOpened(itemName) 
}

function setFilterValue(tableName, filterName, filterValue) {
    cy.contains('.section-header', tableName).parent().within(() => {
        cy.contains('[data-cy="filter-field"]', filterName).click()
    })
    cy.contains('.v-list .v-list-item-title', filterValue).click()
}