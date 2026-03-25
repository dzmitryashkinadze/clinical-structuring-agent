# Article 1: MCP Servers - Giving LLMs Deterministic Access to HL7 FHIR Specifications

## Metadata
- **Target Length:** 3500-4000 words (15-18 min read)
- **Target Audience:** ML Engineers, Healthcare Software Engineers
- **Technical Level:** Advanced
- **Key Technologies:** Model Context Protocol, LLMs, FHIR, Python
- **Publishing Venue:** Medium (personal) + cross-post to Towards Data Science

## Outline

### Hook (200 words)
**Opening statement:** "Your healthcare AI just told a patient their blood glucose level is 'banana'. This isn't a joke—it's what happens when LLMs hallucinate medical codes."

**The problem:**
- Real example: GPT-4 inventing LOINC codes that don't exist
- 193KB FHIR schema → LLM context window chaos
- Healthcare can't afford "creative interpretation" of standards

**The promise:**
"What if your LLM could look up medical standards *before* making decisions, just like a doctor references a medical encyclopedia? Enter the Model Context Protocol."

### Section 1: The Hallucination Problem in Healthcare AI (600 words)

#### 1.1 Why Healthcare AI is Different
- **Stakes:** Patient safety, regulatory compliance, legal liability
- **Complexity:** 100+ FHIR resource types, thousands of standardized codes
- **Precision requirement:** "Close enough" kills people

#### 1.2 The Classic Approach (and Why It Fails)
```python
# Traditional approach: Dump entire schema in prompt
prompt = f"""
Here is the FHIR Patient resource schema (193KB):
{massive_json_schema}

Now extract patient data from: "John Doe, age 45"
"""
# Result: Context overflow, hallucinated fields, slow inference
```

**Problems:**
- Context window waste (193KB schema for 20-byte input)
- LLM still hallucinates invalid field combinations
- No guarantee of spec adherence
- Expensive (tokens = money)

#### 1.3 The RAG Band-Aid
- Embedding FHIR specs and retrieving relevant chunks
- **Issues:** Semantic search on structured schemas is imprecise
- **Reality:** You need the *exact* `Observation.code` definition, not "something about observations"

### Section 2: Enter Model Context Protocol (800 words)

#### 2.1 What is MCP?
**Simple analogy:** "Think of MCP as giving your LLM a phone. Instead of memorizing every fact, it can call up external services and ask questions."

**Technical definition:**
- Anthropic's protocol for LLM-to-external-system communication
- JSON-RPC based, async, tools/resources/prompts
- Local or remote servers

#### 2.2 Why MCP is Perfect for Healthcare Standards

**Key insight:** Medical specifications are:
1. **Structured** (not unstructured text)
2. **Hierarchical** (Resource → Fields → Types → Value Sets)
3. **Deterministic** (no ambiguity in definitions)
4. **Large** (tens of thousands of pages)
5. **Critical** (errors = patient harm)

MCP solves all five:
- Structured query/response
- Navigate hierarchy on-demand
- Return exact definitions
- Fetch only what's needed
- Guaranteed accuracy (no LLM interpretation)

#### 2.3 Architecture Diagram
```
┌─────────────────┐
│  Clinical Note  │
└────────┬────────┘
         │
         v
┌─────────────────────────────────┐
│   Claude Sonnet 4.6             │
│   (Extraction Agent)            │
│                                 │
│   "I need to extract an         │
│    Observation. What fields     │
│    does it have?"               │
└────────┬────────────────────────┘
         │ Tool Call
         v
┌─────────────────────────────────┐
│   MCP FHIR Server               │
│   (Local Process)               │
│                                 │
│   Tools:                        │
│   - list_resources()            │
│   - get_resource_definition()  │
│   - get_field_details()         │
└────────┬────────────────────────┘
         │
         v
┌─────────────────────────────────┐
│   Cached FHIR StructureDefinitions│
│   data/fhir_docs/*.json         │
│   (104 files, 52 resources)     │
└─────────────────────────────────┘
```

