// capability: impact
// gqc: ../../gqc/impact.gqc.yaml
// engine: cypher_age
// runtime: Apache AGE
// language: openCypher subset as accepted by Apache AGE
// renderer: alm_graph.age:_query_impact
//
// Runtime binding facts:
// - The Python renderer JSON-quotes the requirement id and inlines it as a Cypher literal.
// - The Python renderer casts max_depth to int and inlines it into the variable-length path.
// - The query is executed through Postgres as:
//     SELECT * FROM cypher('alm', $cy$ ... $cy$) AS (defect agtype);
// - AGE returns agtype scalars; the renderer parses the returned value back to a Python string.
//
// Template placeholders below mirror the renderer substitutions:
// - {requirement_literal}: JSON-quoted Cypher string, for example "REQ-0110"
// - {max_depth}: integer, for example 6

MATCH (r:Requirement {id: {requirement_literal}})-[:satisfied_by]->(e0:ArchitectureElement)
MATCH (e0)-[:composed_of*0..{max_depth}]->(e:ArchitectureElement)
MATCH (d:Defect)-[:affects]->(e)
RETURN DISTINCT d.id

