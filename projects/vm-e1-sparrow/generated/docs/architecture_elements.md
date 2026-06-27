---
search:
  boost: 5.0
---

# Slot: architecture_elements 

<div data-search-exclude markdown="1">



URI: [alm:architecture_elements](https://vectormind.example/alm-ontology/architecture_elements)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Dataset](Dataset.md) | Top-level container (used for collection-level validation/generation) |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [ArchitectureElement](ArchitectureElement.md) |
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
| self | alm:architecture_elements |
| native | alm:architecture_elements |




## LinkML Source

<details>
```yaml
name: architecture_elements
from_schema: https://vectormind.example/alm-ontology
rank: 1000
owner: Dataset
domain_of:
- Dataset
range: ArchitectureElement
multivalued: true
inlined: true
inlined_as_list: true

```
</details></div>