# FHIR Agent Prompts

This directory contains system prompts used by the GenAI agents in the FHIR structuring pipeline.

## Files

- **`clinical_analyst.txt`**: System prompt for the primary extraction agent (Gemini 3 Flash)
  - Defines the "Lookup-then-Extract" workflow
  - Specifies FHIR JSON formatting requirements
  - Used by: `src/clinical_analyst/agent.py`

- **`validator_supervisor.txt`**: System prompt for the validation supervisor agent (Claude Sonnet 4.6)
  - Defines validation criteria and decision logic
  - Specifies feedback format for corrections
  - Used by: `src/validator/agent.py`

## Prompt Versioning

When modifying prompts, document changes here:

### Version History

**v1.0** (2026-03-24)
- Initial extraction from codebase
- Established baseline prompts for both agents

## A/B Testing Notes

Record performance metrics and variations here for future optimization.

## Best Practices

1. **Clarity**: Use clear, unambiguous instructions
2. **Structure**: Break complex instructions into numbered steps
3. **Examples**: Include examples in prompts when helpful
4. **Constraints**: Explicitly state what NOT to do
5. **Format**: Specify exact output format requirements
