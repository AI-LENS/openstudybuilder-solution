const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let structure_tests_study_uid

When('The study for testing study structure is selected', () => {
      cy.sendGetRequest('/studies?include_sections=study_description&sort_by[current_metadata.identification_metadata.study_id]=true&page_size=0').then((response) => {
             structure_tests_study_uid = response.body.items
                .find(study => study.current_metadata.identification_metadata.study_number == 9877)
                .uid
    })
})

When('The study {string} page is opened for that study', (page) => {
    cy.visit(`/studies/${structure_tests_study_uid}/study_structure/${page}`)
})

When('The user defines multiple arms for the study through Study with cohorts, branch arms and subpopulations section', () => {
    cy.intercept('**/study-design-classes').as('designClass')
    cy.wait('@designClass').then((req) => {
        expect(req.response.statusCode).to.eq(200)
    })
    cy.get('.mdi-plus').click()
    cy.clickButton('full-design-study')
    cy.clickButton('continue-stepper')
    cy.selectVSelect('arm-type', 'Placebo Arm')
    cy.fillInput('arm-name', 'Test Placebo Arm')
    cy.fillInput('arm-short-name', 'PArm')
    cy.fillInput('randomization-group', 'RA')
    cy.fillInput('arm-code', 'A')
    cy.fillInput('arm-description', 'Test Arm A')
    cy.clickButton('arm-push')

    cy.get('[data-cy="arm-type"]').eq(1).click()
    cy.get('.v-list')
        .filter(':visible')
        .should('not.contain', 'No data available')
        .within(() => cy.get('.v-list-item').first().click())
    cy.get('[data-cy="arm-name"]').eq(1).type('Test Arm Two')
    cy.get('[data-cy="arm-short-name"]').eq(1).type('CArm')
    cy.get('[data-cy="randomization-group"]').eq(1).type('RB')
    cy.get('[data-cy="arm-code"]').eq(1).type('B')
    cy.get('[data-cy="arm-description"]').eq(1).type('Test Arm B')
    cy.clickButton('arm-push')
    cy.get('[data-cy="arm-type"]').eq(2).click()
    cy.get('.v-list')
        .filter(':visible')
        .should('not.contain', 'No data available')
        .within(() => cy.get('.v-list-item').last().click())
    cy.get('[data-cy="arm-name"]').eq(2).type('Test Arm Three')
    cy.get('[data-cy="arm-short-name"]').eq(2).type('CArmX')
    cy.get('[data-cy="randomization-group"]').eq(2).type('RBX')
    cy.get('[data-cy="arm-code"]').eq(2).type('BX')
    cy.get('[data-cy="arm-description"]').eq(2).type('Test Arm BX')
    cy.clickButton('save-close-stepper')
    cy.wait(2000)

})

Then('The multiple arms are created for the study', () => {
    cy.tableContains('Test Placebo Arm')
    cy.tableContains('PArm')
    cy.tableContains('RA')
    cy.tableContains('Test Arm A')
    cy.tableContains('Test Arm Two')
    cy.tableContains('CArm')
    cy.tableContains('RB')
    cy.tableContains('Test Arm B')
})

When('The user updates arms for the study through Study with cohorts, branch arms and subpopulations section', () => {
    cy.intercept('**/study-design-classes').as('designClass')
    cy.wait('@designClass').then((req) => {
        expect(req.response.statusCode).to.eq(200)
    })
    cy.get('.mdi-pencil').click()
    cy.get('[data-cy="arm-name"]').eq(0).clear().type('Test Arm Two 2')
    cy.get('[data-cy="arm-short-name"]').eq(0).clear().type('CArm2')
    cy.get('[data-cy="randomization-group"]').eq(0).clear().type('RB2')
    cy.get('[data-cy="arm-code"]').eq(0).clear().type('B2')
    cy.get('[data-cy="arm-description"]').eq(0).clear().type('Test Arm B2')

    cy.get('[data-cy="arm-name"]').eq(1).clear().type('Test Arm Two 1')
    cy.get('[data-cy="arm-short-name"]').eq(1).clear().type('BArm1')
    cy.get('[data-cy="randomization-group"]').eq(1).clear().type('RA1')
    cy.get('[data-cy="arm-code"]').eq(1).clear().type('A1')
    cy.get('[data-cy="arm-description"]').eq(1).clear().type('Test Arm A1')
    cy.clickButton('save-close-stepper')
    cy.wait(2000)

})


Then('The arms are updated for the study', () => {
    cy.tableContains('Test Arm Two 2')
    cy.tableContains('CArm2')
    cy.tableContains('RB2')
    cy.tableContains('B2')
    cy.tableContains('Test Arm B2')
    cy.tableContains('Test Arm Two 1')
    cy.tableContains('BArm1')
    cy.tableContains('A1')
})

When('The user removes arms from the study through Study with cohorts, branch arms and subpopulations section', () => {
    cy.intercept('**/study-design-classes').as('designClass')
    cy.wait('@designClass').then((req) => {
        expect(req.response.statusCode).to.eq(200)
    })
    cy.get('.mdi-pencil').click()
    cy.clickFirstButton('remove-arm')
    cy.clickButton('continue-popup')
    cy.wait(2000)
    cy.clickButton('save-close-stepper')
    cy.wait(2000)

})

