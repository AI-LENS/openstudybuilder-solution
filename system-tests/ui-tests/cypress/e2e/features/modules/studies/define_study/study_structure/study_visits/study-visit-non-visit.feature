@REQ_ID:1074254
Feature: Studies - Define Study - Study Structure - Study Visits - Non Visit

    See shared notes for study visits in file study-visit-intro-notes.txt

    Background: User is logged in and study has been selected
        Given The user is logged in
        And The study with uid 'Study_000003' is selected
        And [API] The epoch with type 'Pre Treatment' and subtype 'Screening' exists in selected study

    Scenario: [Create][Non visit] User must be able to create non visit for given study
        Given The '/studies/Study_000003/study_structure/visits' page is opened
        And User waits for epochs to load
        When Add visit button is clicked
        And Visit scheduling type is selected as 'NON_VISIT'
        And Form continue button is clicked
        And Epoch 'Basic' is selected for the visit
        And Form continue button is clicked
        And Form save button is clicked
        And The pop up displays 'Visit added'
        When User searches for 'Non-visit'
        Then Study visit class is 'Non visit' and the timing is empty

    @BUG_ID:2776541
    Scenario: [EDIT][Special visit] User must not be able to edit non visit number
        Given The '/studies/Study_000003/study_structure/visits' page is opened
        When User searches for 'Non-visit'
        And The 'Edit' option is clicked from the three dot menu list
        And Form continue button is clicked
        And Form continue button is clicked 
        Then Visit number field is disabled