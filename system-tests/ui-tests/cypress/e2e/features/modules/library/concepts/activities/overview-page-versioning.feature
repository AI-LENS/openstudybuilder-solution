@REQ_ID:1070683

Feature: Library - Concepts - Activities - Overview Page Versioning
  As a user, I want to verify that every Overview Page in the Concepts Library, including Activities, 
        Activity Groups, Activity Subgroups, and Activity Instances can manage the version correctly.

  Background: User is logged in
    Given The user is logged in
    #When The '/administration' page is opened
    #And The 'Feature flags' button is clicked
    #Then Activity instance wizard feature flag is turned off
    When [API] Activity Instance in status Final with Final group, subgroup and activity linked exists
    And Group, subgroup, activity and instance names created through API are found
   
  Scenario: [Activity][Overview][Edit] Edit the activity
    Given The '/library/activities/activities' page is opened
    When User sets status filter to 'all'
    And Activity created via API is searched for and found
    And User goes to activity overview page by clicking its name
    And Activity overview page is opened
    When I click 'New version' button
    And The status displayed on the summary has value 'Draft' and version is '1.1'
    And The linked activity instance is found in the Acivity Instances table with status 'Final' and version '1.0'
    And Activity instance is expanded by clicking chevron button
    And The previous version of linked activity instance is found in the Acivity Instances table with status 'Draft' and version '0.1'
    When I click 'Edit' button 
    And Activity name is changed
    And Form save button is clicked
    And The status displayed on the summary has value 'Draft' and version is '1.2'
    And The Activity Instances table is empty
    
  Scenario: [Activity][Overview][Approve] Approve the Activity
    Given The '/library/activities/activities' page is opened
    When User sets status filter to 'all'
    And Activity created via API is searched for and found
    And User goes to activity overview page by clicking its name
    And Activity overview page is opened
    When I click 'Approve' button
    And The status displayed on the summary has value 'Final' and version is '2.0'
    And The linked activity instance is found in the Acivity Instances table with status 'Final' and version '2.0'
    And Activity instance is expanded by clicking chevron button
    Then The previous version of linked activity instance is found in the Acivity Instances table with status 'Draft' and version '1.2'

  @pending_implementation   
  Scenario: [Activity][Overview][Edit] Edit the activity with draft instance
    Given A test activity approved with draft instance is linked through API
    And The '/library/activities/activities' page is opened
    When User sets status filter to 'all'
    And Activity created via API is searched for and found
    And User goes to activity overview page by clicking its name
    And Activity created via API is searched for and found
    And User goes to activity overview page by clicking its name
    And Activity overview page is opened
    When I click 'New version' button
    And The status displayed on the summary has value 'Draft' and version is '1.1'
    When I click 'Edit' button 
    And Activity name is changed
    And Form save button is clicked
    And The status displayed on the summary has value 'Draft' and version is '1.2'
    When I click 'Approve' button
    And The status displayed on the summary has value 'Final' and version is '2.0'
    And The Activity Instances table is empty

