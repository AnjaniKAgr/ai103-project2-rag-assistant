import hashlib
import os
from pathlib import Path

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SearchableField,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery
from openai import OpenAI


EMBEDDING_DIMENSIONS = 1536
CHUNK_SIZE_WORDS = 180
CHUNK_OVERLAP_WORDS = 30
EMBEDDING_BATCH_SIZE = 16
UPLOAD_BATCH_SIZE = 100

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIRECTORY = PROJECT_ROOT / "data"


def required_environment_variable(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required environment variable is missing: {name}")
    return value


def get_title(text, fallback):
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def split_into_chunks(text):
    """Split text into overlapping word-based chunks."""
    words = text.split()
    step = CHUNK_SIZE_WORDS - CHUNK_OVERLAP_WORDS

    return [
        " ".join(words[start:start + CHUNK_SIZE_WORDS])
        for start in range(0, len(words), step)
        if words[start:start + CHUNK_SIZE_WORDS]
    ]


def load_chunks():
    source_files = sorted(DATA_DIRECTORY.glob("*.md"))
    if not source_files:
        raise RuntimeError(f"No Markdown documents found in {DATA_DIRECTORY}")

    chunks = []

    for source_file in source_files:
        text = source_file.read_text(encoding="utf-8")
        title = get_title(text, source_file.stem)

        for chunk_number, content in enumerate(split_into_chunks(text)):
            stable_key = f"{source_file.name}:{chunk_number}"
            chunk_id = hashlib.sha256(stable_key.encode("utf-8")).hexdigest()

            chunks.append(
                {
                    "id": chunk_id,
                    "document_id": source_file.stem,
                    "title": title,
                    "source": source_file.name,
                    "chunk_number": chunk_number,
                    "content": content,
                }
            )

    return chunks


def create_or_update_index(index_client, index_name):
    fields = [
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True,
        ),
        SimpleField(
            name="document_id",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SearchableField(
            name="title",
            type=SearchFieldDataType.String,
        ),
        SimpleField(
            name="source",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SimpleField(
            name="chunk_number",
            type=SearchFieldDataType.Int32,
            filterable=True,
        ),
        SearchableField(
            name="content",
            type=SearchFieldDataType.String,
        ),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            hidden=True,
            vector_search_dimensions=EMBEDDING_DIMENSIONS,
            vector_search_profile_name="default-vector-profile",
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(name="default-hnsw"),
        ],
        profiles=[
            VectorSearchProfile(
                name="default-vector-profile",
                algorithm_configuration_name="default-hnsw",
            ),
        ],
    )

    index = SearchIndex(
        name=index_name,
        fields=fields,
        vector_search=vector_search,
    )

    index_client.create_or_update_index(index)
    print(f"Search index ready: {index_name}")


def add_embeddings(chunks, openai_client, embedding_deployment):
    for start in range(0, len(chunks), EMBEDDING_BATCH_SIZE):
        batch = chunks[start:start + EMBEDDING_BATCH_SIZE]
        response = openai_client.embeddings.create(
            model=embedding_deployment,
            input=[chunk["content"] for chunk in batch],
            dimensions=EMBEDDING_DIMENSIONS,
        )

        for chunk, embedding in zip(batch, response.data):
            chunk["content_vector"] = embedding.embedding

        print(f"Embedded {min(start + len(batch), len(chunks))}/{len(chunks)} chunks")


def upload_chunks(search_client, chunks):
    failed_uploads = []

    for start in range(0, len(chunks), UPLOAD_BATCH_SIZE):
        batch = chunks[start:start + UPLOAD_BATCH_SIZE]
        results = search_client.upload_documents(documents=batch)
        failed_uploads.extend(result for result in results if not result.succeeded)
        print(f"Uploaded {min(start + len(batch), len(chunks))}/{len(chunks)} chunks")

    if failed_uploads:
        messages = "; ".join(
            f"{result.key}: {result.error_message}" for result in failed_uploads
        )
        raise RuntimeError(f"Some documents failed to upload: {messages}")


def verify_index(search_client, openai_client, embedding_deployment):
    query = "What percentage of AI-103 covers generative AI and agentic solutions?"
    query_embedding = openai_client.embeddings.create(
        model=embedding_deployment,
        input=query,
        dimensions=EMBEDDING_DIMENSIONS,
    ).data[0].embedding

    vector_query = VectorizedQuery(
        vector=query_embedding,
        k_nearest_neighbors=3,
        fields="content_vector",
    )

    results = search_client.search(
        search_text=query,
        vector_queries=[vector_query],
        select=["title", "source", "chunk_number", "content"],
        top=3,
    )

    print("\nVerification search results:")
    for rank, result in enumerate(results, start=1):
        preview = result["content"][:180].replace("\n", " ")
        print(
            f"{rank}. {result['title']} "
            f"({result['source']}, chunk {result['chunk_number']})\n"
            f"   Score: {result['@search.score']:.4f}\n"
            f"   {preview}..."
        )


def main():
    openai_endpoint = required_environment_variable("AZURE_OPENAI_ENDPOINT")
    embedding_deployment = required_environment_variable(
        "EMBEDDING_MODEL_DEPLOYMENT"
    )
    search_endpoint = required_environment_variable("AZURE_SEARCH_ENDPOINT")
    index_name = os.environ.get("AZURE_SEARCH_INDEX_NAME", "ai103-study-index")

    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(
        credential,
        "https://cognitiveservices.azure.com/.default",
    )
    openai_client = OpenAI(
        base_url=f"{openai_endpoint.rstrip('/')}/openai/v1/",
        api_key=token_provider,
    )
    index_client = SearchIndexClient(
        endpoint=search_endpoint,
        credential=credential,
    )
    search_client = SearchClient(
        endpoint=search_endpoint,
        index_name=index_name,
        credential=credential,
    )

    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks from {DATA_DIRECTORY}")

    create_or_update_index(index_client, index_name)
    add_embeddings(chunks, openai_client, embedding_deployment)
    upload_chunks(search_client, chunks)
    verify_index(search_client, openai_client, embedding_deployment)


if __name__ == "__main__":
    main()
