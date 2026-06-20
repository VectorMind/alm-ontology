---
search:
  boost: 5.0
---

# Slot: violates 


_Requirement(s) this defect violates._



<div data-search-exclude markdown="1">



URI: [alm:violates](https://vectormind.example/alm-ontology/violates)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Defect](Defect.md) | A problem that violates requirement(s) in affected component(s) |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Requirement](Requirement.md) |
| Domain Of | [Defect](Defect.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Multivalued | Yes |










## Identifier and Mapping Information





### Schema Source


* from schema: https://vectormind.example/alm-ontology




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | alm:violates |
| native | alm:violates |




## LinkML Source

<details>
```yaml
name: violates
description: Requirement(s) this defect violates.
from_schema: https://vectormind.example/alm-ontology
rank: 1000
domain_of:
- Defect
range: Requirement
multivalued: true

```
</details></div>