Then('The arms are removed from the study', () => {
    cy.contains('Test Arm Two 2').should('not.exist')
    cy.contains('CArm2').should('not.exist')
    cy.contains('RB2').should('not.exist')
    cy.contains('B2').should('not.exist')
})

When('The user defines multiple cohorts for the study through Study with cohorts, branch arms and subpopulations section', () => {
    cy.get('.mdi-pencil').click()
    cy.get('[data-cy="cohort-code"]').eq(0).clear().type('C0')
    cy.get('[data-cy="cohort-name"]').eq(0).clear().type('Cohort Test 1')
    cy.get('[data-cy="cohort-short-name"]').eq(0).clear().type('CT1')
    cy.get('[data-cy="cohort-description"]').eq(0).clear().type('Description C1')
    cy.clickButton('cohort-push')
    cy.get('[data-cy="cohort-code"]').eq(1).clear().type('C1')
    cy.get('[data-cy="cohort-name"]').eq(1).clear().type('Cohort Test 2')
    cy.get('[data-cy="cohort-short-name"]').eq(1).clear().type('CT2')
    cy.get('[data-cy="cohort-description"]').eq(1).clear().type('Description C2')
    cy.clickButton('cohort-push')
    cy.get('[data-cy="cohort-code"]').eq(2).clear().type('C2')
    cy.get('[data-cy="cohort-name"]').eq(2).clear().type('Cohort Test 3')
    cy.get('[data-cy="cohort-short-name"]').eq(2).clear().type('CT3')
    cy.get('[data-cy="cohort-description"]').eq(2).clear().type('Description C3')
    cy.clickButton('save-close-stepper')

})

When('The multiple cohorts are created for the study', () => {
    cy.tableContains('C0')
    cy.tableContains('Cohort Test 1')
    cy.tableContains('CT1')
    cy.tableContains('Description C1')
    cy.tableContains('C1')
    cy.tableContains('Cohort Test 2')
    cy.tableContains('CT2')
    cy.tableContains('Description C2')
})

When('The user updates cohorts for the study through Study with cohorts, branch arms and subpopulations section', () => {
    cy.get('.mdi-pencil').click()
    cy.get('[data-cy="cohort-code"]').eq(0).clear().type('C0A')
    cy.get('[data-cy="cohort-name"]').eq(0).clear().type('Cohort Test 1A')
    cy.get('[data-cy="cohort-short-name"]').eq(0).clear().type('CT1A')
    cy.get('[data-cy="cohort-description"]').eq(0).clear().type('Description C1A')
    cy.get('[data-cy="cohort-code"]').eq(1).clear().type('C1B')
    cy.get('[data-cy="cohort-name"]').eq(1).clear().type('Cohort Test 2B')
    cy.get('[data-cy="cohort-short-name"]').eq(1).clear().type('CT2B')
    cy.get('[data-cy="cohort-description"]').eq(1).clear().type('Description C2B')
    cy.clickButton('save-close-stepper')
})

When('The cohorts are updated for the study', () => {
    cy.tableContains('C0A')
    cy.tableContains('Cohort Test 1A')
    cy.tableContains('CT1A')
    cy.tableContains('Description C1A')
    cy.tableContains('C1B')
    cy.tableContains('Cohort Test 2B')
    cy.tableContains('CT2B')
    cy.tableContains('Description C2B')
})

When('The user removes cohorts from the study through Study with cohorts, branch arms and subpopulations section', () => {
    cy.intercept('**/study-design-classes').as('designClass')
    cy.wait('@designClass').then((req) => {
        expect(req.response.statusCode).to.eq(200)
    })
    cy.get('.mdi-pencil').click()
    cy.clickFirstButton('remove-cohort')
    cy.clickButton('continue-popup')
    cy.wait(2000)
    cy.clickButton('save-close-stepper')
    cy.wait(2000)
})

When('The cohorts are removed from the study', () => {
    cy.contains('C0A').should('not.exist')
    cy.contains('Cohort Test 1A').should('not.exist')
    cy.contains('CT1A').should('not.exist')
    cy.contains('Description C1A').should('not.exist')
})

When('The user assigns number of participants in the branches', () => {
    cy.intercept('**/study-design-classes').as('designClass')
    cy.wait('@designClass').then((req) => {
        expect(req.response.statusCode).to.eq(200)
    })
    cy.get('.mdi-pencil').click()
    cy.wait(1000)
    cy.get('[data-cy="number-of-subjects-single-arm"]').eq(0).clear().type(22)
    cy.get('[data-testid="increment"]').eq(0).click()
    cy.get('[data-cy="number-of-subjects-single-arm"]').eq(1).clear().type(50)
    cy.clickButton('continue-stepper')
    cy.wait(2500)

})

Then('The number of participants are correctly assigned to the branches', () => {
    cy.tableContains('23')
    cy.tableContains('50')

})

Then('The user copies the number of participants to all rows', () => {
    cy.intercept('**/study-design-classes').as('designClass')
    cy.wait('@designClass').then((req) => {
        expect(req.response.statusCode).to.eq(200)
    })
    cy.get('.mdi-pencil').click()
    cy.wait(1000)
    cy.get('[data-cy="number-of-subjects-single-arm"]').eq(0).clear().type(10)
    cy.clickButton('copy-branches')
    cy.clickButton('continue-stepper')
    cy.wait(2500)

})

Then('The number of participants is updated in each row', () => {
    cy.tableContains('10')
})
