-- # Class: Requirement Description: A binding specification statement, with a DAL.
--     * Slot: id Description: Stable identifier (e.g. REQ-0001, ARC-PROP, TST-0007, DEF-0003).
--     * Slot: title Description: Short human-readable title.
--     * Slot: statement Description: The binding specification text — what shall be achieved.
--     * Slot: acceptance Description: Acceptance criteria that decide whether the requirement is met.
--     * Slot: rationale Description: Why this exists.
--     * Slot: dal Description: Design Assurance Level of a requirement.
--     * Slot: Dataset_id Description: Autocreated FK slot
-- # Class: ArchitectureElement Description: A feature/component in the technical breakdown.
--     * Slot: id Description: Stable identifier (e.g. REQ-0001, ARC-PROP, TST-0007, DEF-0003).
--     * Slot: name Description: Human-readable name.
--     * Slot: kind Description: Coarse kind of an architecture element.
--     * Slot: description Description: Free-text description.
--     * Slot: Dataset_id Description: Autocreated FK slot
-- # Class: TestCase Description: A verification that asserts a requirement, carrying an outcome.
--     * Slot: id Description: Stable identifier (e.g. REQ-0001, ARC-PROP, TST-0007, DEF-0003).
--     * Slot: title Description: Short human-readable title.
--     * Slot: description Description: Free-text description.
--     * Slot: verifies Description: The single requirement this test case verifies (carries an outcome).
--     * Slot: outcome Description: Result carried by a verification relationship.
--     * Slot: Dataset_id Description: Autocreated FK slot
-- # Class: Defect Description: A problem that violates requirement(s) in affected component(s).
--     * Slot: id Description: Stable identifier (e.g. REQ-0001, ARC-PROP, TST-0007, DEF-0003).
--     * Slot: title Description: Short human-readable title.
--     * Slot: description Description: Free-text description.
--     * Slot: severity
--     * Slot: status
--     * Slot: Dataset_id Description: Autocreated FK slot
-- # Class: Dataset Description: Top-level container (used for collection-level validation/generation).
--     * Slot: id
-- # Class: Requirement_refines
--     * Slot: Requirement_id Description: Autocreated FK slot
--     * Slot: refines_id Description: This requirement refines (decomposes) the referenced parent(s); transitive.
-- # Class: Requirement_satisfied_by
--     * Slot: Requirement_id Description: Autocreated FK slot
--     * Slot: satisfied_by_id Description: Inverse allocation — this requirement is satisfied by the referenced architecture element(s). This relation is derived from ArchitectureElement `satisfies` in the authored data.
-- # Class: ArchitectureElement_composed_of
--     * Slot: ArchitectureElement_id Description: Autocreated FK slot
--     * Slot: composed_of_id Description: This element is composed of the referenced sub-element(s); transitive.
-- # Class: ArchitectureElement_satisfies
--     * Slot: ArchitectureElement_id Description: Autocreated FK slot
--     * Slot: satisfies_id Description: Allocation — this architecture element is allocated the referenced requirement(s) (i.e. the requirement is satisfied by this element).
-- # Class: Defect_affects
--     * Slot: Defect_id Description: Autocreated FK slot
--     * Slot: affects_id Description: Architecture element(s) where this defect manifests.
-- # Class: Defect_violates
--     * Slot: Defect_id Description: Autocreated FK slot
--     * Slot: violates_id Description: Requirement(s) this defect violates.

CREATE TABLE "Dataset" (
	id INTEGER NOT NULL,
	PRIMARY KEY (id)
);
CREATE INDEX "ix_Dataset_id" ON "Dataset" (id);

CREATE TABLE "Requirement" (
	id TEXT NOT NULL,
	title TEXT,
	statement TEXT,
	acceptance TEXT,
	rationale TEXT,
	dal VARCHAR(1),
	"Dataset_id" INTEGER,
	PRIMARY KEY (id),
	FOREIGN KEY("Dataset_id") REFERENCES "Dataset" (id)
);
CREATE INDEX "ix_Requirement_id" ON "Requirement" (id);

CREATE TABLE "ArchitectureElement" (
	id TEXT NOT NULL,
	name TEXT,
	kind VARCHAR(9),
	description TEXT,
	"Dataset_id" INTEGER,
	PRIMARY KEY (id),
	FOREIGN KEY("Dataset_id") REFERENCES "Dataset" (id)
);
CREATE INDEX "ix_ArchitectureElement_id" ON "ArchitectureElement" (id);

