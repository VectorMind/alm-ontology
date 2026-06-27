-- capability: impact
-- gqc: ../../gqc/impact.gqc.yaml
-- engine: recursive_sql
-- runtime: Postgres
-- language: SQL with recursive CTE
-- renderer: alm_graph.sql:_impact_recursive
--
-- Parameters, in psycopg placeholder order:
--   1. requirement text
--   2. max_depth integer

WITH RECURSIVE reach(elem, depth) AS (
    SELECT element, 0 FROM edge_satisfied_by WHERE req = %s
    UNION
    SELECT c.child, r.depth + 1
    FROM reach r
    JOIN edge_composed_of c ON c.parent = r.elem
    WHERE r.depth < %s
)
SELECT DISTINCT a.defect AS defect
FROM edge_affects a
JOIN reach r ON a.element = r.elem
ORDER BY defect

