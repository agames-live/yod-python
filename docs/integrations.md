# LLM Integration Guide

This guide shows how to integrate Amemo with popular LLM frameworks to add personal memory to your AI applications.

## Overview

Amemo provides personal memory for LLMs by:
1. **Storing** user information via the ingest endpoint
2. **Retrieving** relevant context via the chat endpoint
3. **Augmenting** LLM prompts with personalized context

This enables LLMs to "remember" user preferences, facts, and history across conversations.

---

## OpenAI Integration

### Basic Context Injection

Inject user memories into your OpenAI prompts:

```python
from openai import OpenAI
from amemo import AmemoClient

openai_client = OpenAI()
amemo_client = AmemoClient(api_key="sk-amemo-...")

def chat_with_memory(user_message: str) -> str:
    # 1. Get relevant memories
    memory_response = amemo_client.chat(user_message)

    # 2. Build system prompt with context
    system_prompt = f"""You are a helpful assistant with access to the user's personal information.

User Context (from their stored memories):
{memory_response.answer}

Use this context to personalize your responses. If the context doesn't contain relevant information, respond based on the conversation alone."""

    # 3. Generate response with context
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )

    return response.choices[0].message.content

# Usage
response = chat_with_memory("Can you recommend a gift for my dog?")
# With Amemo, the LLM knows the dog's name is Max!
```

### Function Calling Integration

Use Amemo as a tool with OpenAI's function calling:

```python
from openai import OpenAI
from amemo import AmemoClient
import json

openai_client = OpenAI()
amemo_client = AmemoClient(api_key="sk-amemo-...")

# Define tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_user_memory",
            "description": "Retrieve personal information about the user from their stored memories. Use this when you need to know user preferences, facts, relationships, or history.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The question to ask about the user's memories"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "store_user_memory",
            "description": "Store new information the user shares about themselves. Use this when the user tells you personal facts, preferences, or updates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "information": {
                        "type": "string",
                        "description": "The information to store"
                    }
                },
                "required": ["information"]
            }
        }
    }
]

def handle_tool_call(tool_call):
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)

    if name == "get_user_memory":
        response = amemo_client.chat(args["query"])
        return response.answer
    elif name == "store_user_memory":
        amemo_client.ingest_chat(args["information"])
        return "Information stored successfully."

    return "Unknown function"

def chat_with_tools(user_message: str, conversation_history: list) -> str:
    messages = conversation_history + [{"role": "user", "content": user_message}]

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    message = response.choices[0].message

    # Handle tool calls
    if message.tool_calls:
        messages.append(message)

        for tool_call in message.tool_calls:
            result = handle_tool_call(tool_call)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

        # Get final response
        final_response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        return final_response.choices[0].message.content

    return message.content

# Usage
history = [{"role": "system", "content": "You are a helpful assistant."}]
response = chat_with_tools("What's my favorite color?", history)
```

### Structured Output with Memories

Combine memories with structured outputs:

```python
from pydantic import BaseModel
from openai import OpenAI
from amemo import AmemoClient

class GiftRecommendation(BaseModel):
    gift_name: str
    reason: str
    price_range: str
    personalization_note: str

def get_personalized_recommendation(recipient: str) -> GiftRecommendation:
    # Get relevant memories
    memory = amemo_client.chat(f"What do I know about {recipient}?")

    response = openai_client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"User context: {memory.answer}"},
            {"role": "user", "content": f"Recommend a gift for {recipient}"}
        ],
        response_format=GiftRecommendation
    )

    return response.choices[0].message.parsed

# If user has stored "My sister Sarah loves gardening"
rec = get_personalized_recommendation("my sister Sarah")
# Returns personalized gardening gift recommendation!
```

---

## Anthropic (Claude) Integration

### Basic Integration

```python
import anthropic
from amemo import AmemoClient

claude = anthropic.Anthropic()
amemo = AmemoClient(api_key="sk-amemo-...")

def chat_with_memory(user_message: str) -> str:
    # Get memories
    memory = amemo.chat(user_message)

    response = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=f"""You are a helpful assistant with access to the user's personal memories.

User Context:
{memory.answer}

Sources: {', '.join([c.quote for c in memory.citations[:3]])}

Use this context to personalize your response.""",
        messages=[
            {"role": "user", "content": user_message}
        ]
    )

    return response.content[0].text
```

