@REQ_ID:1070683
Feature: Library - Concepts - CRFs - Item Groups

    As a user, I want to manage every CRF Item Group in the Library

    Background: User is logged in the system
        Given The user is logged in

    Scenario: [Navigation] User must be able to navigate to the Items Group page
        Given The '/library' page is opened
        When The 'CRFs' submenu is clicked in the 'Concepts' section
        And The 'Item Groups' tab is selected
        Then The current URL is '/library/crfs/item-groups'

    Scenario: [Table][Columns][Names] User must be able to see the data of the CRF Item Group tab
        Given The 'library/crfs/item-groups' page is opened
        Then A table is visible with following headers
            | headers              |
            | OID                  |
            | Name                 |
            | Description          |
            | Implementation Notes |
            | Repeating            |
            | Links                |
            | Version              |
            | Status               |
            
    Scenario: [Table][Columns][Visibility] User must be able to select visibility of columns in the table 
        Given The '/library/crfs/item-groups' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Create][Positive case] User must be able to add an Item Group
        Given The single language CRFs are enabled
        And The 'library/crfs/item-groups' page is opened
        When The 'add-crf-item-group' button is clicked
        And The CRF Item Group definition container is filled with data and saved
        Then The pop up displays 'Item Group created'
        And Created CRF Item Group is found

    #Done after study design merges - commands for the validations included there
    # Scenario: User must not be able to create CRF Item Group without Name provided
    #     Given The 'library/crfs/item-groups' page is opened
    #     And The CRF Item Group definition is filled without name provided and the next button is clicked
    #     Then The validation appears for the 'crf-form-name' field

    Scenario: [Actions][Edit][version 0.1] User must be able to update an existing a Item Group
        Given The single language CRFs are enabled
        And The 'library/crfs/item-groups' page is opened
        And Created CRF Item Group is found
        When The 'Edit' option is clicked from the three dot menu list
        And The CRF Item Group metadata are updated and saved
        #Then The pop up displays 'Item Group updated'
        And Created CRF Item Group is found

    Scenario: [Actions][Approve] User must be able to approve an Item Group in draft status
        Given The 'library/crfs/item-groups' page is opened
        And Created CRF Item Group is found
        When The 'Approve' option is clicked from the three dot menu list
        #Then The pop up displays 'Item Group approved'
        And The item has status 'Final' and version '1.0'

    Scenario: [Actions][Inactivate] User must be able to inactivate currently active Item Group
        Given The 'library/crfs/item-groups' page is opened
        And Created CRF Item Group is found
        When The 'Inactivate' option is clicked from the three dot menu list
        #Then The pop up displays 'Item Group inactivated'
        And The item has status 'Retired' and version '1.0'

    Scenario: [Actions][Reactivate] User must be able to reactivate currently retired Item Group
        Given The 'library/crfs/item-groups' page is opened
        And Created CRF Item Group is found
        When The 'Reactivate' option is clicked from the three dot menu list
        #Then The pop up displays 'Item Group reactivated'
        And The item has status 'Final' and version '1.0'

    Scenario: [Actions][New version] User must be able to create a new version of an Item Group
        Given The 'library/crfs/item-groups' page is opened
        And Created CRF Item Group is found
        When The 'New version' option is clicked from the three dot menu list
        #Then The pop up displays 'New version created'
        And The item has status 'Draft' and version '1.1'

    Scenario: [Actions][Delete] User must be able to delete CRF Item Group in draft status
        Given The 'library/crfs/item-groups' page is opened
        When The 'add-crf-item-group' button is clicked
        And The CRF Item Group definition container is filled with data and saved
        And Created CRF Item Group is found
        When The 'Delete' option is clicked from the three dot menu list
        Then The CRF Item Group is no longer available

    @manual_test    
    Scenario: User must be able to read change history of selected element
        Given The 'library/crfs/item-groups' page is opened
        And The 'Show history' option is clicked from the three dot menu list
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames