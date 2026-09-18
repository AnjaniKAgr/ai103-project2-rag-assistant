# Microsoft Foundry Agent Runtime

Last reviewed: September 14, 2026

## Core components

Microsoft Foundry Agent Service uses agents, conversations, and responses as its core runtime components.

An agent is a reusable, versioned definition containing a model, instructions, tools, parameters, and optional safety or governance controls. Use an agent when many requests should share the same behavior and tool configuration.

A conversation stores input and output items across turns. Use a conversation when later questions need server-side history. Conversation memory within a session is different from persistent memory across separate sessions.

A response is one execution of a model or agent against input. A response can contain natural-language output, function calls, or other output items. Every interaction produces a response, whether or not the application uses a persisted agent or conversation.

## Typical lifecycle

1. The application selects an agent.
2. It creates or reuses a conversation.
3. The user message is submitted as input to a response.
4. The model returns text or requests tools.
5. The application executes client-side tools and returns outputs with their matching call identifiers.
6. Tool processing repeats until the model provides a final answer.
7. The response items are retained in the conversation for later turns.

## Tools and knowledge

Tools let an agent retrieve information or perform actions. Examples include custom function calls, Azure AI Search, file search, web search, OpenAPI tools, MCP servers, code execution, and Azure Functions.

Custom function calling is appropriate when tool code runs inside the client application. Azure Functions or MCP-hosted tools can provide stronger separation, centralized management, reuse, scaling, and security isolation for enterprise scenarios.

Knowledge retrieval is different from action tools. Retrieval supplies grounded context from approved sources. Action tools change or query external systems. Both should follow least-privilege access and should expose clear schemas and descriptions.

## State and memory

A conversation preserves history within that conversation. Persistent memory can retain selected facts across sessions but should be used deliberately. Applications must decide what to store, for how long, and under which user identity. Sensitive information, deletion requirements, and user consent are important design considerations.

## Reliability and security

Production agent loops should handle multiple tool calls, invalid arguments, unknown tools, timeouts, rate limits, incomplete responses, and repeated tool-call cycles. Set limits on autonomous actions and require approval before sensitive operations.

Use Microsoft Entra ID and managed identities where possible. Restrict each agent and tool to the permissions required for its task. Add tracing so developers can inspect inputs, tool calls, outputs, latency, failures, and token usage without logging secrets.

## Official sources

- Runtime components: https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/runtime-components
- Foundry Agent Service overview: https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview
- Azure Functions tools: https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/azure-functions
