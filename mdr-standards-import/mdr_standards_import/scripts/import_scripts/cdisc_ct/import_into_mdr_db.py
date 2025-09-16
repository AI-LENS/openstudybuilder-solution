import time
import re
from mdr_standards_import.scripts.utils import (
    are_lists_equal,
    create_user,
    get_sentence_case_string,
    REPLACEMENTS,
)


AUTHOR_ID = "CDISC_IMPORT"


def print_ignored_stats(tx, effective_date):
    result = tx.run(
        """
        MATCH (import:Import{effective_date: date($effective_date)})
        
        CALL { WITH import
            MATCH (import)-[:INCLUDES]->(package)
            WHERE (:Inconsistency)-[:AFFECTS_PACKAGE]->(package)
            RETURN count(package) AS num_packages
        } 
        
        CALL { WITH import
            MATCH (import)-[:INCLUDES]->(package)-[:CONTAINS]->(codelist)
            WHERE (:Inconsistency)-[:AFFECTS_CODELIST]->(codelist)
            RETURN count(DISTINCT codelist) AS num_codelists
        }
        
        CALL { WITH import
            MATCH (import)-[:INCLUDES]->(package)-[:CONTAINS_TERM]->(term)
            WHERE (:Inconsistency)-[:AFFECTS_TERM]->(term)
            RETURN count(DISTINCT term) AS num_terms
        }

        RETURN num_packages, num_codelists, num_terms
        """,
        effective_date=effective_date,
    ).single()

    print("==  ! Unresolved inconsistencies will not be imported !")
    print("==  ! The following concepts will be ignored:")
    print(f"==     # packages: {result.get('num_packages', 'n/a')}")
    print(f"==    # codelists: {result.get('num_codelists', 'n/a')}")
    print(f"==        # terms: {result.get('num_terms', 'n/a')}")
    print("==")


def get_packages(tx, effective_date):
    packages_data = tx.run(
        """
        MATCH (:Import{effective_date: date($effective_date)})-[:INCLUDES]->(package)
        WHERE NOT (:Inconsistency)-[:AFFECTS_PACKAGE]->(package)
        RETURN
            package{uid: package.name, .name, .catalogue_name} AS package,
            [(package)-[:CONTAINS]->(codelist) | codelist{uid: codelist.concept_id, .concept_id}] AS codelists
        """,
        effective_date=effective_date,
    ).data()

    return packages_data


def get_codelists(tx, effective_date):
    replace_chars = "\n".join(
        [
            f'WITH replace(submval, "{old}", "{new}") AS submval'
            for old, new in REPLACEMENTS
        ]
    )
    query_str1 = """
        MATCH (:Import{effective_date: date($effective_date)})
            -[:INCLUDES]->(package)-[:CONTAINS]->(codelist)
        WHERE NOT (:Inconsistency)-[:AFFECTS_PACKAGE]->(package) AND
              NOT (:Inconsistency)-[:AFFECTS_CODELIST]->(codelist)
        WITH
            codelist,
            collect(DISTINCT package) AS packages
        CALL { WITH codelist
            MATCH (codelist)-[:CONTAINS]->(term)
            WHERE NOT (:Inconsistency)-[:AFFECTS_TERM]->(term)
            CALL { WITH term
                WITH term.code_submission_value AS submval
        """

    query_str2 = """
                RETURN submval AS clean_submval
            }
            RETURN collect({
                term: term{
                    uid: term.concept_id + '_' + clean_submval,
                    .concept_id, .code_submission_value, .name_submission_value, .preferred_term, .definition, .synonyms
                },
                packages: [(term)<-[:CONTAINS_TERM]-(package) | package]
            }) AS terms_data
        }
        RETURN
            codelist,
            terms_data,
            packages
        """
    full_query = query_str1 + replace_chars + query_str2
    result = tx.run(full_query, effective_date=effective_date)
    return result.data()


def merge_codelist_version_independent_data(tx, codelist_data):
    tx.run(
        """
        MERGE (library:Library{name: 'CDISC'})
        WITH library, $codelist_data as data
        MERGE (cl_root:CTCodelistRoot{uid: data.codelist.concept_id})
        MERGE (library)-[:CONTAINS_CODELIST]->(cl_root)
        MERGE (cl_root)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)
        MERGE (cl_root)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)
        """,
        codelist_data=codelist_data,
        author_id=AUTHOR_ID,
    )


def merge_codelist_packages_version_independent_data(tx, codelist_data, effective_date):
    tx.run(
        """
        WITH $codelist_data as data
        MATCH (library:Library{name: 'CDISC'})-[:CONTAINS_CODELIST]->(cl_root:CTCodelistRoot{uid: data.codelist.concept_id})

        WITH library, data, cl_root
        // for each catalogue that has this codelist
        FOREACH (package IN data.packages |
            MERGE (ct_package:CTPackage{uid: package.name})
            MERGE (catalogue:CTCatalogue{name: package.catalogue_name})
            MERGE (catalogue)-[has_codelist:HAS_CODELIST]->(cl_root)
            ON CREATE SET
                has_codelist.start_date=datetime($start_date),
                has_codelist.author_id=$author_id
            MERGE (package_codelist:CTPackageCodelist{uid: package.name + '_' + data.codelist.concept_id})
            MERGE (ct_package)-[:CONTAINS_CODELIST]->(package_codelist)
        )
        """,
        codelist_data=codelist_data,
        start_date=effective_date,
        author_id=AUTHOR_ID,
    )


