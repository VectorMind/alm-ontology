# LinkML Adoption Landscape: Who Is Using It and How

**Research compiled June 2026 — based on peer-reviewed literature, official project documentation, and community sources**

---

## What Is LinkML?

LinkML (Linked Data Modeling Language) is an open-source, YAML-based data modeling framework that brings semantic-web standards to mainstream data engineering. Schemas are authored as human-readable YAML, then automatically compiled into JSON Schema, OWL, SHACL, ShEx, SQL DDL, Python dataclasses, and more. Every element in a LinkML schema automatically gets a globally unique URI, making all schemas FAIR (Findable, Accessible, Interoperable, Reusable) from day one.

The framework originates from the Lawrence Berkeley National Laboratory (LBNL) Biosciences group and has since expanded well beyond life sciences. A landmark 36-author paper — *"LinkML: An Open Data Modeling Framework"* (Moxon et al., *GigaScience*, 2026) — documents its growing community and adoption across biology, chemistry, biomedicine, microbiome research, finance, electrical engineering, transportation, and commercial software.

---

## 1. Biomedical Knowledge Graphs & Retrieval Systems

### 1.1 NCATS Biomedical Data Translator (NIH)

**Organisation:** National Center for Advancing Translational Sciences (NCATS), U.S. NIH  
**Use:** Federated biomedical knowledge graph with reasoning agents

The Translator is one of the most ambitious biomedical knowledge integration efforts in existence. Its semantic backbone is the **Biolink Model** — a comprehensive, ontology-aligned schema that connects biological concepts across diverse domains, built entirely with LinkML. The Biolink Model enables semantic harmonization and reasoning across more than **300 heterogeneous data sources**, including drug databases, genomic data, disease ontologies, and clinical records.

The Translator architecture includes Autonomous Relay Agents (ARAs) and Knowledge Providers (KPs) that all communicate using Biolink as their common language. It is designed to accelerate the path from biomedical hypotheses to clinical trials by enabling multi-hop queries across integrated knowledge graphs — a form of evidence-driven retrieval that predates what we now call GraphRAG.

**Key reference:** Unni et al., *Clinical and Translational Science*, 2022; NCATS Translator Consortium.

---

### 1.2 Monarch Initiative

**Organisation:** Multi-institutional (LBNL, EMBL-EBI, Oregon Health & Science University, and others)  
**Use:** Cross-species phenotype and disease knowledge graph

The Monarch Initiative integrates phenotype, gene, and disease data across species (human, mouse, zebrafish, fly, nematode, etc.) using LinkML-based schemas and the Biolink Model. Its infrastructure powers clinical diagnostic tools such as Exomiser and PhenIX, which use phenotypic similarity algorithms to help identify the genetic cause of rare diseases. In 2024, Monarch was updated to serve as an analytic platform with improved cross-species gene–disease–phenotype reasoning.

---

### 1.3 Alliance of Genome Resources (AGR)

**Organisation:** Coalition of major model organism databases (FlyBase, Mouse Genome Informatics, WormBase, Zebrafish Information Network, Saccharomyces Genome Database, RGD, and others)  
**Use:** Unified schema for model organism genetics and genomics

The AGR uses a LinkML schema to integrate data from multiple model organism databases. Class hierarchies, semantically defined slots, and ontology mappings in LinkML handle complex biological relationships and species-specific constraints. The schema defines how genetic entities — genes, alleles, disease associations, phenotypes, expression data — can be represented consistently across organisms, enabling the web portal, download files, and APIs to work from a single model.

---

### 1.4 RTX-KG2 / ARAX (NCATS Translator Knowledge Provider)

**Organisation:** Oregon State University / NCATS  
**Use:** Automated biomedical reasoning system for drug repositioning

RTX-KG2 is a large, Biolink-standardized knowledge graph serving as the core knowledge base for ARAX, a web-based reasoning system. It integrates sources including UMLS, SemMedDB, ChEMBL, Reactome, and DrugBank. All knowledge is canonicalized to the LinkML-defined Biolink schema, enabling ARAX to answer multi-hop queries such as "What are the mechanisms of action of drug X?" and identify novel drug repositioning candidates. Since Biolink is authored in LinkML, every concept and relation in this system is formally modeled.

