@REQ_ID:1070683
Feature: Library - Concepts - CRFs from Veeva EDC

  As a user, I want to verify that the CRFs Library exported from Veeva EDC Libary are correctly displayed 
  so that I can ensure the integrity and accuracy of the CRF data within the StudyBuilder CRF Library.

  Background: User must be logged in
    Given The user is logged in
    And The '/library' page is opened

  Scenario: [Navigation] User must be able to navigate to CRFs page
    Given The '/library' page is opened
    When The 'CRFs' submenu is clicked in the 'Concepts' section
    Then The current URL is '/library/crfs/templates'
    
@manual_test
  Scenario: Verify the exporting CRFs from Veeva EDC to StudyBuilder CRF Library
    When I view the StudyBuilder CRF library
    And The Form should be visible in the StudyBuilder CRF library (verify "vital sign" exists in Form)
    Then The number of forms in the CRF library should match the number of forms in Veeva EDC library (23 in SB)
    And The number of items in the CRF form should match the number of items in Veeva EDC library form 
    And The number of item groups in the CRF form should match the number of item groups in Veeva EDC library form


@manual_test
  Scenario: Verify Properties of CRF Items between Veeva EDC and CRF Library (vital sign)
    When I open the CRF items page in CRF library
    Then The OID of the item in CRF in library should be the same as the item name in Veeva EDC library
    And For a numeric field, the number of digits set on an item in Veeva EDC library should match the number of digits set for the item in CRF library
    And The label of the unit displayed in CRF library should match the label of the unit in Veeva EDC library form
    And The label of the item displayed in CRF library should match the label of the item displayed in Veeva EDC library form
    And The number of options for selection in a unit field should be the same in both systems if there are more than 1 option to select
    And If an item is required in Veeva EDC library form, then the same item should be set as required in CRF library form
    And When an item is required, a red '*' should appear before the label of the item

@manual_test
  Scenario: Verify Properties of CRF Item Groups between Veeva EDC and CRF Library (vital sign)
    When I open the CRF item groups page in CRF library
    Then The item group OID in CRF group should be the same as the item group name in Veeva EDC library form
    And The item group label in StudyBuilder should be the same as the item group label in Veeva EDC library form
    And If the item group is checked as repeating in Veeva EDC library form, it should be checked as repeating in StudyBuilder library item group