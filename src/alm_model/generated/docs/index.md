# ALM Ontology (VM-E1 example slice)

LinkML model (Layer 0, the spine) for the ALM ontology POC. Defines the entity types, controlled vocabularies (DAL), and permitted relationships for the fictional VM-E1 'Sparrow' single-seat electric aircraft. This single artifact is the source of truth from which Pydantic types, SQL DDL, and documentation are generated. FULLY AI-GENERATED DUMMY MODEL — not for real-world use.

URI: https://vectormind.example/alm-ontology

Name: alm-ontology



## Classes

| Class | Description |
| --- | --- |
| [ArchitectureElement](ArchitectureElement.md) | A feature/component in the technical breakdown |
| [Dataset](Dataset.md) | Top-level container (used for collection-level validation/generation) |
| [Defect](Defect.md) | A problem that violates requirement(s) in affected component(s) |
| [Requirement](Requirement.md) | A binding specification statement, with a DAL |
| [TestCase](TestCase.md) | A verification that asserts a requirement, carrying an outcome |



## Slots

| Slot | Description |
| --- | --- |
| [acceptance](acceptance.md) | Acceptance criteria that decide whether the requirement is met |
| [affects](affects.md) | Architecture element(s) where this defect manifests |
| [architecture_elements](architecture_elements.md) |  |
| [composed_of](composed_of.md) | This element is composed of the referenced sub-element(s); transitive |
| [dal](dal.md) | Design Assurance Level of a requirement |
| [defects](defects.md) |  |
| [description](description.md) | Free-text description |
| [id](id.md) | Stable identifier (e |
| [kind](kind.md) | Coarse kind of an architecture element |
| [name](name.md) | Human-readable name |
| [outcome](outcome.md) | Result carried by a verification relationship |
| [rationale](rationale.md) | Why this exists |
| [refines](refines.md) | This requirement refines (decomposes) the referenced parent(s); transitive |
| [requirements](requirements.md) |  |
| [satisfied_by](satisfied_by.md) | Inverse allocation — this requirement is satisfied by the referenced architec... |
| [satisfies](satisfies.md) | Allocation — this architecture element is allocated the referenced requiremen... |
| [severity](severity.md) |  |
| [statement](statement.md) | The binding specification text — what shall be achieved |
| [status](status.md) |  |
| [test_cases](test_cases.md) |  |
| [title](title.md) | Short human-readable title |
| [verifies](verifies.md) | The single requirement this test case verifies (carries an outcome) |
| [violates](violates.md) | Requirement(s) this defect violates |


## Enumerations

| Enumeration | Description |
| --- | --- |
| [DALEnum](DALEnum.md) | Design Assurance Level (DO-178C / ARP4754A) |
| [DefectStatusEnum](DefectStatusEnum.md) | Defect lifecycle status |
| [ElementKindEnum](ElementKindEnum.md) | Coarse kind of an architecture element |
| [OutcomeEnum](OutcomeEnum.md) | Outcome carried by a verification (test -> requirement) relationship |
| [SeverityEnum](SeverityEnum.md) | Defect severity |


## Types

| Type | Description |
| --- | --- |


## Subsets

| Subset | Description |
| --- | --- |
