@REQ_ID:1074254
Feature: Studies - Define Study - Study Structure Wizard

    As a system user,
    I want the system to ensure [Scenario],
    So that I must be able to make complete and consistent specification of study structure.

    Background: User is logged in and study has been selected
        Given The user is logged in

    Scenario: User must be able to create  arms using stepper wizard
        Given The study for testing study structure is selected
        When The study 'arms' page is opened for that study
        And The user defines multiple arms for the study through Study with cohorts, branch arms and subpopulations section
        Then The multiple arms are created for the study

    Scenario: User must be able to edit arms using stepper wizard
        Given The study for testing study structure is selected
        When The study 'arms' page is opened for that study
        And The user updates arms for the study through Study with cohorts, branch arms and subpopulations section
        Then The arms are updated for the study

    Scenario: User must be able to remove arms using stepper wizard
        Given The study for testing study structure is selected
        When The study 'arms' page is opened for that study
        And The user removes arms from the study through Study with cohorts, branch arms and subpopulations section
        Then The arms are removed from the study

    Scenario: User must be able to create cohorts using stepper wizrd
        Given The study for testing study structure is selected
        When The study 'cohorts' page is opened for that study
        And The user defines multiple cohorts for the study through Study with cohorts, branch arms and subpopulations section
        Then The multiple cohorts are created for the study

    Scenario: User must be able to edit cohorts using stepper wizard
        Given The study for testing study structure is selected
        When The study 'cohorts' page is opened for that study
        And The user updates cohorts for the study through Study with cohorts, branch arms and subpopulations section
        Then The cohorts are updated for the study

    Scenario: User must be able to remove cohorts using stepper wizard
        Given The study for testing study structure is selected
        When The study 'cohorts' page is opened for that study
        And The user removes cohorts from the study through Study with cohorts, branch arms and subpopulations section
        Then The cohorts are removed from the study

    Scenario: User must be able to define number of participants in branches using stepper wizard
        Given The study for testing study structure is selected
        When The study 'branches' page is opened for that study
        And The user assigns number of participants in the branches
        Then The number of participants are correctly assigned to the branches

    Scenario: User must be able to copy number of participants in branche to all other branches/rows
        Given The study for testing study structure is selected
        When The study 'branches' page is opened for that study
        And The user copies the number of participants to all rows
        Then The number of participants is updated in each row

