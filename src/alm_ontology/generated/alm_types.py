from __future__ import annotations

import re
import sys
from datetime import (
    date,
    datetime,
    time
)
from decimal import Decimal
from enum import Enum
from typing import (
    Any,
    ClassVar,
    Literal,
    Optional,
    Union
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer
)


metamodel_version = "1.11.0"
version = "None"


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        serialize_by_alias = True,
        validate_by_name = True,
        validate_assignment = True,
        validate_default = True,
        extra = "forbid",
        arbitrary_types_allowed = True,
        use_enum_values = True,
        strict = False,
    )





class LinkMLMeta(RootModel):
    root: dict[str, Any] = {}
    model_config = ConfigDict(frozen=True)

    def __getattr__(self, key:str):
        return getattr(self.root, key)

    def __getitem__(self, key:str):
        return self.root[key]

    def __setitem__(self, key:str, value):
        self.root[key] = value

    def __contains__(self, key:str) -> bool:
        return key in self.root


linkml_meta = LinkMLMeta({'default_prefix': 'alm',
     'default_range': 'string',
     'description': 'LinkML model (Layer 0, the spine) for the ALM ontology POC. '
                    'Defines the entity types, controlled vocabularies (DAL), and '
                    "permitted relationships for the fictional VM-E1 'Sparrow' "
                    'single-seat electric aircraft. This single artifact is the '
                    'source of truth from which Pydantic types, SQL DDL, and '
                    'documentation are generated. FULLY AI-GENERATED DUMMY MODEL — '
                    'not for real-world use.',
     'id': 'https://vectormind.example/alm-ontology',
     'imports': ['linkml:types'],
     'license': 'MIT',
     'name': 'alm-ontology',
     'prefixes': {'alm': {'prefix_prefix': 'alm',
                          'prefix_reference': 'https://vectormind.example/alm-ontology/'},
                  'linkml': {'prefix_prefix': 'linkml',
                             'prefix_reference': 'https://w3id.org/linkml/'}},
     'source_file': 'C:\\dev\\VectorMind\\alm-ontology\\src\\alm_ontology\\model\\alm.yaml',
     'title': 'ALM Ontology (VM-E1 example slice)'} )

class DALEnum(str, Enum):
    """
    Design Assurance Level (DO-178C / ARP4754A). A is most critical (catastrophic), E is no-effect. Aerospace analogue of automotive ASIL.
    """
    A = "A"
    """
    Catastrophic — failure may cause loss of aircraft/life
    """
    B = "B"
    """
    Hazardous — large negative safety margin reduction
    """
    C = "C"
    """
    Major — significant reduction in safety margin
    """
    D = "D"
    """
    Minor — slight reduction in safety margin
    """
    E = "E"
    """
    No safety effect
    """


class OutcomeEnum(str, Enum):
    """
    Outcome carried by a verification (test -> requirement) relationship.
    """
    passed = "passed"
    failed = "failed"
    not_run = "not_run"


class SeverityEnum(str, Enum):
    """
    Defect severity.
    """
    critical = "critical"
    major = "major"
    minor = "minor"


class DefectStatusEnum(str, Enum):
    """
    Defect lifecycle status.
    """
    open = "open"
    in_analysis = "in_analysis"
    fixed = "fixed"
    closed = "closed"


class ElementKindEnum(str, Enum):
    """
    Coarse kind of an architecture element.
    """
    system = "system"
    subsystem = "subsystem"
    component = "component"