def merge_codelist_terms_version_independent_data(tx, codelist_data):
    tx.run(
        """
        WITH $codelist_data as data
        MATCH (library:Library{name: 'CDISC'})-[:CONTAINS_CODELIST]->(cl_root:CTCodelistRoot{uid: data.codelist.concept_id})

        WITH library, data, cl_root
        // for each term of the codelist
        FOREACH (term_data IN data.terms_data |
            MERGE (t_root:CTTermRoot{uid: term_data.term.uid})
            SET t_root.concept_id = term_data.term.concept_id
            MERGE (library)-[:CONTAINS_TERM]->(t_root)
            MERGE (t_root)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)
            MERGE (t_root)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)
            FOREACH (package IN term_data.packages |
                MERGE (package_codelist:CTPackageCodelist{uid: package.name + '_' + data.codelist.concept_id})
                MERGE (package_term:CTPackageTerm{uid: package.name + "_" + term_data.term.uid})
                MERGE (package_codelist)-[:CONTAINS_TERM]->(package_term)
            )
        )
        """,
        codelist_data=codelist_data,
        author_id=AUTHOR_ID,
    )


def update_has_term_and_had_term_relationships(tx, codelists_data, effective_date):
    nbr_added_terms = 0
    nbr_removed_terms = 0
    nbr_unchanged_terms = 0
    for codelist_data in codelists_data:
        codelist = codelist_data.get("codelist", None)

        codelist_term_uids = [
            terms_data["term"]["uid"] for terms_data in codelist_data["terms_data"]
        ]

        result = tx.run(
            """
            MATCH (:CTCodelistRoot{uid: $codelist_uid})-[ht:HAS_TERM]->(term_root)
            WHERE ht.start_date <= datetime($effective_date)
            RETURN DISTINCT term_root.uid AS uid, ht.start_date as start_date
            """,
            codelist_uid=codelist["concept_id"],
            effective_date=effective_date,
        )
        matching_active_term_uids = list(result.value())

        result = tx.run(
            """
            MATCH (:CTCodelistRoot{uid: $codelist_uid})-[ht:HAD_TERM]->(term_root)
            WHERE ht.start_date <= datetime($effective_date) AND ht.end_date > datetime($effective_date)
            RETURN DISTINCT term_root.uid AS uid
            """,
            codelist_uid=codelist["concept_id"],
            effective_date=effective_date,
        )
        retired_term_uids = list(result.value())

        term_uids_to_deactivate = [
            term_uid
            for term_uid in matching_active_term_uids
            if term_uid not in codelist_term_uids and term_uid not in retired_term_uids
        ]

        nbr_removed_terms += len(term_uids_to_deactivate)
        tx.run(
            """
            MATCH (codelist_root:CTCodelistRoot{uid: $codelist_uid})-[has_term:HAS_TERM]->(term_root)
            WHERE term_root.uid IN $term_uids_to_deactivate

            CREATE (codelist_root)-[had_term:HAD_TERM]->(term_root)
            SET
                had_term.start_date = has_term.start_date,
                had_term.end_date = datetime($end_date),
                had_term.author_id = has_term.author_id
            DELETE has_term
            """,
            end_date=effective_date,
            codelist_uid=codelist["concept_id"],
            term_uids_to_deactivate=term_uids_to_deactivate,
        )

        term_uids_to_add = [
            term_uid
            for term_uid in codelist_term_uids
            if term_uid not in matching_active_term_uids
            and term_uid not in retired_term_uids
        ]
        nbr_added_terms += len(term_uids_to_add)
        tx.run(
            """
            MATCH (codelist_root:CTCodelistRoot{uid: $codelist_uid})
            MATCH (term_root:CTTermRoot)
            WHERE term_root.uid IN $new_term_uids

            CREATE (codelist_root)-[:HAS_TERM{
                start_date: datetime($start_date),
                author_id: $author_id
            }]->(term_root)
            """,
            start_date=effective_date,
            codelist_uid=codelist["concept_id"],
            new_term_uids=term_uids_to_add,
            author_id=AUTHOR_ID,
        )
        nbr_unchanged_terms += (
            len(codelist_term_uids)
            - len(term_uids_to_add)
            - len(term_uids_to_deactivate)
        )
    # delete_contains_term_relationships(tx)
    return nbr_added_terms, nbr_removed_terms, nbr_unchanged_terms


def delete_contains_term_relationships(tx):
    result = tx.run(
        """
        MATCH (library:Library{name: 'CDISC'})-[contains_term:CONTAINS_TERM]->(term_root)
        WHERE NOT (:CTCodelistRoot)-[:HAS_TERM]->(term_root)
        DELETE contains_term
        RETURN collect(term_root.uid) AS term_concept_ids_that_have_been_removed
        """
    ).single()

    return result.get("term_concept_ids_that_have_been_removed", [])


def merge_catalogues_and_packages(tx, packages_data, effective_date):
    tx.run(
        """
        MERGE (library:Library{name: 'CDISC'})
        ON CREATE SET library.is_editable = false
        WITH library
        UNWIND $packages_data AS package_data
            MERGE (catalogue:CTCatalogue{name: package_data.package.catalogue_name})
            MERGE (library)-[:CONTAINS_CATALOGUE]->(catalogue)
            MERGE (package:CTPackage{uid: package_data.package.name})
            ON CREATE SET
                package.name = package_data.package.name,
                package.label = package_data.package.label,
                package.description = package_data.package.description,
                package.source = package_data.package.source,
                package.effective_date = date($effective_date),
                package.registration_status = package_data.package.registration_status,
                package.href = package_data.package.href,
                
                package.import_date = datetime(),
                package.author_id = $author_id
            MERGE (catalogue)-[:CONTAINS_PACKAGE]->(package)
        """,
        packages_data=packages_data,
        effective_date=effective_date,
        author_id=AUTHOR_ID,
    )


