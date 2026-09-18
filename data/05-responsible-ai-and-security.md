# Responsible AI and Security for Foundry Applications

Last reviewed: September 14, 2026

## Lifecycle

Microsoft groups responsible AI work for Foundry agents into three broad stages: discover, protect, and govern.

Discover means identifying quality, safety, privacy, and security risks before and after deployment. Activities include documenting the use case, identifying affected users, testing ordinary and adversarial inputs, and measuring how often failures occur.

Protect means applying controls at both model and agent runtime levels. Examples include content filters, guardrails, input validation, tool restrictions, approval requirements, data-access controls, and defenses against prompt injection.

Govern means maintaining oversight through traceability, monitoring, alerts, incident response, compliance processes, and periodic reevaluation.

## RAG-specific risks

RAG applications can retrieve inaccurate, stale, unauthorized, or malicious content. A document may contain instructions designed to manipulate the model. These indirect prompt-injection attacks should not override application or agent instructions.

Retrieval can also expose information to the wrong user if authorization is applied only after search. Access control should be enforced during retrieval so unauthorized chunks never enter the model context.

Citations improve transparency but must be validated. A citation should point to evidence that actually supports the claim. The application should not invent filenames, page numbers, URLs, or quotations.

## Controls

- Use trusted data sources and record provenance.
- Scan and validate content before ingestion.
- Separate document content from system instructions.
- Apply identity-aware filters during retrieval.
- Grant least-privilege permissions to applications, agents, indexes, and tools.
- Prefer managed identity and keyless authentication.
- Instruct the model to acknowledge missing or conflicting evidence.
- Limit autonomous actions and require approval for sensitive operations.
- Evaluate unsafe content, data leakage, prompt injection, and prohibited actions.
- Trace retrieval and generation while redacting secrets and personal data.

## Monitoring and operations

Monitor search health, ingestion failures, latency, token use, model errors, grounding quality, safety events, and changes in user behavior. Store enough provenance to reproduce important decisions. Define an incident process for unsafe output, unexpected tool use, or information exposure.

Responsible AI is iterative. After applying a mitigation, repeat the measurement that identified the problem. A control is not complete until testing shows that it reduces the targeted risk without causing unacceptable new failures.

## Official sources

- Responsible AI for Microsoft Foundry: https://learn.microsoft.com/en-us/azure/foundry/responsible-use-of-ai-overview
- Risk and safety evaluators: https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/risk-safety-evaluators
