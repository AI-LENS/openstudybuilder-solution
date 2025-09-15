@REQ_ID:1070683

Feature: Library - Concepts - Activities - Activity Overview Page (Version 2)
    As a user, I want to verify that the Activity Overview Page version 2 in the Concepts Library, can display correctly.


    Background: 
        Given The user is logged in
        When [API] Activity Instance in status Final with Final group, subgroup and activity linked exists
        And Group, subgroup, activity and instance names created through API are found
        Given The '/library/activities/activities' page is opened
        And User waits for the table

    Scenario: Verify that the activities overview page version 2 displays correctly
        And Activity created via API is searched for and found
        And User goes to activity overview page by clicking its name
        Then Activity overview page is opened
        And User waits for the table
        And The 'Activity groupings' table is displaying correct columns
        |  header                  |
        |  Activity group          |
        |  Activity subgroup       |
        |  Activity instances      |
        And The 'Activity instances' table is displaying correct columns
        |  header                   |
        |  Name                     |
        |  Version                  |
        |  Status                   |
        |  Activity Instance class  |
        |  Topic code               |
        |  Adam parameter code      |
        And The Activity linked group, subgroup and instance are displayed in the Activity groupings table
        And The free text search field should be displayed in the 'Activity groupings' table
        Then The linked activity instance is found in the Acivity Instances table with status 'Final' and version '1.0'
        And The free text search field should be displayed in the 'Activity instances' table
        And Activity instance is expanded by clicking chevron button
        And The previous version of linked activity instance is found in the Acivity Instances table with status 'Draft' and version '0.1'

    Scenario: Verify that the activities overview page version 2 can link to the correct groups, subgroups and instances
        And Activity created via API is searched for and found
        And User goes to activity overview page by clicking its name
        Then Activity overview page is opened
        When Version '0.1' is selected from the Version dropdown list
        And The status displayed on the summary has value 'Draft' and version is '0.1'
        And The Start date value is saved
        Then The correct End date should be displayed
        And The activity instance is not available in Activity groupings table
        And The Activity Instances table is empty
        When Version '1.0' is selected from the Version dropdown list
        And The status displayed on the summary has value 'Final' and version is '1.0'
        And User waits for linked 'Activity instances' table data to load
        Then The Activity linked group, subgroup and instance are displayed in the Activity groupings table
        Then The linked activity instance is found in the Acivity Instances table with status 'Final' and version '1.0'
        And User waits for 1 seconds
        And Activity instance is expanded by clicking chevron button
        And The previous version of linked activity instance is found in the Acivity Instances table with status 'Draft' and version '0.1'

@manual_test
    Scenario: Verify that the pagination works in both Activity groupings and Activity instances table
        And Activity created via API is searched for and found
        And User goes to activity overview page by clicking its name
        Then Activity overview page is opened
        When I select 5 rows per page from dropdown list in the Activity groupings table
        Then The Activity groupings table should be displayed with 5 rows per page
        When I click on the next page button in the Activity groupings table
        Then The Activity groupings table should display the next page within 5 rows per page
        When I select 10 rows per page from the dropdown list in the Activity instances table
        Then The Activity instances table should be displayed with 10 rows per page
        When I click on the next page button in the Activity instances table
        Then The Activity instances table should display the next page with 10 rows per page

@manual_test
Scenario: Verify that the filter and export functionality work in both Activity groupings and Activity instances table
        And Activity created via API is searched for and found
        And User goes to activity overview page by clicking its name
        Then Activity overview page is opened
        And The free text search field works in both Activity groupings and Activity instances table
        And The Export functionality works in both Activity groupings and Activity instances table
        And The Filter functionality works in both Activity groupings and Activity instances table

Scenario: [Table][Search][Negative case] User must be able to search not existing grouping and table will be correctly filtered
        And Activity created via API is searched for and found
        And User goes to activity overview page by clicking its name
        Then Activity overview page is opened
        When User searches for non-existing item in 'Activity groupings' table
        Then The Activity groupings table is empty

Scenario: [Table][Search][Negative case] User must be able to search not existing instance and table will be correctly filtered
        And Activity created via API is searched for and found
        And User goes to activity overview page by clicking its name
        Then Activity overview page is opened
        And User waits for linked 'Activity instances' table data to load
        When User searches for non-existing item in 'Activity instances' table
        Then The Activity Instances table is empty

Scenario: [Table][Search][Postive case] User must be able to search subgroups connected to group
        When [API] An activity connected to two instances is created
        And [API] Fetch names of activity with two connected instances
        And Activity created via API is searched for and found
        And User goes to activity overview page by clicking its name
        Then Activity overview page is opened
        And User waits for linked 'Activity instances' table data to load
        And User searches for instance in linked Instances table
        Then 1 result is present in the 'Activity instances' table
        And Activity Instance name is present in first row of the linked Instances table
        And User searches for instance by using partial name in linked Instances table
        Then 2 result is present in the 'Activity instances' table

Scenario: [Table][Search][Case sensitivity] User must be able to search item ignoring case sensitivity in subroup table
        And [API] Fetch names of activity with two connected instances
        And Activity created via API is searched for and found
        And User goes to activity overview page by clicking its name
        Then Activity overview page is opened
        And User waits for linked 'Activity instances' table data to load
        And User searches for instance by using lowecased name in linked Instances table
        Then 1 result is present in the 'Activity instances' table
        And Activity Instance name is present in first row of the linked Instances table

Scenario: [Table][Filtering] User must have access to filters
        And Activity created via API is searched for and found
        And User goes to activity overview page by clicking its name
        Then Activity overview page is opened
        And Filters for the 'Activity groupings' table are expanded
        Then Following filters are available in the table 'Activity groupings'
        | filter by             |
        | Activity group        |
        | Activity subgroup     |
        | Activity instances    |

Scenario: [Table][Filtering] User must have access to filters
        And Activity created via API is searched for and found
        And User goes to activity overview page by clicking its name
        Then Activity overview page is opened
        And Filters for the 'Activity instances' table are expanded
        Then Following filters are available in the table 'Activity instances'
        | filter by                 |
        |  Name                     |
        |  Version                  |
        |  Status                   |
        |  Activity Instance class  |
        |  Topic code               |
        |  Adam parameter code      |

Scenario: [Table][Filtering] User must be able to narrow down table result by using Name filter
        And [API] Fetch names of activity with two connected instances
        And Activity created via API is searched for and found
        And User goes to activity overview page by clicking its name
        Then Activity overview page is opened
        And User waits for linked 'Activity instances' table data to load
        And 2 result is present in the 'Activity instances' table
        And Filters for the 'Activity instances' table are expanded
        And Activity Instance name is selected from filters
        Then 1 result is present in the 'Activity instances' table
        And Activity Instance name is present in first row of the linked Instances table

Scenario: [Table][Filtering][Search] User must be able combine search and filters
        And [API] Fetch names of activity with two connected instances
        And Activity created via API is searched for and found
        And User goes to activity overview page by clicking its name
        Then Activity overview page is opened
        And User waits for linked 'Activity instances' table data to load
        And Filters for the 'Activity instances' table are expanded
        And Activity Instance name is selected from filters
        When User searches for non-existing item in 'Activity instances' table
        Then The Activity subgroups table is empty
        And User searches for subgroup in linked Subgroups table
        Then 1 result is present in the 'Activity instances' table
        And Activity Instance name is present in first row of the linked Instances table