def retire_codelists(tx, packages_data, effective_date):
    for package_data in packages_data:
        package = package_data.get("package")
        codelist_concept_ids = [
            codelist.get("concept_id") for codelist in package_data.get("codelists", [])
        ]
        removed_codelist_concept_ids = delete_has_codelist_relationships(
            tx,
            package.get("catalogue_name"),
            codelist_concept_ids,
            effective_date=effective_date,
        )
        print(
            f"==    - Removed the following codelists from the catalogue='{package.get('catalogue_name')}': {removed_codelist_concept_ids}"
        )

    codelist_concept_ids_for_retirement = get_codelists_for_retirement(tx)
    for concept_id in codelist_concept_ids_for_retirement:
        retire_codelist_attributes_value(tx, concept_id)
        retire_codelist_name_value(tx, concept_id)
    removed_codelist_concept_ids = delete_contains_codelist_relationships(
        tx, codelist_concept_ids_for_retirement
    )
    print(
        f"==    - Retired and removed the following codelists from the CDISC library: {removed_codelist_concept_ids}"
    )


def delete_has_codelist_relationships(
    tx, catalogue_name, existing_codelist_concept_ids, effective_date
):
    result = tx.run(
        """
        MATCH (catalogue:CTCatalogue{name: $catalogue_name})-[has_codelist:HAS_CODELIST]->(codelist_root)
        WHERE NOT codelist_root.uid IN $codelist_concept_ids
        MERGE (catalogue)-[had_codelist:HAD_CODELIST]->(codelist_root)
        ON CREATE SET 
            had_codelist.start_date=has_codelist.start_date,
            had_codelist.end_date=datetime($effective_date),
            had_codelist.author_id=$author_id
        DELETE has_codelist
        RETURN collect(codelist_root.uid) AS codelist_concept_ids_that_have_been_removed
        """,
        catalogue_name=catalogue_name,
        codelist_concept_ids=existing_codelist_concept_ids,
        effective_date=effective_date,
        author_id=AUTHOR_ID,
    ).single()

    return result.get("codelist_concept_ids_that_have_been_removed", [])


def get_codelists_for_retirement(tx):
    result = tx.run(
        """
        MATCH (codelist_root:CTCodelistRoot)
        WHERE NOT ()-[:HAS_CODELIST]->(codelist_root)
        RETURN collect(codelist_root.uid) AS codelist_concept_ids_for_retirement
        """
    ).single()
    return result.get("codelist_concept_ids_for_retirement", [])


def retire_codelist_attributes_value(tx, codelist_concept_id):
    tx.run(
        """
        MATCH (:CTCodelistRoot{uid: $concept_id})-[:HAS_ATTRIBUTES_ROOT]
            ->(cl_attributes_root)-[latest_final:LATEST_FINAL]->(cl_current_attributes_value)
            <-[:LATEST]-(cl_attributes_root)
        WITH cl_attributes_root, cl_current_attributes_value, latest_final
        MATCH (cl_attributes_root)-[has_version:HAS_VERSION]->(cl_current_attributes_value)
        SET has_version.end_date = datetime()
        DELETE latest_final
       
        WITH cl_attributes_root, cl_current_attributes_value, has_version.version AS version LIMIT 1
        CREATE (cl_attributes_root)-[:LATEST_RETIRED]->(cl_current_attributes_value)
        CREATE (cl_attributes_root)-[:HAS_VERSION{
            start_date: datetime(),
            status: 'Retired',
            version: toString(coalesce(toInteger(split(version, '.')[0]), 0) + 1) + '.0',
            change_description: 'The codelist was discontinued by CDISC.',
            author_id: $author_id
        }]->(cl_current_attributes_value)
        """,
        concept_id=codelist_concept_id,
        author_id=AUTHOR_ID,
    )


def retire_codelist_name_value(tx, codelist_concept_id):
    tx.run(
        """
        MATCH (:CTCodelistRoot{uid: $concept_id})-[:HAS_NAME_ROOT]
            ->(cl_name_root)-[latest_final:LATEST_FINAL]->(cl_current_name_value)
            <-[:LATEST]-(cl_name_root)
        WITH cl_name_root, cl_current_name_value, latest_final
        MATCH (cl_name_root)-[has_version:HAS_VERSION]->(cl_current_name_value)
        SET has_version.end_date = datetime()
        DELETE latest_final

        WITH cl_name_root, cl_current_name_value, has_version.version as version LIMIT 1
        CREATE (cl_name_root)-[:LATEST_RETIRED]->(cl_current_name_value)
        CREATE (cl_name_root)-[:HAS_VERSION{
            start_date: datetime(),
            status: 'Retired',
            version: toString(coalesce(toInteger(split(version, '.')[0]), 0) + 1) + '.0',
            change_description: 'The codelist was discontinued by CDISC.',
            author_id: $author_id
        }]->(cl_current_name_value)
        """,
        concept_id=codelist_concept_id,
        author_id=AUTHOR_ID,
    )


def delete_contains_codelist_relationships(tx, codelist_concept_ids):
    result = tx.run(
        """
        MATCH (library:Library{name: 'CDISC'})-[contains_codelist:CONTAINS_CODELIST]->(codelist_root)
        WHERE codelist_root.uid IN $codelist_concept_ids
        DELETE contains_codelist
        RETURN collect(codelist_root.uid) AS codelist_concept_ids_that_have_been_removed
        """,
        codelist_concept_ids=codelist_concept_ids,
    ).single()

    return result.get("codelist_concept_ids_that_have_been_removed", [])


