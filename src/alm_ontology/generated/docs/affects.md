---
search:
  boost: 5.0
---

# Slot: affects 


_Architecture element(s) where this defect manifests._



<div data-search-exclude markdown="1">



URI: [alm:affects](https://vectormind.example/alm-ontology/affects)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Defect](Defect.md) | A problem that violates requirement(s) in affected component(s) |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [ArchitectureElement](ArchitectureElement.md) |
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
| self | alm:affects |
| native | alm:affects |




## LinkML Source

<details>
```yaml
name: affects
description: Architecture element(s) where this defect manifests.
from_schema: https://vectormind.example/alm-ontology
rank: 1000
domain_of:
- Defect
range: ArchitectureElement
multivalued: true

```
</details></div>