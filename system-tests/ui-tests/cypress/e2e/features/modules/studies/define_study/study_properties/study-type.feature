Feature: Studies - Define Study - Study Properties - Study Type

    Background: User is logged in and study has been selected
        Given The user is logged in

    Scenario: [Navigation] User must be able to navigate to Study Type page using side menu
        Given A test study is selected
        And The '/studies' page is opened
        When The 'Study Properties' submenu is clicked in the 'Define Study' section
        Then The current URL is '/studies/Study_000001/study_properties/type'

    @REQ_ID:987736
    Scenario: [Table][Columns][Names] User must be able to see the Study Type table with following columns
        Given The '/studies/Study_000001/study_properties/type' page is opened
        Then A table is visible with following headers
            | headers                |
            | Study type information |
            | Selected values        |
            | Reason for missing     |
        And The table display following predefined data
            | row | column                  | value                                 |
            | 0   | Study type information  | Study type                            |
            | 1   | Study type information  | Trial type                            |
            | 2   | Study type information  | Study phase classification            |
            | 3   | Study type information  | Extension study                       |
            | 4   | Study type information  | Adaptive design                       |
            | 5   | Study type information  | Study stop rules                      |
            | 6   | Study type information  | Confirmed response minimum duration   |
            | 7   | Study type information  | Post authorization safety study ind   |
    
    Scenario: [Table][Options] User must be able to see the Study Type table with following options
        Given The '/studies/Study_000001/study_properties/type' page is opened
        And A table is visible with following options
            | options              |
            | Copy from study      |
            | Edit content         |
            | Show version history |

    Scenario: [Online help] User must be able to read online help for the page
        Given The '/studies/Study_000001/study_properties/type' page is opened
        And The online help button is clicked
        Then The online help panel shows 'Study Type' panel with content 'Overall description of the study by selection of prespecified controlled terms. This information is part of the mandatory SDTM.TS domain (Trial Summary).'

    Scenario: [Actions][Edit] Editing the study type
        Given The '/studies/Study_000001/study_properties/type' page is opened
        When The study type is fully defined
        Then The study type data is reflected in the table

    Scenario: [Actions][Edit][Stop rule][None] User must be able to use NONE value for study stop rule
        Given The '/studies/Study_000001/study_properties/type' page is opened
        When The Study Stop Rule NONE option is selected
        Then The Study Stop Rule field is disabled

    Scenario: [Actions][Edit][Minimum duration][N/A] User must be able to use NA value for the Confirmed response minimum duration
        Given The '/studies/Study_000001/study_properties/type' page is opened
        When The Confirmed response minimum duration NA option is selected
        Then The Confirmed response minimum duration field is disabled

    @unstable_disabled
    Scenario: User must be able to copy the study type data from other existing study without overwriting the data
        Given The '/studies/Study_000001/study_properties/type' page is opened
        And Another study with study type defined exists
        When The study type is partially defined
        And The study type is copied from another study without overwriting
        Then Only the missing information is filled from another study in the study type form

    @unstable_disabled
    Scenario: User must be able to copy the study type data from other existing study with overwriting the data
        Given The '/studies/Study_000001/study_properties/type' page is opened
        And Another study with study type defined exists
        When The study type is fully defined
        And The study type is copied from another study with overwriting
        Then All the informations are overwritten in the study type

    @manual_test
    Scenario: User must be able to read change history of output
        Given The '/studies/Study_000001/study_properties/type' page is opened
        When The user opens version history
        Then The user is presented with version history of the output containing timestamp and username

    @manual_test
    Scenario: User must be able to read change history of selected element
        Given The '/studies/Study_000001/study_properties/type' page is opened
        And The 'Show history' option is clicked from the three dot menu list
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames