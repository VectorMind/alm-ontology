---
search:
  boost: 2.0
---


# Enum: DALEnum 




_Design Assurance Level (DO-178C / ARP4754A). A is most critical (catastrophic), E is no-effect. Aerospace analogue of automotive ASIL._



<div data-search-exclude markdown="1">

URI: [alm:DALEnum](https://vectormind.example/alm-ontology/DALEnum)

## Permissible Values
| Value | Meaning | Description |
| --- | --- | --- |
| A | None | Catastrophic — failure may cause loss of aircraft/life |
| B | None | Hazardous — large negative safety margin reduction |
| C | None | Major — significant reduction in safety margin |
| D | None | Minor — slight reduction in safety margin |
| E | None | No safety effect |




## Slots

| Name | Description |
| ---  | --- |
| [dal](dal.md) | Design Assurance Level of a requirement |










## Identifier and Mapping Information





### Schema Source


* from schema: https://vectormind.example/alm-ontology






## LinkML Source

<details>
```yaml
name: DALEnum
description: Design Assurance Level (DO-178C / ARP4754A). A is most critical (catastrophic),
  E is no-effect. Aerospace analogue of automotive ASIL.
from_schema: https://vectormind.example/alm-ontology
rank: 1000
permissible_values:
  A:
    text: A
    description: Catastrophic — failure may cause loss of aircraft/life
  B:
    text: B
    description: Hazardous — large negative safety margin reduction
  C:
    text: C
    description: Major — significant reduction in safety margin
  D:
    text: D
    description: Minor — slight reduction in safety margin
  E:
    text: E
    description: No safety effect

```
</details>

</div>