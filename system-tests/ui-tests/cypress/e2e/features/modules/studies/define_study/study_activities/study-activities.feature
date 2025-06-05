@REQ_ID:1074260
Feature: Studies - Define Study - Study Activities - Study Activities

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study activities.

    Background: User is logged in and study has been selected
        Given The user is logged in

    Scenario: [Navigation] User must be able to navigate to Study Activity page using side menu
        Given A test study is selected
        And The '/studies' page is opened
        When The 'Study Activities' submenu is clicked in the 'Define Study' section
        Then The current URL is '/studies/Study_000001/activities/soa'

    Scenario: [Table][Columns][Names] User must be able to see the Study Activities table with options listed in this scenario
        Given The '/studies/Study_000001/activities/list' page is opened
        Then A table is visible with following headers
            | headers           |
            #| #                 |
            | Library           |
            | SoA group         |
            | Activity group    |
            | Activity subgroup |
            | Activity          |
            | Data collection   |
            | Modified          |
            | Modified by       |

    Scenario: [Table][Columns][Visibility] User must be able to use column selection option
        Given The '/studies/Study_000001/activities/list' page is opened
        And Study activities for Study_000001 are loaded
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Create][Existing Study][By Id] User must be able to create a Study Activity from an existing study by study id
        And The '/studies/Study_000001/activities/list' page is opened
        When The Study Activity is added from an existing study by study id
        And The new Study Activity added from Library is visible in table
        Then The Study Activity copied from existing study is visible within the Study Activities table

    Scenario: [Actions][Delete][Activity] User must be able to delete a Study Activity
        Given The '/studies/Study_000001/activities/list' page is opened
        And [API] Study Activity is created and approved
        And User adds newly created activity with status Final
        And Study Activity is found
        When The 'Remove Activity' option is clicked from the three dot menu list
        And Action is confirmed by clicking continue
        Then The activity is no longer available

    Scenario: [Create][Existing Study][By Acronym] User must be able to create a Study Activity from an existing study by study acronym
        And The '/studies/Study_000001/activities/list' page is opened
        When The Study Activity is added from an existing study by study acronym
        And The new Study Activity added from Library is visible in table
        Then The Study Activity copied from existing study is visible within the Study Activities table

    Scenario: [Create][From Library] User must be able to create a Study Activity from the library
        And The activity exists in the library
        And The '/studies/Study_000001/activities/list' page is opened
        When The Study Activity is added from the library
        Then The Study Activity created from library is visible within the Study Activities table

    Scenario: [Create][Placeholder] User must be able to create a Study Activity placeholder as an activity concept request
        And The '/studies/Study_000001/activities/list' page is opened
        When The Study Activity is added as a placeholder for new activity request
        And Activity placeholder is found
        Then The Study Activity placeholder is visible within the Study Activities table

    Scenario: [Actions][Delete][Placeholder] User must be able to delete a Study Activity placeholder
        Given The '/studies/Study_000001/activities/list' page is opened
        And Activity placeholder is found
        When The 'Remove Activity' option is clicked from the three dot menu list
        And Action is confirmed by clicking continue
        Then The Study Activity Placeholder is no longer available

    Scenario: [Actions][Edit][version 0.1][Activity] User must be able to edit a Study Activity
        Given The '/studies/Study_000001/activities/list' page is opened
        And [API] Study Activity is created and approved
        And User adds newly created activity with status Final
        And Study Activity is found
        When The 'Edit' option is clicked from the three dot menu list
        And The SoA group can be changed
        Then The edited Study Activity data is reflected within the Study Activity table

    # Note, currently only the SoA group can be changed, not the request, will be specified and updated in later release
    Scenario: [Actions][Edit][version 0.1][Placeholder] User must be able to edit a Study Activity placeholder
        Given The '/studies/Study_000001/activities/list' page is opened
        When The Study Activity is added as a placeholder for new activity request
        And Activity placeholder is found
        When The 'Edit' option is clicked from the three dot menu list
        And The SoA group can be changed
        Then The edited Study Activity data is reflected within the Study Activity table

    Scenario: [Create][Mandatory fields][Activity] User must not be able to create Study Activity from studies without study selected
        Given The '/studies/Study_000001/activities/list' page is opened
        When The Study Activity select from study form is opened on second step
        And The user tries to go to Activity Selection without study chosen
        Then The validation appears and Create Activity form stays on Study Selection

    Scenario: [Create][Mandatory fields][Activity] User must not be able to create Study Activity from library without SoA group selected
        Given The '/studies/Study_000001/activities/list' page is opened
        When The Study Activity select from library form is opened on second step
        And The user tries to go further without SoA group chosen
        Then The validation appears and Create Activity form stays on SoA group selection

    Scenario: [Create][Mandatory fields][Placeholder] User must not be able to create Study Activity placeholder without SoA group selected
        Given The '/studies/Study_000001/activities/list' page is opened
        When The Study Activity create placeholder form is opened on second step
        And The user tries to go further in activity placeholder creation without SoA group chosen
        Then The validation appears under empty SoA group selection

    Scenario: [Actions][Approve] User must be able to add newly created approved Activity
        Given The '/studies/Study_000001/activities/list' page is opened
        And [API] Study Activity is created and approved
        When User adds newly created activity with status Final
        Then The new Study Activity added from Library is visible in table

    Scenario: [Create][Negative case][Draft Activity] User must mot be able to add newly created draft Activity
        Given The '/studies/Study_000001/activities/list' page is opened
        And [API] Study Activity is created and not approved
        When User tries to add Activity in Draft status
        Then The Activity in Draft status is not found

    Scenario: [Create][Negative case][Draft Group] User must not be able to add activity that has Draft group until it is approved
        Given The '/studies/Study_000001/activities/list' page is opened
        And [API] Study Activity is created and group is drafted
        When User initiate adding Study Activity from Library
        Then Warning that 'Draft' 'groups' can not be added to the study is displayed
        And [API] Activity group is approved
        When User adds newly created activity with status Final
        Then The new Study Activity added from Library is visible in table
        
    Scenario: [Create][Negative case][Retired Group]  User must not be able to add activity that has Retired group until it is approved
        Given The '/studies/Study_000001/activities/list' page is opened
        And [API] Study Activity is created and group is inactivated
        When User initiate adding Study Activity from Library
        Then Warning that 'Retired' 'groups' can not be added to the study is displayed
        And [API] Activity group is reactivated
        When User adds newly created activity with status Final
        Then The new Study Activity added from Library is visible in table
        
    Scenario: [Create][Negative case][Draft Subgroup] User must not be able to add activity that has Draft subgroup until it is approved
        Given The '/studies/Study_000001/activities/list' page is opened
        And [API] Study Activity is created and subgroup is drafted
        When User initiate adding Study Activity from Library
        Then Warning that 'Draft' 'subgroups' can not be added to the study is displayed
        And [API] Activity subgroup is approved
        When User adds newly created activity with status Final
        Then The new Study Activity added from Library is visible in table
        
    Scenario: [Create][Negative case][Retired Subgroup] User must not be able to add activity that has Retired subgroup until it is approved
        Given The '/studies/Study_000001/activities/list' page is opened
        And [API] Study Activity is created and subgroup is inactivated
        When User initiate adding Study Activity from Library
        Then Warning that 'Retired' 'subgroups' can not be added to the study is displayed
        And [API] Activity subgroup is reactivated
        When User adds newly created activity with status Final
        Then The new Study Activity added from Library is visible in table

    Scenario: [Export][CSV] User must be able to export the data in CSV format
        Given The '/studies/Study_000001/activities/list' page is opened
        And The user exports the data in 'CSV' format
        Then The study specific 'StudyActivities' file is downloaded in 'csv' format

    Scenario: [Export][Json] User must be able to export the data in JSON format
        Given The '/studies/Study_000001/activities/list' page is opened
        And The user exports the data in 'JSON' format
        Then The study specific 'StudyActivities' file is downloaded in 'json' format

    Scenario: [Export][Xml] User must be able to export the data in XML format
        Given The '/studies/Study_000001/activities/list' page is opened
        And The user exports the data in 'XML' format
        Then The study specific 'StudyActivities' file is downloaded in 'xml' format

    Scenario: [Export][Excel] User must be able to export the data in EXCEL format
        Given The '/studies/Study_000001/activities/list' page is opened
        And The user exports the data in 'EXCEL' format
        Then The study specific 'StudyActivities' file is downloaded in 'xlsx' format