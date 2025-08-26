@REQ_ID:1074254
Feature: Studies - Define Study - Study Structure - Study Cohorts

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study cohorts.

    Background: User is logged in
        Given The user is logged in

    Scenario: [Navigation] User must be able to navigate to Study Cohorts page using side menu
        Given A test study is selected
        And The '/studies' page is opened
        When The 'Study Structure' submenu is clicked in the 'Define Study' section
        And The 'Study Cohorts' tab is selected
        Then The current URL is '/study_structure/cohorts'

    Scenario: [Table][Options] User must be able to see the Study Cohorts table with following options
        Given A test study is selected
        And The test study '/study_structure/cohorts' page is opened
        Then A table is visible with following options
            | options                                                         |
            | Add Study Cohort                                                |
            | Columns                                                         |
            | Add select boxes to table to allow selection of rows for export |
    
    Scenario: [Table][Columns][Names] User must be able to see the Study Cohorts table with following columns
        Given A test study is selected
        And The test study '/study_structure/cohorts' page is opened
        And A table is visible with following headers
            | headers            |
            | #                  |
            | Arm name           |
            | Branch Arm name    |
            | Cohort Name        |
            | Cohort Short Name  |
            | Cohort Code        |
            | Number of subjects |
            | Description        |
            | Colour             |
            | Modified           |
            | Modified by        |

    Scenario: [Online help] User must be able to read online help for the page
        Given The test study '/study_structure/cohorts' page is opened
        And The online help button is clicked
        Then The online help panel shows 'Study Cohorts' panel with content "A group of individuals who share a common exposure, experience or characteristic or a group of individuals followed-up or traced over time in a cohort study. Example could be first human dose-escalation studies where increasing doses are given until stopping criteria are met. Some dose-escalation studies enroll a new cohort of subjects (a new group of subjects) for each new dose. Cohorts are also used for observational studies where no randomisation takes place or single arm randomised study. Then cohorts are being defined based on some characteristics and comparisons are made between the different cohorts, e.g. treatment of a drug in subjects with a liver disease compared to a group of healthy subjects. Cohorts are not the same as strata. Stratification is the process of dividing members of the population into homogeneous subgroups before sampling/randomisation. If the study with liver diseased and healthy subjects had to examine the effect of a drug compared to placebo then liver diseased/healthy would be a stratification factor, since it is expected that the treatment responses will be different in the two groups. Stratification is made to ensure homogeneity of the groups in which the treatments are being compared."

    Scenario: [Table][Columns][Visibility] User must be able to use column selection option
        Given The test study '/study_structure/cohorts' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column
    
    Scenario: [Create][Positive case] User must be able to create a new study cohort
        Given A study with Study Arms has been selected
        And The test study '/study_structure/cohorts' page is opened
        When The form for new study cohort is filled and saved
        Then The study cohort is visible within the table

    Scenario: [Actions][Edit] User must be able to edit the Study Cohort
        Given A study with Study Arms has been selected
        And The test study '/study_structure/cohorts' page is opened
        When The Study Cohort is found
        And The 'Edit' option is clicked from the three dot menu list
        When The study cohort is edited
        And The Study Cohort is found
        Then The study cohort with updated values is visible within the table

    Scenario: [Actions][Edit] User must be able to edit the Arm and Branch Arm while editing the Study Cohort
        # Given A study with Study Arms has been selected
        Given A test study is selected
        And The test study '/study_structure/cohorts' page is opened
        When The 'Edit' option is clicked from the three dot menu list
        Then The fields of Arm and Branch arms in the cohort edit form are active for editing

    Scenario Outline: [Create][Fields check] User must not be able to provide value other than positive integer for Number of subjects
        Given A study with Study Arms has been selected
        And The test study '/study_structure/cohorts' page is opened
        When The value '<number>' is entered for the field Number of subjects in the Study Cohorts form
        Then The validation appears under the field in the Study Cohorts form

        Examples:
            | number |
            | -123   |
            | -1     |
            | 0      |

    Scenario: [Create][Fields check] User must not be able to provide a value for number of subjects higher than the number defined for the study arm
        Given A study with Study Arms has been selected
        And The test study '/study_structure/cohorts' page is opened
        When The value entered for the field Number of subjects is higher than the value defined for the selected study arm in the Study Cohorts form
        Then The message 'Number of subjects in a cohort cannot exceed total number of subject in the study' is displayed

    Scenario: [Create][Mandatory fields] User must not be able to create a Study Cohort without providing necessary data as in this scenario
        Given A study with Study Arms has been selected
        And The test study '/study_structure/cohorts' page is opened
        When The form for new study cohort is filled
        And The Cohort name field is not populated
        And The Cohort short name field is not populated
        And The Cohort code field is not populated
        And The 'save-button' button is clicked
        Then The form is not closed

    Scenario: [Create][Uniqueness check][Name] User must not be able to create two Cohorts within one study using the same Cohort name
        Given A study with Study Arms has been selected
        And The test study '/study_structure/cohorts' page is opened
        When The Study Cohort is created with given cohort name
        And Another Study Cohort is created with the same cohort name
        Then The system displays the message "Value 'Cohort Test Name' in field Cohort Name is not unique for the study"
        And The form is not closed

    Scenario: [Create][Uniqueness check][Short Name] User must not be able to create two Cohorts within one study using the same Cohort short name
        Given A study with Study Arms has been selected
        And The test study '/study_structure/cohorts' page is opened
        When The Study Cohort is created with given cohort short name
        And Another Study Cohort is created with the same cohort short name
        Then The system displays the message "Value 'CH Test Short Name' in field Cohort Short Name is not unique for the study"
        And The form is not closed

    Scenario: [Create][Uniqueness check][Cohort code] User must not be able to create two Cohorts within one study using the same Cohort code
        Given A study with Study Arms has been selected
        And The test study '/study_structure/cohorts' page is opened
        When The Study Cohort is created with given cohort code
        And Another Study Cohort is created with the same cohort code
        Then The system displays the message "Value '88' in field Cohort code is not unique for the study"
        And The form is not closed

    Scenario: [Create][Mandatory fields] Outline: User must not be able to use text longer than specified in this scenario for Study Cohorts form
        Given A study with Study Arms has been selected
        And The test study '/study_structure/cohorts' page is opened
        When For the '<field>' a text longer than '<length>' is provided in the Study Cohorts form
        Then The message "This field must not exceed <length> characters" is displayed

        Examples:
            | field                   | length |
            | study-cohort-name       | 200    |
            | study-cohort-short-name | 20     |

    Scenario: [Create][Mandatory fields] User must not be able to create a Cohort with code less than 1
        Given A study with Study Arms has been selected
        And The test study '/study_structure/cohorts' page is opened
        When For the 'study-cohort-code' a '0' value is provided in Study Cohort form
        Then The message "Value can't be less than 1" is displayed

    Scenario: [Create][Mandatory fields] User must not be able to create a Cohort with code bigger than 99
        Given A study with Study Arms has been selected
        And The test study '/study_structure/cohorts' page is opened
        When For the 'study-cohort-code' a '100' value is provided in Study Cohort form
        Then The message "Value must be less than 99" is displayed

    Scenario: [Export][CSV] User must be able to export the data in CSV format
        Given The test study '/study_structure/cohorts' page is opened
        And The user exports the data in 'CSV' format
        Then The study specific 'StudyCohorts' file is downloaded in 'csv' format

    Scenario: [Export][Json] User must be able to export the data in JSON format
        Given The test study '/study_structure/cohorts' page is opened
        And The user exports the data in 'JSON' format
        Then The study specific 'StudyCohorts' file is downloaded in 'json' format

    Scenario: [Export][Xml] User must be able to export the data in XML format
        Given The test study '/study_structure/cohorts' page is opened
        And The user exports the data in 'XML' format
        Then The study specific 'StudyCohorts' file is downloaded in 'xml' format

    Scenario: [Export][Excel] User must be able to export the data in EXCEL format
        Given The test study '/study_structure/cohorts' page is opened
        And The user exports the data in 'EXCEL' format
        Then The study specific 'StudyCohorts' file is downloaded in 'xlsx' format

    @manual_test
    Scenario: User must be able to remove the Study Cohort
        Given The test study '/study_structure/cohorts' page is opened
        And The test Study Cohort is available
        When The delete action is clicked for the test Study Cohort
        Then The test Study Cohort is no longer available
        And related Study Design Cell selections are cascade deleted

    @manual_test
    Scenario: User must be able to read change history of output
        Given The test study '/study_structure/cohorts' page is opened
        When The user opens version history
        Then The user is presented with version history of the output containing timestamp and username

    @manual_test
    Scenario: User must be able to read change history of selected element
        Given The test study '/study_structure/cohorts' page is opened
        And The 'Show history' option is clicked from the three dot menu list
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames