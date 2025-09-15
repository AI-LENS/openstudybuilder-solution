const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let topicCode, instanceName

Then("Topic code is changed to the unique one", () => cy.contains('.v-stepper-window-item .v-input', 'Topic code').clear().type(Date.now()))

Then("Created activity is visible in table", () => cy.searchAndCheckPresence(instanceName, true))

Then("Activity instance is not visible in table", () => cy.searchAndCheckPresence(instanceName, false))

Given("The Activity Instance Wizard Stepper {string} page is displayed", (stepperPage) => {
    cy.contains('.v-stepper-item', stepperPage).should('have.class', 'v-stepper-item--selected')
})

Given("Add activity item class button is clicked", () => cy.get('.v-window-item button').filter(':visible').contains('Add Activity Item Class').eq(0).click())

When("An Activity is selected from the activity list", () => {
    cy.get('.v-overlay-container table tbody tr [type="radio"]').eq(0).check()
})

When("The {string} is selected from the Activity instance class field", name => requiredTabSelection('Activity instance', name))

When("First value is selected from the Data domain field", () => selectFirstDataDomain())

When("Value {string} is selected for {int} Activity item class field", (value, index) => selectOptionalActivityItemClass(index, value))

When("The first Activity item class is selected", () => selectFirstActivityItemClass())

When("The {string} is selected from the Activity instance domain field", name => requiredTabSelection('Data domain', name))

Then("The mandatory value field is outlined in red", () => cy.get('.v-field--error').should('be.visible'))

Then("The test_code, test_name, unit_dimention and standard_unit fields are inactive", () => validateRequiredInstanceClassFields('have.class', 'v-input--disabled'))

Then("The test_code, test_name, unit_dimention and standard_unit values are empty", () => validateRequiredInstanceClassFields('have.value', ''))

Then("The Required Activity Item Classes field is displayed", () => cy.contains('.v-overlay .v-row .dialog-title', 'Required Activity Item Classes'). should('be.visible'))

Then("Warning is displayed for mandatory field {string}", (fieldName) => warningIsDisplayed(fieldName))

Then("Warning about not matching name and sentence case name is displayed", () => warningIsDisplayed('Sentence case name', "Sentence case name can only differ in case compared to name value"))

Then("Warning about already existing topic code is displayed", () => cy.checkSnackbarMessage(`Activity Instance with Topic Code '${topicCode}' already exists`))

Then("Warning about already existing activity name is displayed", () => cy.checkSnackbarMessage(`Activity Instance with Name '${instanceName}' already exists`))

Then("Warning about not selected acitivity is displayed", () => cy.checkSnackbarMessage(`You must select an activity from the list`))

Then("Mandatory field {string} is cleared", (fieldName) => clearField(fieldName))

Then("Field {string} is filled with value {string}", (fieldName, value) => fillField(fieldName, value))

Then("Automatically assigned activity instance name is saved", () => {
    cy.contains('.v-stepper-window-item .v-input', 'Activity instance name').find('input').invoke('val').then(text => instanceName = text)
})

Then("Activity instance is created", () => createInstance(true, true))

Then("Second Activity instance with the same topic code is created", () => createInstance(true, false))

Then("Second Activity instance with the same name is created", () => createInstance(false, true))

Then("The test_code value is automatically populated", () => cy.contains('.d-flex .v-input', 'test_code').next().should('not.be.empty'))

Then("The standard_unit value is not automatically populated", () => cy.contains('.d-flex .v-input', 'standard_unit').next().should('have.value', ''))

Then("The test_code value is enabled for picking different value", () => {
    cy.contains('.d-flex .v-input', 'test_code').next().click()
    cy.get('.v-overlay .v-list-item').eq(1).click()
})

Then("Sentence case name is lowercased version of instance name", () => {
    cy.contains('.v-stepper-window-item .v-input', 'Activity instance name').find('input').invoke('val').then(nameText => {
        cy.contains('.v-stepper-window-item .v-input', 'Sentence case name').find('input').invoke('val').should('equal', nameText.toLowerCase())
    })
})