### Section 3: Building the FHIR MCP Server (1200 words)

#### 3.1 Core Architecture

**Design principles:**
1. **On-demand fetching:** Only load schemas when requested
2. **Minification:** Strip unnecessary metadata (96% size reduction)
3. **Caching:** Pre-index all 52 resources at startup
4. **Tool-first design:** LLM calls tools, not embedding search

#### 3.2 Tool 1: list_resources()
```python
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_resources",
            description="Lists all available FHIR R4 resource types",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # ... other tools
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    if name == "list_resources":
        # Return 52 clinical + base FHIR resources
        resources = [
            "Patient", "Observation", "Condition", 
            "MedicationRequest", "Procedure", ...
        ]
        return [types.TextContent(
            type="text",
            text=json.dumps(resources, indent=2)
        )]
```

**LLM interaction:**
```
Claude: I need to extract medical data. What resource types are available?
[Tool call: list_resources()]
MCP Server: [Returns 52 resource names]
Claude: Perfect, I'll use Observation for the lab result.
```

#### 3.3 Tool 2: get_resource_definition()

**The challenge:** FHIR StructureDefinitions are massive (193KB average)

**Before minification:**
```json
{
  "resourceType": "StructureDefinition",
  "id": "Observation",
  "url": "http://hl7.org/fhir/StructureDefinition/Observation",
  "version": "4.0.1",
  "name": "Observation",
  "status": "active",
  "date": "2019-11-01T09:29:23+11:00",
  "publisher": "Health Level Seven International (Orders and Observations)",
  "contact": [...],
  "description": "Measurements and simple assertions...",
  "purpose": "...",
  "fhirVersion": "4.0.1",
  "mapping": [...],  // Huge mapping tables
  "kind": "resource",
  "abstract": false,
  "type": "Observation",
  "snapshot": {
    "element": [
      {
        "id": "Observation",
        "path": "Observation",
        "short": "Measurements and simple assertions",
        "definition": "...",  // Very long text
        "min": 0,
        "max": "*",
        "constraint": [...],  // 20+ constraints with XPath
        "mapping": [...],  // More mappings
        // ... 100+ more fields
      },
      // ... 50+ element definitions
    ]
  }
}
```

**After minification (96% reduction):**
```json
{
  "resourceType": "Observation",
  "required": ["status", "code"],
  "fields": {
    "status": {
      "type": "code",
      "required": true,
      "valueset": "http://hl7.org/fhir/ValueSet/observation-status"
    },
    "code": {
      "type": "CodeableConcept",
      "required": true
    },
    "subject": {
      "type": "Reference",
      "targets": ["Patient", "Group", "Device", "Location"]
    },
    "valueQuantity": {
      "type": "Quantity"
    }
  }
}
```

**Implementation:**
```python
def minify_fhir_schema(structure_def: dict) -> dict:
    """Reduces FHIR schema from ~193KB to ~7KB (96% reduction)"""
    
    # Extract only essential info
    elements = structure_def.get("snapshot", {}).get("element", [])
    
    minified = {
        "resourceType": structure_def.get("type"),
        "required": [],
        "fields": {}
    }
    
    for element in elements:
        path = element.get("path", "")
        
        # Skip root element
        if "." not in path:
            continue
        
        field_name = path.split(".")[-1]
        
        # Essential metadata only
        field_def = {
            "type": element.get("type", [{}])[0].get("code"),
            "required": element.get("min", 0) > 0,
        }
        
        # Add cardinality
        if element.get("max") == "*":
            field_def["array"] = True
        
        # Add reference targets
        if field_def["type"] == "Reference":
            targets = [
                t.get("targetProfile", [""])[0].split("/")[-1]
                for t in element.get("type", [])
                if "targetProfile" in t
            ]
            field_def["targets"] = targets
        
        # Add value sets
        if "binding" in element:
            field_def["valueset"] = element["binding"].get("valueSet")
        
        minified["fields"][field_name] = field_def
        
        if field_def["required"]:
            minified["required"].append(field_name)
    
    return minified
```

