set search_path=':';
\set ON_ERROR_STOP on
\set ECHO all

-- DataGrip: start execution from here
SET TIMEZONE = 'US/Eastern';

create procedure stg_scopus_merge_publication_identifiers()
    language plpgsql
as
$$
BEGIN
INSERT INTO scopus_publication_identifiers(scp, document_id, document_id_type)
SELECT
FROM stg_scopus_publication_identifiers
ON CONFLICT (scp, document_id, document_id_type) DO UPDATE SET document_id=excluded.document_id,
                                                               document_id_type=excluded.document_id_type;
END
$$;