---

## 2. Environmental & Earth Science Data Standards

### 2.1 National Microbiome Data Collaborative (NMDC)

**Organisation:** U.S. Department of Energy (DOE), multi-institutional  
**Use:** FAIR microbiome metadata schema and data portal

The NMDC mission is to build a FAIR microbiome data-sharing network across medicine, agriculture, bioenergy, and the environment. Its entire data infrastructure rests on a **LinkML schema** (`nmdc.yaml` and subsidiary schemas) that unifies metadata about studies, biological samples, biogeochemical parameters, omics datasets, and functional predictions.

The schema weaves together existing standards and ontologies — including ENVO (Environment Ontology) terms in enumerations — to standardize how samples and analyses are described, regardless of where they were collected. The resulting NMDC data portal (api.microbiomedata.org) currently holds data for millions of biosamples and studies. The NMDC schema is distributed as a PyPI package, allowing downstream tools to validate and process NMDC data programmatically.

---

### 2.2 iSamples — Internet of Samples (NSF)

**Organisation:** Columbia University, University of Arizona, University of Kansas, Smithsonian NMNH — funded by the U.S. National Science Foundation  
**Use:** Cross-domain cyberinfrastructure for tracking physical samples

iSamples is a standards-based collaboration to uniquely identify material samples from natural science (geoscience, archaeology, biology) and link them persistently to derived data, publications, and other samples. Its **core metadata schema is authored in LinkML** (`iSamplesCoreSchema.yml`), from which JSON Schema and JSON-LD context files are automatically generated for use in REST APIs and semantic-web applications.

As of April 2025, the iSamples repository holds over **6.6 million sample records** spanning SESAR (geoscience), Open Context (archaeology/anthropology), GEOME (genomic observatories), and Smithsonian collections. The LinkML schema defines universal fields (material type, sampled feature, specimen type) while allowing domain-specific extensions — an architectural pattern made clean by LinkML's inheritance model.

---

## 3. Cancer Research & Clinical Data Harmonization

### 3.1 Center for Cancer Data Harmonization (CCDH) — NCI

**Organisation:** National Cancer Institute (NCI), U.S. NIH  
**Use:** Harmonized data model for cancer research

The CCDH uses LinkML to define a unified data model for human patient and cancer sample data, covering demographics, diagnoses, treatments, omics data, and imaging. The schema (`ccdhmodel`) sits at the heart of the NCI Cancer Research Data Commons, enabling interoperability across disparate cancer data repositories (GDC, PDC, IDC, CDS). LinkML's support for inheritance and polymorphism is critical here — cancer data is extraordinarily heterogeneous, with different data types (genomic, proteomic, imaging) requiring both shared and domain-specific representations.

---

### 3.2 NIH INCLUDE Project (Down Syndrome Research)

**Organisation:** U.S. NIH  
**Use:** Data schema for Down syndrome research and harmonization

The INCLUDE (INvestigation of Co-occurring conditions across the Lifespan to Understand Down syndromE) project uses LinkML schemas to standardize data collection and sharing across its research network, enabling multi-site studies on the biomedical complexity of Down syndrome. This allows researchers from different institutions to contribute data that can be compared and pooled.

---

## 4. AI Readiness & Traceability Infrastructure

### 4.1 Bridge2AI — NIH Flagship Program ($130M)

**Organisation:** U.S. National Institutes of Health (NIH), 40+ institutions, 400+ researchers  
**Use:** AI-readiness schemas, Datasheets, and FAIRSCAPE framework

Bridge2AI is a $130 million NIH program to produce AI-ready biomedical datasets for tackling complex clinical and biological challenges. It consists of four Grand Challenges: Cell Maps for AI (CM4AI), Collaborative Hospital Repository Uniting Standards (CHoRUS), Voice as a Biomarker of Health, and AI-READI (diabetes). 

LinkML plays a central role in Bridge2AI's data standards infrastructure:

