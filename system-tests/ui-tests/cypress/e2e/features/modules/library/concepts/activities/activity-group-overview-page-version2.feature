@REQ_ID:1070683

Feature: Library - Concepts - Activities - Activity Group Overview Page (Version 2)
    As a user, I want to verify that the Activity Group Overview Page version 2 in the Concepts Library, can display correctly.

    Background: 
        Given The user is logged in
        When [API] Activity Instance in status Final with Final group, subgroup and activity linked exists
        And Group, subgroup, activity and instance names created through API are found
        Given The '/library/activities/activity-groups' page is opened

    Scenario: Verify that the activity group overview page version 2 displays correctly
        And Group created via API is searched for and found
        When User goes to group overview page by clicking its name
        Then Group overview page is opened
        And The 'Activity subgroups' table is displaying correct columns
        |  header     |
        |  Name       |
        |  Definition |
        |  Version    |
        |  Status     |
        And The linked subgroup is found in the Groups table with status 'Final' and version '1.0'
        And The free text search field should be displayed in the 'Activity subgroups' table
 
    Scenario: Verify that the activities group overview page version 2 can link to the correct subgroup
        And Group created via API is searched for and found
        When User goes to group overview page by clicking its name
        Then Group overview page is opened
        When Version '0.1' is selected from the Version dropdown list
        And The status displayed on the summary has value 'Draft' and version is '0.1'
        And The Start date value is saved
        Then The correct End date should be displayed
        And The Activity subgroups table is empty
        When Version '1.0' is selected from the Version dropdown list
        And The status displayed on the summary has value 'Final' and version is '1.0'
        Then The linked subgroup is found in the Groups table with status 'Final' and version '1.0'
  
    Scenario: Verify that the activities group overview page version 2 can link to the correct subgroup with different versions
        And Group created via API is searched for and found
        When User goes to group overview page by clicking its name
        Then Group overview page is opened
        When I click 'New version' button
        And The status displayed on the summary has value 'Draft' and version is '1.1'
        And The linked subgroup is found in the Groups table with status 'Final' and version '1.0'
        When I click 'Edit' button 
        And Group name is changed
        And Form save button is clicked
        And The status displayed on the summary has value 'Draft' and version is '1.2'
        And The Activity subgroups table is empty
        When I click 'Approve' button
        And The status displayed on the summary has value 'Final' and version is '2.0'
        And The Activity subgroups table is empty
        When The '/library/activities/activity-subgroups' page is opened
        And The Add activity subgroup button is clicked
        And I create a new subgroup and link it to the existing group
        And Form save button is clicked
        And User sets status filter to 'all'
        And New Subgroup is searched for and found
        When The 'Approve' option is clicked from the three dot menu list
        When The '/library/activities/activity-groups' page is opened
        And Group created via API is searched for and found
        And User goes to group overview page by clicking its name
        Then Group overview page is opened
        When Version '2.0' is selected from the Version dropdown list
        And The status displayed on the summary has value 'Final' and version is '2.0'
        Then The new linked subgroup is found in the Groups table with status 'Final' and version '1.0'
        And The Activity subgroup created via API is not available in the table
  

@manual_test
    Scenario: Verify that the pagination works in the Activity subgroups table
        Given The '/library/activities/activity-groups' page is opened
        When I search for the test activity group through the filter field
        And Group created via API is searched for and found
        When User goes to group overview page by clicking its name
        Then Group overview page is opened
        When I select 5 rows per page from dropdown list in the Activity subgroups table
        Then The Activity subgroups table should be displayed with 5 rows per page
        When I click on the next page button in the Activity subgroups table
        Then The Activity subgroups table should display the next page within 5 rows per page
         When I select 10 rows per page from dropdown list in the Activity subgroups table
        Then The Activity subgroups table should be displayed with 10 rows per page
        When I click on the next page button in the Activity subgroups table
        Then The Activity subgroups table should display the next page within 10 rows per page

@manual_test
Scenario: Verify that the filter and export functionality work in the Activity subgroups table
        Given The '/library/activities/activity-groups' page is opened
        When I search for the test activity group through the filter field
        And Group created via API is searched for and found
        When User goes to group overview page by clicking its name
        Then Group overview page is opened
        And The free text search field works in the Activity subgroups table
        And The Export functionality works in the Activity subgroups table
        And The Filter functionality works in the Activity subgroups table

Scenario: [Table][Search][Negative case] User must be able to search not existing subgroup and table will be correctly filtered
        And Group created via API is searched for and found
        When User goes to group overview page by clicking its name
        Then Group overview page is opened
        When User searches for non-existing item in 'Activity subgroups' table
        Then The Activity subgroups table is empty

Scenario: [Table][Search][Postive case] User must be able to search subgroups connected to group
        When [API] A group connected to two subgroups is created
        And [API] Fetch names of group with two connected subgroups
        And Group created via API is searched for and found
        When User goes to group overview page by clicking its name
        Then Group overview page is opened
        And User searches for subgroup in linked Subgroups table
        Then 1 result is present in the 'Activity subgroup' table
        And Subgroup name is present in first row of the Activity Subgroup table
        And User searches for subgroup by using partial name in linked Subgroups table
        Then 2 result is present in the 'Activity subgroup' table

Scenario: [Table][Search][Case sensitivity] User must be able to search item ignoring case sensitivity in subroup table
        And [API] Fetch names of group with two connected subgroups
        And Group created via API is searched for and found
        When User goes to group overview page by clicking its name
        Then Group overview page is opened
        And User searches for subgroup by using lowecased name in linked Subgroups table
        Then 1 result is present in the 'Activity subgroup' table
        And Subgroup name is present in first row of the Activity Subgroup table

Scenario: [Table][Filtering] User must have access to filters
        And Group created via API is searched for and found
        When User goes to group overview page by clicking its name
        Then Group overview page is opened
        And Filters for the 'Activity subgroup' table are expanded
        Then Following filters are available in the table 'Activity subgroup'
        | filter by   |
        | Name        |
        | Definition  |
        | Version     |
        | Status      |

Scenario: [Table][Filtering] User must be able to narrow down table result by using Name filter
        And [API] Fetch names of group with two connected subgroups
        And Group created via API is searched for and found
        When User goes to group overview page by clicking its name
        Then Group overview page is opened
        And User waits for linked 'Activity subgroup' table data to load
        And 2 result is present in the 'Activity subgroup' table
        And Filters for the 'Activity subgroup' table are expanded
        And Subgroup name is selected from filters
        Then 1 result is present in the 'Activity subgroup' table
        And Subgroup name is present in first row of the Activity Subgroup table

Scenario: [Table][Filtering][Search] User must be able combine search and filters
        And [API] Fetch names of group with two connected subgroups
        And Group created via API is searched for and found
        When User goes to group overview page by clicking its name
        Then Group overview page is opened
        And User waits for linked 'Activity subgroup' table data to load
        And Filters for the 'Activity subgroup' table are expanded
        And Subgroup name is selected from filters
        When User searches for non-existing item in 'Activity subgroups' table
        Then The Activity subgroups table is empty
        And User searches for subgroup in linked Subgroups table
        Then 1 result is present in the 'Activity subgroup' table
        And Subgroup name is present in first row of the Activity Subgroup table