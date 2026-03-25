# Article 1 Version Comparison

## Draft v1 vs v2: Code-Heavy vs Story-Driven

### v1 (01-mcp-servers-DRAFT.md)
**Style:** Technical documentation with extensive code examples

**Stats:**
- Word count: ~4,000
- Code blocks: 30+
- Reading time: 18-20 min
- Tone: Technical reference guide

**Structure:**
- Heavy focus on implementation details
- Multiple complete code examples
- Step-by-step how-to sections
- Deployment checklists
- Production guide format

**Example excerpt:**
```python
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Expose three tools to the LLM"""
    return [
        types.Tool(
            name="list_resources",
            description=(
                "Lists all 52 FHIR R4 clinical resource types supported by this server. "
                "Use this to discover what resources are available for extraction."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        # ... full implementation
    ]
```

**Pros:**
- ✅ Complete code reference
- ✅ Copy-paste ready examples
- ✅ Comprehensive implementation guide

**Cons:**
- ❌ Reads like documentation
- ❌ Code overwhelms narrative
- ❌ Hard to skim
- ❌ Loses reader interest

---

### v2 (01-mcp-servers-DRAFT-v2.md) ⭐ RECOMMENDED
**Style:** Narrative-driven technical story

**Stats:**
- Word count: ~3,200
- Code blocks: 5
- Reading time: 12-14 min
- Tone: Conversational blog post

**Structure:**
- Story-first approach
- Human anecdotes (doctor on rounds)
- Problem → failed attempts → insight → solution
- Metrics in tables, not prose
- Code as supporting evidence only

**Example excerpt:**
> The insight came from watching a junior doctor during rounds. She didn't memorize drug dosing guidelines—she pulled out her phone and looked them up in UpToDate. She didn't know every ICD-10 code by heart—she used a coding reference.
>
> **Doctors don't memorize everything. They have tools to look things up.**
>
> What if we gave our LLM the same capability?

**Pros:**
- ✅ Engaging narrative flow
- ✅ Easy to skim and share
- ✅ Memorable analogies
- ✅ Shows impact, not just mechanics
- ✅ Better for Medium/social sharing

**Cons:**
- ⚠️ Less complete as implementation guide
- ⚠️ Readers need to visit GitHub for full code

---

## Key Differences

### Opening Hook

**v1:** Immediately shows code
```python
# Traditional approach: Put the spec in the prompt
fhir_observation_schema = load_file("observation_structure_definition.json")
```

**v2:** Human story
> Your healthcare AI just told a patient their blood glucose level is "banana."

---

### Explaining the Solution

**v1:** Full code walkthrough
```python
async def list_resources_handler(arguments: dict) -> list[TextContent]:
    indexed = [
        f.name.replace(".profile.json", "") for f in DATA_DIR.glob("*.profile.json")
    ]
    return [TextContent(type="text", text="\n".join(sorted(indexed)))]
```

**v2:** Conceptual description
> **Tool 1: list_resources()**  
> Returns all 52 FHIR resource types we support, with short descriptions. The LLM calls this first to see what's available, like browsing a table of contents.

---

### Performance Results

**v1:** Scattered throughout text
> **Result:** 193KB → 7KB (96%)  
> **Information preserved:** 100% of what the LLM needs  
> **Noise removed:** Publisher metadata, RIM mappings...

**v2:** Clean comparison table
| Metric | Full Schema | RAG | MCP | Improvement |
|--------|------------|-----|-----|-------------|
| Latency | 12.3s | 8.1s | 6.4s | **48% faster** |
| Cost/note | $0.18 | $0.09 | $0.04 | **78% cheaper** |
| Accuracy | 73% | 81% | 98% | **34% better** |

---

## Recommendation: Use v2 for Publication

**Why v2 is better for Medium:**

1. **Engagement:** Story hooks keep readers scrolling
2. **Shareability:** Analogies ("library card for LLMs") are memorable and tweetable
3. **Broader appeal:** Engineers understand concepts without getting lost in implementation
4. **Medium algorithm:** Longer read time (people finish it) = better distribution
5. **Comments:** Readers ask "how did you implement X?" → drives engagement

**What to do with v1:**

Keep it as a **GitHub deep-dive** linked from the article:
- `docs/IMPLEMENTATION_GUIDE.md` - Full code walkthrough
- Reference from v2: "For complete implementation details, see our [technical guide]"

**Best of both worlds:**
- v2 tells the story and gets readers excited
- GitHub docs satisfy engineers who want to implement it
- Separation of concerns: inspiration vs documentation

---

## Side-by-Side Section Comparison

### Section: "Why Healthcare Standards Break LLMs"

**v1 approach:**
```python
# Traditional approach
prompt = f"""
Here is the FHIR Patient resource schema (193KB):
{massive_json_schema}

Now extract patient data from: "John Doe, age 45"
"""
# Result: Context overflow, hallucinated fields, slow inference
```

**v2 approach:**
> A complete FHIR Observation schema is **193 kilobytes** of JSON—roughly 45,000 tokens. That's the equivalent of a short novel, just to describe one resource type. And FHIR has 145 resource types.
>
> Even with Claude's 200K token context window, you can't stuff in all the specifications you need. You have to choose: which schemas matter for this note? But you can't know which schemas you need until you've analyzed the note. Catch-22.

---

### Section: "The Solution"

**v1 approach:**
Full server setup code (50+ lines):
```python
# src/fhir_doc_tool/server.py
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp import types
import mcp.server.stdio

server = Server("fhir-doc-server")

CLINICAL_RESOURCES = [
    "Patient", "Observation", "Condition", "Procedure",
    # ... full list
]
```

**v2 approach:**
Conceptual explanation with dialogue:
> The LLM calls this first to see what's available, like browsing a table of contents.
>
> **Claude:** "I see a lab result in this note. What resources are available?"  
> **MCP Server:** *[Returns list of 52 resources with descriptions]*  
> **Claude:** "Observation looks right for lab results. What fields does it have?"

---

## Final Verdict

| Aspect | v1 | v2 |
|--------|----|----|
| **For Medium publication** | ❌ | ✅ |
| **For GitHub docs** | ✅ | ❌ |
| **Engagement** | Low | High |
| **Shareability** | Low | High |
| **Technical depth** | Very high | Medium-high |
| **Accessibility** | Engineers only | Broader tech audience |
| **Read completion rate** | ~40% | ~75% (estimated) |

**Action:** Publish v2 to Medium, move v1 content to GitHub docs

---

## User Feedback Summary

> "I did read the draft for the first article and I did not like that there was too much code and not enough text. It should read as a story"

**Response:** v2 addresses this by:
- Removing 80% of code blocks
- Adding human stories and analogies
- Using conversational tone
- Showing impact before implementation
- Making code support the story, not be the story

The article now **reads like a blog post**, not documentation.
