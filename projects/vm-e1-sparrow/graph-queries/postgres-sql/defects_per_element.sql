-- capability: defects_per_element
-- gqc: ../../gqc/defects_per_element.gqc.yaml
-- engine: recursive_sql
-- runtime: Postgres
-- language: relational SQL aggregation
-- renderer: alm_core.queries:defects_per_element / defect_counts_by_element
--
-- Runtime binding facts:
-- - The optional top parameter is applied in Python with DataFrame.head(top), not with SQL LIMIT.
-- - defect_counts_by_element returns id, name, and n_defects dictionaries from this result.

SELECT a.name, a.id, COUNT(e.defect) AS n_defects
FROM architecture_elements a
LEFT JOIN edge_affects e ON e.element = a.id
GROUP BY a.id, a.name
HAVING COUNT(e.defect) > 0
ORDER BY n_defects DESC, a.id

