DROP TABLE IF EXISTS theta_plus.imm1985;
CREATE TABLE theta_plus.imm1985
TABLESPACE theta_plus_tbs AS
SELECT sp.scp FROM public.scopus_publications sp
INNER JOIN public.scopus_publication_groups spg
ON sp.scp=spg.sgr
AND spg.pub_year=1985
AND sp.citation_type='ar'
AND sp.citation_language='English'
AND sp.pub_type='core'
INNER JOIN scopus_classes sc
ON sp.scp=sc.scp
AND sc.class_code='2403';
CREATE INDEX imm1985_idx
ON theta_plus.imm1985(scp)
TABLESPACE index_tbs;

DROP TABLE IF EXISTS theta_plus.imm1985_testcase_cited;
DROP TABLE IF EXISTS theta_plus.imm1985_cited;
CREATE TABLE theta_plus.imm1985_cited
TABLESPACE theta_plus_tbs AS
SELECT tp.scp as citing,sr.ref_sgr AS cited
FROM theta_plus.imm1985 tp
INNER JOIN scopus_references sr on tp.scp = sr.scp;
CREATE INDEX imm1985_cited_idx
ON theta_plus.imm1985_cited(citing,cited)
TABLESPACE index_tbs;

DROP TABLE IF EXISTS theta_plus.imm1985_citing;
CREATE TABLE theta_plus.imm1985_citing TABLESPACE theta_plus_tbs AS
SELECT sr.scp as citing,tp.scp as cited FROM theta_plus.imm1985 tp
INNER JOIN scopus_references sr on tp.scp=sr.ref_sgr;
CREATE INDEX imm1985_citing_idx ON theta_plus.imm1985_citing(citing,cited)
TABLESPACE index_tbs;

select count(1) from imm1985;
select count(1) from imm1985_cited;
select count(1) from imm1985_citing;

DROP TABLE IF EXISTS theta_plus.imm1985_citing_cited;
CREATE TABLE theta_plus.imm1985_citing_cited
TABLESPACE theta_plus_tbs AS
SELECT DISTINCT citing,cited from imm1985_cited UNION
SELECT DISTINCT citing,cited from imm1985_citing;
SELECT count(1) from imm1985_citing_cited;

-- clean up Scopus data
DELETE FROM theta_plus.imm1985_citing_cited
WHERE citing=cited;

--remove all non-core publications by joining against
-- scopus publications and requiring type = core
-- and language = English
DROP TABLE IF EXISTS XX;
ALTER TABLE theta_plus.imm1985_citing_cited
RENAME TO XX;

CREATE TABLE theta_plus.imm1985_citing_cited AS
WITH cte AS(SELECT citing,cited FROM XX
INNER JOIN scopus_publications sp
ON XX.citing=sp.scp
AND sp.citation_language='English'
AND sp.pub_type='core')
SELECT citing,cited FROM cte
INNER JOIN scopus_publications sp2
ON cte.cited=sp2.scp
AND sp2.citation_language='English'
AND sp2.pub_type='core';
DROP TABLE XX;

DROP TABLE IF EXISTS theta_plus.imm1985_nodes;
CREATE TABLE theta_plus.imm1985_nodes
TABLESPACE theta_plus_tbs AS
SELECT distinct citing as scp
FROM theta_plus.imm1985_citing_cited
UNION
SELECT distinct cited
FROM theta_plus.imm1985_citing_cited;
CREATE INDEX imm1985_nodes_idx ON theta_plus.imm1985_nodes(scp);

DROP TABLE IF EXISTS theta_plus.imm1985_title_abstracts;
CREATE TABLE theta_plus.imm1985_title_abstracts
TABLESPACE theta_plus_tbs AS
SELECT tpin.scp,st.title,sa.abstract_text
FROM theta_plus.imm1985_nodes tpin
INNER JOIN scopus_titles st ON tpin.scp=st.scp
INNER JOIN scopus_abstracts sa ON tpin.scp=sa.scp
AND sa.abstract_language='eng'
AND st.language='English';

select scp,title from theta_plus.imm1985_title_abstracts limit 5;
select count(1) from theta_plus.imm1985_title_abstracts;

-- Merging with the citation counts table
DROP TABLE IF EXISTS theta_plus.imm1985_citation_counts;
CREATE TABLE theta_plus.imm1985_citation_counts
TABLESPACE theta_plus_tbs AS
SELECT ielu.scp, scc.citation_count, ielu.cluster_no
FROM theta_plus.imm1985_edge_list_unshuffled ielu
LEFT JOIN public.scopus_citation_counts scc
  ON ielu.scp = scc.scp;

