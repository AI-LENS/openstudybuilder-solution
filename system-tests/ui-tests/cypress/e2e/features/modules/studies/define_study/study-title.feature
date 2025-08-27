@REQ_ID:1074250
Feature: Studies - Define Study - Study Title

    As a User I want to have ability to define title of my study.

    Background: User is logged in and study has been selected
        Given The user is logged in   
        And A test study is selected

    Scenario: [Navigation] User must be able to navigate to the Study Title page
        Given The '/studies' page is opened
        When The 'Study Title' submenu is clicked in the 'Define Study' section
        Then The current URL is '/study_title'

    Scenario: [Create][Postive case] User must be able to add a new Study Title
        Given The test study '/study_title' page is opened
        And A test study is selected
        When The 'Edit study title' button is clicked
        And The study title form is filled with new title and saved
        Then The study selected has new title appended

    Scenario: [Actions][Edit] User must be able to copy the Study Title from currently existing study
        Given The test study '/study_title' page is opened
        And A test study is selected
        When The 'Edit study title' button is clicked
        And The study title is copied from another study
        Then The study selected has new title copied

    Scenario: [Online help] User must be able to read online help for the page
        Given The test study '/study_title' page is opened
        And The online help button is clicked
        Then The online help panel shows 'Study Title' panel with content 'The title of the clinical study, corresponding to the title of the protocol.'