When("The test_name value is selected", () => {
    cy.wait(2500)
    selectRequiredActivityItemClass('test_name')
})

When("The unit_dimension value is selected", () => selectRequiredActivityItemClass('unit_dimension'))

When("The Required Activity Item Classes field is filled with data", () => {
    cy.wait(5000)
    selectRequiredActivityItemClass('test_name')
    selectRequiredActivityItemClass('unit_dimension')
    selectRequiredActivityItemClass('standard_unit')
})

When("Activity created via API is searched for", () => {
    cy.getActivityNameByUid().then(name => cy.searchForInPopUp(name))
})

Then("Correct instance overview page is displayed", () => cy.contains('.page-title', instanceName))

function createInstance(uniqueName, uniqueTopicCode) {
    cy.intercept('/api/concepts/activities/activity-instances').as('createInstance')
    if (uniqueName) instanceName = `Instance${Date.now()}`
    if (uniqueTopicCode) topicCode = `Topic${Date.now()}`
    cy.clickButton('add-activity')
    cy.wait(1000)
    cy.get('.v-overlay-container table tbody tr [type="radio"]').eq(0).check()
    cy.clickFormActionButton('continue')
    requiredTabSelection('Activity instance', 'CategoricFindings')
    selectFirstDataDomain()
    cy.clickFormActionButton('continue')
    fillField('ADaM parameter', 'ADAM')
    fillField('Topic code', topicCode)
    fillField('Activity instance name', instanceName)
    fillField('Sentence case name', instanceName.toLowerCase())
    cy.clickFormActionButton('continue')
    cy.clickFormActionButton('save')
    cy.wait('@createInstance')
    cy.waitForTable()
}

function selectRequiredActivityItemClass(type) {
    cy.contains('.d-flex .v-input', type).siblings('.v-input .v-field.v-field--loading').should('not.exist')
    cy.contains('.d-flex .v-input', type).next().click()
    cy.get('.v-overlay .v-list-item').eq(0).click()
}

function selectFirstActivityItemClass() {
    cy.get('.v-form .v-card-text').filter(':visible').eq(0).contains('.d-flex .v-input', 'Activity item class').click()
    cy.get('.v-overlay .v-list-item').eq(0).click()
}

function selectOptionalActivityItemClass(index, itemClassName) {
    cy.get('.v-form .v-card-text').filter(':visible').eq(index).contains('.d-flex .v-input', 'Activity item class').click()
    cy.contains('.v-overlay .v-list-item', itemClassName).click()
    cy.get('.v-form .v-card-text').filter(':visible').eq(index).contains('.d-flex .v-input', 'Activity item class').next().click()
    cy.get('.v-overlay .v-list-item').eq(0).should('not.have.text', 'No data available').click()
    cy.wait(1000)
}

function requiredTabSelection(dropdown_name, value) {
    cy.contains('.v-stepper-window-item .v-input', dropdown_name).click()
    cy.contains('.v-overlay .v-list-item', value).click()
}

function selectFirstDataDomain() {
    cy.contains('.v-stepper-window-item .v-input', 'Data domain').click()
    cy.get('.v-overlay .v-list-item').eq(0).click()
}

function warningIsDisplayed(fieldName, message = 'This field is required') {
    cy.contains('.v-stepper-window-item .v-input', fieldName).contains(message).should('be.visible')
}

function clearField(fieldName) {
    cy.contains('.v-stepper-window-item .v-input', fieldName).clear()
}

function fillField(fieldName, value) {
    cy.contains('.v-stepper-window-item .v-input', fieldName).clear().type(value)
}

function validateRequiredInstanceClassFields(validationRule, validationValue) {
    cy.contains('.d-flex .v-input', 'test_name').should(validationRule, validationValue)
    cy.contains('.d-flex .v-input', 'test_code').should(validationRule, validationValue)
    cy.contains('.d-flex .v-input', 'unit_dimension').should(validationRule, validationValue)
    cy.contains('.d-flex .v-input', 'standard_unit').should(validationRule, validationValue)
}