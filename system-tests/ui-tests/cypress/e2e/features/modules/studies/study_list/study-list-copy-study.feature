@REQ_ID:987736 @development_only
Feature: Studies - Study List - Study List - Copy Study

    As a user, I want to verify that I can create a new study from an existing study in the Study List page and the data is copied correctly.

    Background: User must be logged in
        Given The user is logged in
        And The 'studies/select_or_add_study' page is opened

    Scenario: [Copy][Study selection] User must be able to select which study to use for structury copying
        Given The 'add-study' button is clicked
        And The user selects the "Create a study from an existing study" option
        And The user populates new study project, number and acronym
        And Form continue button is clicked
        Then The user is presented study selection dropdown

    Scenario: [Copy][Preview] User must be able to preview structure of copied study
        Given The user is on Select what to copy step in form
        When The user selects study to use for copy
        Then The user is presented with visual representation of designated study structure

    Scenario: [Copy][Arms category] User must be able to select Arms category
        Given The 'add-study' button is clicked
        And The user selects the "Create a study from an existing study" option
        And The user populates new study project, number and acronym
        And Form continue button is clicked        
        When The user selects study to use for copy
        When The user selects 'Arms' category to be copied
        Then The 'Branches' category with 'branch_count' derived from source study is presented for selection

    Scenario: [Copy][Branches category] User must be able to select Branches category
        Given The 'add-study' button is clicked
        And The user selects the "Create a study from an existing study" option
        And The user populates new study project, number and acronym
        And Form continue button is clicked      
        When The user selects study to use for copy
        When The user selects 'Arms' category to be copied
        When The user selects 'Branches' category to be copied
        Then The 'Cohorts' category with 'cohort_count' derived from source study is presented for selection

    Scenario: [Copy][Cohorts category] User must be able to select Cohorts category
        Given The 'add-study' button is clicked
        And The user selects the "Create a study from an existing study" option
        And The user populates new study project, number and acronym
        And Form continue button is clicked     
        When The user selects study to use for copy
        When The user selects 'Arms' category to be copied
        When The user selects 'Branches' category to be copied
        When The user selects 'Cohorts' category to be copied
        Then The 'Cohorts' category with 'cohort_count' derived from source study is presented for selection

    Scenario: [Copy][Epochs category] User must be able to select Epochs category
        Given The 'add-study' button is clicked
        And The user selects the "Create a study from an existing study" option
        And The user populates new study project, number and acronym
        And Form continue button is clicked
        When The user selects study to use for copy
        When The user selects 'Arms' category to be copied
        When The user selects 'Branches' category to be copied
        When The user selects 'Cohorts' category to be copied
        When The user selects 'Epochs' category to be copied
        Then The 'Include footnotes' option is visible under 'Epochs' category showing appropiate 'epoch_footnote_count' number
        Then The 'Study visits' category with 'visit_count' derived from source study is presented for selection
    
    Scenario: [Copy][Visits category] User must be able to select Study Visits category
        Given The 'add-study' button is clicked
        And The user selects the "Create a study from an existing study" option
        And The user populates new study project, number and acronym
        And Form continue button is clicked     
        When The user selects study to use for copy
        When The user selects 'Arms' category to be copied
        When The user selects 'Branches' category to be copied
        When The user selects 'Cohorts' category to be copied
        When The user selects 'Epochs' category to be copied
        When The user selects 'Study visits' category to be copied
        Then The 'Include footnotes' option is visible under 'Study visits' category showing appropiate 'visit_footnote_count' number
        Then The 'Elements' category with 'element_count' derived from source study is presented for selection

    Scenario: [Copy][Elements category] User must be able to select elements category
        Given The 'add-study' button is clicked
        And The user selects the "Create a study from an existing study" option
        And The user populates new study project, number and acronym
        And Form continue button is clicked   
        When The user selects study to use for copy
        When The user selects 'Arms' category to be copied
        When The user selects 'Branches' category to be copied
        When The user selects 'Cohorts' category to be copied
        When The user selects 'Epochs' category to be copied
        When The user selects 'Study visits' category to be copied
        When The user selects 'Elements' category to be copied
        Then The Design matrix category is presented for selection
        
    Scenario: [Create][Positive case] User must be able to copy study structure after correctly filling the form
        Given The 'add-study' button is clicked
        And The user selects the "Create a study from an existing study" option
        And The user populates new study project, number and acronym
        And Form continue button is clicked  
        When The user selects study to use for copy
        When The user selects 'Arms' category to be copied
        When The user selects 'Branches' category to be copied
        When The user selects 'Cohorts' category to be copied
        When The user selects 'Epochs' category to be copied
        When The user selects 'Study visits' category to be copied
        When The user selects 'Elements' category to be copied
        When The user selects 'Design matrix' category to be copied
        When The user saves the form with selected data to be copied
        Then The new study is created with selected data

    Scenario: [Create][Mandatory fields] User must not be able to copy study structure without selecting any category to copy
        Given The 'add-study' button is clicked
        And The user selects the "Create a study from an existing study" option
        And The user populates new study project, number and acronym
        And Form continue button is clicked 
        When The user selects study to use for copy
        And The user did not select any category to be copied
        And The 'save-button' button is clicked
        Then The pop up displays 'You must select something to copy'

    Scenario: [Create][Mandatory fields] User must not be able to use existing study number for new study
        Given The 'add-study' button is clicked
        And The user selects the "Create a study from an existing study" option
        And The user selects study project and uses existing study number
        And Form continue button is clicked    
        When The user selects study to use for copy
        When The user selects 'Arms' category to be copied
        And The 'save-button' button is clicked
        Then The system informs user that already existing number cannot be used

    



