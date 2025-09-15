@REQ_ID:1070683
Feature: Library - Concepts - Activities - Overview Page Display
    As a user, I want to verify that every Overview Page in the Concepts Library, including Activities, 
        Activity Groups, Activity Subgroups, and Activity Instances can display correctly.

    Background: 
        Given The user is logged in
        When [API] Activity Instance in status Final with Final group, subgroup and activity linked exists
        And Group, subgroup, activity and instance names created through API are found

    Scenario: [Activity][Overview][Sections check] Verify that the activities overview page displays correctly
        Given The '/library/activities/activities' page is opened
        When Activity created via API is searched for and found
        And User goes to group overview page by clicking its name
        Then Group overview page is opened
        Given The '/library/activities/activities' page is opened
        When Activity created via API is searched for and found
        And User goes to subgroup overview page by clicking its name
        Then Subgroup overview page is opened
        Given The '/library/activities/activities' page is opened
        And Activity created via API is searched for and found
        And User goes to activity overview page by clicking its name
        Then Activity overview page is opened
        When I click on the history button
        Then The history page is opened
        And The 'close-button' button is clicked
        And The Activity linked group, subgroup and instance are displayed in the Activity groupings table
        And The group overview page can be opened by clicking the group link in overview page
        And User goes back to the previous page
        And The subgroup overview page can be opened by clicking the subgroup link in overview page
        And User goes back to the previous page
        When I click on the COSMoS YAML tab
        Then The COSMoS YAML page should be opened with Download button and Close button displayed
        When The Download YAML content button is clicked
        Then The 'COSMoS-overview' file without timestamp is downloaded in 'yml' format
        # And the COSMoS YAML file should be saved with correct content (this step should be tested manually)
        When I click on the Close button in the COSMoS YAML page
        Then Activity overview page is opened

    Scenario: [Activity instance][Overview][Sections check] Verify that the instance overview page displays correctly
        Given The '/library/activities/activity-instances' page is opened
        When User waits for the table
        When Activity instance created via API is searched for and found
        Then Activity group, activity subgroup and activity values are available in the table
        When User goes to group overview page by clicking its name
        Then Group overview page is opened
        Given The '/library/activities/activity-instances' page is opened
        When User waits for the table
        When Activity instance created via API is searched for and found
        And User goes to subgroup overview page by clicking its name
        Then Subgroup overview page is opened
        Given The '/library/activities/activity-instances' page is opened
        When User waits for the table
        When Activity instance created via API is searched for and found
        And User goes to instance overview page by clicking its name
        Then Instance overview page is opened
        When I click on the history button
        Then The history page is opened
        And The 'close-button' button is clicked
        And The Instance linked group, subgroup and instance are displayed in the Activity groupings table
        And The group overview page can be opened by clicking the group link in overview page
        And User goes back to the previous page
        And The subgroup overview page can be opened by clicking the subgroup link in overview page
        And User goes back to the previous page
        And The activity overview page can be opened by clicking the activity link in overview page
        And User goes back to the previous page
        When I click on the COSMoS YAML tab
        Then The COSMoS YAML page should be opened with Download button and Close button displayed
        When The Download YAML content button is clicked
        Then The 'COSMoS-overview' file without timestamp is downloaded in 'yml' format
        # Ad the COSMoS YAML file should be saved with correct content (this step should be tested manually)
        When I click on the Close button in the COSMoS YAML page
        Then Instance overview page is opened

    Scenario: [Group][Overview][Sections check] Verify that the group overview page displays correctly
        Given The '/library/activities/activity-groups' page is opened
        When Group created via API is searched for and found
        And User goes to group overview page by clicking its name
        Then Group overview page is opened
        When I click on the history button
        Then The history page is opened
        And The 'close-button' button is clicked
        And The linked subgroup is found in the Groups table with status 'Final' and version '1.0'
        And The subgroup overview page can be opened by clicking the subgroup link in overview page
        And User goes back to the previous page
        When I click on the COSMoS YAML tab
        Then The COSMoS YAML page should be opened with Download button and Close button displayed
        When The Download YAML content button is clicked
        Then The 'COSMoS-overview' file without timestamp is downloaded in 'yml' format
        # And the COSMoS YAML file should be saved with correct content (this step should be tested manually)
        When I click on the Close button in the COSMoS YAML page
        Then Group overview page is opened

    Scenario: [Subgroup][Overview][Sections check] Verify that the subgroup overview page displays correctly
        Given The '/library/activities/activity-subgroups' page is opened
        When Subgroup created via API is searched for and found
        And User goes to group overview page by clicking its name
        Then Group overview page is opened
        Given The '/library/activities/activity-subgroups' page is opened
        When Subgroup created via API is searched for and found
        And User goes to subgroup overview page by clicking its name
        Then Subgroup overview page is opened
        When I click on the history button
        Then The history page is opened
        And The 'close-button' button is clicked
        Then The linked group is found in the Groups table with status 'Final' and version '1.0'
        And The linked activity is found in the Acivities table with status 'Final' and version '1.0'
        When I click on the COSMoS YAML tab
        Then The COSMoS YAML page should be opened with Download button and Close button displayed
        When The Download YAML content button is clicked
        Then The 'COSMoS-overview' file without timestamp is downloaded in 'yml' format
        # And the COSMoS YAML file should be saved with correct content (this step should be tested manually)
        When I click on the Close button in the COSMoS YAML page
        Then Subgroup overview page is opened
