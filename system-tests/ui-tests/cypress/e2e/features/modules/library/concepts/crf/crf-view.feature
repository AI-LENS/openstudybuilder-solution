@REQ_ID:xxx
Feature: Library - Concepts - CRFs - CRF View

  As a user, I want to integrate and display CRFs exported from Veeva EDC so that 
    I can efficiently manage and maintain CRFs within the StudyBuilder Library.

  Background: User must be logged in
    Given The user is logged in
    And The '/library' page is opened

  Scenario: [Navigation] User must be able to navigate to CRF View page
    Given The '/library' page is opened
    When The 'CRFs' submenu is clicked in the 'Concepts' section
    And The 'CRF View' tab is selected
    Then The current URL is '/library/crfs/odm-viewer'
    
@manual_test
  Scenario: Exporting CRFs from Veeva EDC to StudyBuilder CRF Library
    Given a CRF is exported from Veeva EDC
    When I view the StudyBuilder CRF library
    Then the items should be visible in the StudyBuilder CRF library
    And the item groups should be visible in the StudyBuilder CRF library
    And the form should be visible in the StudyBuilder CRF library
@manual_test
  Scenario: Matching Properties of Items between Veeva EDC and StudyBuilder CRF Library
    Given a CRF is exported from Veeva EDC
    When I check the properties of items in StudyBuilder CRF library
    Then the OID of the item in CRF in StudyBuilder library should be the same as the item name in Veeva EDC library
    And for a numeric field, the number of digits set on an item in Veeva EDC library should match the number of digits set for the item in StudyBuilder library
    And the label of the unit displayed in StudyBuilder library should match the label of the unit in Veeva EDC library form
    And the label of the item displayed in StudyBuilder library should match the label of the item displayed in Veeva EDC library form
    And the number of options for selection in a unit field should be the same in both systems if there are more than 1 option to select
    And if an item is required in Veeva EDC library form, then the same item should be set as required in StudyBuilder library form
    And when an item is required, a red '*' should appear before the label of the item
@manual_test
  Scenario: Matching Properties of Item Groups between Veeva EDC and StudyBuilder CRF Library
    Given a CRF is exported from Veeva EDC
    When I check the properties of item groups in StudyBuilder CRF library
    Then the item group OID in StudyBuilder should be the same as the item group name in Veeva EDC library form
    And the item group label in StudyBuilder should be the same as the item group label in Veeva EDC library form
    And if the item group is checked as repeating in Veeva EDC library form, it should be checked as repeating in StudyBuilder library item group