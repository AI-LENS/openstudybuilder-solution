@REQ_ID:1074254
Feature: Studies - Define Study - Study Structure - Study Visits

    See shared notes for study visits in file study-visit-intro-notes.txt

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study visits.

    Background: User is logged in and study has been selected
        Given The user is logged in

    Scenario: [Navigation] User must be able to navigate to Study Visit page using side menu
        Given A test study is selected
        And The '/studies' page is opened
        When The 'Study Structure' submenu is clicked in the 'Define Study' section
        And The 'Study Visits' tab is selected
        Then The current URL is '/study_structure/visits'

    Scenario: [Table][Options] User must be able to see the Study Visit table with following options
        Given The test study '/study_structure/visits' page is opened
        Then A table is visible with following options
            | options                                                         |
            | Add content                                                     |
            | Edit                                                            |
            | Show version history                                            |
            | Filters                                                         |
            | Columns                                                         |
            | Export                                                          |
            | Add select boxes to table to allow selection of rows for export |

    Scenario: [Table][Columns][Names] User must be able to see the Study Visit table with following columns
        Given The test study '/study_structure/visits' page is opened
        And A table is visible with following headers
            | headers                     |
            | Epoch                       |
            | Visit type                  |
            | SoA Milestone               |
            | Visit Class                 |
            | Visit Subclass              |
            | Repeating frequency         |
            | Visit name                  |
            | Anchor visit in visit group |
            | Visit group                 |
            | Global anchor visit         |
            | Contact mode                |
            | Time reference              |
            | Timing                      |
            | Visit number                |
            | Unique visit number         |
            | Visit short name            |
            | Study duration days         |
            | Study duration weeks        |
            | Visit window                |
            | Collapsible visit group     |
            | Show Visit                  |
            | Visit description           |
            | Epoch Allocation Rule       |
            | Visit start rule            |
            | Visit end rule              |
            | Study day                   |
            | Study week                  |
            | Week in Study               |
            | Modified                    |
            | Modified by                 |

    Scenario: [Online help] User must be able to read online help for the page
        Given The test study '/study_structure/visits' page is opened
        And The online help button is clicked
        Then The online help panel shows 'Study Visits' panel with content "A clinical encounter where the the subject interacts with the investigator. There can be one more visits in an Epoch. To edit visit(s) in the table view click on the pencil in the top-right menu."

    Scenario: [Table][Columns][Visibility] User must be able to use column selection option
        Given The '/studies/Study_000005/study_structure/visits' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Create][Pre-condition] User must not be able to add a new Study Visit when no Study Epoch has been defined
        Given The '/studies/Study_000005/study_structure/visits' page is opened
        When The 'add-visit' button is clicked
        Then The the user is prompted with a notification message "To add visits, you need to difine the epochs first. Would you like to define epochs?"
        And The 'Add epoch' button is visible
        And The 'Cancel' button is visible

    Scenario: [Create][Mandatory fields] User must not be able to create an visit without epoch selected
        Given The study with uid 'Study_000001' is selected
        And [API] The epoch with type 'Pre Treatment' and subtype 'Screening' exists in selected study
        And User waits for 3 seconds
        And The '/studies/Study_000001/study_structure/visits' page is opened
        And User waits for epochs to load
        When Add visit button is clicked
        And Form continue button is clicked
        And Form continue button is clicked
        Then The validation appears for missing study period

    Scenario: [Create][Mandatory fields] User must not be able to create an visit without type, contact mode, time reference and timing defined
        Given The study with uid 'Study_000001' is selected
        And [API] The epoch with type 'Pre Treatment' and subtype 'Screening' exists in selected study
        And The '/studies/Study_000001/study_structure/visits' page is opened
        And User waits for epochs to load
        When Add visit button is clicked
        And Form continue button is clicked
        And First available epoch is selected
        And Form continue button is clicked
        And Form save button is clicked
        Then The validation appears for missing visit type
        And The validation appears for missing contact mode
        And The validation appears for missing time reference
        And The validation appears for missing visit timing
    
    Scenario: [Create][Fields check] User must not be able to select time referece for an anchor visit
        Given The study with uid 'Study_000003' is selected
        Given [API] Study vists uids are fetched for study 'Study_000003'
        And [API] Visits group 'V2-V4' is removed
        And [API] Visits group 'V2,V3,V4' is removed
        And [API] Visits group 'V1,V2' is removed
        And [API] Visits group 'V2,V3' is removed
        And [API] Study visits in study 'Study_000003' are cleaned-up
        And The study with uid 'Study_000003' is selected
        And [API] The epoch with type 'Pre Treatment' and subtype 'Screening' exists in selected study
        And User waits for 3 seconds
        And The '/studies/Study_000003/study_structure/visits' page is opened
        And User waits for epochs to load
        When Add visit button is clicked
        And Form continue button is clicked
        And Epoch 'Screening' is selected for the visit
        And Form continue button is clicked
        And Anchor visit checkbox is checked
        Then It is not possible to edit Time Reference for anchor visit

    Scenario: [Create][Anchor visit][Positive case] User must be able to create an anchor visit
        Given The study with uid 'Study_000003' is selected
        And [API] The epoch with type 'Pre Treatment' and subtype 'Screening' exists in selected study
        And The '/studies/Study_000003/study_structure/visits' page is opened
        And User waits for epochs to load
        When Add visit button is clicked
        And Form continue button is clicked
        And Epoch 'Screening' is selected for the visit
        And Form continue button is clicked
        And Visit data is filled in: visit class 'single-visit', visit type 'Randomisation', contact mode 'On Site Visit', time unit 'day'
        And Anchor visit checkbox is checked
        When Form save button is clicked
        Then The new Anchor Visit is visible within the Study Visits table

    @manual_test
    Scenario: User must be able to create an information visit with visit 0
        Given The study with uid 'Study_000001' is selected
        And [API] The epoch with type 'Pre Treatment' and subtype 'Screening' exists in selected study
        When The '/studies/Study_000001/study_structure/visits' page is opened
        Given A test study is selected
        And The epoch exists in selected study
        When The test study '/study_structure/visits' page is opened
        And The first scheduled visit is created with the visit type as an Information visit
        And The visit timing is set to the lowest timing of all existing visit when compared to the Global Anchor time reference
        Then The Information visit should be created with 0 as Visit number
        And No reordering of existing visits should happen

    Scenario: [Create][Anchor visit][Negative case] User must not be able to create an anchor visit if one already exists
        And The '/studies/Study_000003/study_structure/visits' page is opened
        And User waits for epochs to load
        When Add visit button is clicked
        And Form continue button is clicked
        And Epoch 'Screening' is selected for the visit
        And Form continue button is clicked
        Then The Anchor visit checkbox is disabled

    Scenario: [Actions][Edit] User must be able to edit the study visit
        Given The study with uid 'Study_000003' is selected
        And [API] The static visit data is fetched
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Randomisation', epoch 'Screening'
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1
        Given The '/studies/Study_000003/study_structure/visits' page is opened
        When User searches for 'V2'
        And The 'Edit' option is clicked from the three dot menu list
        And Form continue button is clicked
        And Form continue button is clicked
        And Visit description is changed to 'Testing edition'
        And Form save button is clicked
        Then Visit description is displayed in the table as 'Testing edition'

    Scenario: [Actions][Edit][Fields check] User must be able to update study visit epoch
        Given The '/studies/Study_000003/study_structure/visits' page is opened
        When User searches for 'V2'
        And The 'Edit' option is clicked from the three dot menu list
        And Form continue button is clicked
        Then The study epoch field is enabled for editing

    Scenario: [Export][CSV] User must be able to export the data in CSV format
        Given The test study '/study_structure/visits' page is opened
        And The user exports the data in 'CSV' format
        Then The study specific 'StudyVisits' file is downloaded in 'csv' format

    Scenario: [Export][Json] User must be able to export the data in JSON format
        Given The test study '/study_structure/visits' page is opened
        And The user exports the data in 'JSON' format
        Then The study specific 'StudyVisits' file is downloaded in 'json' format

    Scenario: [Export][Xml] User must be able to export the data in XML format
        Given The test study '/study_structure/visits' page is opened
        And The user exports the data in 'XML' format
        Then The study specific 'StudyVisits' file is downloaded in 'xml' format

    Scenario: [Export][Excel] User must be able to export the data in EXCEL format
        Given The test study '/study_structure/visits' page is opened
        And The user exports the data in 'EXCEL' format
        Then The study specific 'StudyVisits' file is downloaded in 'xlsx' format

    @pending_implementation
    Scenario: User must not be able to update study epoch without updating the timing to correct chronological order
        Given The '/studies/Study_000002/study_structure/visits' page is opened
        And There are at least 3 visits created for the study
        When The user tries to update last treatment visit epoch to Screening without updating the timing
        Then The system displays the message "The following visit can't be created as the next Epoch Name 'Treatment' starts at the '1' Study Day"

    @manual_test
    Scenario: User must be able to edit the study information visit with visit 0 to other visit type
        Given The '/studies/Study_000003/study_structure/visits' page is opened
        And A studty inforamtion visit with visit 0 is created
        When This study information visit is edited to be a different visit type
        Then This visit can no longer be Visit 0
        And Reordering will occur of existing visits

    @manual_test
    Scenario: User must be able to edit the study information visit with visit 0 to same visit type
        Given The '/studies/Study_000003/study_structure/visits' page is opened
        And A studty inforamtion visit with visit 0 is created
        When This study information visit is edited to the same visit type
        Then This visit should be given the visit number of 0
        When This visit is edited to higher visit timing compare to the Global Anchor time reference
        Then Reordering of other visits will occur

    Scenario: [Actions][Delete] User must be able to delete the study visit
        Given The '/studies/Study_000003/study_structure/visits' page is opened
        And The 'Delete' option is clicked from the three dot menu list
        Then The pop up displays 'Visit deleted'

    @manual_test
    Scenario: User must be able to delete the study information visit with visit 0
        Given The '/studies/Study_000003/study_structure/visits' page is opened
        And A studty inforamtion visit with visit 0 is created
        When This study information visit is deleted
        Then No reordering of other visits will occur

    @manual_test
    Scenario: User must be able to delete the study information visit without visit 0
        Given The '/studies/Study_000003/study_structure/visits' page is opened
        And A studty inforamtion visit without visit 0 is created
        When This study information visit is deleted
        Then The reordering of other visits will occur