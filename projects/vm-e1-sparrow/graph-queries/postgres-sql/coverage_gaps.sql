-- capability: coverage_gaps
-- gqc: ../../gqc/coverage_gaps.gqc.yaml
-- engine: recursive_sql
-- runtime: Postgres
-- language: relational SQL anti-join
-- renderer: alm_core.queries:coverage_gaps / coverage_gap_ids
--
-- Runtime binding facts:
-- - The Python renderer converts min_dal into a concrete DAL list using DAL_SEVERITY.
-- - The concrete DAL literals are inlined into the IN clause before execution.
-- - coverage_gap_ids returns only the id column from this result.
--
-- Template placeholder:
--   {critical_dal_literals}: quoted DAL list, for example 'A' or 'A', 'B'

SELECT
    r.id,
    r.title,
    r.dal,
    COUNT(t.id) AS n_tests,
    COALESCE(STRING_AGG(t.outcome, ', '), '') AS outcomes
FROM requirements r
LEFT JOIN test_cases t ON t.verifies = r.id
WHERE r.dal IN ({critical_dal_literals})
  AND NOT EXISTS (
      SELECT 1 FROM test_cases tp
      WHERE tp.verifies = r.id AND tp.outcome = 'passed'
  )
GROUP BY r.id, r.title, r.dal
ORDER BY r.dal, r.id