class Requirement(ConfiguredBaseModel):
    """
    A binding specification statement, with a DAL.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://vectormind.example/alm-ontology'})

    id: str = Field(default=..., description="""Stable identifier (e.g. REQ-0001, ARC-PROP, TST-0007, DEF-0003).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Requirement', 'ArchitectureElement', 'TestCase', 'Defect']} })
    title: Optional[str] = Field(default=None, description="""Short human-readable title.""", json_schema_extra = { "linkml_meta": {'annotations': {'embeddable': {'tag': 'embeddable', 'value': True},
                         'searchable': {'tag': 'searchable', 'value': True}},
         'domain_of': ['Requirement', 'TestCase', 'Defect']} })
    statement: Optional[str] = Field(default=None, description="""The binding specification text — what shall be achieved.""", json_schema_extra = { "linkml_meta": {'annotations': {'embeddable': {'tag': 'embeddable', 'value': True},
                         'searchable': {'tag': 'searchable', 'value': True}},
         'domain_of': ['Requirement']} })
    acceptance: Optional[str] = Field(default=None, description="""Acceptance criteria that decide whether the requirement is met.""", json_schema_extra = { "linkml_meta": {'annotations': {'embeddable': {'tag': 'embeddable', 'value': True},
                         'searchable': {'tag': 'searchable', 'value': True}},
         'domain_of': ['Requirement']} })
    rationale: Optional[str] = Field(default=None, description="""Why this exists.""", json_schema_extra = { "linkml_meta": {'annotations': {'embeddable': {'tag': 'embeddable', 'value': True},
                         'searchable': {'tag': 'searchable', 'value': True}},
         'domain_of': ['Requirement']} })
    dal: Optional[DALEnum] = Field(default=None, description="""Design Assurance Level of a requirement.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Requirement']} })
    refines: Optional[list[str]] = Field(default=None, description="""This requirement refines (decomposes) the referenced parent(s); transitive.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Requirement']} })
    satisfied_by: Optional[list[str]] = Field(default=None, description="""Inverse allocation — this requirement is satisfied by the referenced architecture element(s). This relation is derived from ArchitectureElement `satisfies` in the authored data.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Requirement'], 'inverse': 'satisfies'} })


class ArchitectureElement(ConfiguredBaseModel):
    """
    A feature/component in the technical breakdown.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://vectormind.example/alm-ontology'})

    id: str = Field(default=..., description="""Stable identifier (e.g. REQ-0001, ARC-PROP, TST-0007, DEF-0003).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Requirement', 'ArchitectureElement', 'TestCase', 'Defect']} })
    name: Optional[str] = Field(default=None, description="""Human-readable name.""", json_schema_extra = { "linkml_meta": {'annotations': {'embeddable': {'tag': 'embeddable', 'value': True},
                         'searchable': {'tag': 'searchable', 'value': True}},
         'domain_of': ['ArchitectureElement']} })
    kind: Optional[ElementKindEnum] = Field(default=None, description="""Coarse kind of an architecture element.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ArchitectureElement']} })
    description: Optional[str] = Field(default=None, description="""Free-text description.""", json_schema_extra = { "linkml_meta": {'annotations': {'embeddable': {'tag': 'embeddable', 'value': True},
                         'searchable': {'tag': 'searchable', 'value': True}},
         'domain_of': ['ArchitectureElement', 'TestCase', 'Defect']} })
    composed_of: Optional[list[str]] = Field(default=None, description="""This element is composed of the referenced sub-element(s); transitive.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ArchitectureElement']} })
    satisfies: Optional[list[str]] = Field(default=None, description="""Allocation — this architecture element is allocated the referenced requirement(s) (i.e. the requirement is satisfied by this element).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ArchitectureElement'], 'inverse': 'satisfied_by'} })


class TestCase(ConfiguredBaseModel):
    """
    A verification that asserts a requirement, carrying an outcome.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://vectormind.example/alm-ontology'})

    id: str = Field(default=..., description="""Stable identifier (e.g. REQ-0001, ARC-PROP, TST-0007, DEF-0003).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Requirement', 'ArchitectureElement', 'TestCase', 'Defect']} })
    title: Optional[str] = Field(default=None, description="""Short human-readable title.""", json_schema_extra = { "linkml_meta": {'annotations': {'embeddable': {'tag': 'embeddable', 'value': True},
                         'searchable': {'tag': 'searchable', 'value': True}},
         'domain_of': ['Requirement', 'TestCase', 'Defect']} })
    description: Optional[str] = Field(default=None, description="""Free-text description.""", json_schema_extra = { "linkml_meta": {'annotations': {'embeddable': {'tag': 'embeddable', 'value': True},
                         'searchable': {'tag': 'searchable', 'value': True}},
         'domain_of': ['ArchitectureElement', 'TestCase', 'Defect']} })
    verifies: Optional[str] = Field(default=None, description="""The single requirement this test case verifies (carries an outcome).""", json_schema_extra = { "linkml_meta": {'domain_of': ['TestCase']} })
    outcome: Optional[OutcomeEnum] = Field(default=None, description="""Result carried by a verification relationship.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TestCase']} })


class Defect(ConfiguredBaseModel):
    """
    A problem that violates requirement(s) in affected component(s).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://vectormind.example/alm-ontology'})

    id: str = Field(default=..., description="""Stable identifier (e.g. REQ-0001, ARC-PROP, TST-0007, DEF-0003).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Requirement', 'ArchitectureElement', 'TestCase', 'Defect']} })
    title: Optional[str] = Field(default=None, description="""Short human-readable title.""", json_schema_extra = { "linkml_meta": {'annotations': {'embeddable': {'tag': 'embeddable', 'value': True},
                         'searchable': {'tag': 'searchable', 'value': True}},
         'domain_of': ['Requirement', 'TestCase', 'Defect']} })
    description: Optional[str] = Field(default=None, description="""Free-text description.""", json_schema_extra = { "linkml_meta": {'annotations': {'embeddable': {'tag': 'embeddable', 'value': True},
                         'searchable': {'tag': 'searchable', 'value': True}},
         'domain_of': ['ArchitectureElement', 'TestCase', 'Defect']} })
    severity: Optional[SeverityEnum] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Defect']} })
    status: Optional[DefectStatusEnum] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Defect']} })
    affects: Optional[list[str]] = Field(default=None, description="""Architecture element(s) where this defect manifests.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Defect']} })
    violates: Optional[list[str]] = Field(default=None, description="""Requirement(s) this defect violates.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Defect']} })


class Dataset(ConfiguredBaseModel):
    """
    Top-level container (used for collection-level validation/generation).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://vectormind.example/alm-ontology', 'tree_root': True})

    requirements: Optional[list[Requirement]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Dataset']} })
    architecture_elements: Optional[list[ArchitectureElement]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Dataset']} })
    test_cases: Optional[list[TestCase]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Dataset']} })
    defects: Optional[list[Defect]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Dataset']} })


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
Requirement.model_rebuild()
ArchitectureElement.model_rebuild()
TestCase.model_rebuild()
Defect.model_rebuild()
Dataset.model_rebuild()
