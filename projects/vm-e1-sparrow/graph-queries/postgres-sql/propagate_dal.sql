-- capability: propagate_dal
-- gqc: ../../gqc/propagate_dal.gqc.yaml
-- engine: recursive_sql
-- runtime: Postgres
-- language: SQL with recursive CTE plus Python reduction
-- renderer: alm_graph.sql:propagate_dal
--
-- Runtime binding facts:
-- - This SQL returns all candidate DAL assignments per architecture element.
-- - The Python renderer reduces those rows to the strongest effective DAL per element with
--   alm_core.queries:dal_severity, then sorts by element id.
-- - Therefore this file is not the complete final-result query by itself; it is the lower-layer
--   SQL currently used by the renderer.

WITH RECURSIVE reach(element, dal) AS (
    SELECT s.element, r.dal
    FROM edge_satisfied_by s
    JOIN requirements r ON r.id = s.req
    UNION
    SELECT c.child, reach.dal
    FROM reach
    JOIN edge_composed_of c ON c.parent = reach.element
)
SELECT a.id, reach.dal
FROM architecture_elements a
LEFT JOIN reach ON reach.element = a.id
ORDER BY a.id

