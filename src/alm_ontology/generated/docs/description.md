---
search:
  boost: 5.0
---

# Slot: description 


_Free-text description._



<div data-search-exclude markdown="1">



URI: [alm:description](https://vectormind.example/alm-ontology/description)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ArchitectureElement](ArchitectureElement.md) | A feature/component in the technical breakdown |  no  |
| [TestCase](TestCase.md) | A verification that asserts a requirement, carrying an outcome |  no  |
| [Defect](Defect.md) | A problem that violates requirement(s) in affected component(s) |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [xsd:string](http://www.w3.org/2001/XMLSchema#string) |
| Domain Of | [ArchitectureElement](ArchitectureElement.md), [TestCase](TestCase.md), [Defect](Defect.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |










## Identifier and Mapping Information





### Schema Source


* from schema: https://vectormind.example/alm-ontology




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | alm:description |
| native | alm:description |




## LinkML Source

<details>
```yaml
name: description
description: Free-text description.
from_schema: https://vectormind.example/alm-ontology
rank: 1000
domain_of:
- ArchitectureElement
- TestCase
- Defect
range: string

```
</details></div>