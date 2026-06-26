---
search:
  boost: 5.0
---

# Slot: acceptance 


_Acceptance criteria that decide whether the requirement is met._



<div data-search-exclude markdown="1">



URI: [alm:acceptance](https://vectormind.example/alm-ontology/acceptance)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Requirement](Requirement.md) | A binding specification statement, with a DAL |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [xsd:string](http://www.w3.org/2001/XMLSchema#string) |
| Domain Of | [Requirement](Requirement.md) |

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
| self | alm:acceptance |
| native | alm:acceptance |




## LinkML Source

<details>
```yaml
name: acceptance
annotations:
  searchable:
    tag: searchable
    value: true
  embeddable:
    tag: embeddable
    value: true
description: Acceptance criteria that decide whether the requirement is met.
from_schema: https://vectormind.example/alm-ontology
rank: 1000
domain_of:
- Requirement
range: string

```
</details></div>