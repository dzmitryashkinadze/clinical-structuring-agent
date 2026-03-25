# Diagram 1: MCP Architecture - Agent ↔ MCP ↔ Cache

```mermaid
%%{init: {'theme':'base', 'themeVariables': { 'primaryColor':'#FEF3BD','primaryTextColor':'#000','primaryBorderColor':'#FF6B6B','lineColor':'#4ECDC4','secondaryColor':'#95E1D3','tertiaryColor':'#F38181','noteBkgColor':'#FEF3BD','noteTextColor':'#000','noteBorderColor':'#FF6B6B'}}}%%

graph TB
    subgraph Clinical["<b>📋 Input Layer</b>"]
        Note["<b>Clinical Note</b><br/>Patient's HbA1c is 7.2%<br/>Type 2 Diabetes"]
    end
    
    subgraph Agent["<b>🤖 Extraction Agent (Claude Sonnet 4.6)</b>"]
        Claude["<b>Claude Analysis</b><br/>1. Parse clinical note<br/>2. Identify resource types needed<br/>3. Look up FHIR schemas<br/>4. Generate valid JSON"]
        
        Tools["<b>Available Tools</b><br/>• list_resources()<br/>• get_resource_definition()<br/>• get_field_details()<br/>• search_terminology()"]
    end
    
    subgraph MCP["<b>🔌 MCP FHIR Server (Local Process)</b>"]
        Server["<b>MCP Server</b><br/>Port: stdio<br/>Protocol: JSON-RPC<br/>Status: ⚡ Ready"]
        
        Tool1["<b>list_resources()</b><br/>Returns 52 resource names"]
        Tool2["<b>get_resource_definition(name)</b><br/>Returns minified schema (7KB)"]
        Tool3["<b>get_field_details(path)</b><br/>Returns field constraints"]
    end
    
    subgraph Cache["<b>💾 FHIR Schema Cache</b>"]
        Files["<b>data/fhir_docs/</b><br/>📄 Patient.json (193KB)<br/>📄 Observation.json (193KB)<br/>📄 Condition.json (193KB)<br/>...<br/>52 resources total"]
        
        Minify["<b>Minification Engine</b><br/>193KB → 7KB (96% reduction)<br/>Keeps: fields, types, required<br/>Removes: mappings, examples"]
    end
    
    subgraph Output["<b>✅ Output Layer</b>"]
        FHIR["<b>Valid FHIR JSON</b><br/>{<br/>  resourceType: 'Observation',<br/>  status: 'final',<br/>  code: {...},<br/>  valueQuantity: {...}<br/>}"]
    end
    
    Note --> Claude
    Claude --> |"Tool Call: list_resources()"| Tool1
    Claude --> |"Tool Call: get_resource_definition('Observation')"| Tool2
    Claude --> |"Tool Call: get_field_details('Observation.code')"| Tool3
    
    Tool1 --> |"Returns: [Patient, Observation, ...]"| Claude
    Tool2 --> |"Load from cache"| Files
    Tool2 --> |"Minify schema"| Minify
    Minify --> |"Return 7KB JSON"| Claude
    Tool3 --> |"Field constraints"| Claude
    
    Claude --> |"Generate FHIR"| FHIR
    
    style Note fill:#FEF3BD,stroke:#FF6B6B,stroke-width:3px,color:#000
    style Claude fill:#95E1D3,stroke:#4ECDC4,stroke-width:3px,color:#000
    style Server fill:#F38181,stroke:#FF6B6B,stroke-width:3px,color:#fff
    style Files fill:#FEF3BD,stroke:#FF6B6B,stroke-width:2px,color:#000
    style FHIR fill:#95E1D3,stroke:#4ECDC4,stroke-width:3px,color:#000
    style Minify fill:#FFE66D,stroke:#FF6B6B,stroke-width:2px,color:#000
```

**Caption:** The MCP architecture enables dynamic schema lookup. The agent queries the MCP server for FHIR specifications on-demand, receiving minified schemas (96% smaller) from a local cache. This eliminates context window bloat and hallucinations.
