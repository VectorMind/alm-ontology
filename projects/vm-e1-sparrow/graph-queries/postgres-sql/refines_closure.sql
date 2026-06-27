-- capability: refines_closure
-- gqc: ../../gqc/refines_closure.gqc.yaml
-- engine: recursive_sql
-- runtime: Postgres
-- language: SQL with recursive CTE
-- renderer: alm_graph.sql:refines_closure
--
-- Parameters, in psycopg placeholder order:
--   1. requirement text
--   2. max_depth integer

WITH RECURSIVE closure(req, depth) AS (
    SELECT dst, 1 FROM edge_refines WHERE src = %s
    UNION
    SELECT e.dst, c.depth + 1
    FROM closure c
    JOIN edge_refines e ON e.src = c.req
    WHERE c.depth < %s
)
SELECT req AS id, MIN(depth) AS depth
FROM closure
GROUP BY req
ORDER BY depth, id

