---
search:
  boost: 5.0
---

# Slot: title 


_Short human-readable title._



<div data-search-exclude markdown="1">



URI: [alm:title](https://vectormind.example/alm-ontology/title)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Requirement](Requirement.md) | A binding specification statement, with a DAL |  no  |
| [TestCase](TestCase.md) | A verification that asserts a requirement, carrying an outcome |  no  |
| [Defect](Defect.md) | A problem that violates requirement(s) in affected component(s) |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [xsd:string](http://www.w3.org/2001/XMLSchema#string) |
| Domain Of | [Requirement](Requirement.md), [TestCase](TestCase.md), [Defect](Defect.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |










## Identifier and Mapping Information



### Annotations

| property | value |
| --- | --- |
| searchable | True |
| embeddable | True |




### Schema Source


* from schema: https://vectormind.example/alm-ontology




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | alm:title |
| native | alm:title |




## LinkML Source

<details>
```yaml
name: title
annotations:
  searchable:
    tag: searchable
    value: true
  embeddable:
    tag: embeddable
    value: true
description: Short human-readable title.
from_schema: https://vectormind.example/alm-ontology
rank: 1000
domain_of:
- Requirement
- TestCase
- Defect
range: string

```
</details></div>