def retire_term(tx, concept_id, effective_date):
    reason = (
        f"There are multiple submission values where each is dependent on the codelist. "
        f"So we split this term and created multiple terms where the concept_id starts with '{concept_id}_' "
        f"followed by the submission value."
    )

    retire_term_attributes_value(tx, concept_id, effective_date, reason)
    retire_term_name_value(tx, concept_id, effective_date, reason)


def retire_term_attributes_value(tx, term_uid, effective_date, reason):
    tx.run(
        """
        MATCH (:CTTermRoot{uid: $term_uid})-[:HAS_ATTRIBUTES_ROOT]
            ->(attributes_root)-[latest_final:LATEST_FINAL]->(current_attributes_value)
            <-[:LATEST]-(attributes_root)
        WITH attributes_root, current_attributes_value, latest_final
        MATCH (attributes_root)-[has_version:HAS_VERSION]->(current_attributes_value)
        SET has_version.end_date = datetime($effective_date_string)
        DELETE latest_final

        WITH attributes_root, current_attributes_value, has_version.version AS version LIMIT 1
        CREATE (attributes_root)-[:LATEST_RETIRED]->(current_attributes_value)
        CREATE (attributes_root)-[:HAS_VERSION{
            start_date: datetime($effective_date_string),
            status: 'Retired',
            version: toString(coalesce(toInteger(split(version, '.')[0]), 0) + 1) + '.0',
            change_description: $change_description,
            author_id: $author_id
        }]->(current_attributes_value)
        """,
        term_uid=term_uid,
        effective_date_string=effective_date,
        change_description=reason,
        author_id=AUTHOR_ID,
    )


def retire_term_name_value(tx, term_uid, effective_date, reason):
    tx.run(
        """
        MATCH (:CTTermRoot{uid: $term_uid})-[:HAS_NAME_ROOT]
            ->(name_root)-[latest_final:LATEST_FINAL]->(current_name_value)
            <-[:LATEST]-(name_root)
        WITH name_root, current_name_value, latest_final
        MATCH (name_root)-[has_version:HAS_VERSION]->(current_name_value)
        SET has_version.end_date = datetime($effective_date_string)
        DELETE latest_final

        WITH name_root, current_name_value, has_version.version AS version LIMIT 1
        CREATE (name_root)-[:LATEST_RETIRED]->(current_name_value)
        CREATE (name_root)-[:HAS_VALUE{
            start_date: datetime($effective_date_string),
            status: 'Retired',
            version: toString(coalesce(toInteger(split(version, '.')[0]), 0) + 1) + '.0',
            change_description: $change_description,
            author_id: $author_id
        }]->(current_name_value)
        """,
        term_uid=term_uid,
        effective_date_string=effective_date,
        change_description=reason,
        author_id=AUTHOR_ID,
    )


def _are_attribute_values_equal(a, b):
    result = (
        a.get("name", None) == b.get("name", None)
        and a.get("submission_value", None) == b.get("submission_value", None)
        and a.get("preferred_term", None) == b.get("preferred_term", None)
        and a.get("definition", None) == b.get("definition", None)
        and a.get("extensible", None) == b.get("extensible", None)
        and are_lists_equal(a.get("synonyms", None), b.get("synonyms", None))
    )
    return result


def _fetch_all_codelists(tx, concept_ids, effective_date):
    query = """
        MATCH (root:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(attr_root)-[:LATEST]->(cl_attributes_value)
        WHERE root.uid IN $concept_ids
        OPTIONAL MATCH (attr_root)-[hv:HAS_VERSION]->(cl_attributes_value_for_date)
        WHERE hv.end_date IS NOT NULL AND hv.start_date <= datetime($effective_date) AND hv.end_date > datetime($effective_date)
        RETURN root.uid AS cid, cl_attributes_value, cl_attributes_value_for_date
    """
    result = tx.run(query, effective_date=effective_date, concept_ids=concept_ids)
    codelists = {}
    for codelist in result:
        codelists[codelist["cid"]] = codelist
    # print(f"got {len(codelists)} codelists")
    return codelists


def update_attributes(tx, codelists_data, effective_date):
    new_terms = 0
    updated_terms = 0
    unchanged_terms = 0

    new_codelists = 0
    updated_codelists = 0
    unchanged_codelists = 0

    cl_concept_ids = [cl["codelist"]["concept_id"] for cl in codelists_data]
    all_existing_codelists = _fetch_all_codelists(tx, cl_concept_ids, effective_date)
    for codelist_data in codelists_data:
        codelist = codelist_data.get("codelist", None)
        terms_data = codelist_data.get("terms_data", {})
        packages = codelist_data.get("packages", None)

        record = all_existing_codelists.get(codelist["concept_id"])

        if record is None:
            create_initial_codelist_attributes_value(
                tx, effective_date, codelist, packages
            )
            create_initial_codelist_name(
                tx, codelist, codelist.get("name", None), "Initial import from CDISC"
            )
            new_codelists += 1
        else:
            value = record["cl_attributes_value"]
            value_for_date = record["cl_attributes_value_for_date"]

            if value_for_date is not None:
                if _are_attribute_values_equal(value_for_date, codelist):
                    # print(f"Codelist {codelist['concept_id']} already has a version for {effective_date}, skipping")
                    unchanged_codelists += 1
                else:
                    print(codelist)
                    print(value_for_date)
                    raise RuntimeError(
                        f"Oh my god! Codelist {codelist['concept_id']} already has a version for {effective_date} but the definition has changed!"
                    )

            elif not _are_attribute_values_equal(value, codelist):
                # if codelist["concept_id"] == "C100133":
                #    print("create_new_version_codelist_attributes_value", effective_date, codelist, packages)
                create_new_version_codelist_attributes_value(
                    tx, effective_date, codelist, packages
                )
                updated_codelists += 1
            else:
                use_existing_codelist_attributes_value(tx, codelist, packages)
                unchanged_codelists += 1

        new_t, upd_t, unch_t = merge_term_values(
            tx, codelist, effective_date, terms_data
        )
        new_terms += new_t
        updated_terms += upd_t
        unchanged_terms += unch_t
    return {
        "new_codelists": new_codelists,
        "updated_codelists": updated_codelists,
        "unchanged_codelists": unchanged_codelists,
        "new_terms": new_terms,
        "updated_terms": updated_terms,
        "unchanged_terms": unchanged_terms,
    }