### Tool Use with Claude

```python
import anthropic
from amemo import AmemoClient

claude = anthropic.Anthropic()
amemo = AmemoClient(api_key="sk-amemo-...")

tools = [
    {
        "name": "get_user_memory",
        "description": "Retrieve personal information about the user from their stored memories.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Question about user's memories"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "store_user_memory",
        "description": "Store new personal information the user shares.",
        "input_schema": {
            "type": "object",
            "properties": {
                "information": {
                    "type": "string",
                    "description": "Information to store"
                }
            },
            "required": ["information"]
        }
    }
]

def process_tool_use(tool_name: str, tool_input: dict) -> str:
    if tool_name == "get_user_memory":
        response = amemo.chat(tool_input["query"])
        return response.answer
    elif tool_name == "store_user_memory":
        amemo.ingest_chat(tool_input["information"])
        return "Stored successfully"
    return "Unknown tool"

def chat_with_tools(user_message: str) -> str:
    messages = [{"role": "user", "content": user_message}]

    response = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=tools,
        messages=messages
    )

    # Handle tool use
    while response.stop_reason == "tool_use":
        tool_use = next(b for b in response.content if b.type == "tool_use")
        tool_result = process_tool_use(tool_use.name, tool_use.input)

        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": tool_result
            }]
        })

        response = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            tools=tools,
            messages=messages
        )

    return response.content[0].text
```

---

## LangChain Integration

### As a Custom Tool

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.tools import StructuredTool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from amemo import AmemoClient

amemo = AmemoClient(api_key="sk-amemo-...")

def get_user_memory(query: str) -> str:
    """Retrieve personal information about the user from their stored memories."""
    response = amemo.chat(query)
    return f"Answer: {response.answer}\nSources: {[c.quote for c in response.citations]}"

def store_user_memory(information: str) -> str:
    """Store new personal information the user shares."""
    amemo.ingest_chat(information)
    return "Information stored successfully."

tools = [
    StructuredTool.from_function(
        func=get_user_memory,
        name="get_user_memory",
        description="Get personal information about the user from their memories"
    ),
    StructuredTool.from_function(
        func=store_user_memory,
        name="store_user_memory",
        description="Store new personal information the user shares"
    )
]

llm = ChatOpenAI(model="gpt-4o")

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant with access to user memories."),
    MessagesPlaceholder("chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])

agent = create_openai_functions_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)

# Usage
response = agent_executor.invoke({"input": "What's my dog's name?"})
print(response["output"])
```

### As a Custom Retriever

```python
from langchain.schema import BaseRetriever, Document
from amemo import AmemoClient
from typing import List

class AmemoRetriever(BaseRetriever):
    """Retriever that fetches user memories from Amemo."""

    client: AmemoClient

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(self, query: str) -> List[Document]:
        response = self.client.chat(query)

        documents = []
        for citation in response.citations:
            documents.append(Document(
                page_content=citation.quote,
                metadata={"source_id": citation.source_id}
            ))

        # Add the synthesized answer as a document too
        if response.answer:
            documents.insert(0, Document(
                page_content=response.answer,
                metadata={"type": "synthesized_answer"}
            ))

        return documents

    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        return self._get_relevant_documents(query)

# Usage with RAG
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

retriever = AmemoRetriever(client=AmemoClient(api_key="sk-amemo-..."))
llm = ChatOpenAI(model="gpt-4o")

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever
)

answer = qa_chain.invoke("What are my hobbies?")
```

---

## LlamaIndex Integration

### As a Custom Query Engine

```python
from llama_index.core import QueryBundle
from llama_index.core.query_engine import BaseQueryEngine
from llama_index.core.response.schema import Response
from amemo import AmemoClient

class AmemoQueryEngine(BaseQueryEngine):
    """Query engine that retrieves from Amemo memories."""

    def __init__(self, amemo_client: AmemoClient):
        self._client = amemo_client
        super().__init__(callback_manager=None)

    def _query(self, query_bundle: QueryBundle) -> Response:
        response = self._client.chat(query_bundle.query_str)

        # Create source nodes from citations
        from llama_index.core.schema import NodeWithScore, TextNode
        source_nodes = [
            NodeWithScore(
                node=TextNode(text=c.quote, id_=c.source_id),
                score=1.0
            )
            for c in response.citations
        ]

        return Response(
            response=response.answer,
            source_nodes=source_nodes,
            metadata={"memory_ids": response.used_memory_ids}
        )

    async def _aquery(self, query_bundle: QueryBundle) -> Response:
        return self._query(query_bundle)

