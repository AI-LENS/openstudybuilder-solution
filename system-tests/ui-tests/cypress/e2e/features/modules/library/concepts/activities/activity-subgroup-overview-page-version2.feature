@REQ_ID:1070683

Feature: Library - Concepts - Activities - Activity Subgroup Overview Page (Version 2)
    As a user, I want to verify that the Activity Subgroup Overview Page version 2 in the Concepts Library, can display correctly.

    Background: 
        Given The user is logged in
        When [API] Activity Instance in status Final with Final group, subgroup and activity linked exists
        And Group, subgroup, activity and instance names created through API are found
        Given The '/library/activities/activity-subgroups' page is opened

    Scenario: Verify that the activity subgroup overview page version 2 displays correctly
        And Subgroup created via API is searched for and found
        And User goes to subgroup overview page by clicking its name
        Then Subgroup overview page is opened
        And The 'Activity group' table is displaying correct columns
        |  header     |
        |  Name       |
        |  Version    |
        |  Status     |
        And The 'Activities' table is displaying correct columns
        |  header     |
        |  Name       |
        |  Version    |
        |  Status     |
        And The linked group is found in the Groups table with status 'Final' and version '1.0'
        And The free text search field should be displayed in the 'Activity group' table
        And The linked activity is found in the Acivities table with status 'Final' and version '1.0'
        And The free text search field should be displayed in the 'Activities' table

    Scenario: Verify that the activities subgroup overview page version 2 can link to the correct subgroup
        And Subgroup created via API is searched for and found
        And User goes to subgroup overview page by clicking its name
        Then Subgroup overview page is opened
        When Version '0.1' is selected from the Version dropdown list
        And The status displayed on the summary has value 'Draft' and version is '0.1'
        And The Start date value is saved
        Then The correct End date should be displayed
        And The linked group is found in the Groups table with status 'Final' and version '1.0'
        And The Activities table is empty
        When Version '1.0' is selected from the Version dropdown list
        And The status displayed on the summary has value 'Final' and version is '1.0'
        Then The linked group is found in the Groups table with status 'Final' and version '1.0'
        And The linked activity is found in the Acivities table with status 'Final' and version '1.0'

@manual_test
    Scenario: Verify that the pagination works in both Activity group and Activities table
        Given The '/library/activities/activity-subgroups' page is opened
        When I search for the test activity subgroup through the filter field
        And Subgroup created via API is searched for and found
        And User goes to subgroup overview page by clicking its name
        Then Subgroup overview page is opened
        When I select 5 rows per page from dropdown list in the Activity group table
        Then The Activity group table should be displayed with 5 rows per page
        When I click on the next page button in the Activity group table
        Then The Activities table should display the next page within 5 rows per page
        When I select 5 rows per page from dropdown list in the Activities table
        Then The Activities table should be displayed with 5 rows per page
        When I click on the next page button in the Activities table
        Then The Activities table should display the next page within 5 rows per page

@manual_test
    Scenario: Verify that the filter and export functionality work in both Activity group and Activities table
        Given The '/library/activities/activity-subgroups' page is opened
        When I search for the test activity subgroup through the filter field
        And Subgroup created via API is searched for and found
        And User goes to subgroup overview page by clicking its name
        Then Subgroup overview page is opened
        And The free text search field works in both Activity group and Activities table
        And The Export functionality works in both Activity group and Activities table
        And The Filter functionality works in both Activity group and Activities table

    Scenario: [Table][Search][Negative case] User must be able to search not existing group and table will be correctly filtered
        And Subgroup created via API is searched for and found
        And User goes to subgroup overview page by clicking its name
        Then Subgroup overview page is opened
        When User searches for non-existing item in 'Activity group' table
        Then The Activities groups table is empty

    Scenario: [Table][Search][Negative case] User must be able to search not existing activity and table will be correctly filtered
        And Subgroup created via API is searched for and found
        And User goes to subgroup overview page by clicking its name
        Then Subgroup overview page is opened
        When User searches for non-existing item in 'Activities' table
        Then The Activities table is empty

    Scenario: [Table][Search][Postive case] User must be able to search groups connected to subgroup
        When [API] A subgroup connected to two to groups is created
        And [API] Fetch names of subgroup with two connected groups
        And Subgroup created via API is searched for and found
        And User goes to subgroup overview page by clicking its name
        Then Subgroup overview page is opened
        And User searches for group in linked Activity Group table
        Then 1 result is present in the 'Activity group' table
        And Group name is present in first row of the Activity Group table
        And User searches for group by using partial name in linked Activity Group table
        Then 2 result is present in the 'Activity group' table

    Scenario: [Table][Search][Case sensitivity] User must be able to search item ignoring case sensitivity in group table
        And [API] Fetch names of subgroup with two connected groups
        And Subgroup created via API is searched for and found
        And User goes to subgroup overview page by clicking its name
        Then Subgroup overview page is opened
        And User searches for group by using lowecased name in linked Activity Group table
        Then 1 result is present in the 'Activity group' table
        And Group name is present in first row of the Activity Group table

    Scenario: [Table][Search][Postive case] User must be able to search created activities connected to subgroup
        When [API] A subgroup connected to two activities is created
        And [API] Fetch names of subgroup with two connected activities
        And Subgroup created via API is searched for and found
        And User goes to subgroup overview page by clicking its name
        Then Subgroup overview page is opened
        And User searches for activity in linked Activities table
        Then 1 result is present in the 'Activities' table
        And Activity name is present in first row of the linked Activity table
        And User searches for activity by using partial name in linked Activities table
        Then 2 result is present in the 'Activities' table

    Scenario: [Table][Search][Case sensitivity] User must be able to search item ignoring case sensitivity in activities table
        And [API] Fetch names of subgroup with two connected activities
        And Subgroup created via API is searched for and found
        And User goes to subgroup overview page by clicking its name
        Then Subgroup overview page is opened
        And User searches for activity by using lowecased name in linked Activities table
        Then 1 result is present in the 'Activities' table
        And Activity name is present in first row of the linked Activity table
