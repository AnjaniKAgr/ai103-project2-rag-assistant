import os

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import OpenAI


EMBEDDING_DIMENSIONS = 1536
TOP_K = 4
VECTOR_CANDIDATES = 10
MAX_HISTORY_MESSAGES = 6


def required_environment_variable(name):
    """Return a required configuration value from the environment.

    The function looks up ``name`` in the process environment. It raises a
    clear error immediately when the value is missing so the application does
    not fail later with a less useful authentication or connection error.
    """
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required environment variable is missing: {name}")
    return value


def create_clients():
    """Create authenticated clients for Azure OpenAI and Azure AI Search.

    The function reads the service endpoints and index name, obtains an Azure
    identity through ``DefaultAzureCredential``, and converts that identity
    into a bearer-token provider for Azure OpenAI. The same credential is used
    directly by the Search client. It returns both clients so they can be
    reused for every question instead of being recreated on each turn.
    """
    openai_endpoint = required_environment_variable("AZURE_OPENAI_ENDPOINT")
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
    search_client = SearchClient(
        endpoint=search_endpoint,
        index_name=index_name,
        credential=credential,
    )
    return openai_client, search_client


def retrieve_context(
    question,
    openai_client,
    search_client,
    embedding_deployment,
):
    """Retrieve study passages related to the user's question.

    The question is first converted into a 1,536-dimension embedding with the
    configured embedding deployment. Azure AI Search then runs a hybrid query:
    ``search_text`` performs keyword search while ``VectorizedQuery`` finds
    semantically similar vectors. A wider vector candidate pool is merged
    with keyword matches, then only the best ``TOP_K`` chunks are returned.
    """
    query_embedding = openai_client.embeddings.create(
        model=embedding_deployment,
        input=question,
        dimensions=EMBEDDING_DIMENSIONS,
    ).data[0].embedding

    vector_query = VectorizedQuery(
        vector=query_embedding,
        k_nearest_neighbors=VECTOR_CANDIDATES,
        fields="content_vector",
    )
    results = search_client.search(
        search_text=question,
        search_fields=["content"],
        vector_queries=[vector_query],
        select=["title", "source", "chunk_number", "content"],
        top=TOP_K,
    )
    return list(results)


def format_context(results):
    """Convert Search results into numbered context for the chat model.

    Each retrieved chunk receives a bracketed source number and includes its
    title, filename, chunk number, and content. These numbers let the model
    connect statements in its answer to citations such as ``[1]``.
    """
    sections = []
    for number, result in enumerate(results, start=1):
        sections.append(
            f"[{number}] {result['title']}\n"
            f"Source: {result['source']}, chunk {result['chunk_number']}\n"
            f"{result['content']}"
        )
    return "\n\n".join(sections)


def answer_question(
    question,
    history,
    openai_client,
    search_client,
    embedding_deployment,
    chat_deployment,
):
    """Retrieve evidence and generate one grounded answer with citations.

    The function retrieves relevant chunks, formats them as evidence, and
    builds a chat request containing grounding instructions, recent message
    history, the current question, and the retrieved context. The model is
    instructed to use only that context and admit when evidence is missing.
    Finally, a readable source list is appended to the generated answer.
    """
    results = retrieve_context(
        question,
        openai_client,
        search_client,
        embedding_deployment,
    )
    return generate_answer(
        question,
        history,
        results,
        openai_client,
        chat_deployment,
    )


def generate_answer(
    question,
    history,
    results,
    openai_client,
    chat_deployment,
):
    """Generate a grounded answer from already-retrieved Search results.

    Keeping generation separate from retrieval lets the interactive app and
    the evaluation runner use the exact same answer-generation code. The
    function formats the supplied chunks, builds the grounded chat prompt,
    calls the chat deployment, and appends the numbered source list.
    """
    if not results:
        return "I could not find relevant information in the study documents."

    context = format_context(results)
    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI-103 study assistant. Answer only from the "
                "retrieved context supplied with the current question. "
                "If the context is insufficient, say you do not have enough "
                "information. Cite supporting passages with bracketed source "
                "numbers such as [1] or [2]. Be concise and accurate."
            ),
        },
        *history[-MAX_HISTORY_MESSAGES:],
        {
            "role": "user",
            "content": (
                f"Question:\n{question}\n\n"
                f"Retrieved context:\n{context}"
            ),
        },
    ]

    response = openai_client.chat.completions.create(
        model=chat_deployment,
        messages=messages,
        temperature=0,
    )
    answer = response.choices[0].message.content

    sources = []
    for number, result in enumerate(results, start=1):
        sources.append(
            f"[{number}] {result['source']} (chunk {result['chunk_number']})"
        )
    return f"{answer}\n\nSources:\n" + "\n".join(sources)


def main():
    """Run the command-line conversation loop for the RAG assistant.

    Startup loads deployment settings and creates reusable service clients.
    The loop reads questions until the user enters ``exit`` or ``quit``, calls
    the complete retrieve-and-generate pipeline, prints the answer, and saves
    recent turns for conversational context. Empty input, Ctrl+C, and runtime
    errors are handled without an unhelpful stack trace.
    """
    embedding_deployment = required_environment_variable(
        "EMBEDDING_MODEL_DEPLOYMENT"
    )
    chat_deployment = os.environ.get("CHAT_MODEL_DEPLOYMENT", "gpt-4o")
    openai_client, search_client = create_clients()
    history = []

    print("AI-103 RAG Study Assistant")
    print("Ask a question, or type 'exit' to quit.\n")

    while True:
        try:
            question = input("You: ").strip()
            if question.lower() in {"exit", "quit"}:
                break
            if not question:
                continue

            answer = answer_question(
                question,
                history,
                openai_client,
                search_client,
                embedding_deployment,
                chat_deployment,
            )
            print(f"\nAssistant: {answer}\n")
            history.extend(
                [
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": answer},
                ]
            )
        except KeyboardInterrupt:
            print("\nGoodbye.")
            break
        except Exception as error:
            print(f"\nError: {error}\n")


if __name__ == "__main__":
    main()