# Usage
from amemo import AmemoClient

amemo = AmemoClient(api_key="sk-amemo-...")
query_engine = AmemoQueryEngine(amemo)

response = query_engine.query("What do I like to do on weekends?")
print(response.response)
print([n.node.text for n in response.source_nodes])
```

### As a Tool for Agents

```python
from llama_index.core.tools import FunctionTool
from llama_index.agent.openai import OpenAIAgent
from llama_index.llms.openai import OpenAI
from amemo import AmemoClient

amemo = AmemoClient(api_key="sk-amemo-...")

def get_user_memory(query: str) -> str:
    """Get personal information about the user from their stored memories.

    Args:
        query: The question to ask about user memories
    """
    response = amemo.chat(query)
    return response.answer

def store_user_memory(information: str) -> str:
    """Store new personal information that the user shares.

    Args:
        information: The information to store
    """
    amemo.ingest_chat(information)
    return "Stored successfully"

tools = [
    FunctionTool.from_defaults(fn=get_user_memory),
    FunctionTool.from_defaults(fn=store_user_memory)
]

llm = OpenAI(model="gpt-4o")
agent = OpenAIAgent.from_tools(tools, llm=llm, verbose=True)

response = agent.chat("What's my favorite programming language?")
```

---

## Best Practices

### 1. Efficient Memory Retrieval

```python
# Good: Specific, focused queries
memory = amemo.chat("What is the user's preferred programming language?")

# Avoid: Overly broad queries that return too much context
memory = amemo.chat("Tell me everything about the user")
```

### 2. Automatic Memory Ingestion

Store new information automatically during conversations:

```python
def process_user_message(message: str) -> str:
    # Check if message contains new personal information
    if contains_personal_info(message):
        amemo.ingest_chat(message)

    # Continue with normal processing
    memory = amemo.chat(message)
    return generate_response(message, memory)
```

### 3. Handle Missing Memories Gracefully

```python
memory = amemo.chat("What's my favorite restaurant?")

if not memory.citations:
    # No relevant memories found
    response = "I don't have any stored information about your favorite restaurant. What's your favorite?"
else:
    response = f"Based on what you've told me: {memory.answer}"
```

### 4. Use Temporal Queries for Context

```python
# Get memories as they were at a specific time
historical = amemo.chat(
    question="Where did I work?",
    as_of="2023-01-01T00:00:00Z"
)
```

### 5. Batch Operations for Efficiency

```python
# Ingest multiple pieces of information
conversation = """
User mentioned their name is Alex.
They work as a software engineer.
Their favorite color is blue.
They have a dog named Max.
"""
amemo.ingest_chat(conversation, source_id="onboarding-session")
```

---

## Error Handling

```python
from amemo import (
    AmemoError,
    RateLimitError,
    AuthenticationError
)

def safe_memory_query(query: str) -> str | None:
    try:
        response = amemo.chat(query)
        return response.answer
    except RateLimitError:
        # Wait and retry, or use cached context
        return get_cached_context(query)
    except AuthenticationError:
        # Handle auth issues
        log.error("Amemo authentication failed")
        return None
    except AmemoError as e:
        # General error handling
        log.warning(f"Memory retrieval failed: {e}")
        return None
```

---

## Performance Tips

1. **Cache frequently accessed memories** - User profile facts don't change often
2. **Use async clients for concurrent requests** - `AsyncAmemoClient` for high-throughput
3. **Batch ingestion** - Combine related information in single requests
4. **Set appropriate timeouts** - Balance responsiveness with reliability

```python
from amemo import AsyncAmemoClient
import asyncio

async def parallel_memory_queries(queries: list[str]) -> list[str]:
    async with AsyncAmemoClient(api_key="sk-amemo-...") as client:
        tasks = [client.chat(q) for q in queries]
        responses = await asyncio.gather(*tasks)
        return [r.answer for r in responses]
```