def create_initial_codelist_attributes_value(
    tx, effective_date_string, codelist, packages
):
    tx.run(
        """
        MATCH (:CTCodelistRoot{uid: $codelist.concept_id})-[:HAS_ATTRIBUTES_ROOT]->(cl_attributes_root)
        CREATE (cl_attributes_value: CTCodelistAttributesValue)
        SET
            cl_attributes_value.name = $codelist.name,
            cl_attributes_value.submission_value = $codelist.submission_value,
            cl_attributes_value.preferred_term = $codelist.preferred_term,
            cl_attributes_value.definition = $codelist.definition,
            cl_attributes_value.extensible = coalesce(toBoolean($codelist.extensible), false),
            cl_attributes_value.synonyms = $codelist.synonyms
        CREATE (cl_attributes_root)-[:LATEST]->(cl_attributes_value)
        CREATE (cl_attributes_root)-[:LATEST_FINAL]->(cl_attributes_value)
        CREATE (cl_attributes_root)-[:HAS_VERSION{
            start_date: datetime($effective_date_string),
            status: 'Final',
            version: '1.0',
            change_description: 'Imported from CDISC',
            author_id: $author_id
        }]->(cl_attributes_value)

        WITH cl_attributes_value
        FOREACH (package IN $packages |
            MERGE (package_codelist:CTPackageCodelist{uid: package.name + "_" + $codelist.concept_id})
            CREATE (package_codelist)-[:CONTAINS_ATTRIBUTES]->(cl_attributes_value)
        )
        """,
        effective_date_string=effective_date_string,
        codelist=codelist,
        packages=packages,
        author_id=AUTHOR_ID,
    )


def create_initial_codelist_name(tx, codelist, name, change_description):
    tx.run(
        """
        MATCH (codelist_root:CTCodelistRoot{uid: $codelist_uid})-[:HAS_NAME_ROOT]->(name_root)
        WHERE NOT (name_root)-[:LATEST]->()
        CREATE (name_root)-[:LATEST]->(name_value:CTCodelistNameValue)
        SET
            name_value.name = $name
        CREATE (name_root)-[:LATEST_FINAL]->(name_value)
        CREATE (name_root)-[:HAS_VERSION{
            start_date: datetime(),
            status: 'Final',
            version: '1.0',
            change_description: $change_description,
            author_id: $author_id
        }]->(name_value)
        """,
        codelist_uid=codelist["concept_id"],
        name=name,
        author_id=AUTHOR_ID,
        change_description=change_description,
    ).consume()


def create_new_version_codelist_attributes_value(
    tx, effective_date_string, codelist, packages
):
    tx.run(
        """
        MATCH (:CTCodelistRoot{uid: $codelist.concept_id})-[:HAS_ATTRIBUTES_ROOT]
            ->(cl_attributes_root)-[latest_final:LATEST_FINAL]->(cl_old_attributes_value)
            <-[latest:LATEST]-(cl_attributes_root)
        WITH cl_attributes_root, cl_old_attributes_value, latest, latest_final
        MATCH (cl_attributes_root)-[has_version:HAS_VERSION]->(cl_old_attributes_value)
        SET has_version.end_date = datetime($effective_date_string)
        DELETE latest, latest_final

        WITH cl_attributes_root, has_version.version AS version LIMIT 1
        CREATE (cl_new_attributes_value:CTCodelistAttributesValue)
        SET
            cl_new_attributes_value.name = $codelist.name,
            cl_new_attributes_value.submission_value = $codelist.submission_value,
            cl_new_attributes_value.preferred_term = $codelist.preferred_term,
            cl_new_attributes_value.definition = $codelist.definition,
            cl_new_attributes_value.extensible = coalesce(toBoolean($codelist.extensible), false),
            cl_new_attributes_value.synonyms = $codelist.synonyms
        CREATE (cl_attributes_root)-[:LATEST_FINAL]->(cl_new_attributes_value)
        CREATE (cl_attributes_root)-[:HAS_VERSION{
            start_date: datetime($effective_date_string),
            status: 'Final',
            version: toString(coalesce(toInteger(split(version, '.')[0]), 0) + 1) + '.0',
            change_description: 'Imported from CDISC',
            author_id: $author_id
        }]->(cl_new_attributes_value)
        CREATE (cl_attributes_root)-[:LATEST]->(cl_new_attributes_value)

        WITH cl_new_attributes_value
        FOREACH (package IN $packages |
            MERGE (package_codelist:CTPackageCodelist{uid: package.name + "_" + $codelist.concept_id})
            CREATE (package_codelist)-[:CONTAINS_ATTRIBUTES]->(cl_new_attributes_value)
        )
        """,
        effective_date_string=effective_date_string,
        codelist=codelist,
        packages=packages,
        author_id=AUTHOR_ID,
    )


