@REQ_ID:1070683

Feature: Library - Concepts - Activities - Overview Page Versioning
  As a user, I want to verify that every Overview Page in the Concepts Library, including Activities, 
        Activity Groups, Activity Subgroups, and Activity Instances can manage the version correctly.

  Background: User is logged in
    Given The user is logged in
    When The '/administration' page is opened
    And The 'Feature flags' button is clicked
    Then Activity instance wizard feature flag is turned off
    And [API] Activity Instance in status Final with Final group, subgroup and activity linked exists
    And [API] Activity, activity instance, group and subgroup names are fetched
   
  Scenario: [Activity][Overview][Edit] Edit the activity
    Given The '/library/activities/activities' page is opened
    When User sets status filter to 'all'
    And A test activity overview page is opened
    When I click 'New version' button
    Then I verify that the activity version is '1.1' and status is 'Draft'
    And I verify that there is an instance linked with status 'Final' and version '1.0'
    # And I verify that there is an instance linked with status 'Draft' and version '0.1' (we decided to only show the latest version of each instance)
    When I click 'Edit' button 
    And I make changes to the activity, enter a reason for change and save
    Then I verify that the activity version is '1.2' and status is 'Draft'
    And I verify that linked Activity Instances table is empty
    
  Scenario: [Activity][Overview][Approve] Approve the Activity
    Given The '/library/activities/activities' page is opened
    When User sets status filter to 'all'
    And A test activity overview page is opened
    When I click 'Approve' button
    Then I verify that the activity version is '2.0' and status is 'Final'
    And I verify that there is an instance linked with status 'Final' and version '2.0'
    # When I click on the arrow beside the linked instance name in the Activitiy instance table
    # Then I verify that it displays the test instance with version 1.2 and status Draft, and version 2.0 and status Final (@pending_implementation  )

     @pending_implementation   
  Scenario: [Activity][Overview][Edit] Edit the activity with draft instance
    Given A test activity approved with draft instance is linked through API
    And The '/library/activities/activities' page is opened
    When User sets status filter to 'all'
    And A test activity overview page is opened
    When I click 'New version' button
    Then I verify that the activity version is '1.1' and status is 'Draft'
    When I click 'Edit' button 
    And I make changes to the activity, enter a reason for change and save
    Then I verify that the activity version is '1.2' and status is 'Draft'
    When I click 'Approve' button
    Then I verify that the activity version is '2.0' and status is 'Final'
    And I verify that linked Activity Instances table is empty