CREATE TABLE "Defect" (
	id TEXT NOT NULL,
	title TEXT,
	description TEXT,
	severity VARCHAR(8),
	status VARCHAR(11),
	"Dataset_id" INTEGER,
	PRIMARY KEY (id),
	FOREIGN KEY("Dataset_id") REFERENCES "Dataset" (id)
);
CREATE INDEX "ix_Defect_id" ON "Defect" (id);

CREATE TABLE "TestCase" (
	id TEXT NOT NULL,
	title TEXT,
	description TEXT,
	verifies TEXT,
	outcome VARCHAR(7),
	"Dataset_id" INTEGER,
	PRIMARY KEY (id),
	FOREIGN KEY(verifies) REFERENCES "Requirement" (id),
	FOREIGN KEY("Dataset_id") REFERENCES "Dataset" (id)
);
CREATE INDEX "ix_TestCase_id" ON "TestCase" (id);

CREATE TABLE "Requirement_refines" (
	"Requirement_id" TEXT,
	refines_id TEXT,
	PRIMARY KEY ("Requirement_id", refines_id),
	FOREIGN KEY("Requirement_id") REFERENCES "Requirement" (id),
	FOREIGN KEY(refines_id) REFERENCES "Requirement" (id)
);
CREATE INDEX "ix_Requirement_refines_refines_id" ON "Requirement_refines" (refines_id);
CREATE INDEX "ix_Requirement_refines_Requirement_id" ON "Requirement_refines" ("Requirement_id");

CREATE TABLE "Requirement_satisfied_by" (
	"Requirement_id" TEXT,
	satisfied_by_id TEXT,
	PRIMARY KEY ("Requirement_id", satisfied_by_id),
	FOREIGN KEY("Requirement_id") REFERENCES "Requirement" (id),
	FOREIGN KEY(satisfied_by_id) REFERENCES "ArchitectureElement" (id)
);
CREATE INDEX "ix_Requirement_satisfied_by_satisfied_by_id" ON "Requirement_satisfied_by" (satisfied_by_id);
CREATE INDEX "ix_Requirement_satisfied_by_Requirement_id" ON "Requirement_satisfied_by" ("Requirement_id");

CREATE TABLE "ArchitectureElement_composed_of" (
	"ArchitectureElement_id" TEXT,
	composed_of_id TEXT,
	PRIMARY KEY ("ArchitectureElement_id", composed_of_id),
	FOREIGN KEY("ArchitectureElement_id") REFERENCES "ArchitectureElement" (id),
	FOREIGN KEY(composed_of_id) REFERENCES "ArchitectureElement" (id)
);
CREATE INDEX "ix_ArchitectureElement_composed_of_composed_of_id" ON "ArchitectureElement_composed_of" (composed_of_id);
CREATE INDEX "ix_ArchitectureElement_composed_of_ArchitectureElement_id" ON "ArchitectureElement_composed_of" ("ArchitectureElement_id");

CREATE TABLE "ArchitectureElement_satisfies" (
	"ArchitectureElement_id" TEXT,
	satisfies_id TEXT,
	PRIMARY KEY ("ArchitectureElement_id", satisfies_id),
	FOREIGN KEY("ArchitectureElement_id") REFERENCES "ArchitectureElement" (id),
	FOREIGN KEY(satisfies_id) REFERENCES "Requirement" (id)
);
CREATE INDEX "ix_ArchitectureElement_satisfies_satisfies_id" ON "ArchitectureElement_satisfies" (satisfies_id);
CREATE INDEX "ix_ArchitectureElement_satisfies_ArchitectureElement_id" ON "ArchitectureElement_satisfies" ("ArchitectureElement_id");

CREATE TABLE "Defect_affects" (
	"Defect_id" TEXT,
	affects_id TEXT,
	PRIMARY KEY ("Defect_id", affects_id),
	FOREIGN KEY("Defect_id") REFERENCES "Defect" (id),
	FOREIGN KEY(affects_id) REFERENCES "ArchitectureElement" (id)
);
CREATE INDEX "ix_Defect_affects_Defect_id" ON "Defect_affects" ("Defect_id");
CREATE INDEX "ix_Defect_affects_affects_id" ON "Defect_affects" (affects_id);

CREATE TABLE "Defect_violates" (
	"Defect_id" TEXT,
	violates_id TEXT,
	PRIMARY KEY ("Defect_id", violates_id),
	FOREIGN KEY("Defect_id") REFERENCES "Defect" (id),
	FOREIGN KEY(violates_id) REFERENCES "Requirement" (id)
);
CREATE INDEX "ix_Defect_violates_Defect_id" ON "Defect_violates" ("Defect_id");
CREATE INDEX "ix_Defect_violates_violates_id" ON "Defect_violates" (violates_id);
