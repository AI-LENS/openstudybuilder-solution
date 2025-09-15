const studyActivityUrl = (study_uid, study_activity_uid) => `/studies/${study_uid}/study-activities/${study_activity_uid}`
const studyActivitiesUrl = (study_uid) => `/studies/${study_uid}/study-activities`

Cypress.Commands.add('deleteActivityFromStudy', (study_uid, activity_uid) => cy.sendDeleteRequest(studyActivityUrl(study_uid, activity_uid)))

Cypress.Commands.add('getExistingStudyActivities', (study_uid) => {
  cy.sendGetRequest(studyActivitiesUrl(study_uid)).then((response) => {
    let uid_array = []
    response.body.items.forEach(item => uid_array.push(item.study_activity_uid))
    return uid_array
  })
})