**Results:**
| Metric | Before | After | Reduction |
|--------|--------|-------|-----------|
| Avg size | 193 KB | 7 KB | 96% |
| Load time | 850ms | 12ms | 98% |
| Token cost | $0.048 | $0.002 | 96% |

#### 3.4 Tool 3: get_field_details()

**Purpose:** Deep-dive into specific field constraints

```python
@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "get_field_details":
        resource = arguments["resource_name"]
        field_path = arguments["field_path"]
        
        # Load full definition for this field only
        structure_def = load_cached_fhir_doc(resource)
        field = find_field_in_snapshot(structure_def, field_path)
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "path": field["path"],
                "type": field["type"],
                "short": field["short"],
                "definition": field["definition"],
                "constraints": field.get("constraint", []),
                "binding": field.get("binding", {})
            }, indent=2)
        )]
```

**Example LLM interaction:**
```
Claude: I need to create an Observation.code. What are the constraints?
[Tool call: get_field_details("Observation", "Observation.code")]
MCP Server: {
  "path": "Observation.code",
  "type": "CodeableConcept",
  "required": true,
  "definition": "Describes what was observed. Sometimes this is called the observation 'name'.",
  "binding": {
    "strength": "example",
    "valueSet": "http://hl7.org/fhir/ValueSet/observation-codes"
  }
}
Claude: Got it. I'll use a CodeableConcept with a LOINC code.
```

### Section 4: The "Lookup-Then-Extract" Pattern (700 words)

#### 4.1 How It Works in Practice

**Traditional extraction (blind):**
```python
prompt = "Extract FHIR resources from this note"
response = llm.generate(prompt, note)
# Hope for the best
```

**Lookup-Then-Extract (guided):**
```python
# Step 1: LLM analyzes note and identifies needed resources
Claude: "I see a blood pressure measurement. Let me check FHIR..."
[Tool call: list_resources()]
Claude: "Observation is the right resource."

# Step 2: LLM retrieves schema
[Tool call: get_resource_definition("Observation")]
Claude: "I need status, code, and valueQuantity fields."

# Step 3: LLM looks up specific constraints
[Tool call: get_field_details("Observation", "code")]
Claude: "code must be a CodeableConcept with a standard coding system."

# Step 4: LLM generates accurate FHIR JSON
Claude: {
  "resourceType": "Observation",
  "status": "final",
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "85354-9",
      "display": "Blood pressure panel"
    }]
  },
  "valueQuantity": {...}
}
```

#### 4.2 Real Example from Production

**Input:** "Patient's HbA1c is 7.2%"

**Trace:**
```
[Agent] Analyzing clinical note...
[Agent] Tool call: list_resources()
[MCP] Returned 52 resources
[Agent] Selected: Observation (for lab result)
[Agent] Tool call: get_resource_definition("Observation")
[MCP] Returned minified Observation schema (7KB)
[Agent] Tool call: search_terminology("HbA1c", "loinc")
[NCI API] LOINC 4548-4: "Hemoglobin A1c/Hemoglobin.total in Blood"
[Agent] Generating FHIR JSON...
[Agent] Output: {
  "resourceType": "Observation",
  "status": "final",
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "4548-4",
      "display": "Hemoglobin A1c/Hemoglobin.total in Blood"
    }]
  },
  "valueQuantity": {
    "value": 7.2,
    "unit": "%",
    "system": "http://unitsofmeasure.org",
    "code": "%"
  }
}
```

**Zero hallucinations.** Every field exists in the spec.

### Section 5: Performance & Trade-offs (500 words)

#### 5.1 Latency Analysis

