@REQ_ID:2866954

Feature: Administration - Feature Flags

  Background: User is logged in
    Given The user is logged in with all.in profile

  Scenario: [Navigation] User must be able to navigate to the feature flags page in the Administration Page
      Given The '/administration' page is opened
      When The 'Feature flags' button is clicked
      Then The current URL is '/administration/featureflags'

  Scenario: [Table][Columns][Names] User must be able to see the columns list on the main page as below
     Given The '/administration/featureflags' page is opened
     Then A table is visible with following headers
        |  header                   |
        |  Name                     |
        |  Description              |

  Scenario: [Feature flags] User must be able to toggle off feature flags
    Given The '/administration/featureflags' page is opened
    And The toggle is set to off
    When The '/studies' page is opened
    And Click the View Listings side-menu
    Then The sub-menu Analysis Study Metadata should not exist

  Scenario Outline: [Feature flags] User must not be able to use disabled page
    Given A test study is selected
    When The '/studies' page is opened
    And The '<page>' is not listed after the dropdown '<name>' is clicked
    
    Examples:
      | page                          | name                |
      | Analysis Study Metadata (New) | View Listings       |

  Scenario: [Feature flags] User must be able to toggle on feature flags
    Given The '/administration/featureflags' page is opened
    And The toggle is set to on
    When The '/studies' page is opened
    And Click the View Listings side-menu
    Then The sub-menu Analysis Study Metadata should exist

  Scenario Outline: [Feature flags] User must be able to use enabled page
    Given A test study is selected
    And The '/studies' page is opened
    When The '<page>' is clicked in the dropdown of '<name>' tile
    Then The current URL is '<url>'

    Examples:
      | page                          | name                | url                                  |
      | Analysis Study Metadata (New) | View Listings       | /analysis_study_metadata_new/mdvisit |

