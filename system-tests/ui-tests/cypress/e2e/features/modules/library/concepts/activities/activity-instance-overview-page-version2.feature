@REQ_ID:1070683

Feature: Library - Concepts - Activities - Activity Instance Overview Page (Version 2)
    As a user, I want to verify that the Activity Instance Overview Page version 2 in the Concepts Library, can display correctly.

    Background: 
        Given The user is logged in
        When [API] Activity Instance in status Final with Final group, subgroup and activity linked exists
        And Group, subgroup, activity and instance names created through API are found
        Given The '/library/activities/activity-instances' page is opened
        When User waits for the table
        
    Scenario: Verify that the activities instance overview page version 2 displays correctly
        When Activity instance created via API is searched for and found
        And User goes to instance overview page by clicking its name
        Then Instance overview page is opened
        And User waits for linked 'Activity groupings' table data to load
        And The 'Activity groupings' table is displaying correct columns
        |  header                  |
        |  Activity group          |
        |  Activity subgroup       |
        |  Activity                |
        And User waits for linked 'Activity Items' table data to load
        And The 'Activity Items' table is displaying correct columns
        |  header                  |
        |  Data type               |
        |  Name                    |
        |  Activity Item Class     |
        And The Instance linked group, subgroup and instance are displayed in the Activity groupings table
        And The free text search field should be displayed in the 'Activity groupings' table
        And The free text search field should be displayed in the 'Activity Items' table

    Scenario: Verify that the activities instance overview page version 2 can link to the correct groups, subgroups and activities
        When Activity instance created via API is searched for and found
        And User goes to instance overview page by clicking its name
        Then Instance overview page is opened
        When Version '0.1' is selected from the Version dropdown list
        And The status displayed on the summary has value 'Draft' and version is '0.1'
        And The Start date value is saved
        Then The correct End date should be displayed
        And The Instance linked group, subgroup and instance are displayed in the Activity groupings table
        And The Activity Items table is empty
        When Version '1.0' is selected from the Version dropdown list
        And The status displayed on the summary has value 'Final' and version is '1.0'
        Then The Instance linked group, subgroup and instance are displayed in the Activity groupings table

@pending_development
    Scenario: Verify that the pagination works in both Activity groupings and Activity items table
        When Activity instance created via API is searched for and found
        And User goes to instance overview page by clicking its name
        Then Instance overview page is opened
        When I select 5 rows per page from dropdown list in the Activity groupings table
        Then The Activity groupings table should be displayed with 5 rows per page
        When I click on the next page button in the Activity groupings table
        Then The Activity grouping table should display the next page within 5 rows per page
        When I select 5 rows per page from dropdown list in the Activity items table
        Then The Activity items table should be displayed with 5 rows per page
        When I click on the next page button in the Activity items table
        Then The Activity items table should display the next page within 5 rows per page

@manual_test
Scenario: Verify that the filter and export functionality work in both Activity groupings and Activity items table
        When Activity instance created via API is searched for and found
        And User goes to instance overview page by clicking its name
        Then Instance overview page is opened
        And The free text search field works in both Activity groupings and Activity items table
        And The Export functionality works in both Activity groupings and Activity items table
        And The Filter functionality works in both Activity groupings and Activity items table

Scenario: [Table][Search][Negative case] User must be able to search not existing grouping and table will be correctly filtered
        When Activity instance created via API is searched for and found
        And User goes to instance overview page by clicking its name
        Then Instance overview page is opened
        When User searches for non-existing item in 'Activity groupings' table
        Then The Activity groupings table is empty

Scenario: [Table][Search][Negative case] User must be able to search not existing activity items and table will be correctly filtered
        When Activity instance created via API is searched for and found
        And User goes to instance overview page by clicking its name
        Then Instance overview page is opened
        And User waits for linked 'Activity Items' table data to load
        When User searches for non-existing item in 'Activity Items' table
        Then The Activity Items table is empty

Scenario: [Table][Filtering] User must have access to filters
        When Activity instance created via API is searched for and found
        And User goes to instance overview page by clicking its name
        Then Instance overview page is opened
        And Filters for the 'Activity groupings' table are expanded
        Then Following filters are available in the table 'Activity groupings'
        | filter by             |
        | Activity group        |
        | Activity subgroup     |
        | Activity              |

Scenario: [Table][Filtering] User must have access to filters
        When Activity instance created via API is searched for and found
        And User goes to instance overview page by clicking its name
        Then Instance overview page is opened
        And Filters for the 'Activity Items' table are expanded
        Then Following filters are available in the table 'Activity Items'
        | filter by                |
        |  Data type               |
        |  Name                    |
        |  Activity Item Class     |