Scenario: [Activity Instance][Overview][Edit] Edit the Instance
    Given The '/library/activities/activity-instances' page is opened
    When User sets status filter to 'all'
    And A test instance overview page is opened
    When I click 'New version' button
    Then User verifies that version is '2.1' and status is 'Draft'
    And I verify that in the table Activity groupings there is an activity with status 'Final' and version '2.0'
    When I click 'Edit' button 
    And I make changes to the instance and save
    Then User verifies that version is '2.2' and status is 'Draft'
    # I verify that no 'Activity' is linked (API and UI not implemented yet)

  Scenario: [Activity Instance][Overview][Approve] Approve the Instance
    Given The '/library/activities/activity-instances' page is opened
    When User sets status filter to 'all'
    And A test instance overview page is opened
    When I click 'Approve' button
    Then User verifies that version is '3.0' and status is 'Final'
    And I verify that in the table Activity groupings there is an activity with status 'Final' and version '2.0'

  Scenario: [Group][Overview][Edit] Edit the Group
    Given The '/library/activities/activity-groups' page is opened
    When User sets status filter to 'all'
    And Subgroup name created through API is found
    And A test group overview page is opened
    When I click 'New version' button
    Then I verify that the group version is '1.1' and status is 'Draft'
    And I verify that the test subgroup with status 'Final' and version '1.0' is linked
    When I click 'Edit' button 
    And I make changes to the group, enter a reason for change and save
    Then I verify that the group version is '1.2' and status is 'Draft'
    And The Activity subgroups table should be empty

  Scenario: [Group][Overview][Approve] Approve the Group
    Given The '/library/activities/activity-groups' page is opened
    When User sets status filter to 'all'
    And A test group overview page is opened
    When I click 'Approve' button
    Then I verify that the group version is '2.0' and status is 'Final'
    And The Activity subgroups table should be empty 

  Scenario: [Subgroup][Overview][Edit] Edit the SubGroup
    Given The '/library/activities/activity-subgroups' page is opened
    When User sets status filter to 'all'
    And A test subgroup overview page is opened
    When I click 'New version' button
    And I verify that in the table Activities there is an activity with status 'Final' and version '2.0'
    #waiting for API implementation
    #And I verify that there is a group with status 'Final' and version '2.0'
    Then User verifies that version is '1.1' and status is 'Draft'
    When I click 'Edit' button 
    And I make changes to the subgroup, enter a reason for change and save
    Then User verifies that version is '1.2' and status is 'Draft'
    And I verify that no Activities are linked
    # And I verify that no 'Activity group' is linked  (API and UI not implemented yet)

  Scenario: [Subgroup][Overview][Approve] Approve the SubGroup
    Given The '/library/activities/activity-subgroups' page is opened
    When User sets status filter to 'all'
    And A test subgroup overview page is opened
    When I click 'Approve' button
    Then User verifies that version is '2.0' and status is 'Final'
    #waiting for API implmentation
    #And I verify that in the table Activities there is an activity with status 'Draft' and version '1.2'
    #And I verify that in the table Activities there is an activity with status 'Final' and version '2.0'
    #And I verify that there is a group with status 'Final' and version '2.0'

 @manual_test 
  Scenario: Switch between edit version and previous version for instance overview page 
    Given The '/library/activities/activity-instances' page is opened
    When User sets status filter to 'all'
    And A test instance overview page is opened
    Then User verifies that version is '2.0' and status is 'Final'
    And I verify the definition is 'def'
    When I click 'New version' button
    Then User verifies that version iss '2.1' and status is 'Draft'
    When I click 'Edit' button 
    And I update definition to "new def", enter a reason for change and save
    Then User verifies that version is '2.2' and status is 'Draft'
    And I verify the definition is 'new def'
    When I select the earlier version 2.0 from the version dropdown list
    Then User verifies that version is '2.0' and status is 'Final'
    And I verify the definition is 'def'

  @manual_test  
  Scenario: Switch between edit version and previous version for activity overview page
    Given The '/library/activities/activities' page is opened
    When User sets status filter to 'all'
    And A test activity overview page is opened
    Then User verifies that version is '2.0' and status is 'Final'
    And I verify the definition is 'def'
    When I click 'New version' button
    Then User verifies that version is '2.1' and status is 'Draft'
    When I click 'Edit' button 
    And I update definition to "new def", enter a reason for change and save
    Then User verifies that version is '2.2' and status is 'Draft'
    And I verify the definition is 'new def'
    When I select the earlier version 2.0 from the version dropdown list
    Then User verifies that version is '2.0' and status is 'Final'
    And I verify the definition is 'def'

  @manual_test 
  Scenario: Switch between edit version and previous version for group overview page 
    Given The '/library/activities/activity-groups' page is opened
    When User sets status filter to 'all'
    And A test group overview page is opened
    Then User verifies that version is '2.0' and status is 'Final'
    And I verify the definition is 'def'
    When I click 'New version' button
    Then User verifies that version is '2.1' and status is 'Draft'
    When I click 'Edit' button 
    And I update definition to "new def", enter a reason for change and save
    Then User verifies that version is '2.2' and status is 'Draft'
    And I verify the definition is 'new def'
    When I select the earlier version 2.0 from the version dropdown list
    Then User verifies that version is '2.0' and status is 'Final'
    And I verify the definition is 'def'

@manual_test
  Scenario: Switch between edit version and previous version for subgroup overview page 
    Given The '/library/activities/activity-subgroups' page is opened
    When User sets status filter to 'all'
    And A test subgroup overview page is opened
    Then User verifies that version is '2.0' and status is 'Final'
    And I verify the definition is 'def'
    When I click 'New version' button
    Then User verifies that version is '2.1' and status is 'Draft'
    When I click 'Edit' button 
    And I update definition to "new def", enter a reason for change and save
    Then User verifies that version is '2.2' and status is 'Draft'
    And I verify the definition is 'new def'
    When I select the earlier version 2.0 from the version dropdown list
    Then User verifies that version is '2.0' and status is 'Final'
    And I verify the definition is 'def'
