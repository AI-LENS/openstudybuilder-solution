let tableBodyLocator = 'table tbody'
let tableBodyLocatorInPopUp = '.v-sheet table tbody'
let tableRowLocator = 'table tbody tr'
let tableHeaderLocator = 'table thead'
let tableHeaderCellLocator = 'table thead th'
let tableHeaderCellLocatorInPopUp = '.v-sheet table thead th'
let expandActionsLocator = 'table-item-action-button'
let regex = (column) => new RegExp(`^${column}$`, 'g')

Cypress.Commands.add('tableRowActions', (rowIndex, action) => {
    cy.clickTableActionsButton(rowIndex)
    cy.clickButton(action, true)
})

Cypress.Commands.add('tableHeaderActions', (headerName, action) => {
    cy.waitForTable()
    cy.clickHeaderActionsButton(headerName)
    cy.contains('button', action).click()
})

Cypress.Commands.add('performActionOnSearchedItem', (action, message = null) => {
    cy.tableRowActions(0, action)
    if (message != null) cy.checkSnackbarMessage(message)
    cy.wait(1500)
})

Cypress.Commands.add('performActionOnFlaggedItem', (action) => {
    cy.get('table tbody tr button').click()
    cy.clickButton(action)
})

Cypress.Commands.add('clickTableActionsButton', (rowIndex) => {
    cy.get(tableRowLocator).filter(':visible').eq(rowIndex).within(() => cy.clickButton('table-item-action-button', true))
})

Cypress.Commands.add('clickHeaderActionsButton', (headerName) => {
    cy.get(tableHeaderLocator).filter(':visible').contains(headerName).parent().find('button').click()
})

Cypress.Commands.add('searchAndCheckPresence', (value, shouldBePresent) => {
    cy.waitForTable()
    cy.searchFor(value, false)
    shouldBePresent ? cy.tableContains(value) : cy.confirmNoResultsFound(value)
})

Cypress.Commands.add('checkIfMoreThanOneResultFound', () => cy.get(tableRowLocator).should('have.length.above', 1))

Cypress.Commands.add('confirmNoResultsFound', () => cy.get(tableRowLocator).should('have.text', 'No data available'))

Cypress.Commands.add('searchFor', (value, delay = true) => {
    delay ? cy.fillInput('search-field', value) : cy.fillInputWithoutDeplay('search-field', value)
    cy.wait(1500)
})

Cypress.Commands.add('searchForInPopUp', (value) => {
    cy.get('.v-overlay__content [data-cy="search-field"]').type(value)
    cy.wait(1500)
})

Cypress.Commands.add('headerContains', (value) => {
    cy.get('button.v-btn--loading').should('not.exist')
    cy.get(tableHeaderLocator).should('contain', value.toString())
})

Cypress.Commands.add('tableContains', (value) => {
    cy.get('table tbody').should('contain', value)
})

Cypress.Commands.add('tableContainsPredefinedData', (dataTable) => {
    dataTable.hashes().forEach(data => cy.checkRowByIndex(data.row, data.column, data.value))
})

Cypress.Commands.add('checkRowByIndex', (rowIndex, columnName, expected) => {
    checkValue(rowIndex, columnName, expected)
})

Cypress.Commands.add('checkLastRow', (columnName, expectedValue) => {
    cy.get(tableRowLocator).then(rows => checkValue(rows.length - 1, columnName, expectedValue))
})

Cypress.Commands.add('getRowIndex', (rowKey) => {
    return cy.contains(tableRowLocator, rowKey).invoke('index')
})

Cypress.Commands.add('getCellValue', (rowIndex, columnName) => {
    return getCellByName(rowIndex, columnName).invoke('text')
})

Cypress.Commands.add('getCellValueNoVisibilityCheck', (rowIndex, columnName) => {
    return getCellByNameNoVisibilityCheck(rowIndex, columnName).invoke('text')
})

Cypress.Commands.add('getCellValueInPopUp', (rowIndex, columnName) => {
    return getCellByNameInPopUp(rowIndex, columnName).invoke('text')
})

Cypress.Commands.add('addTableFilter', (filerName) => {
    cy.waitForTable()
    cy.contains(tableHeaderCellLocator, filerName).find('button').click()
    cy.contains('.v-overlay__content .v-list-item', 'Add to filter').click()
})

function getCellByName(rowIndex, columnName) {
    return cy.contains(tableHeaderCellLocator, regex(columnName))
            .invoke('index')
            .then((columnIndex) => cy.get(tableBodyLocator).filter(':visible').find('tr').eq(rowIndex).find('td').eq(columnIndex))
}

function getCellByNameNoVisibilityCheck(rowIndex, columnName) {
    return cy.contains(tableHeaderCellLocator, regex(columnName))
            .invoke('index')
            .then((columnIndex) => cy.get(tableBodyLocator).find('tr').eq(rowIndex).find('td').eq(columnIndex))
}

function getCellByNameInPopUp(rowIndex, columnName) {
    return cy.contains(tableHeaderCellLocatorInPopUp, regex(columnName)).invoke('index')
            .then((columnIndex) => cy.get(tableBodyLocatorInPopUp).find('tr').eq(rowIndex).find('td').eq(columnIndex))
}

function checkValue(rowIndex, columnName, expected) {
    if (expected == null) {
        getCellByName(rowIndex, columnName).should('be.empty')
    } else {
        getCellByName(rowIndex, columnName).should('contain', expected)
    }
}
