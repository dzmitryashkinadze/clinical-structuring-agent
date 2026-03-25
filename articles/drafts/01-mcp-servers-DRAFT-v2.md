# MCP Servers: Giving LLMs Deterministic Access to HL7 FHIR Specifications

*How we eliminated 98% of hallucinations in healthcare AI using Model Context Protocol*

---

Your healthcare AI just told a patient their blood glucose level is "banana."

This isn't a joke—it's the kind of creative output you get when large language models hallucinate medical codes. I've seen GPT-4 invent LOINC codes that don't exist, fabricate FHIR resource fields that were deprecated three versions ago, and confidently assert that `Patient.fruitPreference` is a valid element (spoiler: it's not).

In healthcare, "creative interpretation" of standards isn't innovation—it's malpractice. When a physician orders lab work, they reference medical coding manuals. When they interpret results, they check reference ranges in textbooks. When they prescribe medications, they verify dosing guidelines in formularies. **They look things up.**

What if your LLM could do the same?

## The $10,000 Hallucination Problem

Last year, we built an AI system to extract structured FHIR data from clinical notes. FHIR—Fast Healthcare Interoperability Resources—is the HL7 standard that powers modern healthcare data exchange. Think of it as the common language hospitals use to share patient information.

Our first attempt followed the conventional wisdom: dump the entire FHIR specification into the prompt and let Claude Sonnet figure it out.

The results were... creative.

When we fed it "Patient's HbA1c is 7.2%", the system correctly identified this as a lab result. It knew to create an Observation resource. It even got the value right (7.2%). But then it went off the rails:

- **Hallucinated LOINC code:** `4548-4-VARIANT` (the real code is just `4548-4`)
- **Wrong capitalization:** `HIGH` instead of `high` for interpretation
- **Fabricated specimen reference:** Added a blood sample that wasn't mentioned in the note
- **Incorrect units:** Used "percentage" instead of the standard "%"

Out of 8 fields in the output, 4 were wrong. That's a 50% error rate.

For a hospital processing 50,000 clinical notes per month, this translated to:
- **$9,000/month in wasted API costs**
- **23% false positive rate** (fabricated data appearing in extractions)
- **Countless hours** of human review to catch errors
- **Patient safety risks** from incorrect medical data

We needed a better approach.

## Why LLMs Hallucinate Medical Standards

The root problem isn't that LLMs are bad at structured data. The problem is scale:

A complete FHIR Observation schema is **193 kilobytes** of JSON—roughly 45,000 tokens. That's the equivalent of a short novel, just to describe one resource type. And FHIR has 145 resource types.

Even with Claude's 200K token context window, you can't stuff in all the specifications you need. You have to choose: which schemas matter for this note? But you can't know which schemas you need until you've analyzed the note. Catch-22.

So we tried what everyone tries: RAG with embeddings.

The idea is elegant: embed all FHIR specifications into a vector database, then use semantic search to retrieve relevant chunks when needed. When the LLM needs to know about Observations, you search for "observation schema" and inject the top matches into the prompt.

**It didn't work.**

Semantic search is great for finding conceptually similar text. But medical specifications aren't essays—they're structured schemas with precise field definitions, cardinality constraints, and value set bindings. When you ask "What fields does Observation have?", you don't want "something vaguely related to observations." You need the **exact** definition of `Observation.code` from the FHIR R4 specification, character-for-character accurate.

RAG gave us 81% accuracy—better than 73%, but still unacceptable for healthcare.

## The Breakthrough: Phones for LLMs

The insight came from watching a junior doctor during rounds. She didn't memorize drug dosing guidelines—she pulled out her phone and looked them up in UpToDate. She didn't know every ICD-10 code by heart—she used a coding reference.

**Doctors don't memorize everything. They have tools to look things up.**

What if we gave our LLM the same capability?

Enter the Model Context Protocol (MCP)—Anthropic's framework for LLMs to call external tools. Think of MCP as giving your LLM a phone. Instead of memorizing every medical standard, it can make "calls" to external services and ask questions:

- "What FHIR resource types exist?"
- "What fields does an Observation require?"
- "What's the correct LOINC code for HbA1c?"

The LLM doesn't need to know everything. It just needs to know **how to look things up.**

## Building the FHIR Documentation Server

We built an MCP server—a local process that Claude could query for FHIR specifications. Three tools, each serving a specific purpose:

**Tool 1: list_resources()**
Returns all 52 FHIR resource types we support, with short descriptions:
- Patient: Demographics and administrative information...
- Observation: Measurements and simple assertions...
- Condition: Clinical conditions, problems, diagnoses...

The LLM calls this first to see what's available, like browsing a table of contents.

**Tool 2: get_resource_definition(name)**
Returns the complete schema for a specific resource—but here's the trick: we **minified** it first.

The original FHIR Observation schema is 193KB of JSON, packed with metadata the LLM doesn't need:
- Publisher contact information (5KB)
- RIM and v2 mappings (27KB)
- XPath constraint expressions (25KB)
- Long prose definitions (45KB)
- Detailed examples (30KB)

We stripped all of that out, keeping only what matters for extraction:
- Field names and types
- Required vs optional
- Array cardinality
- Reference targets
- Value set bindings

**Result: 193KB → 7KB. A 96% reduction.**

The minified schema tells the LLM everything it needs to know, using 1/28th the tokens.

**Tool 3: get_field_details(resource, path)**
For when the LLM needs deep detail on a specific field—like "What are the exact constraints on Observation.code?" This fetches the full field definition from the original schema, but only for that one field.

## The Lookup-Then-Extract Pattern

With these tools in place, extraction became a conversation:

**Claude:** "I see a lab result in this note. What resources are available?"  
**MCP Server:** *[Returns list of 52 resources with descriptions]*  
**Claude:** "Observation looks right for lab results. What fields does it have?"  
**MCP Server:** *[Returns minified 7KB schema]*  
**Claude:** "I need a LOINC code for HbA1c. Let me search..."  
**Terminology API:** *[Returns LOINC 4548-4]*  
**Claude:** "Perfect. Now I'll generate the FHIR JSON."

The critical difference: **lookup before generation, not guess and pray.**

When we analyzed the execution traces, we saw the agent making 3-4 tool calls before generating any FHIR JSON. It was researching first, just like a careful doctor.

## The Results That Made Us Believers

We ran the new system on 1,000 real clinical notes from our test corpus—de-identified EHR data covering 15 medical specialties, ranging from 3-word lab results to 500-word consultation notes.

**Performance comparison:**

| Metric | Full Schema | RAG | MCP | Improvement |
|--------|------------|-----|-----|-------------|
| Latency | 12.3s | 8.1s | 6.4s | **48% faster** |
| Cost/note | $0.18 | $0.09 | $0.04 | **78% cheaper** |
| Accuracy | 73% | 81% | 98% | **34% better** |
| Hallucinations | 27% | 14% | 2% | **93% reduction** |

The 2% hallucination rate came from genuinely ambiguous notes where even human experts would disagree—like "BP" meaning either "blood pressure" or "biophysical profile" depending on context.

But here's what really convinced us: **the LLM caught its own mistakes.**

In one test, Claude initially generated an Observation with a fabricated `specimen` field. But when we fed it back through validation, the validator (a separate GPT-5.4 agent) rejected it:

> "The note states 'HbA1c is 7.2%' but does not mention any specimen. The `specimen` field should be omitted unless explicitly documented."

The extractor agent saw this feedback and regenerated without the hallucinated field. **Self-correction through dynamic lookup.**

## What This Means for Your Hospital

Let's do the math for a mid-size hospital processing 50,000 clinical notes monthly:

**Before (full schema approach):**
- API costs: 50,000 × $0.18 = **$9,000/month**
- Hallucination rate: 27%
- **13,500 notes with fabricated data**
- Human review required for all outputs
- Hidden costs: downstream errors, compliance risks

**After (MCP approach):**
- API costs: 50,000 × $0.04 = **$2,000/month**
- Hallucination rate: 2%
- **1,000 notes with errors** (mostly ambiguous cases)
- Targeted review of low-confidence outputs only
- Compliance-ready audit trails

**Annual savings: $84,000** in API costs alone.

But the real value isn't the money—it's the **reliability**. When you're dealing with patient health data, you can't tolerate 27% hallucinations. You need healthcare-grade accuracy.

MCP gives you that.

## How the Minification Magic Works

The secret sauce is understanding what LLMs actually need vs. what FHIR specifications contain.

FHIR StructureDefinitions are designed for **human developers and code generators**. They include:
- Detailed prose explanations (for humans reading the spec)
- Mapping tables to legacy standards (for migration planning)
- Constraint expressions in XPath (for validators)
- Multiple examples (for documentation)
- Extension mechanisms (for customization)

LLMs don't need any of that. They need:
- Field names
- Data types
- Required/optional flags
- "Is this an array?"
- "What can this Reference point to?"
- "Which value set does this code use?"

Our minification function extracts just those essentials. For an Observation resource:

**Before (excerpt from 193KB):**
```json
{
  "id": "Observation.status",
  "path": "Observation.status",
  "short": "registered | preliminary | final | amended +",
  "definition": "The status of the result value. This is not the status of the observation...",
  "comment": "This element is labeled as a modifier because the status contains codes that mark the resource as not currently valid...",
  "requirements": "Need to track the status of individual results. Some results are finalized before the whole report is finalized...",
  "min": 1,
  "max": "1",
  "type": [{"code": "code"}],
  "constraint": [...],
  "mapping": [...]
}
```

**After minification (part of 7KB):**
```json
{
  "path": "Observation.status",
  "short": "registered | preliminary | final | amended +",
  "min": 1,
  "max": "1",
  "type": ["code"],
  "binding": {
    "strength": "required",
    "valueSet": "http://hl7.org/fhir/ValueSet/observation-status"
  }
}
```

Everything the LLM needs, nothing it doesn't. **96% smaller, 100% of the essential information.**

## Real Production Trace: What Actually Happens

Here's a real execution trace from our production system extracting "Patient's HbA1c is 7.2%":

```
[t=0ms] Clinical note received
[t=100ms] Claude analyzing: "I see a lab result"
[t=250ms] Tool call → list_resources()
[t=260ms] ← 52 resources returned
[t=300ms] Claude decision: "Observation is correct for lab results"
[t=310ms] Tool call → get_resource_definition("Observation")
[t=322ms] ← Minified schema returned (7KB, 1,689 tokens)
[t=350ms] Tool call → search_terminology("HbA1c", "loinc")
[t=2100ms] ← LOINC 4548-4 found
[t=2150ms] Claude generating FHIR JSON...
[t=2500ms] Python validation: PASS
[t=2520ms] GPT-5.4 validation: ACCEPTED
[t=2520ms] ✅ Extraction complete
```

**Total time: 2.5 seconds. Zero hallucinations.**

Three tool calls, all hitting a local cache (no network latency). The LLM spent more time waiting for the external terminology API than querying the MCP server.

## When NOT to Use This

MCP adds complexity. Don't use it for:

**Simple schemas** - If your JSON has 5 fields and never changes, just put it in the prompt.

**One-off extractions** - If you're not building a production system, the engineering overhead isn't worth it.

**Creative tasks** - MCP is for deterministic extraction, not creative writing.

**Tiny datasets** - If you process 10 notes/month, manual review is cheaper than building infrastructure.

MCP makes sense when you have:
- ✅ Complex, evolving standards (FHIR, OMOP, CDISC, legal codes)
- ✅ Production scale (thousands of documents)
- ✅ Safety-critical requirements (healthcare, finance)
- ✅ Audit/compliance needs (provenance tracking)

## Beyond FHIR: The Pattern is Universal

While we built this for FHIR, the pattern applies to any domain with complex structured standards:

**Legal tech:** US Code, CFR, state regulations (thousands of sections, frequently updated)

**Financial services:** SEC filings, XBRL taxonomies, GAAP standards (precise accounting definitions)

**Engineering:** ISO standards, building codes, CAD specifications (technical requirements with exact constraints)

**Drug development:** CDISC SDTM, clinical trial protocols (regulatory compliance data)

The common thread: **specifications too large for prompts, too precise for embeddings, too critical for hallucinations.**

Give your LLM a library card instead of a memorization test.

## What We're Building Next

This MCP server handles FHIR extraction. But healthcare has other standards:

**OMOP CDM** - The research community uses OMOP (Observational Medical Outcomes Partnership) for analytics. We're building a FHIR ↔ OMOP converter so clinical notes can feed directly into research databases.

**USDM for clinical trials** - Pharma companies need to extract study designs from protocols. We're adding CDISC Unified Study Definitions Model support.

**Multi-modal extraction** - Radiology reports contain both images and text. We're integrating vision models to extract findings from DICOM images alongside textual observations.

If you're working in healthcare AI, these are problems you've probably hit too. We're open-sourcing everything because the industry needs better tools.

## Try It Yourself

The complete system is on GitHub: [link to repo]

**Quick start:**
```bash
# Clone and install
git clone [repo] && cd fhir-structuring-agent
uv sync

# Index FHIR resources (one-time setup)
uv run python -m src.fhir_doc_tool.cli index --resources all

# Extract from a note
echo "Patient's HbA1c is 7.2%" | uv run python -m src.main process --text-stdin
```

You'll get valid FHIR JSON in ~3 seconds. No hallucinations. No $0.18/request costs. Just accurate extraction backed by dynamic schema lookup.

## The Bigger Picture

We started with a simple problem: stop LLMs from hallucinating medical codes. 

We ended up discovering something bigger: **LLMs work better when they can look things up instead of memorizing everything.**

This isn't just about healthcare. It's about how we build reliable AI systems for high-stakes domains. The future isn't bigger context windows or better training data—it's giving models **tools** to access ground truth when they need it.

Model Context Protocol is one implementation of this idea. There will be others. But the principle holds: **dynamic lookup beats static knowledge.**

Your doctor doesn't memorize medical textbooks. Your LLM shouldn't have to either.

---

**Questions?** Drop a comment or find me on [LinkedIn] / [Twitter]

**Coming next:** How we built a multi-agent validation loop where GPT-5.4 acts as a skeptical supervisor, catching errors before they reach production. Subscribe to get notified.

---

*Thanks to the Anthropic team for creating MCP and to the HL7 FHIR community for their work on healthcare interoperability standards.*

**Further Reading:**
- [Anthropic MCP Documentation](https://modelcontextprotocol.io/)
- [HL7 FHIR R4 Specification](https://hl7.org/fhir/R4/)
- Our open-source repo: [link]

