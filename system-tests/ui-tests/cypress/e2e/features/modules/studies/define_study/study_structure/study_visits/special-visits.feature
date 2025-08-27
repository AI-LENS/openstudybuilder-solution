@REQ_ID:1074254
Feature: Studies - Define Study - Study Structure - Study Visits - Special Visits

    See shared notes for study visits in file study-visit-intro-notes.txt

    Background: User is logged in and study has been selected
        Given The user is logged in
        And The study with uid 'Study_000003' is selected
        And [API] The epoch with type 'Pre Treatment' and subtype 'Screening' exists in selected study
        And [API] Global Anchor visit within epoch 'Screening' exists

    Scenario: [Create][Special visit] User must be able to create special visit for given epoch
        Given The '/studies/Study_000003/study_structure/visits' page is opened
        And User waits for epochs to load
        When Add visit button is clicked
        And Visit scheduling type is selected as 'SPECIAL_VISIT'
        And Form continue button is clicked
        And Epoch 'Screening' is selected for the visit
        And Form continue button is clicked
        And Visit Type is selected as 'Treatment'
        And Contact mode is selected as 'On Site Visit'
        And Time reference is selected as 'Visit 1'
        And Form save button is clicked
        And The pop up displays 'Visit added'
        And User searches for 'V1A'
        And Study visit class is 'Special visit' and the timing is empty
        When Add visit button is clicked
        And Visit scheduling type is selected as 'SPECIAL_VISIT'
        And Form continue button is clicked
        And Epoch 'Screening' is selected for the visit
        And Form continue button is clicked
        And Visit Type is selected as 'Treatment'
        And Contact mode is selected as 'On Site Visit'
        And Time reference is selected as 'Visit 1'
        And Form save button is clicked
        And The pop up displays 'Visit added'
        And User searches for 'V1B'
        And Study visit class is 'Special visit' and the timing is empty

    Scenario: [Create][Discontinuation visit] User must be able to create discontinuation special visit for given epoch
        Given The '/studies/Study_000003/study_structure/visits' page is opened
        And User waits for epochs to load
        When Add visit button is clicked
        And Visit scheduling type is selected as 'SPECIAL_VISIT'
        And Form continue button is clicked
        And Epoch 'Screening' is selected for the visit
        And Form continue button is clicked
        And Visit Type is selected as 'Early discontinuation'
        And Contact mode is selected as 'On Site Visit'
        And Time reference is selected as 'Visit 1'
        And Form save button is clicked
        And The pop up displays 'Visit added'
        And User searches for 'V1X'
        And Study visit class is 'Special visit' and the timing is empty

    @BUG_ID:2844670
    Scenario: [EDIT][Special visit] User must be able to edit special visit
        Given The '/studies/Study_000003/study_structure/visits' page is opened
        And User waits for epochs to load
        When User searches for 'V1B'
        And The 'Edit' option is clicked from the three dot menu list
        And Form continue button is clicked
        And Form continue button is clicked
        And Visit description is changed to 'Testing edition'
        And Form save button is clicked
        Then Visit description is displayed in the table as 'Testing edition'