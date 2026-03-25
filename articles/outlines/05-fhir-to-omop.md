# Article 5: FHIR to OMOP CDM - Building a Bidirectional Healthcare Data Bridge

## Metadata
- **Target Length:** 4000-4500 words
- **Technical Level:** Advanced
- **Key Technologies:** FHIR, OMOP CDM, OHDSI, Vocabulary mapping
- **System Expansion:** New `omop-converter/` module

## Hook
"Your hospital has FHIR data. Your research team needs OMOP. They speak different languages. Time to build a translator."

**The problem:**
- EHRs use FHIR (HL7 standard)
- Research uses OMOP CDM (OHDSI standard)
- Manual conversion is error-prone and slow
- Vocabulary mapping is complex (SNOMED → OMOP concept_id)

**The promise:**
"What if you could extract from clinical notes directly into OMOP format—or convert existing FHIR to research-ready datasets with one command?"

## Outline

### Section 1: FHIR vs OMOP - Two Worlds (800 words)
- FHIR: Clinical interoperability, real-time, resource-oriented
- OMOP: Research analytics, retrospective, table-oriented
- Why both exist and why we need bridges
- Real use case: COVID-19 research across 200M patient records

### Section 2: The OMOP Common Data Model (700 words)
- Core tables: Person, Observation_Period, Condition_Occurrence, Drug_Exposure, etc.
- Standardized vocabularies (SNOMED, LOINC, RxNorm → concept_id)
- Why OMOP is optimized for analytics (star schema, denormalized)

### Section 3: Vocabulary Mapping - The Hard Part (1000 words)
- SNOMED CT code → OMOP concept_id lookup
- LOINC → OMOP measurement concepts
- RxNorm → OMOP drug concepts
- Using OHDSI Athena vocabulary tables
- Handling unmapped codes (standard_concept = 'S')

### Section 4: Building the FHIR → OMOP Converter (1200 words)
**Architecture:**
```python
class OMOPConverter:
    def convert_bundle(self, fhir_bundle: list) -> OMOPDataset:
        """Converts FHIR Bundle → OMOP CDM tables"""

        omop_data = {
            "person": [],
            "condition_occurrence": [],
            "drug_exposure": [],
            "measurement": [],
            "observation": [],
        }

        for resource in fhir_bundle:
            if resource["resourceType"] == "Patient":
                omop_data["person"].append(self.convert_patient(resource))
            elif resource["resourceType"] == "Condition":
                omop_data["condition_occurrence"].append(self.convert_condition(resource))
            # ...

        return OMOPDataset(**omop_data)
```

**Key conversions:**
- Patient → Person
- Condition → Condition_Occurrence
- Observation (lab) → Measurement
- MedicationRequest → Drug_Exposure
- Procedure → Procedure_Occurrence

### Section 5: Bidirectional Conversion - OMOP → FHIR (600 words)
- Why you'd want to go backwards (research findings → clinical action)
- Challenges (OMOP is lossy, FHIR is lossier)
- Practical limitations

### Section 6: Agentic OMOP Extraction (500 words)
- Can we extract *directly* to OMOP from clinical notes?
- Agent prompt modifications
- Vocabulary lookup integration
- Performance comparison (FHIR-then-convert vs direct)

### Conclusion (300 words)
- Bridging clinical and research standards
- Impact: Faster research, better patient outcomes
- What's next: USDM for clinical trials

## Code Components to Build
1. `OMOPConverter` class
2. Vocabulary mapping service (Athena integration)
3. OMOP table Pydantic models
4. Concept ID lookup cache
5. Validation for OMOP CDM constraints

## Data Examples
- Real FHIR bundle → OMOP tables (side-by-side)
- Vocabulary mapping table (SNOMED code → concept_id)
- OMOP dataset ready for analysis (SQL queries)

## Diagrams
1. FHIR vs OMOP comparison (resource vs table structure)
2. Conversion pipeline architecture
3. Vocabulary mapping flow
4. OHDSI ecosystem diagram
