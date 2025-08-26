@REQ_ID:1074260
Feature: Studies - Define Study - Study Activities - Study Activities Placeholder

    Background: User is logged in and study has been selected
        Given The user is logged in
        And A test study is selected
        And The test study '/activities/list' page is opened

    Scenario: [Update][Positive Case][Shared Activity Request] User must be able to accept changes to activity request copied from other study
        When Study activity add button is clicked
        And Activity from placeholder is selected
        And Form continue button is clicked
        When Activity placeholder data is filled in
        And Selected study id is saved
        And Form save button is clicked
        And User waits for 3 seconds
        And The '/studies/Study_000002/activities/list' page is opened
        When Study activity add button is clicked
        When Activity from studies is selected
        And Study by id is selected
        And Form continue button is clicked
        And Activity placeholder is searched for
        And The existing activity request is selected
        And Form save button is clicked
        And Activity placeholder is found
        And The 'Edit' option is clicked from the three dot menu list
        And The study activity request is edited
        And Modal window 'Save' button is clicked
        And The form is no longer available
        And The test study '/activities/list' page is opened
        And Activity placeholder is found
        And The 'Update activity version' option is clicked for flagged item
        And The user is presented with the changes to request
        And Modal window 'Accept' button is clicked
        And The form is no longer available
        Then The activity request changes are applied

    Scenario: [Update][Positive Case][Shared Activity Request] User must be able to decline and keep changes to activity request copied from other study
        When Study activity add button is clicked
        And Activity from placeholder is selected
        And Form continue button is clicked
        When Activity placeholder data is filled in
        And Selected study id is saved
        And Form save button is clicked
        And The '/studies/Study_000002/activities/list' page is opened
        When Study activity add button is clicked
        When Activity from studies is selected
        And Study by id is selected
        And Form continue button is clicked
        And Activity placeholder is searched for
        And The existing activity request is selected
        And Form save button is clicked
        And Activity placeholder is found
        And The 'Edit' option is clicked from the three dot menu list
        And The study activity request is edited
        And Modal window 'Save' button is clicked
        And The form is no longer available
        And The test study '/activities/list' page is opened
        And Activity placeholder is found
        And The 'Update activity version' option is clicked for flagged item
        Then The user is presented with the changes to request
        And Modal window 'Decline and keep' button is clicked
        And The form is no longer available
        Then The activity request changes not applied

    Scenario: [Update][Positive Case][Shared Activity Request] User must be able to decline changes and remove activity request copied from other study
        When Study activity add button is clicked
        And Activity from placeholder is selected
        And Form continue button is clicked
        When Activity placeholder data is filled in
        And Selected study id is saved
        And Form save button is clicked
        And The '/studies/Study_000002/activities/list' page is opened
        When Study activity add button is clicked
        When Activity from studies is selected
        And Study by id is selected
        And Form continue button is clicked
        And Activity placeholder is searched for
        And The existing activity request is selected
        And Form save button is clicked
        And Activity placeholder is found
        And The 'Edit' option is clicked from the three dot menu list
        And The study activity request is edited
        And Modal window 'Save' button is clicked
        And The form is no longer available
        And The test study '/activities/list' page is opened
        And Activity placeholder is found
        And The 'Update activity version' option is clicked for flagged item
        And The user is presented with the changes to request
        And Modal window 'Decline and remove' button is clicked
        And The form is no longer available
        Then The activity request is removed from the study

    Scenario: [Update][Positive Case][Shared Activity Request] User must not be notified of changes when SoA group has been updated
        When Study activity add button is clicked
        And Activity from placeholder is selected
        And Form continue button is clicked
        When Activity placeholder data is filled in
        And Selected study id is saved
        And Form save button is clicked
        And User waits for 3 seconds
        And The '/studies/Study_000002/activities/list' page is opened
        When Study activity add button is clicked
        When Activity from studies is selected
        And Study by id is selected
        And Form continue button is clicked
        And Activity placeholder is searched for
        And The existing activity request is selected
        And Form save button is clicked
        And Activity placeholder is found
        And The 'Edit' option is clicked from the three dot menu list
        And The study activity request SoA group field is edited
        And Modal window 'Save' button is clicked
        And The form is no longer available
        And The test study '/activities/list' page is opened
        And Activity placeholder is found
        And The updated notification icon and update option are not present

    Scenario: [Update][Positive Case][Shared Activity Request] User must not be notified of changes when Rationale for activity request has been updated
        When Study activity add button is clicked
        And Activity from placeholder is selected
        And Form continue button is clicked
        When Activity placeholder data is filled in
        And Selected study id is saved
        And Form save button is clicked
        And User waits for 3 seconds
        And The '/studies/Study_000002/activities/list' page is opened
        When Study activity add button is clicked
        When Activity from studies is selected
        And Study by id is selected
        And Form continue button is clicked
        And Activity placeholder is searched for
        And The existing activity request is selected
        And Form save button is clicked
        And Activity placeholder is found
        And The 'Edit' option is clicked from the three dot menu list
        And The study activity request data collection field is edited
        And Modal window 'Save' button is clicked
        And The form is no longer available
        And The test study '/activities/list' page is opened
        And Activity placeholder is found
        And The updated notification icon and update option are not present

    Scenario: [Update][Positive Case][Shared Activity Request] User must not be notified of changes when Rationale for activity request has been updated
        When Study activity add button is clicked
        And Activity from placeholder is selected
        And Form continue button is clicked
        When Activity placeholder data is filled in
        And Selected study id is saved
        And Form save button is clicked
        And User waits for 3 seconds
        And The '/studies/Study_000002/activities/list' page is opened
        When Study activity add button is clicked
        When Activity from studies is selected
        And Study by id is selected
        And Form continue button is clicked
        And Activity placeholder is searched for
        And The existing activity request is selected
        And Form save button is clicked
        And Activity placeholder is found
        And The 'Edit' option is clicked from the three dot menu list
        And The study activity request rationale for activity field is edited
        And Modal window 'Save' button is clicked
        And The form is no longer available
        And The test study '/activities/list' page is opened
        And Activity placeholder is found
        And The updated notification icon and update option are not present