- **Formal LinkML schemas for Datasheets** — extending the ML Datasheets framework to include AI-readiness and regulatory considerations, with automated validation support.
- **LinkML translators** — converting data between formats to ensure interoperability across Grand Challenges.
- **FAIRSCAPE AI-readiness framework** — built partly on top of LinkML, generating, packaging, evaluating, and managing provenance graphs and explainability metadata for biomedical datasets.

This makes Bridge2AI one of the clearest examples of LinkML being used directly in the service of explainable and auditable AI pipelines.

**Key reference:** Clark et al., *Bridge2AI AI-Readiness Recommendations*, bioRxiv 2024.

---

### 4.2 OntoGPT / SPIRES — LLM-Driven Knowledge Extraction

**Organisation:** Lawrence Berkeley National Laboratory (LBNL)  
**Use:** Zero-shot, schema-grounded knowledge extraction using LLMs

**OntoGPT** implements the **SPIRES** (Structured Prompt Interrogation and Recursive Extraction of Semantics) method, a pipeline for populating knowledge bases and ontologies from unstructured text using LLMs (GPT-4, open models), without requiring training data. **The schema backbone is entirely LinkML**: the user defines a LinkML template describing the target knowledge structure, and OntoGPT instructs the LLM to extract entities and relationships that conform to it, grounding terms against ontologies (e.g., Gene Ontology, ENVO, FOODON).

For example, one application scrapes recipe data and extracts structured representations where each recipe is defined by its ingredients and preparation steps — represented as an OWL class via LinkML-OWL — merged with the FOODON food ontology. This is an early and prominent example of **LLM + structured schema → ontology-grounded knowledge graph** — a pattern that has since become central to GraphRAG and knowledge engineering workflows.

**Key reference:** Caufield et al., *Bioinformatics*, 2024; PMC10924283.

---

## 5. Energy & Industrial Infrastructure

### 5.1 ENTSO-E — European Power Grid (CIM Modeling)

**Organisation:** European Network of Transmission System Operators for Electricity  
**Use:** Power systems data standardization (Common Information Model / IEC 61970)

ENTSO-E, which coordinates electricity transmission across Europe's 39 countries, has adopted LinkML as a tool for working with the **IEC Common Information Model (CIM)** — the international standard for representing power system network models and asset data. Open-source tooling generates LinkML schemas directly from CIM RDF schemas conforming to IEC 61970-501, combining the CIM with the Unified Code for Units of Measure (UCUM).

By expressing CIM in LinkML, power system engineers gain access to the full LinkML toolchain: automatic JSON Schema and Python class generation, data validation, and RDF/OWL mappings — bridging the world of industrial energy standards with modern semantic web and software engineering practices.

---

## 6. Research Data Infrastructure

### 6.1 NFDI — National Research Data Infrastructure (Germany)

**Organisation:** German Research Foundation (DFG), 26 disciplinary consortia  
**Use:** Cross-domain research data standards and interoperability

The NFDI is a major German federal initiative (funded at ~€90M/year) to build a sustainable, FAIR research data ecosystem across all scientific disciplines — from humanities to physics. Several NFDI consortia use LinkML to define common metadata schemas that enable interoperability across the decentralised infrastructure. The initiative's Base4NFDI programme (launched 2023, funded until 2028) explicitly develops shared services including metadata standards, and LinkML is one of the modeling tools used in this context.

---

### 6.2 SSSOM — Simple Standard for Sharing Ontological Mappings

**Organisation:** OBO Foundry community / mapping-commons  
**Use:** Standard for exchanging ontology-to-ontology mappings

SSSOM is a community-driven standard for making ontology mappings (e.g., "MONDO:0005148 = OMIM:222100") machine-readable and reusable. Its entire schema is **managed as a LinkML model**, giving SSSOM automatic multi-format outputs (JSON Schema, ShEx, SHACL, OWL) and Python dataclass/validator generation. This is a prominent example of LinkML being used as the single source of truth for a widely-adopted data exchange standard — changes to the SSSOM schema go through a governed community review process that modifies the underlying LinkML YAML.

