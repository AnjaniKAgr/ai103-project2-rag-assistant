# Retrieval-Augmented Generation with Azure AI Search

Last reviewed: September 14, 2026

## What RAG does

Retrieval-augmented generation, or RAG, grounds a model with information retrieved from an external knowledge source. Instead of relying only on model training, the application searches approved content at query time and supplies relevant passages to the model. The model uses those passages to answer and cite its sources.

RAG is useful when information is private, specialized, frequently updated, or must be traceable. It does not guarantee correctness: retrieval can miss important content, return irrelevant passages, or supply conflicting evidence. Generation must therefore be evaluated separately from retrieval.

## Indexing workflow

1. Collect documents and preserve source metadata.
2. Extract clean text from each document.
3. Divide text into chunks that are small enough for focused retrieval but large enough to preserve meaning.
4. Generate vector embeddings for chunks.
5. Store searchable text, vectors, titles, source locations, and other metadata in an Azure AI Search index.

Azure AI Search supports two vectorization patterns. With integrated vectorization, an indexer pipeline performs chunking and embedding. With external vectorization, application code generates embeddings and pushes the resulting documents and vectors into the index.

Useful fields commonly include a unique chunk ID, document ID, title, content, source URL or filename, page or section, content vector, and filterable metadata such as category or date.

## Query workflow

1. Receive the user's question.
2. Convert the question to a vector when vector search is used.
3. Search for relevant chunks.
4. Optionally apply metadata filters and reranking.
5. Add the best chunks to the model prompt as grounding context.
6. Instruct the model to answer only from the evidence and include citations.
7. Return an uncertainty response when the evidence is insufficient.

## Search approaches

Keyword search works well for exact terms, product names, codes, and distinctive phrases. Vector search retrieves semantically similar content even when the query and document use different words.

Hybrid search runs keyword and vector search in the same request, merges the results, and ranks a unified result set. It often works better than either method alone because it combines lexical precision with semantic similarity.

Semantic ranking can improve the ordering and presentation of results using language understanding. Metadata filtering narrows results by fields such as department, document type, date, access group, or language.

## Chunking considerations

Chunks that are too small lose context. Chunks that are too large can mix unrelated topics, consume more prompt space, and weaken retrieval precision. Preserve section headings, source identifiers, and limited overlap between adjacent chunks. Measure results rather than assuming one chunk size is universally best.

## Evaluation

Evaluate retrieval with questions whose supporting passages are known. Measure whether the correct source appears among the top results, whether irrelevant chunks dominate, and whether filters work correctly.

Evaluate generation for groundedness, relevance, completeness, citation correctness, and refusal when evidence is missing. Review failures to determine whether the problem came from ingestion, chunking, embeddings, search configuration, ranking, prompting, or generation.

## Official source

- Azure AI Search vector search overview: https://learn.microsoft.com/en-us/azure/search/vector-search-overview
