# Article Diagrams - Mermaid (Nano Banana Theme)

This directory contains all diagrams for the Medium article series, created using Mermaid with the Nano Banana color theme for visual consistency and appeal.

## Nano Banana Theme Colors

```css
Primary Color: #FEF3BD (Soft banana yellow)
Primary Border: #FF6B6B (Coral red)
Line Color: #4ECDC4 (Turquoise)
Secondary Color: #95E1D3 (Mint green)
Tertiary Color: #F38181 (Salmon pink)
Accent: #FFE66D (Bright yellow)
```

## Article 1: MCP Servers

### Diagram 1: MCP Architecture
**File:** `01-mcp-architecture.md`

**Type:** Graph TB (Top-to-Bottom)

**Purpose:** Shows the complete MCP architecture with layers:
- Input: Clinical note
- Agent: Claude Sonnet 4.6 with tool calling
- MCP Server: Three tools (list, get definition, get field details)
- Cache: Local FHIR StructureDefinitions
- Output: Valid FHIR JSON

**Key Visual Elements:**
- Color-coded layers (input=yellow, agent=mint, server=salmon, cache=yellow, output=mint)
- Tool call arrows showing data flow
- Size annotations (193KB → 7KB)

**Usage in Article:** Section 2.3 "Architecture Diagram"

---

### Diagram 2: Lookup-Then-Extract Flow
**File:** `02-lookup-then-extract-flow.md`

**Type:** Sequence Diagram

**Purpose:** Illustrates the step-by-step interaction between components during extraction:
1. User provides clinical note
2. Claude analyzes and identifies resource type
3. MCP provides schema (with minification)
4. NCI API provides terminology codes
5. Claude generates FHIR JSON
6. GPT-5.4 validates output

**Key Visual Elements:**
- 6 phases with colored backgrounds
- Numbered sequence (1-15 steps)
- Message exchanges between actors
- Real data examples in messages

**Usage in Article:** Section 4.1 "How It Works in Practice"

---

### Diagram 3: Schema Minification
**File:** `03-schema-minification.md`

**Type:** Graph LR (Left-to-Right)

**Purpose:** Visual representation of the minification process:
- Before: 193KB schema with all metadata
- Process: minify_fhir_schema() function
- After: 7KB minified schema
- Results: Performance metrics

**Key Visual Elements:**
- Red box (before) with ❌ removed items
- Yellow process box with transformation steps
- Green box (after) with ✓ kept items
- Yellow metrics box with percentages

**Usage in Article:** Section 3.3 "Tool 2: get_resource_definition()"

---

### Diagram 4: Performance Comparison
**File:** `04-performance-comparison.md`

**Type:** Graph TB with subgraphs

**Purpose:** Side-by-side comparison of 4 approaches:
1. Full schema in prompt (❌ worst)
2. RAG + embeddings (⚠️ medium)
3. MCP (✅ good)
4. MCP + caching (🚀 best)

**Key Visual Elements:**
- 4 parallel flows with metrics boxes
- Color coding: red=bad, yellow=warning, green=good
- Cost savings calculation at bottom
- Real numbers from 1,000 note benchmark

**Usage in Article:** Section 5.1 "Latency Analysis"

---

### Diagram 5: Real Production Trace
**File:** `05-production-trace.md`

**Type:** State Diagram

**Purpose:** Complete execution trace of a real extraction:
- Shows all phases with timestamps
- Tool calls with request/response
- Minification process
- Dual validation (Python + GPT-5.4)

**Key Visual Elements:**
- State transitions with timing (t=0ms, t=100ms, etc.)
- Notes on right side explaining each phase
- Real data from actual extraction
- Success indicators (✅) throughout

**Usage in Article:** Section 4.2 "Real Example from Production"

---

## How to Use These Diagrams

### In Medium Articles

1. **Copy Mermaid code** from .md files
2. **Paste into Medium** using the "Embed" option
3. Or **render to PNG/SVG** using:
   - [Mermaid Live Editor](https://mermaid.live/)
   - [Kroki](https://kroki.io/)
   - CLI: `mmdc -i diagram.md -o diagram.png`

### Rendering Options

**Option 1: Mermaid Live Editor**
```
1. Go to https://mermaid.live/
2. Paste diagram code
3. Download as PNG/SVG
4. Upload to Medium
```

**Option 2: Command Line (recommended)**
```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Render single diagram
mmdc -i 01-mcp-architecture.md -o 01-mcp-architecture.png -w 1200 -H 800

# Render all diagrams
for f in *.md; do
  mmdc -i "$f" -o "${f%.md}.png" -w 1200 -H 800
done
```

**Option 3: Embed in GitHub (automatic rendering)**
GitHub automatically renders Mermaid diagrams in markdown files. Just include them in your README or article draft.

### Customization

All diagrams use the Nano Banana theme variables. To adjust colors, modify the init block:

```javascript
%%{init: {
  'theme':'base',
  'themeVariables': {
    'primaryColor':'#FEF3BD',
    'primaryBorderColor':'#FF6B6B',
    // ... other colors
  }
}}%%
```

## File Organization

```
articles/images/
├── README.md                           # This file
├── 01-mcp-architecture.md             # Graph: MCP system architecture
├── 02-lookup-then-extract-flow.md     # Sequence: Extraction workflow
├── 03-schema-minification.md          # Graph: 193KB → 7KB transformation
├── 04-performance-comparison.md       # Graph: 4 approaches compared
└── 05-production-trace.md             # State: Real execution trace
```

## Future Diagrams (Upcoming Articles)

**Article 2: Multi-Agent Validation**
- Validation loop architecture
- Feedback flow diagram
- Retry mechanism state machine

**Article 3: 52 FHIR Resources**
- Resource hierarchy tree
- Test coverage matrix
- Expansion timeline

**Article 5: FHIR ↔ OMOP**
- FHIR vs OMOP comparison
- Vocabulary mapping flow
- Conversion pipeline

## Tips for Creating New Diagrams

1. **Keep it simple:** One concept per diagram
2. **Use color consistently:** Nano Banana theme throughout
3. **Add real data:** Actual numbers, code snippets, examples
4. **Annotate liberally:** Use notes, labels, captions
5. **Test rendering:** Check on Mermaid Live before committing
6. **Size appropriately:** 1200x800px works well for Medium

## Color Accessibility

The Nano Banana theme provides good contrast:
- ✅ Black text on yellow background: WCAG AA compliant
- ✅ White text on salmon/coral: WCAG AA compliant
- ✅ Dark text on mint/turquoise: WCAG AA compliant

All diagrams are readable in both light and dark modes.

## License

These diagrams are part of the open-source FHIR Structuring Agent project and are licensed under MIT. Feel free to use, modify, and share with attribution.

---

**Questions?** Open an issue or contact the maintainer.