def use_existing_codelist_attributes_value(tx, codelist, packages):
    tx.run(
        """
        MATCH (:CTCodelistRoot{uid: $codelist.concept_id})-[:HAS_ATTRIBUTES_ROOT]->()-[:LATEST]->(cl_attributes_value)
        WITH cl_attributes_value
        UNWIND $packages AS package
            MATCH (package_codelist:CTPackageCodelist{uid: package.name + "_" + $codelist.concept_id})
            MERGE (package_codelist)-[:CONTAINS_ATTRIBUTES]->(cl_attributes_value)
        """,
        codelist=codelist,
        packages=packages,
    )


def _are_term_attribute_values_equal(a, b):
    result = (
        a.get("code_submission_value", None) == b.get("code_submission_value", None)
        and a.get("name_submission_value", None) == b.get("name_submission_value", None)
        and a.get("preferred_term", None) == b.get("preferred_term", None)
        and a.get("definition", None) == b.get("definition", None)
        and are_lists_equal(a.get("synonyms", None), b.get("synonyms", None))
        and a.get("concept_id", None) == b.get("concept_id", None)
    )
    return result


def _fetch_all_terms(tx, term_uids, effective_date):
    query = """
        MATCH (root:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(attr_root)-[:LATEST]->(t_attributes_value)
        WHERE root.uid IN $term_uids
        OPTIONAL MATCH (attr_root)-[hv:HAS_VERSION]->(t_attributes_value_for_date)
        WHERE hv.end_date IS NOT NULL AND hv.start_date <= datetime($effective_date) AND hv.end_date > datetime($effective_date)
        RETURN root.uid AS uid, t_attributes_value, t_attributes_value_for_date
    """
    result = tx.run(query, effective_date=effective_date, term_uids=term_uids)
    terms = {}
    for term in result:
        terms[term["uid"]] = term
    # print(f"got {len(terms)} terms")
    return terms


def merge_term_values(tx, codelist, effective_date_string, terms_data):
    new_terms = 0
    updated_terms = 0
    unchanged_terms = 0
    term_uids = [term["term"]["uid"] for term in terms_data]
    all_existing_terms = _fetch_all_terms(tx, term_uids, effective_date_string)
    for term_data in terms_data:
        term = term_data.get("term", None)
        packages = term_data.get("packages", None)

        record = all_existing_terms.get(term["uid"])

        if record is None:
            create_initial_term_attributes_value(
                tx, effective_date_string, term, packages
            )
            create_initial_term_names(
                tx,
                term,
                sponsor_specific_parse_term_name(codelist, term),
                "Initial import from CDISC",
            )
            new_terms += 1
        else:
            value = record["t_attributes_value"]
            value_for_date = record["t_attributes_value_for_date"]

            if value_for_date is not None:
                if _are_term_attribute_values_equal(value_for_date, term):
                    unchanged_terms += 1
                else:
                    print(term)
                    print(value_for_date)
                    raise RuntimeError(
                        f"Oh my god! Term {term['concept_id']} already has a version for {effective_date_string} but the definition has changed!"
                    )

            elif not _are_term_attribute_values_equal(value, term):
                create_new_version_term_attributes_value(
                    tx, effective_date_string, term, packages
                )
                updated_terms += 1
            else:
                use_existing_term_attributes_value(tx, term, packages)
                unchanged_terms += 1
    return new_terms, updated_terms, unchanged_terms


def create_initial_term_attributes_value(tx, effective_date_string, term, packages):
    tx.run(
        """
        MATCH (:CTTermRoot{uid: $term.uid})-[:HAS_ATTRIBUTES_ROOT]->(t_attributes_root)
        CREATE (t_attributes_value: CTTermAttributesValue)
        SET
            t_attributes_value.code_submission_value = $term.code_submission_value,
            t_attributes_value.name_submission_value = $term.name_submission_value,
            t_attributes_value.preferred_term = $term.preferred_term,
            t_attributes_value.definition = $term.definition,
            t_attributes_value.synonyms = $term.synonyms,
            t_attributes_value.concept_id = $term.concept_id
        CREATE (t_attributes_root)-[:LATEST]->(t_attributes_value)
        CREATE (t_attributes_root)-[:LATEST_FINAL]->(t_attributes_value)
        CREATE (t_attributes_root)-[:HAS_VERSION{
            start_date: datetime($effective_date_string),
            status: 'Final',
            version: '1.0',
            change_description: 'Imported from CDISC',
            author_id: $author_id
        }]->(t_attributes_value)

        WITH t_attributes_value
        FOREACH (package IN $packages |
            MERGE (package_term:CTPackageTerm{uid: package.name + "_" + $term.uid})
            CREATE (package_term)-[:CONTAINS_ATTRIBUTES]->(t_attributes_value)
        )
        """,
        effective_date_string=effective_date_string,
        term=term,
        packages=packages,
        author_id=AUTHOR_ID,
    )


