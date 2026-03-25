# Diagram 2: Lookup-Then-Extract Pattern Flow

```mermaid
%%{init: {'theme':'base', 'themeVariables': { 'primaryColor':'#FEF3BD','primaryTextColor':'#000','primaryBorderColor':'#FF6B6B','lineColor':'#4ECDC4','secondaryColor':'#95E1D3','tertiaryColor':'#F38181'}}}%%

sequenceDiagram
    autonumber
    
    participant User as 👤 User
    participant Claude as 🤖 Claude Sonnet
    participant MCP as 🔌 MCP Server
    participant NCI as 🔍 NCI Terminology API
    participant Validator as ✅ Validator (GPT-5.4)
    
    rect rgb(254, 243, 189)
        Note over User,Claude: Phase 1: Input
        User->>Claude: "Patient's HbA1c is 7.2%"
        Claude->>Claude: Analyze clinical note<br/>Identify: Lab result → Observation
    end
    
    rect rgb(149, 225, 211)
        Note over Claude,MCP: Phase 2: Schema Lookup
        Claude->>MCP: list_resources()
        MCP-->>Claude: [Patient, Observation, Condition, ...]
        
        Claude->>MCP: get_resource_definition("Observation")
        MCP->>MCP: Load 193KB schema<br/>Minify to 7KB
        MCP-->>Claude: Minified schema:<br/>{required: [status, code], fields: {...}}
    end
    
    rect rgb(255, 230, 109)
        Note over Claude,NCI: Phase 3: Terminology Lookup
        Claude->>NCI: search_concept("HbA1c", "loinc")
        NCI-->>Claude: LOINC 4548-4:<br/>"Hemoglobin A1c/Hemoglobin.total in Blood"
    end
    
    rect rgb(149, 225, 211)
        Note over Claude: Phase 4: Generation
        Claude->>Claude: Generate FHIR JSON:<br/>{resourceType: "Observation",<br/> status: "final",<br/> code: {coding: [{<br/>   system: "http://loinc.org",<br/>   code: "4548-4"<br/>}]}, ...}
    end
    
    rect rgb(243, 129, 129)
        Note over Claude,Validator: Phase 5: Validation
        Claude->>Validator: Validate bundle + clinical note
        Validator->>Validator: Check schema compliance<br/>Check source grounding<br/>Check for hallucinations
        Validator-->>Claude: ✅ ACCEPTED<br/>(No errors found)
    end
    
    rect rgb(149, 225, 211)
        Note over Claude,User: Phase 6: Output
        Claude->>User: Valid FHIR Observation resource<br/>Zero hallucinations
    end
```

**Caption:** The Lookup-Then-Extract pattern ensures accuracy by querying specifications before generation. The agent first discovers available resources, retrieves their schemas, looks up standardized terminology codes, then generates FHIR JSON. A separate validator agent provides quality assurance.
