---
search:
  boost: 5.0
---

# Slot: satisfies 


_Allocation — this architecture element is allocated the referenced requirement(s) (i.e. the requirement is satisfied by this element)._



<div data-search-exclude markdown="1">



URI: [alm:satisfies](https://vectormind.example/alm-ontology/satisfies)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ArchitectureElement](ArchitectureElement.md) | A feature/component in the technical breakdown |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Requirement](Requirement.md) |
| Domain Of | [ArchitectureElement](ArchitectureElement.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Multivalued | Yes |
<details>
<summary>Relationship Properties</summary>

| Property | Value |
| --- | --- |
| Inverse | [satisfied_by](satisfied_by.md) |

</details>











## Identifier and Mapping Information





### Schema Source


* from schema: https://vectormind.example/alm-ontology




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | alm:satisfies |
| native | alm:satisfies |




## LinkML Source

<details>
```yaml
name: satisfies
description: Allocation — this architecture element is allocated the referenced requirement(s)
  (i.e. the requirement is satisfied by this element).
from_schema: https://vectormind.example/alm-ontology
rank: 1000
domain_of:
- ArchitectureElement
inverse: satisfied_by
range: Requirement
multivalued: true

```
</details></div>