def create_initial_term_names(tx, term, name, change_description):
    tx.run(
        """
        MATCH (term_root:CTTermRoot{uid: $term_uid})-[:HAS_NAME_ROOT]->(name_root)
        WHERE NOT (name_root)-[:LATEST]->()
        CREATE (name_root)-[:LATEST]->(name_value:CTTermNameValue)
        SET
            name_value.name = $name,
            name_value.name_sentence_case = $name_sentence_case
        CREATE (name_root)-[:LATEST_FINAL]->(name_value)
        CREATE (name_root)-[:HAS_VERSION{
            start_date: datetime(),
            status: 'Final',
            version: '1.0',
            change_description: $change_description,
            author_id: $author_id
        }]->(name_value)
        """,
        term_uid=term["uid"],
        name=name,
        name_sentence_case=get_sentence_case_string(name),
        author_id=AUTHOR_ID,
        change_description=change_description,
    ).consume()


def create_new_version_term_attributes_value(tx, effective_date_string, term, packages):
    tx.run(
        """
        MATCH (:CTTermRoot{uid: $term.uid})-[:HAS_ATTRIBUTES_ROOT]
            ->(t_attributes_root)-[latest_final:LATEST_FINAL]->(t_old_attributes_value)
            <-[latest:LATEST]-(t_attributes_root)
        WITH t_attributes_root, t_old_attributes_value, latest, latest_final
        MATCH (t_attributes_root)-[has_version:HAS_VERSION]->(t_old_attributes_value)
        SET has_version.end_date = datetime($effective_date_string)
        DELETE latest, latest_final

        WITH t_attributes_root, has_version.version AS version LIMIT 1
        CREATE (t_new_attributes_value:CTTermAttributesValue)
        SET
            t_new_attributes_value.code_submission_value = $term.code_submission_value,
            t_new_attributes_value.name_submission_value = $term.name_submission_value,
            t_new_attributes_value.preferred_term = $term.preferred_term,
            t_new_attributes_value.definition = $term.definition,
            t_new_attributes_value.synonyms = $term.synonyms,
            t_new_attributes_value.concept_id = $term.concept_id
        CREATE (t_attributes_root)-[:LATEST_FINAL]->(t_new_attributes_value)
        CREATE (t_attributes_root)-[:HAS_VERSION{
            start_date: datetime($effective_date_string),
            status: 'Final',
            version: toString(coalesce(toInteger(split(version, '.')[0]), 0) + 1) + '.0',
            change_description: 'Imported from CDISC',
            author_id: $author_id
        }]->(t_new_attributes_value)
        CREATE (t_attributes_root)-[:LATEST]->(t_new_attributes_value)

        WITH t_new_attributes_value
        FOREACH (package IN $packages |
            MERGE (package_term:CTPackageTerm{uid: package.name + "_" + $term.uid})
            CREATE (package_term)-[:CONTAINS_ATTRIBUTES]->(t_new_attributes_value)
        )
        """,
        effective_date_string=effective_date_string,
        term=term,
        packages=packages,
        author_id=AUTHOR_ID,
    )


def use_existing_term_attributes_value(tx, term, packages):
    tx.run(
        """
        MATCH (:CTTermRoot{uid: $term.uid})-[:HAS_ATTRIBUTES_ROOT]->()-[:LATEST]->(t_attributes_value)
        WITH t_attributes_value
        UNWIND $packages AS package
            MATCH (package_term:CTPackageTerm{uid: package.name + "_" + $term.uid})
            MERGE (package_term)-[:CONTAINS_ATTRIBUTES]->(t_attributes_value)
        """,
        term=term,
        packages=packages,
    )