---

## 7. Summary Table

| Organisation / Project | Domain | How LinkML Is Used |
|---|---|---|
| NCATS Biomedical Data Translator | Biomedicine / KG | Backbone of Biolink Model; harmonizes 300+ data sources |
| Monarch Initiative | Rare disease / Genomics | Cross-species phenotype-gene-disease knowledge graph |
| Alliance of Genome Resources | Genomics | Unified schema across 7 model organism databases |
| RTX-KG2 / ARAX | Biomedical AI reasoning | Drug repositioning; Biolink-standardized KG |
| NMDC | Environmental science | FAIR microbiome metadata; powers API and portal |
| iSamples (NSF) | Earth & natural sciences | 6.6M+ physical sample records; generates JSON Schema and JSON-LD |
| CCDH / NCI | Cancer research | Data commons harmonization; omics + imaging + clinical |
| NIH INCLUDE | Down syndrome research | Multi-site data harmonization schema |
| NIH Bridge2AI ($130M) | Biomedical AI readiness | Datasheets in LinkML; FAIRSCAPE AI-readiness framework |
| OntoGPT / SPIRES (LBNL) | LLM + knowledge extraction | LLM-driven zero-shot KG population grounded by LinkML schemas |
| ENTSO-E | Power / Energy | CIM (IEC 61970) expressed and validated via LinkML |
| NFDI (Germany) | Cross-domain research | Shared metadata schemas across 26 scientific consortia |
| SSSOM | Ontology interoperability | Entire standard schema managed as a LinkML model |

---

## 8. Observed Patterns of Use

**Schema as a single source of truth.** The dominant pattern is treating LinkML YAML as the master schema definition, then automatically generating all downstream artifacts (JSON Schema, Python classes, OWL, SQL DDL, documentation). This avoids schema drift across formats and teams.

**Knowledge graph interoperability.** Multiple large-scale biomedical knowledge graph projects (Translator, Monarch, AGR) use LinkML-authored schemas — especially Biolink — as the semantic layer that allows data from hundreds of heterogeneous sources to be queried uniformly. This is an operationally deployed form of what graph-RAG research now studies academically.

**AI-readiness and traceability.** Bridge2AI uses LinkML as the formal schema layer for Datasheets and provenance metadata, enabling automated validation of AI-readiness criteria. This addresses EU AI Act-style requirements for documentation and traceability of data used in AI systems.

**LLM-grounded extraction.** OntoGPT demonstrates how a LinkML schema can serve as a prompt-time constraint for LLMs performing information extraction — essentially replacing ad-hoc prompt engineering with a formal, versioned, ontology-backed data model.

**Industrial standards modernisation.** ENTSO-E's use of LinkML to express the IEC CIM illustrates how the framework is migrating legacy industrial data standards into the semantic-web era without requiring a full ontology engineering skillset.

---

## 9. Key Publications

- Moxon SAT et al. **"LinkML: an open data modeling framework."** *GigaScience* 15, giaf152 (2026).
- Moxon S et al. **"The Linked Data Modeling Language (LinkML): A General-Purpose Data Modeling Framework."** CEUR Workshop Proceedings, vol. 3073, pp. 148–151 (2021).
- Unni D et al. **"Biolink Model: A universal schema for knowledge graphs in clinical, biomedical, and translational science."** *Clinical and Translational Science* (2022).
- Caufield JH et al. **"Structured Prompt Interrogation and Recursive Extraction of Semantics (SPIRES)."** *Bioinformatics* (2024). PMC10924283.
- Matentzoglu N et al. **"A Simple Standard for Sharing Ontological Mappings (SSSOM)."** *Database (Oxford)* (2022).
- Clark T et al. **"AI-readiness for Biomedical Data: Bridge2AI Recommendations."** *bioRxiv* (2024). DOI: 10.1101/2024.10.23.619844.

---

*Compiled from: LinkML.io, ArXiv 2511.16935, GigaScience giaf152, PubMed, bioRxiv, GitHub repositories, and official project pages.*
