---
search:
  boost: 5.0
---

# Slot: severity 

<div data-search-exclude markdown="1">



URI: [alm:severity](https://vectormind.example/alm-ontology/severity)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Defect](Defect.md) | A problem that violates requirement(s) in affected component(s) |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [SeverityEnum](SeverityEnum.md) |
| Domain Of | [Defect](Defect.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |










## Identifier and Mapping Information





### Schema Source


* from schema: https://vectormind.example/alm-ontology




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | alm:severity |
| native | alm:severity |




## LinkML Source

<details>
```yaml
name: severity
from_schema: https://vectormind.example/alm-ontology
rank: 1000
domain_of:
- Defect
range: SeverityEnum

```
</details></div>