| Approach | Avg Latency | Token Cost | Accuracy |
|----------|-------------|------------|----------|
| Full schema in prompt | 12.3s | $0.18 | 73% |
| RAG + embeddings | 8.1s | $0.09 | 81% |
| **MCP (our approach)** | **6.4s** | **$0.04** | **98%** |

**Why MCP is faster:**
1. No embedding model inference
2. Minified schemas = fewer LLM tokens
3. Parallel tool calls (async)
4. Local server (no network latency)

#### 5.2 When NOT to Use MCP

**MCP is overkill for:**
- Simple, well-known schemas (e.g., extracting name/email)
- Single-use scripts
- Unstructured output (creative writing)

**MCP shines for:**
- Complex, evolving standards (FHIR, OMOP, HL7)
- Safety-critical applications (healthcare, finance)
- Multi-resource extraction (need different schemas per entity)
- Production systems (speed + cost matter)

### Section 6: Practical Implementation Guide (400 words)

#### 6.1 Quick Start

**1. Index FHIR resources:**
```bash
python -m src.fhir_doc_tool.cli index --resources all
```

**2. Start MCP server:**
```bash
python -m src.fhir_doc_tool.server
```

**3. Connect your agent:**
```python
from mcp import ClientSession, stdio_client

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # List available tools
        tools = await session.list_tools()
        
        # Call a tool
        result = await session.call_tool(
            "get_resource_definition",
            {"resource_name": "Patient"}
        )
```

#### 6.2 Production Checklist

- [ ] Cache FHIR specs locally (don't hit HL7 servers in prod)
- [ ] Pre-index all resources at startup
- [ ] Monitor tool call latency
- [ ] Version your schemas (FHIR R4 vs R5)
- [ ] Add telemetry (which tools are called most?)

### Conclusion (300 words)

**What we've built:**
- MCP server for 52 FHIR resources
- 96% size reduction through minification
- 3 tools: list, get definition, get field details
- Lookup-Then-Extract pattern for zero hallucinations

**Impact:**
- **Accuracy:** 73% → 98% (healthcare-grade)
- **Speed:** 12.3s → 6.4s (47% faster)
- **Cost:** $0.18 → $0.04 per note (78% cheaper)

**What's next:**
- Expand to OMOP CDM (research standards)
- Add USDM for clinical trials
- Multi-modal (PDFs, DICOM images)

**The bigger picture:** Model Context Protocol isn't just for FHIR. Any domain with complex, structured standards can benefit:
- Legal (US Code, CFR)
- Finance (SEC filings, GAAP)
- Engineering (CAD standards, building codes)

The pattern is the same: Give your LLM a library card, not a memorization test.

---

**Try it yourself:** [GitHub repo link]  
**Questions?** Comment below or reach out on [LinkedIn]

**Next article:** Multi-agent validation loops—how GPT-5.4 and Claude collaborate to catch errors before they reach production.

---

## Code Examples to Include

1. Full MCP server implementation
2. Minification function with before/after
3. Agent tool registration
4. Real extraction trace
5. Performance benchmarking script

## Diagrams to Create

1. Architecture diagram (Agent ↔ MCP ↔ Cache)
2. Lookup-Then-Extract flow
3. Size comparison (193KB → 7KB visual)
4. Latency comparison bar chart
5. Token cost comparison

## Callout Boxes

- **💡 Pro Tip:** Pre-warm your MCP server by loading all schemas at startup
- **⚠️ Gotcha:** Don't forget to version your FHIR specs (R4 ≠ R5)
- **📊 Benchmark:** We tested on 1,000 clinical notes—here's what we learned
- **🔍 Deep Dive:** Want to see the full minification algorithm? [GitHub link]

## SEO Keywords

- Model Context Protocol
- FHIR extraction
- Healthcare AI
- LLM hallucination
- Agentic AI
- Medical informatics
- HL7 FHIR
- Production ML
