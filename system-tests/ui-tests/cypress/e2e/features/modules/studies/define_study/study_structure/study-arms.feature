@REQ_ID:1074254
Feature: Studies - Define Study - Study Structure - Study Arms

    As a system user,
    I want the system to ensure [Scenario],
    So that I must be able to make complete and consistent specification of study arms.

    Background: User is logged in and study has been selected
        Given The user is logged in
        And A test study is selected

    Scenario: [Navigation] User must be able to navigate to Study Arms page using side menu
        Given The '/studies' page is opened
        When The 'Study Structure' submenu is clicked in the 'Define Study' section
        And The 'Study Arms' tab is selected
        Then The current URL is '/study_structure/arms'

    Scenario: [Table][Options] User must be able to see the Study Arms table with following options
        Given The test study '/study_structure/arms' page is opened
        Then A table is visible with following options
            | options                                                         |
            | Add study arm                                                   |
            | Columns                                                         |
            | Export                                                          |
            | Show version history                                            |
            | Add select boxes to table to allow selection of rows for export |

    Scenario: [Table][Columns][Names] User must be able to see the Study Arms table with following columns
        Given The test study '/study_structure/arms' page is opened
        And A table is visible with following headers
            | headers             |
            | #                   |
            | Type                |
            | Arm name            |
            | Arm short name      |
            | Randomisation group |
            | Arm code            |
            | Number of subjects  |
            | Connected Branches  |
            | Description         |
            | Colour              |
            | Modified            |
            | Modified by         |

    Scenario: [Online help] User must be able to read online help for the page
        Given The test study '/study_structure/arms' page is opened
        And The online help button is clicked
        Then The online help panel shows 'Study Arms' panel with content "Specification of the planned investigational treatment arms. An arm is a planned 'path' of interventions through the trial, e.g. arm AB is treatment A followed by treatment B."

    Scenario: [Table][Columns][Visibility] User must be able to use column selection option
        Given The test study '/study_structure/arms' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column
    
    Scenario: [Create][Positive case] User must be able to add a new Study Arm
        Given The test study '/study_structure/arms' page is opened
        When The new study arm form is filled and saved
        Then The new study arm is visible within the study arms table

   Scenario: [Actions][Edit] User must be able to edit an existing Study Arm
        Given The test study '/study_structure/arms' page is opened
        And The Study Arm is found
        When The 'Edit' option is clicked from the three dot menu list
        And The arm data is edited and saved
        And The Study Arm is found
        Then The study arm with updated values is visible within the study arms table

    # Scenario: Arm code default value must be populated from Randomisation Group
    #     Given The test study '/study_structure/arms' page is opened
    #     When The Randomisation Group is populated in the Add New Arm form
    #     And no value is specified for the field Arm Code
    #     Then The Arm code field is populated with value from Randomisation group field

    Scenario Outline: [Create][Mandatory fields] User must not be able to provide value other than positive integer for Number of subjects
        Given The test study '/study_structure/arms' page is opened
        And The value '<number>' is entered for the field Number of subjects in the Study Arms form
        Then The validation appears under the field in the Study Arms form

        Examples:
            | number |
            | -1     |
            | 0      |
            | -10    |

    Scenario: [Create][Mandatory fields] User must not be able to create a Study Arm without Arm Name and Arm Short Name provided in the Study Arms form
        Given The test study '/study_structure/arms' page is opened
        When The Arm name field is not populated
        And The Arm short name field is not populated
        And The 'save-button' button is clicked
        Then The required field validation appears for the '2' empty fields
        And The form is not closed

    Scenario: [Create][Uniqueness check][Name] User must not be able to create two Arms within one study using the same Arm name
        Given The test study '/study_structure/arms' page is opened
        When The Study Arm is created with given name
        And Another Study Arm is created with the same arm name
        Then The system displays the message "Value 'Test Arm Name' in field Arm name is not unique for the study"
        And The form is not closed

    Scenario: [Create][Uniqueness check][Short Name] User must not be able to create two Arms within one study using the same Arm short name
        Given The test study '/study_structure/arms' page is opened
        When The Study Arm is created with given short name
        And Another Study Arm is created with the same arm short name
        Then The system displays the message "Value 'Test Short Name' in field Arm short name is not unique for the study"
        And The form is not closed

    Scenario: [Create][Uniqueness check][Randomisation group] User must not be able to create two Arms within one study using the same Arm randomisation group
        Given The test study '/study_structure/arms' page is opened
        When The Study Arm is created with given randomisation group
        And Another Study Arm is created with the same randomisation group
        Then The system displays the message "Value 'Test Randomisation Group' in field Arm Randomization code is not unique for the study"
        And The form is not closed

    # Scenario Outline: User must not be able to use text longer than specified in this scenario for Study Arms form
    #     Given The test study '/study_structure/arms' page is opened
    #     When For the '<field>' a text longer than '<length>' is provided in the Study Arms form
    #     Then The message "This field must not exceed " '<length>' " characters" is displayed

    #     Examples:
    #         | field          | length |
    #         | arm-name       | 200    |
    #         | arm-short-name | 20     |
    # | arm-randomisation-group | 20     |  Comments from Mikkel: This requirement is under disucssion, will be updated later.

    Scenario: [Create][Mandatory fields] User must not be able to use text longer than 20 characters for the Study Arm Arm Code field in the Study Arms form
        Given The test study '/study_structure/arms' page is opened
        When In the Study Arms form randomistaion group is provided
        And The study arm code is updated to exceed 20 characters
        Then The message 'This field must not exceed 20 characters' is displayed

    Scenario: [Export][CSV] User must be able to export the data in CSV format
        Given The test study '/study_structure/arms' page is opened
        And The user exports the data in 'CSV' format
        Then The study specific 'StudyArms' file is downloaded in 'csv' format

    Scenario: [Export][Json] User must be able to export the data in JSON format
        Given The test study '/study_structure/arms' page is opened
        And The user exports the data in 'JSON' format
        Then The study specific 'StudyArms' file is downloaded in 'json' format

    Scenario: [Export][Xml] User must be able to export the data in XML format
        Given The test study '/study_structure/arms' page is opened
        And The user exports the data in 'XML' format
        Then The study specific 'StudyArms' file is downloaded in 'xml' format

    Scenario: [Export][Excel] User must be able to export the data in EXCEL format
        Given The test study '/study_structure/arms' page is opened
        And The user exports the data in 'EXCEL' format
        Then The study specific 'StudyArms' file is downloaded in 'xlsx' format
        
    @BUG_ID:2844762
    Scenario: Table  must not disappear when creating a study arm without arm type provided
        Given The test study '/study_structure/arms' page is opened
        When The study arm is created without arm type provided
        Then The study arms table is displayed correctly

    @manual_test
    Scenario: User must be presented with the warning message when deleting Study Arm
        Given The test study '/study_structure/arms' page is opened
        And The study arm related to study branch arm and study design cell exists
        And The Study Arm is found
        When The 'Delete' option is clicked from the three dot menu list
        Then The warning message appears 'Removing this Study Arm will remove all related Study Cells and Branches'

    @manual_test
    Scenario: User must be able to delete all related items to Study Arm when Study arm is removed
        Given The test study '/study_structure/arms' page is opened
        And The study arm related to study branch arm and study design cell exists
        When The the study arm related to those elements is removed
        Then That study arm no longer exists
        And Related study design cells are deleted
        And Related study branch arms are deleted

    @manual_test
    Scenario: User must be able to read change history of output
        Given The test study '/study_structure/arms' page is opened
        When The user opens version history
        Then The user is presented with version history of the output containing timestamp and username

    @manual_test
    Scenario: User must be able to read change history of selected element
        Given The test study '/study_structure/arms' page is opened
        And The 'Show history' option is clicked from the three dot menu list
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames