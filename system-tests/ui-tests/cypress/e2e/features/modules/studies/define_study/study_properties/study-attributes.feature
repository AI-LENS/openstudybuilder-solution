@REQ_ID:1074257
Feature: Studies - Define Study - Study Properties - Study Attributes

    Background: User is logged in and study has been selected
        Given The user is logged in   
        And A test study is selected

    Scenario: [Navigation] User must be able to navigate to the Study Interventions page
        Given The '/studies' page is opened
        When The 'Study Properties' submenu is clicked in the 'Define Study' section
        And The 'Study Attributes' tab is selected
        Then The current URL is '/study_properties/attributes'

    Scenario: [Table][Columns][Names] User must be able to see the page table with correct columns and options
        Given The test study '/study_properties/attributes' page is opened
        Then A table is visible with following headers
            | headers                             |
            | Study intervention type information |
            | Selected values                     |
            | Reason for missing                  |

        And The table display following predefined data
            | row | column                               | value                          |
            | 0   | Study intervention type information  | Intervention type              |
            | 1   | Study intervention type information  | Study intent type              |
            | 2   | Study intervention type information  | Add-on to existing treatments  |
            | 3   | Study intervention type information  | Control type                   |
            | 4   | Study intervention type information  | Intervention model             |
            | 5   | Study intervention type information  | Study is randomised            |
            | 6   | Study intervention type information  | Stratification factor          |
            | 7   | Study intervention type information  | Study blinding schema          |
            | 8   | Study intervention type information  | Planned study length           |

    Scenario: [Actions][Edit] User must be able to edit the Study Intervention Type
        Given The test study '/study_properties/attributes' page is opened
        When The study intervention type is edited
        Then The study intervention type data is reflected in the table

    @manual_test
    Scenario: User must be able to read change history of output
        Given The test study '/study_properties/attributes' page is opened
        When The user opens version history
        Then The user is presented with version history of the output containing timestamp and username

    @manual_test    
    Scenario: User must be able to read change history of selected element
        Given The test study '/study_properties/attributes' page is opened
        And The 'Show history' option is clicked from the three dot menu list
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames