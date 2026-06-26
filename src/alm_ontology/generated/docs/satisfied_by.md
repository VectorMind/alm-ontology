---
search:
  boost: 5.0
---

# Slot: satisfied_by 


_Inverse allocation — this requirement is satisfied by the referenced architecture element(s). This relation is derived from ArchitectureElement `satisfies` in the authored data._



<div data-search-exclude markdown="1">



URI: [alm:satisfied_by](https://vectormind.example/alm-ontology/satisfied_by)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Requirement](Requirement.md) | A binding specification statement, with a DAL |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [ArchitectureElement](ArchitectureElement.md) |
| Domain Of | [Requirement](Requirement.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Multivalued | Yes |
<details>
<summary>Relationship Properties</summary>

| Property | Value |
| --- | --- |
| Inverse | [satisfies](satisfies.md) |

</details>











## Identifier and Mapping Information





### Schema Source


* from schema: https://vectormind.example/alm-ontology




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | alm:satisfied_by |
| native | alm:satisfied_by |




## LinkML Source

<details>
```yaml
name: satisfied_by
description: Inverse allocation — this requirement is satisfied by the referenced
  architecture element(s). This relation is derived from ArchitectureElement `satisfies`
  in the authored data.
from_schema: https://vectormind.example/alm-ontology
rank: 1000
domain_of:
- Requirement
inverse: satisfies
range: ArchitectureElement
multivalued: true

```
</details></div>