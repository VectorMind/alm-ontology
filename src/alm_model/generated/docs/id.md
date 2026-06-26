---
search:
  boost: 5.0
---

# Slot: id 


_Stable identifier (e.g. REQ-0001, ARC-PROP, TST-0007, DEF-0003)._



<div data-search-exclude markdown="1">



URI: [alm:id](https://vectormind.example/alm-ontology/id)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Requirement](Requirement.md) | A binding specification statement, with a DAL |  no  |
| [ArchitectureElement](ArchitectureElement.md) | A feature/component in the technical breakdown |  no  |
| [TestCase](TestCase.md) | A verification that asserts a requirement, carrying an outcome |  no  |
| [Defect](Defect.md) | A problem that violates requirement(s) in affected component(s) |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [xsd:string](http://www.w3.org/2001/XMLSchema#string) |
| Domain Of | [Requirement](Requirement.md), [ArchitectureElement](ArchitectureElement.md), [TestCase](TestCase.md), [Defect](Defect.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Required | Yes |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Identifier | Yes |












## Identifier and Mapping Information





### Schema Source


* from schema: https://vectormind.example/alm-ontology




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | alm:id |
| native | alm:id |




## LinkML Source

<details>
```yaml
name: id
description: Stable identifier (e.g. REQ-0001, ARC-PROP, TST-0007, DEF-0003).
from_schema: https://vectormind.example/alm-ontology
rank: 1000
identifier: true
domain_of:
- Requirement
- ArchitectureElement
- TestCase
- Defect
range: string
required: true

```
</details></div>