---
search:
  boost: 5.0
---

# Slot: defects 

<div data-search-exclude markdown="1">



URI: [alm:defects](https://vectormind.example/alm-ontology/defects)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Dataset](Dataset.md) | Top-level container (used for collection-level validation/generation) |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Defect](Defect.md) |
| Domain Of | [Dataset](Dataset.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Multivalued | Yes |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [Dataset](Dataset.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://vectormind.example/alm-ontology




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | alm:defects |
| native | alm:defects |




## LinkML Source

<details>
```yaml
name: defects
from_schema: https://vectormind.example/alm-ontology
rank: 1000
owner: Dataset
domain_of:
- Dataset
range: Defect
multivalued: true
inlined: true
inlined_as_list: true

```
</details></div>