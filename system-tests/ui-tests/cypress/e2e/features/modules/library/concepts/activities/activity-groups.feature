@REQ_ID:1070683

Feature: Library - Concepts - Activities - Activity Groups
    As a user, I want to manage every Activity Groups in the Concepts Library
    
    Background: User must be logged in
        Given The user is logged in
        And The '/library/activities/activity-groups' page is opened
        And User sets status filter to 'all'

    Scenario: [Navigation] User must be able to navigate to the Activity Groups page
        Given The '/library' page is opened
        When The 'Activities' submenu is clicked in the 'Concepts' section
        And The 'Activity Groups' tab is selected
        Then The current URL is '/library/activities/activity-groups'

    Scenario: [Table][Options] User must be able to see table with correct options
        Then A table is visible with following options
            | options                                                         |
            | Add activity group                                              |
            | Filters                                                         |
            | Columns                                                         |
            | Export                                                          |
            | Show version history                                            |
            | Add select boxes to table to allow selection of rows for export |
            | search-field                                                    |

    Scenario: [Table][Columns][Names] User must be able to see the columns list on the main page as below
        Then A table is visible with following headers
            | headers            |
            | Activity group     |
            | Sentence case name |
            | Abbreviation       |
            | Definition         |
            | Modified           |
            | Status             |
            | Version            |

    Scenario: [Table][Columns][Visibility] User must be able to select visibility of columns in the table 
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Create][Positive case] User must be able to add a new activity group
        When The add activity group button is clicked
        And The test activity group container is filled with data
        And Activity group is saved and snackbar message says it is 'created'
        And Activity group is searched for and found
        And The newly added activity group is visible in the the table
        And The item has status 'Draft' and version '0.1'

    Scenario: [Create][Mandatory fields] User must not be able to save new activity group without filling mandatory fields of 'Group name', 'Sentence case name' and 'Definition'
        When The add activity group button is clicked
        And The Group name and Sentence case name and Definition fields are not filled with data
        And Form save button is clicked
        Then The user is not able to save the acitivity group
        And The message is displayed as 'This field is required' in the mandatory fields

    Scenario: [Create][Sentence case name validation] System must default value for 'Sentence case name' to lower case value of 'Activity group name'
        When The add activity group button is clicked
        And The user enters a value for Activity group name
        Then The field for Sentence case name will be defaulted to the lower case value of the Activity group name

    Scenario: [Create][Sentence case name validation] System must ensure value of 'Sentence case name' independent of case is identical to the value of 'Activity group name'
        When The add activity group button is clicked
        And The user define a value for Sentence case name and it is not identical to the value of Activity group name
        And Form save button is clicked
        Then The user is not able to save the acitivity group
        And The validation message appears for sentance case name that it is not identical to name

    Scenario: [Actions][New version] User must be able to add a new version for the approved activity group
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And Activity group is searched for and found
        When The 'New version' option is clicked from the three dot menu list
        Then The item has status 'Draft' and version '1.1'

    Scenario: [Actions][Edit][version 1.0] User must be able to edit and approve new version of activity group
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And Activity group is searched for and found
        When The 'New version' option is clicked from the three dot menu list
        Then The item has status 'Draft' and version '1.1'
        When The 'Edit' option is clicked from the three dot menu list
        And The activity group is edited
        And Activity group is saved and snackbar message says it is 'updated'
        And Activity group is searched for and found
        Then The item has status 'Draft' and version '1.2'
        When The 'Approve' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '2.0'

    Scenario: [Actions][Inactivate] User must be able to inactivate the approved version of the activity group
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And Activity group is searched for and found
        When The 'Inactivate' option is clicked from the three dot menu list
        Then The item has status 'Retired' and version '1.0'

    Scenario: [Actions][Reactivate] User must be able to reactivate the inactivated version of the activity group
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And [API] Activity group is inactivated
        And Activity group is searched for and found
        When The 'Reactivate' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '1.0'

    Scenario: [Actions][Edit][version 0.1] User must be able to edit the drafted version of the activity group
        And [API] Activity group in status Draft exists
        And Activity group is searched for and found
        When The 'Edit' option is clicked from the three dot menu list
        And The activity group is edited
        And Activity group is saved and snackbar message says it is 'updated'
        And Activity group is searched for and found
        Then The item has status 'Draft' and version '0.2'
        
    Scenario: [Actions][Approve] User must be able to approve the drafted version of the activity group
        And [API] Activity group in status Draft exists
        And Activity group is searched for and found
        When The 'Approve' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '1.0'

    Scenario: [Actions][Delete] User must be able to Delete the intial created version of the activity group
        And [API] Activity group in status Draft exists
        And Activity group is searched for and found
        When The 'Delete' option is clicked from the three dot menu list
        Then Activity group is searched for and not found

    Scenario: [Cancel][Creation] User must be able to Cancel creation of the activity group
        When The add activity group button is clicked
        And The test activity group container is filled with data
        When Modal window form is closed by clicking cancel button
        Then The form is no longer available
        And Activity group is searched for and not found

    Scenario: [Cancel][Edition] User must be able to Cancel edition of the activity group
        And [API] Activity group in status Draft exists
        And Activity group is searched for and found
        When The 'Edit' option is clicked from the three dot menu list
        When The activity group edition form is filled with data
        And Modal window form is closed by clicking cancel button
        Then The form is no longer available
        And Activity group is searched for and not found

    Scenario: [Actions][Availability][Draft item] User must only have access to aprove, edit, delete, history actions for Drafted version of the activity group
        And [API] Activity group in status Draft exists
        And Activity group is searched for and found
        Then The item actions button is clicked
        Then Only actions that should be avaiable for the Draft item are displayed

    Scenario: [Actions][Availability][Final item] User must only have access to new version, inactivate, history actions for Final version of the activity group
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And Activity group is searched for and found
        Then The item actions button is clicked
        Then Only actions that should be avaiable for the Final item are displayed

    Scenario: [Actions][Availability][Retired item] User must only have access to reactivate, history actions for Retired version of the activity group
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And [API] Activity group is inactivated
        And Activity group is searched for and found
        Then The item actions button is clicked
        Then Only actions that should be avaiable for the Retired item are displayed

    Scenario: [Table][Search][Postive case] User must be able to search created group
        When [API] First activity group for search test is created
        And [API] Second activity group for search test is created
        Then Activity group is searched for and found
        And The existing item is searched for by partial name
        Then More than one result is found 

    Scenario: [Table][Search][Negative case] User must be able to search not existing group and table will correctly filtered
        When The not existing item is searched for
        Then The item is not found and table is correctly filtered

    Scenario: [Table][Search][Filtering] User must be able to combine search and filters to narrow table results
        When User sets status filter to 'final'
        And The existing item is searched for by partial name
        And The item is not found and table is correctly filtered
        And User sets status filter to 'draft'
        And The existing item is searched for by partial name
        Then More than one result is found

    Scenario: [Table][Filtering][Status selection] User must be able to see that Final status is selected by default
        And [API] Activity group in status Draft exists
        And The '/library/activities/activity-groups' page is opened
        And Activity group is searched for and not found
        And [API] Activity group is approved
        And The '/library/activities/activity-groups' page is opened
        And Activity group is searched for and found

    Scenario: [Table][Filtering][Status selection] User must be able to use status selection to find or hide draft activity group
        And [API] Activity group in status Draft exists
        When User sets status filter to 'final'
        And Activity group is searched for and not found
        When User sets status filter to 'draft'
        And Activity group is searched for and found
        When User sets status filter to 'retired'
        And Activity group is searched for and not found
        When User sets status filter to 'all'
        And Activity group is searched for and found

    Scenario: [Table][Filtering][Status selection] User must be able to use status selection to find or hide approved activity group
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        When User sets status filter to 'draft'
        And Activity group is searched for and not found
        When User sets status filter to 'final'
        And Activity group is searched for and found
        When User sets status filter to 'retired'
        And Activity group is searched for and not found
        When User sets status filter to 'all'
        And Activity group is searched for and found

    Scenario: [Table][Filtering][Status selection] User must be able to use status selection to find or hide retired activity group
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And [API] Activity group is inactivated
        When User sets status filter to 'draft'
        And Activity group is searched for and not found
        When User sets status filter to 'retired'
        And Activity group is searched for and found
        When User sets status filter to 'final'
        And Activity group is searched for and not found
        When User sets status filter to 'all'
        And Activity group is searched for and found
    
    Scenario: [Table][Filtering][Status selection] User must be able to use status selection to find or hide new version of activity group
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And [API] Activity group gets new version
        When User sets status filter to 'final'
        And Activity group is searched for and not found
        When User sets status filter to 'draft'
        And Activity group is searched for and found
        When User sets status filter to 'retired'
        And Activity group is searched for and not found
        When User sets status filter to 'all'
        And Activity group is searched for and found

    Scenario: [Table][Filtering][Status selection] User must be able to see that status filter is not available after expanding column based filters
        Then The status filter is not available when expanding available filters

    Scenario: [Table][Search][Case sensitivity] User must be able to search item ignoring case sensitivity
        When The existing item in search by lowercased name
        And More than one result is found

    Scenario Outline: [Table][Filtering] User must be able to filter the table by text fields
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
        | name               |
        | Activity group     |
        | Sentence case name |
        | Abbreviation       |
        | Definition         |
        | Version            |