# RAG Evaluation Report

## Purpose

The evaluation measures the complete Project 2 RAG workflow rather than only
the language model. Six representative AI-103 questions are passed through the
same retrieval and generation functions used by the interactive application.

Three Microsoft evaluators are used:

- **Retrieval:** whether the retrieved chunks are useful for the query
- **Groundedness:** whether the response is supported by retrieved context
- **Relevance:** whether the response directly answers the query

Scores range from 1 to 5. The configured passing threshold is 3.

## Evaluation dataset

The six questions cover RAG stages, hybrid search, chunking, evaluation
metrics, Foundry agent runtime components, and RAG security controls. The test
cases are stored in `eval-data.jsonl`. Generated responses and contexts are
excluded from Git.

An additional regression case in `eval-unsupported.jsonl` asks for the capital
of France. That information is outside the indexed study corpus. The test
passes only when the assistant explicitly says the evidence is insufficient
and does not return the forbidden answer, `Paris`. This case is evaluated
separately so intentionally irrelevant retrieval does not lower the normal
retrieval-quality score.

## Baseline results

The initial configuration used four vector candidates and returned the best
four hybrid-search results.

| Metric | Average score | Pass rate |
|---|---:|---:|
| Retrieval | 4.50 | 83% |
| Groundedness | 5.00 | 100% |
| Relevance | 4.50 | 83% |

The failed case was:

> How do chunk size and chunk overlap affect a RAG system?

The supporting passage existed in `03-rag-and-azure-ai-search.md`, chunk 2,
but it was not included in the four returned chunks. The assistant correctly
refused to invent an answer, preserving the perfect groundedness score.

## Diagnosis

The failure was classified as a retrieval/ranking problem:

1. The answer existed in the source document.
2. The answer existed in the indexed chunk.
3. The correct chunk was absent from the retrieved context.
4. The model correctly reported that the evidence was insufficient.

This ruled out missing data, ingestion failure, and generation hallucination.

## Retrieval tuning

The query-time configuration was changed to:

- Expand the vector candidate pool from 4 to 10.
- Keep the final model context at four chunks.
- Restrict keyword matching to the `content` field.

The larger candidate pool gives hybrid ranking more vector results to merge
without increasing the context sent to the model.

## Tuned results

| Metric | Average score | Pass rate |
|---|---:|---:|
| Retrieval | 4.17 | 100% |
| Groundedness | 5.00 | 100% |
| Relevance | 5.00 | 100% |

All six questions passed after tuning. The average retrieval score decreased
slightly while its pass rate improved. The wider pool fixed the missing-
evidence case but introduced somewhat less-focused context for other questions.
Groundedness remained perfect and relevance improved, making the tradeoff
acceptable for this small study corpus.

## Lessons learned

- Evaluate retrieval and generation separately.
- Inspect the query, retrieved context, and response for every failed row.
- Fix the pipeline stage where the failure originates.
- Do not use prompt changes to compensate for evidence that was never retrieved.
- Preserve a baseline and rerun the same dataset after a controlled change.
- Review both pass rates and average scores.
- Test appropriate refusal separately from in-scope retrieval quality.
- Two retrieval settings changed together, so this run proves the combination
  worked, not which individual setting caused the improvement. A production
  experiment should isolate them in separate runs.
