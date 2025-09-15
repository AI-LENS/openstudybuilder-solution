const { When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let ODMElementName = ''; // Default value for ODM Element Name

When('I select a value from the ODM Element Name dropdown', () => {
    cy.get('.v-select').eq(1)           // To click and open the dropdown
    .click();
    cy.wait(1000); // Wait for the dropdown to open

    cy.get('.v-list-item').last()
    .invoke('text')
    .then((selectedValue) => {
        // Save selected value
        ODMElementName = selectedValue.trim(); // Trim whitespace
    });

    cy.get('.v-list-item').last() // Find the .v-list-item children within the dropdown
    .should('be.visible') // Optional: Ensure that it is visible
    .click(); // select on the last item

})

When ('I click the LOAD button', () => {
    cy.get('.v-btn').contains('Load') // Find the button containing the text 'LOAD'
    .should('be.visible')             // Ensure the button is visible   
    .click();                        // Click the button
})

Then('The imported CRF view page should be displayed', () => {
    cy.get('body').contains(ODMElementName).should('be.visible'); 
})

When('I check the XML Code checkbox', () => {
    cy.contains('label', 'XML Code') // Find the label containing the text
    .click();                     // Click the label, which interacts with the checkbox
})

Then('The XML Code page should be displayed and formatted correctly', () => {
    // Check if the <pre> element's text starts with "<?xml"
    cy.get('pre') // Assuming the <pre> is directly accessible
      .invoke('text') // Get the text content of the <pre>
      .then((text) => {
          // Retrieve the first line by splitting the text into lines
          const firstLine = text.split('\n')[0]; // Get the first line
          
          // Assert that the first line starts with "<?xml"
          expect(firstLine.trimStart()).to.match(/^\s*<\?xml/);
      });
});






