@REQ_ID:1070683

Feature: Library - Concepts - Activities - Activities
    As a user, I want to manage every Activities in the Concepts Library

    Background: User must be logged in
        Given The user is logged in
        And The '/library/activities/activities' page is opened
        And User sets status filter to 'all'

    Scenario: [Navigation] User must be able to navigate to the Activities page
        Given The '/library' page is opened
        When The 'Activities' submenu is clicked in the 'Concepts' section
        Then The current URL is '/library/activities/activities'

    Scenario: [Table][Options] User must be able to see table with correct options
        Then A table is visible with following options
            | options                                                         |
            | Add activity                                                    |
            | Filters                                                         |
            | Columns                                                         |
            | Export                                                          |
            | Show version history                                            |
            | Add select boxes to table to allow selection of rows for export |
            | search-field                                                    |

     Scenario: [Table][Columns][Names] User must be able to see the columns list on the main page as below
        And A table is visible with following headers
            | headers            |
            | Library            |
            | Activity group     |
            | Activity subgroup  |
            | Activity name      |
            | Sentence case name |
            | Synonyms           |     
            | NCI Concept ID     |
            | NCI Concept Name   |
            | Abbreviation       |
            | Data collection    |
            | Legacy usage       |
            | Modified           |
            | Modified by        |
            | Status             |
            | Version            |

    Scenario: [Table][Columns][Visibility] User must be able to select visibility of columns in the table 
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Create][Positive case] User must be able to add a new activity
        When The Add activity button is clicked
        And The activity form is filled with all data
        And Form save button is clicked
        Then Activity is created and confirmation message is shown
        And Activity is searched for and found
        And The newly added activity is added in the table
        And The item has status 'Draft' and version '0.1'

    Scenario: [Create][Mandatory fields] User must not be able to save new activity without mandatory fields of 'Activity group', 'Activity subgroup', 'Activity name'
        When The Add activity button is clicked
        And Form save button is clicked
        Then The user is not able to save the acitivity
        And The validation message appears for activity group
        And The validation message appears for activity name
        When Select a value for Activity group field
        And Form save button is clicked
        Then The validation message appears for activity subgroup

    Scenario: [Create][Uniqueness check][Synonym] User must not be able to save new activity with already existing synonym
        When [API] Activity in status Draft exists
        And The Add activity button is clicked
        And The activity form is filled with only mandatory data
        And The user adds already existing synonym
        And Form save button is clicked
        Then The user is not able to save activity with already existing synonym and error message is displayed

    Scenario: [Create][Mandatory fields] System must ensure value of 'Sentence case name' is mandatory
        When The Add activity button is clicked
        When The user enters a value for Activity name
        And The user clear default value from Sentance case name
        Then The validation message appears for sentance case name

    Scenario: [Create][Mandatory fields] System must default value for 'Data collection' to be checked
        When The Add activity button is clicked
        Then The default value for Data collection must be checked

    Scenario: [Create][Sentence case name validation] System must default value for 'Sentence case name' to lower case value of 'Activity name'
        When The Add activity button is clicked
        And The user enters a value for Activity name
        Then The field for Sentence case name will be defaulted to the lower case value of the Activity name

    Scenario: [Create][Sentence case name validation] System must ensure value of 'Sentence case name' independent of case is identical to the value of 'Activity name'
        When The Add activity button is clicked
        And The user define a value for Sentence case name and it is not identical to the value of Activity name
        And Form save button is clicked
        Then The user is not able to save the acitivity
        And The validation message appears for sentance case name that it is not identical to name

    Scenario: [Actions][New version] User must be able to add a new version for the approved activity
        And [API] Activity in status Draft exists
        And [API] Activity is approved
        And Activity is searched for and found
        When The 'New version' option is clicked from the three dot menu list
        Then The item has status 'Draft' and version '1.1'

    Scenario: [Actions][Edit][version 1.0] User must be able to edit and approve new version of activity
        And [API] Activity in status Draft exists
        And [API] Activity is approved
        And Activity is searched for and found
        When The 'New version' option is clicked from the three dot menu list
        Then The item has status 'Draft' and version '1.1'
        When The 'Edit' option is clicked from the three dot menu list
        And The activity edition form is filled with data
        And Form save button is clicked
        And Activity is searched for and found
        Then The item has status 'Draft' and version '1.2'
        When The 'Approve' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '2.0'

    Scenario: [Actions][Inactivate] User must be able to inactivate the approved version of the activity
        And [API] Activity in status Draft exists
        And [API] Activity is approved
        And Activity is searched for and found
        When The 'Inactivate' option is clicked from the three dot menu list
        Then The item has status 'Retired' and version '1.0' 

    Scenario: [Actions][Reactivate] User must be able to reactivate the inactivated version of the activity
        And [API] Activity in status Draft exists
        And [API] Activity is approved
        And [API] Activity is inactivated
        And Activity is searched for and found
        When The 'Reactivate' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '1.0' 

    Scenario: [Actions][Edit][version 0.1] User must be able to edit the Drafted version of the activity
        And [API] Activity in status Draft exists
        And Activity is searched for and found
        When The 'Edit' option is clicked from the three dot menu list
        And The activity edition form is filled with data
        And Form save button is clicked
        And Activity is searched for and found
        Then The item has status 'Draft' and version '0.2'

    Scenario: [Actions][Approve] User must be able to Approve the drafted version of the activity
        And [API] Activity in status Draft exists
        And Activity is searched for and found
        When The 'Approve' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '1.0'

    Scenario: [Actions][Delete] User must be able to Delete the intial created version of the activity
        And [API] Activity in status Draft exists
        And Activity is searched for and found
        When The 'Delete' option is clicked from the three dot menu list
        Then Activity is searched for and not found

    Scenario: [Create][Negative case][Draft group] User must not be able to create activity linked to Drafted group until it is approved
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And [API] Activity subgroup is created
        And [API] Activity subgroup is approved
        And [API] Activity group gets new version
        And Group name created through API is found
        And User waits for 2 seconds
        Given The '/library/activities/activities' page is opened
        And User sets status filter to 'all'
        When The Add activity button is clicked
        When The activity form is filled in using group and subgroup created through API
        And Form save button is clicked
        Then Validation error for GroupingHierarchy is displayed
        And [API] Activity group is approved
        And Form save button is clicked
        And Activity is searched for and found

    Scenario: [Create][Negative case][Retired group] User must not be able to create activity linked to Retired group until it is approved
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And [API] Activity subgroup is created
        And [API] Activity subgroup is approved
        And [API] Activity group is inactivated
        And Group name created through API is found
        And User waits for 2 seconds
        Given The '/library/activities/activities' page is opened
        And User sets status filter to 'all'
        When The Add activity button is clicked
        When The activity form is filled in using group and subgroup created through API
        And Form save button is clicked
        Then Validation error for GroupingHierarchy is displayed
        And [API] Activity group is reactivated
        And Form save button is clicked
        And Activity is searched for and found

    Scenario: [Create][Negative case][Draft subgroup] User must not be able to create activity linked to Draft subgroup until it is approved
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And [API] Activity subgroup is created
        And Group name created through API is found
        And User waits for 2 seconds
        Given The '/library/activities/activities' page is opened
        And User sets status filter to 'all'
        When The Add activity button is clicked
        And Custom group name is typed and selected in activity form
        And Drafted subgroup is not available during activity creation
        And Overlay cancel button is clicked
        And [API] Activity subgroup is approved
        Given The '/library/activities/activities' page is opened
        And User sets status filter to 'all'
        When The Add activity button is clicked
        And The activity form is filled in using group and subgroup created through API
        And Form save button is clicked
        And Activity is searched for and found

    Scenario: [Create][Negative case][Retired subgroup] User must not be able to create activity linked to Retired subgroup until it is approved
        And [API] Activity group in status Draft exists
        And [API] Activity group is approved
        And [API] Activity subgroup is created
        And [API] Activity subgroup is approved
        And [API] Activity subgroup is inactivated
        And Group name created through API is found
        And User waits for 2 seconds
        Given The '/library/activities/activities' page is opened
        And User sets status filter to 'all'
        When The Add activity button is clicked
        When The activity form is filled in using group and subgroup created through API
        And Form save button is clicked
        Then Validation error for GroupingHierarchy is displayed
        And [API] Activity subgroup is reactivated
        And Form save button is clicked
        And Activity is searched for and found

    Scenario: [Cancel][Creation] User must be able to Cancel creation of the activity
        When The Add activity button is clicked
        And The activity form is filled with only mandatory data
        When Modal window form is closed by clicking cancel button
        And Action is confirmed by clicking continue
        Then The form is no longer available
        And Activity is searched for and not found

    Scenario: [Cancel][Edition] User must be able to Cancel edition of the activity
        And [API] Activity in status Draft exists
        And Activity is searched for and found
        When The 'Edit' option is clicked from the three dot menu list
        When The activity edition form is filled with data
        And Modal window form is closed by clicking cancel button
        And Action is confirmed by clicking continue
        Then The form is no longer available
        And Activity is searched for and not found

    Scenario: [Actions][Availability][Draft item] User must only have access to aprove, edit, delete, history actions for Drafted version of the activity
        When [API] Activity in status Draft exists
        And Activity is searched for and found
        And The item actions button is clicked
        Then Only actions that should be avaiable for the Draft item are displayed

    Scenario: [Actions][Availability][Final item] User must only have access to new version, inactivate, history actions for Final version of the activity
        When [API] Activity in status Draft exists
        And [API] Activity is approved
        And Activity is searched for and found
        And The item actions button is clicked
        Then Only actions that should be avaiable for the Final item are displayed

    Scenario: [Actions][Availability][Retired item] User must only have access to reactivate, history actions for Retired version of the activity
        When [API] Activity in status Draft exists
        And [API] Activity is approved
        And [API] Activity is inactivated
        And Activity is searched for and found
        And The item actions button is clicked
        Then Only actions that should be avaiable for the Retired item are displayed

    Scenario: [Table][Search][Postive case] User must be able to search created activity
        When [API] First activity for search test is created
        And [API] Second activity for search test is created
        Then Activity is searched for and found
        And The existing item is searched for by partial name
        Then More than one result is found 

    Scenario: [Table][Search][Negative case] User must be able to search not existing activity and table will correctly filtered
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
        When [API] Activity in status Draft exists
        And The '/library/activities/activities' page is opened
        And Activity is searched for and not found
        And [API] Activity is approved
        And The '/library/activities/activities' page is opened
        And Activity is searched for and found

    Scenario: [Table][Filtering][Status selection] User must be able to use status selection to find or hide draft activity
        When [API] Activity in status Draft exists
        When User sets status filter to 'final'
        And Activity is searched for and not found
        When User sets status filter to 'draft'
        And Activity is searched for and found
        When User sets status filter to 'retired'
        And Activity is searched for and not found
        When User sets status filter to 'all'
        And Activity is searched for and found

    Scenario: [Table][Filtering][Status selection] User must be able to use status selection to find or hide approved activity
        When [API] Activity in status Draft exists
        And [API] Activity is approved
        When User sets status filter to 'draft'
        And Activity is searched for and not found
        When User sets status filter to 'final'
        And Activity is searched for and found
        When User sets status filter to 'retired'
        And Activity is searched for and not found
        When User sets status filter to 'all'
        And Activity is searched for and found

    Scenario: [Table][Filtering][Status selection] User must be able to use status selection to find or hide retired activity
        When [API] Activity in status Draft exists
        And [API] Activity is approved
        And [API] Activity is inactivated
        When User sets status filter to 'draft'
        And Activity is searched for and not found
        When User sets status filter to 'retired'
        And Activity is searched for and found
        When User sets status filter to 'final'
        And Activity is searched for and not found
        When User sets status filter to 'all'
        And Activity is searched for and found
    
    Scenario: [Table][Filtering][Status selection] User must be able to use status selection to find or hide new version of activity
        When [API] Activity in status Draft exists
        And [API] Activity is approved
        And [API] Activity new version is created
        When User sets status filter to 'final'
        And Activity is searched for and not found
        When User sets status filter to 'draft'
        And Activity is searched for and found
        When User sets status filter to 'retired'
        And Activity is searched for and not found
        When User sets status filter to 'all'
        And Activity is searched for and found

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
        | Library            |
        | Activity group     |
        | Activity subgroup  |
        | Activity name      |
        | Sentence case name |
        | Synonyms           |
        | NCI Concept ID     |
        | NCI Concept Name   |
        | Abbreviation       |
        | Data collection    |
        | Legacy usage       |
        | Modified by        |
        | Version            |

    Scenario: [Table][Pagination] User must be able to use table pagination
        When The user switches pages of the table
        Then The table page presents correct data
