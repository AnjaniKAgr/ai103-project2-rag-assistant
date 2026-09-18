"""Evaluate the complete AI-103 RAG pipeline with Microsoft evaluators."""

import importlib.util
import json
import os
from pathlib import Path

from azure.ai.evaluation import (
    GroundednessEvaluator,
    RelevanceEvaluator,
    RetrievalEvaluator,
    evaluate,
)
from azure.identity import DefaultAzureCredential


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_PATH = PROJECT_ROOT / "eval-data.jsonl"
GENERATED_DATA_PATH = PROJECT_ROOT / "eval-generated.jsonl"
OUTPUT_PATH = PROJECT_ROOT / "eval-results.json"


def load_rag_module():
    """Load ``rag-assistant.py`` even though its filename contains a hyphen.

    Python cannot import a hyphenated filename with a normal import statement,
    so this function creates a module specification from the exact file path
    and executes it as the module named ``rag_assistant``.
    """
    module_path = PROJECT_ROOT / "rag-assistant.py"
    specification = importlib.util.spec_from_file_location(
        "rag_assistant",
        module_path,
    )
    if specification is None or specification.loader is None:
        raise RuntimeError(f"Unable to load {module_path}")

    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def generate_evaluation_data(rag_module):
    """Run every test query through the RAG app and save its outputs.

    Generation happens before ``evaluate`` starts because the evaluation SDK's
    legacy target tracer cannot currently process embedding token-usage
    objects. Each output row contains the original query, the retrieved
    context, and the generated response needed by the three evaluators.
    """
    openai_client, search_client = rag_module.create_clients()
    embedding_deployment = rag_module.required_environment_variable(
        "EMBEDDING_MODEL_DEPLOYMENT"
    )
    chat_deployment = os.environ.get("CHAT_MODEL_DEPLOYMENT", "gpt-4o")

    with DATA_PATH.open(encoding="utf-8") as source_file:
        test_rows = [json.loads(line) for line in source_file if line.strip()]

    with GENERATED_DATA_PATH.open("w", encoding="utf-8") as output_file:
        for number, row in enumerate(test_rows, start=1):
            query = row["query"]
            results = rag_module.retrieve_context(
                query,
                openai_client,
                search_client,
                embedding_deployment,
            )
            context = rag_module.format_context(results)
            response = rag_module.generate_answer(
                query,
                [],
                results,
                openai_client,
                chat_deployment,
            )
            output_file.write(
                json.dumps(
                    {
                        "query": query,
                        "response": response,
                        "context": context,
                    }
                )
                + "\n"
            )
            print(f"Generated {number}/{len(test_rows)} evaluation responses")


def create_evaluators():
    """Create model-assisted evaluators for the important RAG quality areas.

    The configured ``gpt-4o`` deployment acts as the judge. Retrieval measures
    whether the chunks address the query, groundedness checks whether the
    answer is supported by those chunks, and relevance checks whether the
    answer directly addresses the user's question.
    """
    credential = DefaultAzureCredential()
    model_config = {
        "azure_endpoint": os.environ["AZURE_OPENAI_ENDPOINT"],
        "azure_deployment": os.environ.get("CHAT_MODEL_DEPLOYMENT", "gpt-4o"),
    }
    return {
        "retrieval": RetrievalEvaluator(model_config, credential=credential),
        "groundedness": GroundednessEvaluator(
            model_config,
            credential=credential,
        ),
        "relevance": RelevanceEvaluator(model_config, credential=credential),
    }


def main():
    """Run all dataset questions through the RAG app and save the scores.

    The RAG application first creates a dataset containing its response and
    retrieved context for every query. The Azure evaluation SDK then maps those
    fields into the three evaluators. Detailed row-level results and aggregate
    metrics are written to ``eval-results.json`` for later comparison.
    """
    rag_module = load_rag_module()
    generate_evaluation_data(rag_module)
    result = evaluate(
        data=GENERATED_DATA_PATH,
        evaluation_name="ai103-project2-rag-baseline",
        evaluators=create_evaluators(),
        evaluator_config={
            "default": {
                "column_mapping": {
                    "query": "${data.query}",
                    "response": "${data.response}",
                    "context": "${data.context}",
                }
            }
        },
        output_path=OUTPUT_PATH,
    )
    print(f"\nEvaluation complete. Results: {OUTPUT_PATH}")
    print(result.get("metrics", result))


if __name__ == "__main__":
    main()