##########################################################################
# Update this part of the code to apply sponsor-specific transformations #
##########################################################################
def sponsor_specific_parse_term_name(codelist, term):
    """Sponsor specific parsing of term name

    Args:
        codelist (dict): Codelist data
        term (dict): Term data

    Returns:
        str: Parsed term name - including sponsor specific transformations
    """
    newname = term["preferred_term"]
    # Clean by removing any trailing space or newline
    newname = newname.strip(" \n")

    if codelist["concept_id"] == "C99077":
        # Study type codelist

        # Remove "Study" from end
        newname = re.sub(r" Study$", "", newname)

    elif codelist["concept_id"] == "C66736":
        # Trial type codelist

        # Remove "Study" or "Trial" from end
        newname = re.sub(r" (Study|Trial)$", "", newname)

    elif codelist["concept_id"] == "C66785":
        # Control type codelist

        # Remove "Control" from end
        newname = re.sub(r" Control$", "", newname)

    elif codelist["concept_id"] == "C66735":
        # Trial Blinding Schema codelist

        # Remove "Study" from end
        newname = re.sub(r" Study$", "", newname)

    elif codelist["concept_id"] == "C99076":
        # Intervention Model Response codelist

        # Remove "Study" from end
        newname = re.sub(r" Study$", "", newname)

    elif codelist["concept_id"] in ("C66729", "C78420", "C78425"):
        # Main codelist:
        # - Route of Administration, C66729
        # Subsets:
        # - Concomitant Medication Route of Administration, C78420
        # - Exposure Route of Administration, C78425

        # Remove "Route of Administration" at start or end.
        # When at the end, allow both a space and a dash in front.
        newname = re.sub(
            r"((\s|-)Route of Administration$|^Route of Administration )", "", newname
        )

        # If starting with "Administration via" then we use the code submission value
        if newname.startswith("Administration via"):
            newname = term["code_submission_value"].title()

    elif codelist["concept_id"] in ("C66726", "C78418", "C78426"):
        # Main codelist:
        # - Pharmaceutical Dosage Form, C66726
        # Subsets
        # - Concomitant Medication Dose Form, C78418
        # - Exposure Dose Form, C78426

        # Remove "Dosage Form" at start or end or middle
        newname = re.sub(r"^Dosage Form for", "For", newname)
        newname = re.sub(r"(\sDosage Form($|(?=\s))|^Dosage Form\s)", "", newname)

    elif codelist["concept_id"] in (
        "C71620",
        "C78417",
        "C78422",
        "C78428",
        "C78427",
        "C78429",
        "C78421",
        "C78423",
        "C78430",
        "C66770",
        "C66781",
        "C85494",
        "C128685",
        "C128686",
        "C128684",
        "C128683",
    ):
        # Main codelist:
        # - Unit, C71620
        # Subsets:
        # - Concomitant Medication Dose Units, C78417
        # - ECG Original Units, C78422
        # - Total Volume Administration Unit, C78428
        # - Unit for the Duration of Treatment Interruption, C78427
        # - Unit of Measure for Flow Rate, C78429
        # - Unit of Drug Dispensed or Returned, C78421
        # - Units for Exposure, C78423
        # - Units for Planned Exposure, C78430
        # - Units for Vital Signs Results, C66770
        # - Age Unit, C66781
        # - PK Units of Measure, C85494
        # - PK Units of Measure - Dose mg, C128685
        # - PK Units of Measure - Dose ug, C128686
        # - PK Units of Measure - Weight g, C128684
        # - PK Units of Measure - Weight kg, C128683

        # Use code submission value as name
        newname = term["code_submission_value"]

    elif codelist["concept_id"] in ("C71113", "C78419", "C78745"):
        # Main codelist:
        # - Frequency, C71113
        # Subsets:
        # - Concomitant Medication Dosing Frequency per Interval, C78419
        # - Exposure Dosing Frequency per Interval, C78745

        # Clean by removing any trailing period
        # Seen (so far) only for C139178: "Every Night." in sdtmct json-files from before 2019-09-27.
        newname = newname.strip(".")

        # Special cases
        if newname == "Infrequent":
            newname = "Occasional"
        if newname == "Every Evening" and term["code_submission_value"] == "QPM":
            newname = "Every Day"

        # Replace "Per Day/Month" with "Daily/Monthly"
        newname = re.sub(r" Per Day$", " Daily", newname)
        newname = re.sub(r" Per Month$", " Monthly", newname)

    # Print changes as codelist;oldname;newname (easy to copy-paste into excel)
    # if newname != term['preferred_term']:
    #    print(f"{codelist['concept_id']};{term['preferred_term']};{newname}")

    return newname


def import_from_cdisc_db_into_mdr(
    effective_date,
    cdisc_ct_neo4j_driver,
    cdisc_db_name,
    mdr_neo4j_driver,
    mdr_db_name,
    author_id,
):
    global AUTHOR_ID
    AUTHOR_ID = author_id

    start_time = time.time()

    if effective_date is None:
        print("WARNING: No effective date specified. Not importing anything.")
        return

    with cdisc_ct_neo4j_driver.session(database=cdisc_db_name) as session:
        with session.begin_transaction() as tx:
            print_ignored_stats(tx, effective_date)
            tx.commit()

        # read from the CDISC DB
        packages_data = session.read_transaction(get_packages, effective_date)
        codelists_data = session.read_transaction(get_codelists, effective_date)

        session.close()

    with mdr_neo4j_driver.session(database=mdr_db_name) as session:
        # write to the clinical MDR db

        # print("==  * Retiring codelists.")
        # session.write_transaction(retire_codelists, packages_data, effective_date)

        print("==  * Merging structure nodes and relationships.")
        session.write_transaction(
            merge_catalogues_and_packages,
            packages_data,
            effective_date,
        )
        session.close()
    print("==  * Merging version independant codelist data.")
    with mdr_neo4j_driver.session(database=mdr_db_name) as session:
        for data in codelists_data:
            # This is split into three separate transactions to reduce ram footprint
            session.write_transaction(
                merge_codelist_version_independent_data,
                data,
            )
            session.write_transaction(
                merge_codelist_packages_version_independent_data, data, effective_date
            )
            session.write_transaction(
                merge_codelist_terms_version_independent_data,
                data,
            )
        session.close()

    with mdr_neo4j_driver.session(database=mdr_db_name) as session:
        print("==  * Updating HAS_TERM and HAD_TERM relationships.")
        added_terms, removed_terms, unchanged_terms = session.write_transaction(
            update_has_term_and_had_term_relationships, codelists_data, effective_date
        )
        print(f"==      Terms added to codelists:     {added_terms:6}")
        print(f"==      Terms removed from codelists: {removed_terms:6}")
        print(f"==      Unchanged terms in codelists: {unchanged_terms:6}")
        session.close()

    with mdr_neo4j_driver.session(database=mdr_db_name) as session:
        print("==  * Updating attributes.")
        summary = session.write_transaction(
            update_attributes, codelists_data, effective_date
        )
        print(f"==      New codelists:       {summary['new_codelists']:6}")
        print(f"==      Updated codelists:   {summary['updated_codelists']:6}")
        print(f"==      Unchanged codelists: {summary['unchanged_codelists']:6}")
        print(f"==      New terms:           {summary['new_terms']:6}")
        print(f"==      Updated terms:       {summary['updated_terms']:6}")
        print(f"==      Unchanged terms:     {summary['unchanged_terms']:6}")

        session.close()

    with mdr_neo4j_driver.session(database=mdr_db_name) as session:
        session.write_transaction(create_user, author_id)    

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"== Duration: {round(elapsed_time, 1)} seconds")
    print("============================================")
