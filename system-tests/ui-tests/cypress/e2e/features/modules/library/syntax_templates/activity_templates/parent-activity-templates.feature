@REQ_ID:1070684
Feature: Library - Syntax Templates - Activity Instructions - Parent

    As a user, I want to manage every Activity template under the Syntax Template Library
    Background: User must be logged in
        Given The user is logged in

    Scenario: [Navigation] User must be able to navigate to the Activty Instruction template under the Syntax template Library
        Given The '/library' page is opened
        When The 'Activity Instructions' submenu is clicked in the 'Syntax Templates' section
        Then The current URL is '/library/activity_instruction_templates/parent'

    Scenario: [Table][Columns][Names] User must be able to see the table with correct columns
        Given The '/library/activity_instruction_templates/parent' page is opened
        And A table is visible with following headers
            | headers         |
            | Sequence number |
            | Activity        |
            | Parent template |
            | Modified        |
            | Status          |
            | Version         |

    Scenario: [Table][Columns][Visibility] User must be able to select visibility of columns in the table 
        Given The '/library/activity_instruction_templates/parent' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    @api_specification
    Scenario: System must generated sequence number for Activity Parent Templates when they are created
        Given an Activity Parent Template is created
        Then the attribute for 'Sequence number' will hold an automatic generated number as 'OT'+[Order of Activity Parent Template]

    @api_specification
    Scenario: System must generated sequence number for Activity Pre-instance Templates when they are created
        Given an Activity Pre-instance Template is created
        Then the attribute for 'Sequence number' will hold an automatic generated number as 'OT'+[Order of Activity Parent Template]+'-OP'+[Order of Pre-instantiation]

    @pending_implementation
    Scenario: Template Instantiations must be update when parent template has been updated
        Given The test Activity Parent Template exists with a status as 'Draft'
        When The'Approve' option is clicked from the three dot menu list
        Then all related activity template instantiations must be cascade updated to new version and approved
        And the displayed pop-up snack must include information on number of updated activity template instantiations

    Scenario: [Create][Positive case] User must be able to create Activity Instruction template
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The new activity is added in the library
        Then The Activity Instruction template is visible in the table
        And The item has status 'Draft' and version '0.1'

    Scenario: [Create][N/A indexes] User must be able to create Activity Instruction template with NA indexes
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The new Activity is added in the library with not applicable for indexes
        Then The Activity Instruction template is visible in the table
        And The item has status 'Draft' and version '0.1'

    Scenario: [Actions][Edit][0.1 version] User must be able to edit initial version of the Activity Instruction template
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        And The 'library/activity_instruction_templates/parent' page is opened
        And Activity Instruction is searched for
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The 'Edit' option is clicked from the three dot menu list
        And The activity metadata is updated
        Then The Activity Instruction template is visible in the table
        And The item has status 'Draft' and version '0.2'

    Scenario: [Create][Mandatory fields] User must not be able to create Activity Instruction template without: Template Text
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The new Activity template is added without template text
        Then The validation appears for Template name
        And The form is not closed

    Scenario: [Create][Uniqueness check][Name] User must not be able to create Activity Instruction template with not unique Template Text
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        And The 'library/activity_instruction_templates/parent' page is opened
        And The second activity is added with the same template text
        Then The pop up displays 'already exists'
        And The form is not closed

    Scenario: [Create][Mandatory fields] User must not be able to create Activity Instruction template without: Indication or Disorder
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The new Activity template is added without Indication or Disorder
        Then The validation appears for Indication or Disorder field
        And The form is not closed

    Scenario: [Create][Mandatory fields] User must not be able to create Activity Instruction template without: Activity Group
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The new Activity template is added without Activity Group
        Then The validation appears for Activity Group field
        And The form is not closed

    Scenario: [Create][Mandatory fields] User must not be able to create Activity Instruction template without: Activity SubGroup
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The new Activity template is added without Activity Subgroup
        Then The validation appears for Activity Subgroup field
        And The form is not closed

    Scenario: [Create][Mandatory fields] User must not be able to create Activity Instruction template without: Activity
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The new Activity template is added without Activity field
        Then The validation appears for Activity field
        And The form is not closed

    Scenario: [Create][Syntax validation] User must be able to verify syntax when creating Activity Instruction template
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The new template name is prepared with a parameters
        And The syntax is verified
        Then The pop up displays "This syntax is valid"

    Scenario: [Create][Hide parameters] User must be able to hide parameter of the Activity Instruction template
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The new template name is prepared with a parameters
        And The user hides the parameter in the next step
        Then The parameter is not visible in the text representation

    Scenario: [Create][Select parameters] User must be able to select parameter of the Activity Instruction template
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The new template name is prepared with a parameters
        And The user picks the parameter from the dropdown list
        Then The parameter value is visible in the text representation

    Scenario: [Actions][Delete] User must be able to delete the Draft Activity Instruction template in version below 1.0
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        And The 'library/activity_instruction_templates/parent' page is opened
        And Activity Instruction is searched for
        When The 'Delete' option is clicked from the three dot menu list
        Then The parent activity is no longer available

    Scenario: [Actions][Approve] User must be able to approve the Draft Activity Instruction template
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        And The 'library/activity_instruction_templates/parent' page is opened
        And Activity Instruction is searched for
        When The 'Approve' option is clicked from the three dot menu list
        Then The pop up displays 'Activity template is now in Final state'
        And The item has status 'Final' and version '1.0'

    Scenario: [Actions][Edit indexing] User must be able to edit indexing of Final Activity Instruction template
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        And [API] Activity Instruction is approved
        And The 'library/activity_instruction_templates/parent' page is opened
        And Activity Instruction is searched for
        When The 'Edit indexing' option is clicked from the three dot menu list
        And The indexing is updated for the Activity Template
        And The 'Edit indexing' option is clicked from the three dot menu list
        Then The indexes in activity template are updated

    Scenario: [Actions][Edit][Mandatory fields] User must not be able to save changes to Activity Instruction template without: Change description
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        And The 'library/activity_instruction_templates/parent' page is opened
        And Activity Instruction is searched for
        When The 'Edit' option is clicked from the three dot menu list
        When The created activity template is edited without change description provided
        Then The validation appears for activity change description field
        And The form is not closed

    Scenario: [Actions][New version] User must be able to add a new version of the Final Activity Instruction template
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        And [API] Activity Instruction is approved
        And The 'library/activity_instruction_templates/parent' page is opened
        And Activity Instruction is searched for
        When The 'New version' option is clicked from the three dot menu list
        Then The pop up displays 'New version created'
        And The item has status 'Draft' and version '1.1'

    Scenario: [Actions][Inactivate] User must be able to inactivate the Final Activity Instruction template
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        And [API] Activity Instruction is approved
        And The 'library/activity_instruction_templates/parent' page is opened
        And Activity Instruction is searched for
        When The 'Inactivate' option is clicked from the three dot menu list
        Then The pop up displays 'Activity template retired'
        And The item has status 'Retired' and version '1.0'

    Scenario: [Actions][Reactivate] User must be able to reactivate the Retired Activity Instruction template
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        And [API] Activity Instruction is approved
        And [API] Activity Instruction is inactivated
        And The 'library/activity_instruction_templates/parent' page is opened
        And Activity Instruction is searched for
        When The 'Reactivate' option is clicked from the three dot menu list
        Then The pop up displays 'Activity template is now in Final state'
        And The item has status 'Final' and version '1.0'

    @manual_test
    Scenario: User must be able to view the history for the Parent Activity template with a status as 'Retired'
        Given [API] Activity in status Final with Final group and subgroub exists
        And [API] Activity Instruction in status Draft exists
        And [API] Activity Instruction is approved
        And [API] Activity Instruction is inactivated
        And The 'library/activity_instruction_templates/parent' page is opened
        And Activity Instruction is searched for
        When The 'Reactivate' option is clicked from the three dot menu list
        Then The 'History for template' window is displayed with the following column list with values
            | Column | Header                 |
            | 1      | Indication or disorder |
            | 2      | Criterion category     |
            | 3      | Criterion sub-category |
            | 4      | Template               |
            | 5      | Guidance text          |
            | 6      | Status                 |
            | 7      | Version                |
            | 8      | Change type            |
            | 9      | User                   |
            | 10     | From                   |
            | 11     | To                     |

    @manual_test
    Scenario: User must be able to read change history of output
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The user opens version history
        Then The user is presented with version history of the output containing timestamp and username

    @manual_test
    Scenario: User must be able to read change history of selected element
        Given The 'library/activity_instruction_templates/parent' page is opened
        And The 'Show history' option is clicked from the three dot menu list
        When The user clicks on History for particular element
        Then The user is presented with history of changes for that element
        And The history contains timestamps and usernames

    Scenario: [Table][Pagination] User must be able to use table pagination        
        Given The '/library/activity_instruction_templates/parent' page is opened
        When The user switches pages of the table
        Then The table page presents correct data

    Scenario Outline: [Table][Filtering] User must be able to filter the table by text fields
        Given The 'library/activity_instruction_templates/parent' page is opened
        When The user filters field '<name>'
        Then The table is filtered correctly

        Examples:
            | name                   |
            | Indication or disorder |
            | Activity group         |
            | Activity subgroup     |