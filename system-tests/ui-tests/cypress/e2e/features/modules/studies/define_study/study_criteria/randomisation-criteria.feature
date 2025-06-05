@REQ_ID:1074256
Feature: Studies - Define Study - Study Criteria - Randomisation Criteria

    Background: User is logged in and study has been selected
        Given The user is logged in   
        And A test study is selected

    Scenario: [Navigaion] User must be able to navigate to the Randomisation Criteria page
        Given The '/studies' page is opened
        When The 'Study Criteria' submenu is clicked in the 'Define Study' section
        And The 'Randomisation Criteria' tab is selected
        Then The current URL is '/studies/Study_000001/selection_criteria/Randomisation%20Criteria'

    Scenario: [Table][Columns][Names] User must be able to see the page table with correct columns
        Given The '/studies/Study_000001/selection_criteria/Randomisation%20Criteria' page is opened
        Then A table is visible with following headers
            | headers                |
            | #                      |
            | Randomisation Criteria |
            | Guidance text          |
            | Key criteria           |
            | Modified               |
            | Modified by            |

    Scenario: [Online help] User must be able to read online help for the page
        Given The '/studies/Study_000001/selection_criteria/Randomisation%20Criteria' page is opened
        And The online help button is clicked
        Then The online help panel shows 'General' panel with content "Study eligibility criteria as would be described in the protocol"
        Then The online help panel shows 'Study Criteria' panel with content "Follow the tabs to define the different criteria applicable for the study"

    Scenario: [Table][Columns][Visibility] User must be able to use column selection option
        Given The '/studies/Study_000001/selection_criteria/Randomisation%20Criteria' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column
    
    @unstable_disabled
    Scenario: User must be able to create the Randomisation Criteria based on existing criteria template
        Given The '/studies/Study_000001/selection_criteria/Randomisation%20Criteria' page is opened
        When The 'randomisation' criteria is copied from existing template
        Then The 'randomisation' criteria created from existing template is visible within the table with correct data

    Scenario: [Create][From scratch] User must be able to create the Randomisation Criteria from scratch
        Given The '/studies/Study_000001/selection_criteria/Randomisation%20Criteria' page is opened
        When The 'randomisation' criteria is created from scratch
        Then The 'randomisation' criteria created from new template is visible within the table with correct data

    Scenario: [Create][From studies][By Id] User must be able to select Randomisation Criteria from other existing studies by study id
        Given The '/studies/Study_000002/selection_criteria/Randomisation%20Criteria' page is opened
        When The 'Randomisation' criteria is created from studies
        And The test study for 'Randomisation' criteria copying is selected by study id
        And The 'Randomisation' criteria from test study is copied
        Then The 'Randomisation Criteria' copied from test study is visible within the table with correct data

    Scenario: [Export][CSV] User must be able to export the data in CSV format
        Given The '/studies/Study_000001/selection_criteria/Randomisation%20Criteria' page is opened
        And The user exports the data in 'CSV' format
        Then The study specific 'StudyCriteria' file is downloaded in 'csv' format

    Scenario: [Export][Json] User must be able to export the data in JSON format
        Given The '/studies/Study_000001/selection_criteria/Randomisation%20Criteria' page is opened
        And The user exports the data in 'JSON' format
        Then The study specific 'StudyCriteria' file is downloaded in 'json' format

    Scenario: [Export][Xml] User must be able to export the data in XML format
        Given The '/studies/Study_000001/selection_criteria/Randomisation%20Criteria' page is opened
        And The user exports the data in 'XML' format
        Then The study specific 'StudyCriteria' file is downloaded in 'xml' format

    Scenario: [Export][Excel] User must be able to export the data in EXCEL format
        Given The '/studies/Study_000001/selection_criteria/Randomisation%20Criteria' page is opened
        And The user exports the data in 'EXCEL' format
        Then The study specific 'StudyCriteria' file is downloaded in 'xlsx' format

    @pending_implementation
    Scenario: User must be able to select Randomisation Criteria from other existing studies by study acronym
        Given The '/studies/Study_000002/selection_criteria/Randomisation%20Criteria' page is opened
        When The 'Randomisation' criteria is created from studies
        And The test study for 'Randomisation' criteria copying is selected by study acronym
        And The 'Randomisation' criteria from test study is copied
        Then The 'Randomisation Criteria' copied from test study is visible within the table with correct data