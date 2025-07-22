const ctTermUrl = (codelistName) => `ct/terms?page_size=100&sort_by={"name.sponsor_preferred_name":true}&codelist_name=${codelistName}`
const studyEpochsUrl = (study_uid) =>  `/studies/${study_uid}/study-epochs`
const studyVisitUrl = (study_uid) =>  `/studies/${study_uid}/study-visits`
const visitsGroupsUrl = (study_uid, group) => `/studies/${study_uid}/consecutive-visit-groups/${group}`
const visitsGroupsCreateUrl = (study_uid) => `/studies/${study_uid}/consecutive-visit-groups?validate_only=false`
const visitTypeUrl = '/ct/terms/names?page_size=0&codelist_name=VisitType'
const timeUnitUrl = '/concepts/unit-definitions?subset=Study+Time&sort_by[conversion_factor_to_master]=true&page_size=0'
let contactModeTermUid, visitTypeUid, timeReferenceUid, epochAllocationUid, weekUnitUid, daysUnitUid, epochUid
let studyVisitUids = []

Cypress.Commands.add('cleanStudyVisitsUidArray', () => studyVisitUids = [])

Cypress.Commands.add('getContactModeTermUid', (contactMode) => {
    cy.getSpondorData(ctTermUrl('Visit+Contact+Mode'), contactMode).then(uid => contactModeTermUid = uid)
})

Cypress.Commands.add('getTimeReferenceUid', (timeReferenceName) => {
    cy.getSpondorData(ctTermUrl('Time+Point+Reference'), timeReferenceName).then(uid => timeReferenceUid = uid)
})

Cypress.Commands.add('getEpochAllocationUid', () => {
    cy.getSpondorData(ctTermUrl('Epoch+Allocation'), 'Current Visit').then(uid => epochAllocationUid = uid)
})

Cypress.Commands.add('getVisitTypeUid', (visitTypeName) => {
    cy.sendGetRequest(visitTypeUrl).then((response) => {
          visitTypeUid = response.body.items.find(term => term.sponsor_preferred_name == visitTypeName).term_uid
    })
})

Cypress.Commands.add('getDayAndWeekTimeUnitUid', () => {
    cy.sendGetRequest(timeUnitUrl).then((response) => {
        daysUnitUid = response.body.items.find(term => term.name == 'days').uid
        weekUnitUid = response.body.items.find(term => term.name == 'week').uid
    })
})

Cypress.Commands.add('getEpochUid', (study_uid, epochName) => {
    cy.sendGetRequest(studyEpochsUrl(study_uid)).then((response) => epochUid = response.body.items.find(term => term.epoch_name == epochName).uid)
})

Cypress.Commands.add('createVisit', (study_uid, isGlobalAnchorVisit, visitWeek, max_visit_window_value = 0) => {
    cy.sendPostRequest(studyVisitUrl(study_uid), createVisitBody(isGlobalAnchorVisit, visitWeek, max_visit_window_value)).then(response => {
        if (!isGlobalAnchorVisit) studyVisitUids.push(response.body.uid)
    })
})

Cypress.Commands.add('deleteVisitsGroup', (study_uid, group) => cy.sendDeleteRequest(visitsGroupsUrl(study_uid, group)))

Cypress.Commands.add('createVisitsGroup', (study_uid, groupformat) => {
    cy.sendPostRequest(visitsGroupsCreateUrl(study_uid), createVisitGroupBody(groupformat))
})

Cypress.Commands.add('getSpondorData', (url, filterBy) => {
    cy.sendGetRequest(url).then((response) => {
          return response.body.items.find(term => term.name.sponsor_preferred_name == filterBy).term_uid
    })
})

const createVisitBody = (isGlobalAnchorVisit, visitWeek, maxVisitWindowValue) => {
    const visitDay = isGlobalAnchorVisit ? 0 : visitWeek * 7 + 1
    return {
        "is_global_anchor_visit": isGlobalAnchorVisit,
        "visit_class": "SINGLE_VISIT",
        "show_visit": true,
        "min_visit_window_value": 0,
        "max_visit_window_value": maxVisitWindowValue,
        "visit_subclass": "SINGLE_VISIT",
        "visit_window_unit_uid": daysUnitUid,
        "study_epoch_uid": `${epochUid}`,
        "epoch_allocation_uid": epochAllocationUid,
        "time_value": visitWeek,
        "time_reference_uid": timeReferenceUid,
        "visit_type_uid": visitTypeUid,
        "visit_contact_mode_uid": contactModeTermUid,
        "study_day_label": `Day ${visitDay}`,
        "study_week_label": `Week ${isGlobalAnchorVisit ? 0 : visitWeek + 1}`,
        "time_unit_uid": weekUnitUid
    }
}

const createVisitGroupBody = (groupFormat) => {
    return {
        "visits_to_assign": studyVisitUids,
        "format": groupFormat,
        "validate_only": false
    }
}