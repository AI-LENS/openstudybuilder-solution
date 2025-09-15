@REQ_ID:1070683
Feature: Library - Concepts - CRFs - CRF View

 As a user, I want to verify that the CRFs View page exported from Veeva EDC Libary are correctly displayed. 

  Background: User must be logged in
    Given The user is logged in
    And The '/library' page is opened

  Scenario: [Navigation] User must be able to navigate to CRF View page
    Given The '/library' page is opened
    When The 'CRFs' submenu is clicked in the 'Concepts' section
    And The 'CRF View' tab is selected
    Then The current URL is '/library/crfs/odm-viewer'

  Scenario: Verifying XML Code checkbox can be checked and displayed the XML code page
    Given The '/library/crfs/odm-viewer' page is opened
    When I select a value from the ODM Element Name dropdown
    And I click the LOAD button
    Then The imported CRF view page should be displayed
    When I check the XML Code checkbox
    Then The XML Code page should be displayed and formatted correctly
  