Scenario: [Activity Instance][Overview][Edit] Edit the Instance
    Given The '/library/activities/activity-instances' page is opened
    When User sets status filter to 'all'
    And User waits for the table
    And Activity instance created via API is searched for and found
    And User goes to instance overview page by clicking its name
    And Instance overview page is opened
    When I click 'New version' button
    Then The status displayed on the summary has value 'Draft' and version is '2.1'
    And The Instance linked group, subgroup and instance are displayed in the Activity groupings table
    And The Instance linked activity has status 'Final' and version '2.0'
    When I click 'Edit' button
    And User waits for 3 seconds
    And Form continue button is clicked
    And Form continue button is clicked
    And Instance name is changed
    And Form save button is clicked
    Then The status displayed on the summary has value 'Draft' and version is '2.2'
    #And The Activities table is empty

  Scenario: [Activity Instance][Overview][Approve] Approve the Instance
    Given The '/library/activities/activity-instances' page is opened
    When User sets status filter to 'all'
    And User waits for the table
    And Activity instance created via API is searched for and found
    And User goes to instance overview page by clicking its name
    And Instance overview page is opened
    When I click 'Approve' button
    Then The status displayed on the summary has value 'Final' and version is '3.0'
    And The Instance linked group, subgroup and instance are displayed in the Activity groupings table
    And The Instance linked activity has status 'Final' and version '2.0'

  Scenario: [Group][Overview][Edit] Edit the Group
    Given The '/library/activities/activity-groups' page is opened
    When User sets status filter to 'all'
    And Group created via API is searched for and found
    And User goes to group overview page by clicking its name
    And Group overview page is opened
    When I click 'New version' button
    Then The status displayed on the summary has value 'Draft' and version is '1.1'
    And The linked subgroup is found in the Groups table with status 'Final' and version '1.0'
    When I click 'Edit' button 
    And Group name is changed
    And Form save button is clicked
    Then The status displayed on the summary has value 'Draft' and version is '1.2'
    And The Activity subgroups table is empty

  Scenario: [Group][Overview][Approve] Approve the Group
    Given The '/library/activities/activity-groups' page is opened
    When User sets status filter to 'all'
    And Group created via API is searched for and found
    And User goes to group overview page by clicking its name
    And Group overview page is opened
    When I click 'Approve' button
    Then The status displayed on the summary has value 'Final' and version is '2.0'
    And The Activity subgroups table is empty

  Scenario: [Subgroup][Overview][Edit] Edit the SubGroup
    Given The '/library/activities/activity-subgroups' page is opened
    When User sets status filter to 'all'
    And Subgroup created via API is searched for and found
    And User goes to subgroup overview page by clicking its name
    And Subgroup overview page is opened
    When I click 'New version' button
    And The linked activity is found in the Acivities table with status 'Final' and version '2.0'
    #waiting for API implementation
    #And The linked group is found in the Groups table with status 'Final' and version '2.0'
    Then The status displayed on the summary has value 'Draft' and version is '1.1'
    When I click 'Edit' button 
    And Subgroup name is changed
    And Form save button is clicked
    Then The status displayed on the summary has value 'Draft' and version is '1.2'
    And The Activities table is empty
    #And The Group table is empty

  Scenario: [Subgroup][Overview][Approve] Approve the SubGroup
    Given The '/library/activities/activity-subgroups' page is opened
    When User sets status filter to 'all'
    And Subgroup created via API is searched for and found
    And User goes to subgroup overview page by clicking its name
    And Subgroup overview page is opened
    When I click 'Approve' button
    Then The status displayed on the summary has value 'Final' and version is '2.0'
    #waiting for API implmentation
    #And The linked activity is found in the Acivities table with status 'Draft' and version '1.2'
    #And The linked activity is found in the Acivities table with status 'Final' and version '2.0'
    #And The linked group is found in the Groups table with status 'Final' and version '2.0'

 @manual_test 
  Scenario: Switch between edit version and previous version for instance overview page 
    Given The '/library/activities/activity-instances' page is opened
    When User sets status filter to 'all'
    And Activity instance created via API is searched for and found
    And User goes to instance overview page by clicking its name
    And Instance overview page is opened
    Then The status displayed on the summary has value 'Final' and version is '2.0'
    And I verify the definition is 'def'
    When I click 'New version' button
    Then User verifies that version iss '2.1' and status is 'Draft'
    When I click 'Edit' button 
    And I update definition to "new def", enter a reason for change and save
    Then The status displayed on the summary has value 'Draft' and version is '2.2'
    And I verify the definition is 'new def'
    When Version '2.0' is selected from the Version dropdown list
    Then The status displayed on the summary has value 'Final' and version is '2.0'
    And I verify the definition is 'def'

  @manual_test  
  Scenario: Switch between edit version and previous version for activity overview page
    Given The '/library/activities/activities' page is opened
    When User sets status filter to 'all'
    And Activity created via API is searched for and found
    And User goes to activity overview page by clicking its name
    And Activity created via API is searched for and found
    And User goes to activity overview page by clicking its name
    And Activity overview page is opened
    Then The status displayed on the summary has value 'Final' and version is '2.0'
    And I verify the definition is 'def'
    When I click 'New version' button
    Then The status displayed on the summary has value 'Draft' and version is '2.1'
    When I click 'Edit' button 
    And I update definition to "new def", enter a reason for change and save
    Then The status displayed on the summary has value 'Draft' and version is '2.2'
    And I verify the definition is 'new def'
    When Version '2.0' is selected from the Version dropdown list
    Then The status displayed on the summary has value 'Final' and version is '2.0'
    And I verify the definition is 'def'

  @manual_test 
  Scenario: Switch between edit version and previous version for group overview page 
    Given The '/library/activities/activity-groups' page is opened
    When User sets status filter to 'all'
    And Group created via API is searched for and found
    And User goes to group overview page by clicking its name
    And Group overview page is opened
    Then The status displayed on the summary has value 'Final' and version is '2.0'
    And I verify the definition is 'def'
    When I click 'New version' button
    Then The status displayed on the summary has value 'Draft' and version is '2.1'
    When I click 'Edit' button 
    And I update definition to "new def", enter a reason for change and save
    Then The status displayed on the summary has value 'Draft' and version is '2.2'
    And I verify the definition is 'new def'
    When Version '2.0' is selected from the Version dropdown list
    Then The status displayed on the summary has value 'Final' and version is '2.0'
    And I verify the definition is 'def'

@manual_test
  Scenario: Switch between edit version and previous version for subgroup overview page 
    Given The '/library/activities/activity-subgroups' page is opened
    When User sets status filter to 'all'
    And Subgroup created via API is searched for and found
    And User goes to subgroup overview page by clicking its name
    And Subgroup overview page is opened
    Then The status displayed on the summary has value 'Final' and version is '2.0'
    And I verify the definition is 'def'
    When I click 'New version' button
    Then The status displayed on the summary has value 'Draft' and version is '2.1'
    When I click 'Edit' button 
    And I update definition to "new def", enter a reason for change and save
    Then The status displayed on the summary has value 'Draft' and version is '2.2'
    And I verify the definition is 'new def'
    When Version '2.0' is selected from the Version dropdown list
    Then The status displayed on the summary has value 'Final' and version is '2.0'
    And I verify the definition is 'def'
