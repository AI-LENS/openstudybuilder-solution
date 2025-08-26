"""Common query patterns"""

from textwrap import dedent

# Gives ct_terms_datetime for effective study_standard_version of a StudyValue
study_standard_version_ct_terms_datetime = dedent(
    """
    CALL {
        WITH study_value 
        OPTIONAL MATCH (study_value)-[:HAS_STUDY_STANDARD_VERSION]->(study_standard_version:StudyStandardVersion)-[:HAS_CT_PACKAGE]->(ct_package:CTPackage)
        WHERE ct_package.uid CONTAINS "SDTM CT"
        RETURN datetime(toString(ct_package.effective_date) + 'T23:59:59.999999000Z') AS ct_terms_datetime
    }
"""
)

# Gives CTTermNameValue as {value} for a CTTermRoot {root} at given ct_terms_datetime (f-string)
ct_term_name_at_datetime = dedent(
    """
    CALL {{
        WITH {root}, ct_terms_datetime
        OPTIONAL MATCH ({root})-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[version:HAS_VERSION]->(value:CTTermNameValue)
        WHERE version.status IN ['Final', 'Retired']
        WITH *, (ct_terms_datetime IS NULL OR version.start_date <= ct_terms_datetime
            AND (version.end_date IS NULL OR version.end_date > ct_terms_datetime)) AS dates_match
        ORDER BY dates_match DESC, version.start_date DESC
        LIMIT 1
        RETURN value {{
            .*,
            uid: {root}.uid,
            term_uid: {root}.uid,
            sponsor_preferred_name: value.name,
            queried_effective_date: CASE WHEN dates_match THEN ct_terms_datetime ELSE null END,
            date_conflict: NOT dates_match
        }} AS {value}
    }}
"""
).rstrip()
