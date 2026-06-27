---
search:
  boost: 5.0
---

# Slot: requirements 

<div data-search-exclude markdown="1">



URI: [alm:requirements](https://vectormind.example/alm-ontology/requirements)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Dataset](Dataset.md) | Top-level container (used for collection-level validation/generation) |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Requirement](Requirement.md) |
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
| self | alm:requirements |
| native | alm:requirements |




## LinkML Source

<details>
```yaml
name: requirements
from_schema: https://vectormind.example/alm-ontology
rank: 1000
owner: Dataset
domain_of:
- Dataset
range: Requirement
multivalued: true
inlined: true
inlined_as_list: true

```
</details></div>