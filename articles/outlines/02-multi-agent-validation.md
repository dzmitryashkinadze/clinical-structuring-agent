# Article 2: Multi-Agent Validation Loops - How GPT-5.4 and Claude Collaborate to Extract Perfect FHIR Data

## Metadata
- **Target Length:** 3500-4000 words
- **Technical Level:** Advanced
- **Key Technologies:** Multi-agent systems, Claude Sonnet, GPT-5.4, Self-correction loops
- **Code Focus:** Validation architecture, feedback mechanisms, retry logic

## Hook
"Your AI extracted a perfect FHIR bundle. Or did it? Without a second pair of eyes, you'll never know."

**The problem:**
- Single-agent extraction misses 15-20% of issues
- Python schema validation catches syntax, not semantics
- Human review doesn't scale to 50,000 notes/day

**The solution:**
"What if your extractor agent had a supervisor—an AI critic whose only job is to tear apart its work and demand perfection?"

## Outline

### Section 1: Why Single-Agent Extraction Fails (600 words)
- Schema-valid ≠ clinically accurate
- The hallucination taxonomy (missing data, fabricated data, wrong mappings)
- Real failure modes from our production system

### Section 2: The Supervisor Pattern (700 words)
- Extractor vs Validator agent roles
- Why model diversity matters (Claude + GPT-5.4)
- Architecture diagram (extraction loop with feedback)

### Section 3: Building the Validation Agent (1000 words)
- GPT-5.4 as the "skeptical expert"
- Structured output (ValidationDecision model)
- Critique prompt engineering
- Code walkthrough

### Section 4: The Feedback Loop (800 words)
- Retry mechanism (up to 3 attempts)
- Passing validator feedback to extractor
- Message history management
- When to accept vs reject

### Section 5: Real Examples (600 words)
- Success case: Caught hallucinated demographics
- Failure case: Ambiguous clinical term
- Edge case: Multiple valid interpretations

### Section 6: Performance Metrics (400 words)
- Accuracy improvement (single-agent vs multi-agent)
- Latency cost of validation
- When to skip validation (confidence thresholds)

### Conclusion (300 words)
- Multi-agent > single-agent for high-stakes extraction
- Model specialization (Claude for generation, GPT-5.4 for critique)
- What's next: Scaling to 52 resource types

## Key Code Snippets
1. ValidationDecision Pydantic model
2. Validator agent initialization (GPT-5.4)
3. Retry loop with feedback
4. Prompt for validation (full text)
5. Example validator rejection with detailed feedback

## Diagrams
1. Multi-agent architecture (Extractor ↔ Validator)
2. Validation loop flow chart
3. Feedback message structure
4. Accuracy comparison (single vs multi-agent)
