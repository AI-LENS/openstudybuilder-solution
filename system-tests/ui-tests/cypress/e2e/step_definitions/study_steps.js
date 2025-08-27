const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let study_uid, studyNumber, studyAcronym

Given('A test study is selected', () => {
    cy.selectTestStudy(Cypress.env('TEST_STUDY_UID'))
})

Given('A {string} study is selected', (study_id) => {
    cy.selectStudyByStudyId(study_id)
})

Given('A secondary test study is selected', () => {
    cy.selectTestStudy('Study_000002')
})

Given('The study with multiple visists created has been selected', () => {
    cy.selectTestStudy('Study_000003')
})

Given('A study in draft status without study number is selected', () => {
    cy.selectTestStudy('Study_000004')
})

Given('A study in draft status without title is selected', () => {
    cy.selectTestStudy('Study_000005')
})

Given('A study in draft status with defined study number and study title is selected', () => {
    cy.selectTestStudy('Study_000006')
})

Given('A study in locked status with defined study number and study title is selected', () => {
    cy.selectTestStudy('Study_000007')
})

When('A new study is added', () => {
    studyAcronym = `AutomationTestStudy${Date.now()}`
    studyNumber = `${Math.floor(1000 + Math.random() * 9000)}`
    cy.waitForTable()
    cy.clickButton('add-study')
    cy.selectAutoComplete('project-id', 'CDISC DEV')
    cy.fillInput('study-number', studyNumber)
    cy.fillInput('study-acronym', studyAcronym)
    cy.clickButton('save-button')
    cy.wait(2500)
    cy.waitForTable()
})

Then('The study is visible within the table', () => {
    cy.checkRowByIndex(0, 'Study acronym', studyAcronym)
    cy.checkRowByIndex(0, 'Study number', studyNumber)
    cy.checkRowByIndex(0, 'Project ID', 'CDISC DEV')
})

When('Study is found', () => cy.searchAndCheckPresence(studyAcronym, true))

When('[API] Study uid is fetched', () => cy.getStudyUid(studyNumber).then(id => study_uid = id))

When('Go to created study', () => {
    cy.visit(`/studies/${study_uid}/activities/soa`)
    cy.waitForPage()
})

When('Go to {string} study page {string}', (studyNumber, page) => {
    cy.getStudyUidById(studyNumber).then(id => cy.visit(`/studies/${id}/${page}`))
    cy.waitForPage()
})