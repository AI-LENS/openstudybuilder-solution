@REQ_ID:1074260
Feature: Studies - Define Study - Study Activities - Schedule of Activities - Detailed

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study SoA.

    Background: User is logged in and study has been selected
        Given The user is logged in
        And A test study is selected

    Scenario: [TestData] Study visits, epochs and activities are created
        And [API] The epoch with type 'Pre Treatment' and subtype 'Screening' exists in selected study
        And [API] The epoch with type 'Treatment' and subtype 'Observation' exists in selected study
        And [API] Study vists uids are fetched for current study
        When [API] Study visits in current study are cleaned-up
        And [API] The static visit data is fetched
        Given [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Pre-screening', epoch 'Screening'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1, minVisitWindow -1, maxVisitWindow 1
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Randomisation', epoch 'Observation'
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 2, minVisitWindow 3, maxVisitWindow 7
        And [API] All Activities are deleted from study
        Given The test study '/activities/list' page is opened
        And [API] Study Activity is created and approved
        And Group and subgroup names are fetch to be used in SoA
        When Study activity add button is clicked
        And Activity from library is selected
        And Form continue button is clicked
        And User search and select activity created via API
        And Form save button is clicked
        And The pop up displays 'Study activity added'

    Scenario: [Navigation] User must be able to navigate to Detailed SoA page using side menu
        Given The '/studies' page is opened
        When The 'Study Activities' submenu is clicked in the 'Define Study' section
        And The 'Schedule of Activities' tab is selected
        Then The current URL is '/activities/soa'

    Scenario: [Table][Options] User must be able to see the Detailed SoA table with options listed in this scenario
        Given At least '1' activites are present in the selected study
        And The test study '/activities/soa' page is opened
        Then SoA table is available with Bulk actions, Export and Show version history
        And Search is available in SoA table
        And Button for Expanding SoA table is available

    Scenario: [Table][Options] User must be able to see the Detailed SoA Footnotes table with options listed in this scenario
        Given At least '1' activites are present in the selected study
        And The test study '/activities/soa' page is opened
        Then Footnotes table is available with options
            | options                    |
            | Add SoA footnotes          |
            | Filters                    |
            | Show version history       |
            | search-field               |

    Scenario: [Table][Columns][Names] User must be able to see the Footnotes table with specified headers
        Given At least '1' activites are present in the selected study
        And The test study '/activities/soa' page is opened
        And A table is visible with following headers
            | headers      |
            | #            |
            | Footnote     |
            | Linked to    |

    Scenario: [Table][Columns][Names] User must be able to see the SoA table with specified headers
        Given At least '1' activites are present in the selected study
        And The test study '/activities/soa' page is opened
        And SoA table is visible with following headers
            | headers       |
            | Epoch         |
            | Visit         |
            | Study week    |
            | Visit window  |

    Scenario: [Table][Structure][Activity][Detailed SoA] User must be able to view the study activities in the detailed SoA table matrix
        When The test study '/activities/soa' page is opened
        And User expand table
        Then Activity SoA group, group, subgroup and name are visible in the detailed view

    Scenario: [Table][Structure][Epochs][Detailed SoA] User must be able to view the study epochs in the protocol SoA table matrix
        When The test study '/activities/soa' page is opened
        Then Epoch 'Screening' and epoch 'Observation' are visible in the detailed view

    Scenario: [Table][Structure][Visits][Detailed SoA] User must be able to view the study visits in the protocol SoA table matrix
        When The test study '/activities/soa' page is opened
        Then Visits 'V1', 'V2', 'V3' are visible in the detailed view

    Scenario: [Table][Structure][Study weeks][Detailed SoA] User must be able to view the study weeks in the protocol SoA table matrix
        When The test study '/activities/soa' page is opened
        Then Study weeks 0, 1, 2 are visible in the detailed view

    Scenario: [Table][Structure][Study visit windows][Detailed SoA] User must be able to view the study visit window in the protocol SoA table matrix
        When The test study '/activities/soa' page is opened
        Then Study visit windows '0', '±1', '+3/+7' are visible in the detailed view

    Scenario: [Table][Structure][Activity][Protocol SoA] User must be able to view the study activities in the protocol SoA table matrix
        When The test study '/activities/soa' page is opened
        And User expand table
        And User clicks eye icon on activity level
        And User clicks eye icon on SoA group level for 'INFORMED CONSENT'
        And User waits for 1 seconds
        And User switches to the 'protocol' view
        And User waits for the protocol SoA table to load
        Then Activity SoA group, group, subgroup and name are visible in the protocol view

    Scenario: [Table][Structure][Epochs][Protocol SoA] User must be able to view the study epochs in the protocol SoA table matrix
        When The test study '/activities/soa' page is opened
        And User switches to the 'protocol' view
        And User waits for the protocol SoA table to load
        Then Epoch 'Screening' and epoch 'Observation' are visible in the protocol view

    Scenario: [Table][Structure][Visits][Protocol SoA] User must be able to view the study visits in the protocol SoA table matrix
        When The test study '/activities/soa' page is opened
        And User switches to the 'protocol' view
        And User waits for the protocol SoA table to load
        Then Visits 'V1', 'V2', 'V3' are visible in the protocol view

    Scenario: [Table][Structure][Study weeks][Protocol SoA] User must be able to view the study weeks in the protocol SoA table matrix
        When The test study '/activities/soa' page is opened
        And User switches to the 'protocol' view
        And User waits for the protocol SoA table to load
        Then Study weeks 0, 1, 2 are visible in the protocol view

    Scenario: [Table][Structure][Study visit windows][Protocol SoA] User must be able to view the study visit window in the protocol SoA table matrix
        When The test study '/activities/soa' page is opened
        And User switches to the 'protocol' view
        And User waits for the protocol SoA table to load
        Then Study visit windows '0', '±1', '+3/+7' are visible in the protocol view

    @manual_test
    Scenario: User must be presented with time unit of visits the same as defined in first defined study visity
        Given At least '1' activites are present in the selected study
        And The test study '/activities/soa' page is opened
        And The test study data contains defined visits
        Then The SoA is displaying the data using correct time unit

    @manual_test
    Scenario: User must be able to mark a [SoA row] to be displayed in the Detailed SoA
        Given At least '1' activites are present in the selected study
        And The test study '/activities/soa' page is opened
        When The test <SoA row> is marked to be displayed in the Detailed SoA
        And The Detailed SoA tab is opened
        Then The test <SoA row> is displayed in the Detailed SoA

        Examples:
            | SoA row           |
            | SoA Group         |
            | Activity Group    |
            | Activity Subgroup |
            | Activity          |

    @manual_test
    Scenario: User must be able to mark a [SoA row] to be hidden in the Detailed SoA
        Given At least '1' activites are present in the selected study
        And The test study '/activities/soa' page is opened
        When The test <SoA row> is marked to be hidden in the Detailed SoA
        And The Detailed SoA tab is opened
        Then The test <SoA row> is not displayed in the Detailed SoA

        Examples:
            | SoA row           |
            | SoA Group         |
            | Activity Group    |
            | Activity Subgroup |
            | Activity          |

    Scenario: [Actions][Activity][Hide/Unhide] User must me able to hide/unhide group in SoA
        When The test study '/activities/soa' page is opened
        And User switches to the 'protocol' view
        Then Group is visible in the protocol SoA
        And User switches to the 'detailed' view
        And User expand table
        And User clicks eye icon on group level
        And User waits for 1 seconds
        And User switches to the 'protocol' view
        And User waits for the protocol SoA table to load
        Then Group is not visible in the protocol SoA
        And User switches to the 'detailed' view
        And User clicks eye icon on group level
        And User waits for 1 seconds
        And User switches to the 'protocol' view
        Then Group is visible in the protocol SoA

    Scenario: [Actions][Activity][Hide/Unhide] User must me able to hide/unhide subgroup in SoA
        When The test study '/activities/soa' page is opened
        And User switches to the 'protocol' view
        Then Subgroup is visible in the protocol SoA
        And User switches to the 'detailed' view
        And User expand table
        And User clicks eye icon on subgroup level
        And User waits for 1 seconds
        And User switches to the 'protocol' view
        And User waits for the protocol SoA table to load
        Then Subgroup is not visible in the protocol SoA
        And User switches to the 'detailed' view
        And User clicks eye icon on subgroup level
        And User waits for 1 seconds
        And User switches to the 'protocol' view
        Then Subgroup is visible in the protocol SoA

    Scenario: [Actions][Activity][Hide/Unhide] User must me able to hide/unhide activity in SoA
        When The test study '/activities/soa' page is opened
        And User switches to the 'protocol' view
        And User waits for the protocol SoA table to load
        Then Activity is visible in the protocol SoA
        And User switches to the 'detailed' view
        And User expand table
        And User clicks eye icon on activity level
        And User waits for 1 seconds
        And User switches to the 'protocol' view
        Then Activity is not visible in the protocol SoA
        And User switches to the 'detailed' view
        And User clicks eye icon on activity level
        And User waits for 1 seconds
        And User switches to the 'protocol' view
        And User waits for the protocol SoA table to load
        Then Activity is visible in the protocol SoA

    Scenario: [Actions][Remove Activity] User must be able to remove Study Activity from Detailed SoA
        Given At least '1' activites are present in the selected study
        And The test study '/activities/soa' page is opened
        When The user click on 'Remove Activity' action for an Activity
        And The user confirms the deletion pop-up
        Then The pop up displays 'Study activity removed'
        And The Activity is no longer visible in the SoA

    Scenario: [Actions][Add Activity][From Library] User must be able to add Study Activity from Detailed SoA selecting From Library
        Given At least '1' activites are present in the selected study
        And The test study '/activities/soa' page is opened
        When The user click on 'Add activity' action for an Activity
        And Activity from library is selected
        And Form continue button is clicked
        And User selects first available activity and SoA group
        And Form save button is clicked
        Then The pop up displays 'Study activity added'
        And The Activity is visible in the SoA

    Scenario: [Actions][Add Activity][From Study][By Id] User must be able to add Study Activity from Detailed SoA selecting From Study
        Given At least '1' activites are present in the selected study
        And The test study '/activities/soa' page is opened
        When The user click on 'Add activity' action for an Activity
        And Activity from studies is selected
        And Study with id value '999-3000' is selected
        And Form continue button is clicked
        And User selects first available activity
        And Form save button is clicked
        Then The pop up displays 'Study activity added'
        And The Activity is visible in the SoA

    Scenario: [Actions][Add Activity][From Study][By Acronym] User must be able to add Study Activity from Detailed SoA selecting From Study
        Given At least '1' activites are present in the selected study
        And The test study '/activities/soa' page is opened
        When The user click on 'Add activity' action for an Activity
        And Activity from studies is selected
        And Study with acronym value 'DummyStudy 0' is selected
        And Form continue button is clicked
        And User selects first available activity
        And Form save button is clicked
        Then The pop up displays 'Study activity added'
        And The Study Activity is found
        And The Activity is visible in the SoA

    @manual_test
    Scenario: User must be able to change activity grouping for given Study Activity in Detailed SoA
        Given At least '1' activites are present in the selected study
        And The test study '/activities/soa' page is opened
        When The user click on 'Remove activity' action for an Activity
        And The user updates the Activity Group for that Activity in Detailed SoA
        And The user updates the Activity SubGroup for that Activity in Detailed SoA
        And The user provides the rationale for activity request for that Activity in Detailed SoA
        Then The pop up snack displays 'The Study activity Aspartate Aminotransferase has been updated.'
        And The changes are visible in Detailed SoA

    @manual_test
    Scenario: User must be able to exchange activity in given Study in Detailed SoA through selection from studies
        Given At least '1' activites are present in the selected study
        And The test study '/activities/soa' page is opened
        When The user click on 'Exchange Activity' action for an Activity
        And The user goes through selection from studies form
        Then The newly selected avtivity replaces previous activity in study
        And The scheduling is not affected

    Scenario: [Actions][Exchange Activity] User must be able to exchange activity in given Study in Detailed SoA through selection from library
        Given At least '1' activites are present in the selected study
        And The test study '/activities/soa' page is opened
        When The user click on 'Exchange Activity' action for an Activity
        And The user goes through selection from library form
        Then The newly selected activity replaces previous activity in study

    @manual_test
    Scenario: User must be able to exchange activity in given Study in Detailed SoA by creating an placeholder for new Activity Request
        Given At least '1' activites are present in the selected study
        And The test study '/activities/soa' page is opened
        When The user click on 'Exchange Activity' action for an Activity
        And The user goes through creating a placeholder for new Activity Request form
        Then The newly selected avtivity replaces previous activity in study
        And The scheduling is not affected

    @manual_test
    Scenario: User must be able to exchange activity in given Study in Detailed SoA by requesting an activity
        Given At least '1' activites are present in the selected study
        And The test study '/activities/soa' page is opened
        When The user click on 'Exchange Activity' action for an Activity
        And The user goes through creating a placeholder for new Activity Request form
        Then The newly selected avtivity replaces previous activity in study

    @manual_test
    Scenario: User must be able to add activity from different activity group than selected
        Given At least '1' activites are present in the selected study
        And The test study '/activities/soa' page is opened
        When The user adds an activity from different group than selected to add activity
        Then The activity is assigned to group user has selected

    Scenario: [Bulk][Edit] User must be able to open bulk edit activities form on Detailed SoA
        Given At least '2' activites are present in the selected study
        And The test study '/activities/soa' page is opened
        When The user selects rows in SoA table
        And The user clicks on Bulk Edit action on SoA table options
        Then The bulk edit view is presented to user allowing to update Activity Group and Visits for selected activities

    @manual_test @pending_implementation 
    Scenario: User must be able to bulk edit activities on Detailed SoA
        Given At least '2' activites are present in the selected study
        And The test study '/activities/soa' page is opened
        When The user edits activities in bulk
        Then The data for bulk edited activities is updated

    @manual_test @pending_implementation 
    Scenario: User must be able to remove selection of activity on the form for bulk edit in Detailed SoA
        Given At least '2' activites are present in the selected study
        And The test study '/activities/soa' page is opened
        When The user selects rows in SoA table
        And The user clicks on Bulk Edit action on SoA table options
        And The user removes selection of one of Activities on the form
        Then The selection disappears from the form

    Scenario: [Bulk][Mandory fields] User must not be able to bulk edit without selecting Activity Group and Visit
        Given At least '2' activites are present in the selected study
        And The test study '/activities/soa' page is opened
        When The user edits activities in bulk without selecting Activity Group and Visit
        Then The validation appears for Activity Group field in bulk edit form

    Scenario: [Bulk][Delete] User must be able to bulk delete activities on Detailed SoA
        Given At least '2' activites are present in the selected study
        And The test study '/activities/soa' page is opened
        When The user delete activities in bulk
        Then The activities are removed from the study
        
    Scenario: [Actions][Reordering] User must be able to enable reordering of activities in Detailed SoA
        Given At least '3' activities are present in the same 'Acute Kidney Injury' flowchart subgroup and 'TRIAL MATERIAL' group in the selected study
        And The test study '/activities/soa' page is opened
        When The user enables the Reorder Activities function for acitivities in the same 'Acute Kidney Injury' flowchart subgroup and 'TRIAL MATERIAL' group
        And The user updates the order of activities
        Then The new order of activites is visible

    Scenario: [New study] User must be able to see buttons for adding new activity or visit when Study is empty
        Given The '/studies/select_or_add_study/active' page is opened
        When A new study is added
        And [API] Study uid is fetched
        And Go to created study
        Then Text about no added visits and activities is displayed
        And User can click Add visit button
        Then The current URL is '/study_structure/visits'
        And Go to created study
        And User can click Add study activity button
        Then The current URL is '/activities/list'

    Scenario: [Table][Search][Positive case] User must be able to search study activity
        Given The test study '/activities/list' page is opened
        And [API] Study Activity is created and approved
        And Group and subgroup names are fetch to be used in SoA
        When Study activity add button is clicked
        And Activity from library is selected
        And Form continue button is clicked
        And User search and select activity created via API
        And Form save button is clicked
        And The pop up displays 'Study activity added'
        And The test study '/activities/soa' page is opened
        And User expand table
        When User search newly added activity
        Then Activity is found in table

    Scenario: [Table][Search][Case sensitivity] User must be able to search study activity ingnoring case sensitivity
        And The test study '/activities/soa' page is opened
        And User expand table
        When User search newly added activity in lowercase
        Then Activity is found in table

    Scenario: [Table][Search][Partial text] User must be able to search activity by only inputing 3 characters
        And The test study '/activities/soa' page is opened
        And User expand table
        When User search newly added activity by partial name
        Then Activity is found in table

    Scenario: [Table][Search][Negative] User must be able to search non-existing study activity
        Given The test study '/activities/soa' page is opened
        And User expand table
        When User search for non-existing activity
        Then No activities are found

    Scenario: [Table][Search][Negative] User must not be able to search activity by activity subgroup
        Given The test study '/activities/soa' page is opened
        And User expand table
        When User search search activity by subgroup
        Then No activities are found

    Scenario: [Table][Search][Negative] User must not be able to search activity by activity group
        Given The test study '/activities/soa' page is opened
        And User expand table
        When User search search activity by group
        Then No activities are found

    @manual_test @BUG_ID:2851795
    Scenario:[Edit] User must be presented with all activity groups linked when editing the activity
        Given The test study '/activities/soa' page is opened
        And The activity with more than one activity group exists in the table
        When The user opens the edit form for that activity
        Then The Activity group dropdown is presenting all linked activity groups

    @manual_test @BUG_ID:2844670
    Scenario:[Edit] User must be able to hide groups when activity groups has been changed
        Given The test study '/activities/soa' page is opened
        And The activity with linked activity group is present for the study
        When The user hides that activity group
        Then The group is hidden correctly
