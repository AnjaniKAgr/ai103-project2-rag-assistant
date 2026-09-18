# Evaluating Agents and RAG Applications

Last reviewed: September 14, 2026

## Why evaluation matters

Evaluation establishes whether an AI application meets quality and safety expectations before deployment. A baseline captures current behavior. Later runs show whether changes to prompts, models, tools, data, or retrieval improve the system or introduce regressions.

Evaluation criteria should be defined before reviewing results. Teams can set acceptance thresholds, investigate failed cases, make one controlled change, and rerun the same dataset.

## Agent evaluation

Agent evaluation should examine both the final outcome and the process used to reach it. Useful dimensions include task completion, task adherence, intent resolution, tool selection, tool-input accuracy, tool-call success, tool-output utilization, navigation efficiency, coherence, relevance, and safety.

A rubric evaluator applies explicit weighted criteria to responses. A useful rubric describes what success means for the particular agent rather than relying only on generic writing quality. Built-in evaluators can supplement the rubric with quality and safety measurements.

Test datasets should contain normal cases, difficult cases, ambiguous requests, unsupported requests, tool failures, and adversarial inputs. Run repeated trials when nondeterminism could hide inconsistent behavior.

## RAG evaluation

RAG has two linked systems that must be evaluated separately.

Retrieval evaluation asks whether the search system found the right evidence. Useful checks include source coverage, top-k recall, ranking quality, duplicate chunks, filter accuracy, and the amount of irrelevant context.

Generation evaluation asks whether the answer correctly uses retrieved evidence. Important dimensions include groundedness, relevance, completeness, citation correctness, coherence, and appropriate refusal when evidence is absent.

An answer can be fluent but unsupported. It can also be grounded in retrieved passages that are themselves irrelevant to the question. For that reason, a single overall score is insufficient for diagnosing RAG failures.

## Recommended test set

Include:

- Direct questions with one clear supporting passage
- Questions requiring evidence from multiple chunks
- Questions using synonyms rather than exact document wording
- Questions requiring metadata filters
- Questions whose answers are not in the corpus
- Conflicting or outdated passages
- Prompt-injection instructions embedded in source documents
- Requests for citations and source locations

## Improvement loop

1. Save a fixed evaluation dataset.
2. Run the baseline.
3. Categorize each failure as ingestion, retrieval, generation, safety, or application logic.
4. Change one component at a time.
5. Rerun the same evaluation.
6. Compare scores and inspect individual cases.
7. Add newly discovered failures to the permanent regression set.

## Official source

- Evaluate Microsoft Foundry agents: https://learn.microsoft.com/en-us/azure/foundry/observability/how-to/evaluate-agent
