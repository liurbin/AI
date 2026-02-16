---
name: llm-gateway-spec
description: Generate a technology-agnostic LLM API Gateway architecture design spec. Based on the Azure AI Gateway capability model, outputs a complete design specification document that can directly guide LLM code generation.
---

# LLM Gateway Architecture Design Spec Generator

Based on the Azure API Management AI Gateway capability model (https://learn.microsoft.com/en-us/azure/api-management/genai-gateway-capabilities), generate a technology-agnostic LLM API Gateway architecture design framework.

## Goals

Output a structured design specification document that satisfies:
1. **Technology-agnostic** — Not bound to any cloud vendor or specific tech stack; users choose their own implementation
2. **Completeness** — Covers all core LLM Gateway capability modules with no gaps
3. **Actionable** — Detailed enough that an LLM can directly generate concrete code implementations from it
4. **Tailorable** — Users can select which modules to enable based on their needs

## Instructions

### Step 1: Gather User Requirements

Use the AskUserQuestion tool to collect the following information:

**Question 1: Gateway Scale & Scenario**
- Personal / small team (single app, 1-2 models)
- Mid-size team (multiple apps, 3-5 models, billing isolation needed)
- Enterprise (multi-tenant, multiple models, high availability, compliance requirements)

**Question 2: Model Providers to Support** (multi-select)
- OpenAI / Azure OpenAI
- Anthropic Claude
- Self-hosted open-source models (vLLM / Ollama / TGI, etc.)
- Other commercial APIs (Gemini, Deepseek, Qwen, etc.)

**Question 3: Deployment Environment**
- Kubernetes
- Docker Compose
- Bare metal / VM
- Serverless

**Question 4: Required Capability Modules** (multi-select)
- Multi-model routing & load balancing
- Token rate limiting & quota management
- Semantic caching
- Security & authentication
- Observability (metrics + logging)
- Content safety moderation
- All of the above

### Step 2: Generate Design Specification Document

Based on user responses, generate a design document with the following structure. If the user selected "All of the above" or did not explicitly exclude a module, output the full version.

---

## Design Specification Document Structure

Output format is Markdown, containing the following chapters:

### 1. Overview

```
# LLM API Gateway Design Specification

## 1. Overview

### 1.1 Objectives
[Describe based on the user's selected scale/scenario]

### 1.2 Scope
- Supported models: [User's selected model provider list]
- Deployment environment: [User's selected deployment environment]
- Capability modules: [User's selected module list]

### 1.3 Core Design Principles
- Unified interface: All models exposed via OpenAI-compatible API format
- Pluggable: Each capability module is independent, can be enabled/disabled individually
- Stateless gateway: Gateway itself is stateless; state externalized to Redis/DB
- Streaming-first: Native SSE streaming support; non-streaming is the exception
```

### 2. System Architecture

```
## 2. System Architecture

### 2.1 Request Flow

Client → [Auth] → [Rate Limit] → [Cache Lookup] → [Route] → [Load Balance] → Model Backend
                                                                                 ↓
Client ← [Metrics Collection] ← [Logging] ← [Cache Write] ←──────────── Model Response

### 2.2 Core Components
- API Entry Layer: Receives requests, protocol normalization
- Middleware Pipeline: Auth → Rate Limit → Cache → Content Safety (configurable order)
- Routing Engine: Dispatches requests to target models based on rules
- Backend Manager: Model endpoint registration, health checks, connection pooling
- Data Plane: Metrics, logging, audit

### 2.3 Deployment Topology
[Describe recommended deployment architecture based on user's selected environment]
```

### 3. Multi-Model Routing & Load Balancing

```
## 3. Multi-Model Routing & Load Balancing

### 3.1 Model Registration
Each backend model requires the following registration info:
- endpoint_url: Model API address
- provider: Provider type (openai / anthropic / azure / custom)
- model_name: Model identifier
- api_key_ref: Secret reference (never stored in plaintext)
- priority: Priority level (1 = highest)
- weight: Weight (for weighted round-robin)
- max_tpm: TPM ceiling for this endpoint
- region: Deployment region (optional)
- tags: Custom tags for route matching

### 3.2 Routing Strategies
- Exact match: Request specifies model=gpt-4o, routes to corresponding endpoint
- Alias mapping: model=default → maps to the configured default model
- Tag-based routing: Match by tags (e.g., tier=premium routes to PTU instance)
- Fallback chain: On primary model failure, try alternatives in priority order

### 3.3 Load Balancing Algorithms
- round-robin: Simple round-robin
- weighted: Distribute traffic by weight
- priority: Priority mode; overflow to lower priority only when higher is at capacity
- least-tokens: Prefer endpoint with lowest current token consumption (requires real-time counting)
- session-affinity: Keep same session routed to same endpoint (based on session_id)

### 3.4 Health Checks
- Passive checks: Determine backend health based on response status codes and latency
- Active checks: Periodically send lightweight probe requests
- Circuit breaker rules: Trip after N consecutive failures, read Retry-After header for dynamic recovery
- Circuit breaker states: closed → open → half-open → closed
```

### 4. Token Rate Limiting & Quota Management

```
## 4. Token Rate Limiting & Quota Management

### 4.1 Rate Limiting Dimensions
Rate limit keys can be composed along these dimensions:
- api_key: By API Key
- user_id: By user
- org_id: By organization / tenant
- ip: By source IP
- model: By model
- custom: Custom expression (e.g., a header field)

### 4.2 Rate Limiting Metrics
- TPM (Tokens Per Minute): Tokens per minute
- RPM (Requests Per Minute): Requests per minute
- TPD (Tokens Per Day): Daily token quota
- Token Quota: Total token budget over a specified period (weekly / monthly / yearly)

### 4.3 Token Counting Methods
- Post-counting: Extract actual usage from the model response's usage field
- Pre-estimation: Estimate token count from prompt length at request time; reject requests that clearly exceed limits
- Hybrid mode: Pre-estimate to intercept at request time, correct counter with actual values from response

### 4.4 Over-Limit Handling
- Return 429 Too Many Requests with Retry-After header
- Optional: Queue and wait (suitable for batch processing scenarios)
- Optional: Degrade by routing to a lower-priority model

### 4.5 Counter Storage
- Storage medium: Redis (recommended) or in-memory (single-instance scenarios)
- Counter key format: rate:{dimension}:{value}:{window}
- Window algorithm: Sliding window (recommended) or fixed window
```

### 5. Semantic Caching

```
## 5. Semantic Caching

### 5.1 How It Works
1. On receiving a request, convert the prompt to a vector via an Embedding model
2. Search the vector store for historical prompts exceeding the similarity threshold
3. Hit: Return the cached completion directly without calling the backend model
4. Miss: Call backend normally; after response, write prompt vector + completion to cache

### 5.2 Configuration Parameters
- embedding_model: Model used to generate prompt vectors
- similarity_threshold: Similarity threshold (0.0-1.0, recommended 0.95+)
- cache_ttl: Cache expiration time
- max_cache_size: Maximum cache capacity
- excluded_models: Models for which caching is disabled
- excluded_paths: API paths excluded from caching

### 5.3 Cache Key Strategies
- Based on user prompt only (ignore system prompt differences)
- Based on complete messages array
- Based on user prompt + model combination
- Configurable per business scenario

### 5.4 Storage Options
- Redis + RediSearch (vector search module)
- Standalone vector database (Qdrant / Milvus / Weaviate)
- In-memory (single-instance development environments only)

### 5.5 Important Considerations
- Streaming request caching requires full collection before storage
- Cache hits should also be recorded as a "request" for statistics
- Provide a manual cache-clear admin endpoint
```

### 6. Security & Authentication

```
## 6. Security & Authentication

### 6.1 Client Authentication
- API Key: Via header (Authorization: Bearer xxx) or query param
- OAuth 2.0 / JWT: Validate token signature and claims
- mTLS: Mutual TLS certificate authentication (enterprise scenarios)
- Multiple methods can be combined

### 6.2 Backend Authentication
- Gateway centrally manages API keys for each model provider
- Clients do not need backend API keys; only Gateway-issued credentials
- Secret storage: Environment variables / Secret Manager / Vault (never plaintext in config files)

### 6.3 Authorization & Permissions
- Bind accessible model list per API Key
- Bind token quota per API Key
- Bind rate limit rules per API Key
- Optional: RBAC (admin / developer / readonly)

### 6.4 Transport Security
- Gateway ingress must use TLS
- Gateway-to-backend model connections should also use TLS
- Sensitive log redaction (API Keys, PII in prompts)
```

### 7. Observability

```
## 7. Observability

### 7.1 Metrics
Required metrics to collect:
- request_count: Total requests (dimensioned by model / status_code / api_key)
- token_usage: Token consumption (prompt_tokens / completion_tokens / total_tokens)
- latency: Request latency (p50 / p95 / p99)
- ttft: Time to First Token (critical metric for streaming scenarios)
- cache_hit_rate: Semantic cache hit rate
- rate_limit_rejected: Rate limit rejection count
- backend_health: Backend health status
- active_connections: Current active connection count

Metrics output format: Prometheus exposition format (universally compatible)

### 7.2 Logging
Record per request:
- request_id: Unique request identifier
- timestamp: Request time
- api_key_id: Caller identifier (redacted)
- model: Requested model
- backend_endpoint: Actual backend routed to
- prompt_tokens / completion_tokens: Token usage
- latency_ms: Total latency
- status_code: Response status code
- Optional: Full prompt / completion text (for audit; requires encrypted storage)

Log output: Structured JSON, to stdout (container environments) or file

### 7.3 Tracing
- Support OpenTelemetry standard
- Key spans: Auth → Rate Limit → Cache Lookup → Route → Backend Call → Response Processing
- Correlate full request chain via trace_id

### 7.4 Dashboards
Pre-built dashboards should include:
- Global traffic overview (QPS / Token consumption trends)
- Usage distribution by model / tenant
- Latency distribution and anomaly detection
- Backend health status map
- Cost estimation (based on token usage × unit price)
```

### 8. Content Safety Moderation

```
## 8. Content Safety Moderation

### 8.1 Moderation Timing
- Request phase: Check user prompt
- Response phase: Check model completion
- Configurable: check request only, response only, or both

### 8.2 Moderation Strategies
- Keyword filtering: Fast filtering based on blocklists / regex
- Classification model: Call a content safety model for categorization (violence / sexual / hate / self-harm, etc.)
- Custom rules: Business-specific moderation logic (e.g., prohibit discussion of competitors)
- PII detection: Identify and redact personally identifiable information

### 8.3 Moderation Result Handling
- Block: Return standard error response; do not forward to backend
- Alert: Allow through but log an alert
- Rewrite: Auto-redact/replace sensitive content before continuing

### 8.4 Configuration Granularity
- Global default policy
- Per-model override
- Per API Key / tenant override
```

### 9. Configuration Management

```
## 9. Configuration Management

### 9.1 Configuration Structure
Gateway configuration is divided into:
- Global config: Listen port, TLS, log level
- Backend config: Model endpoint list and their attributes
- Routing config: Routing rules and load balancing strategies
- Policy config: Rate limiting, caching, content safety rules
- Tenant config: Per API Key permissions and quotas

### 9.2 Configuration Format
YAML as the primary configuration format. Example skeleton:

gateway:
  listen: 0.0.0.0:8080
  tls: { cert_file: ..., key_file: ... }

backends:
  - name: gpt-4o-primary
    provider: openai
    endpoint: https://api.openai.com/v1
    model: gpt-4o
    api_key_ref: env:OPENAI_API_KEY
    priority: 1
    weight: 100
    max_tpm: 100000

  - name: deepseek-fallback
    provider: custom
    endpoint: https://api.deepseek.com/v1
    model: deepseek-chat
    api_key_ref: env:DEEPSEEK_API_KEY
    priority: 2
    weight: 50

routing:
  default_backend: gpt-4o-primary
  fallback_chain: [gpt-4o-primary, deepseek-fallback]
  rules:
    - match: { model: "gpt-4o" }
      backends: [gpt-4o-primary]
    - match: { header: "x-tier: economy" }
      backends: [deepseek-fallback]

rate_limiting:
  default:
    tpm: 10000
    rpm: 100
  overrides:
    - key_type: api_key
      key_value: "premium-client"
      tpm: 50000

caching:
  enabled: true
  similarity_threshold: 0.95
  ttl: 3600

content_safety:
  enabled: true
  check_request: true
  check_response: false

observability:
  metrics:
    enabled: true
    endpoint: /metrics
  logging:
    level: info
    format: json
    log_prompts: false

### 9.3 Hot Reload
- Support configuration updates without gateway restart
- Backend list changes and rate limit rule changes should support hot reload
- TLS certificates and listen port changes require restart
```

### 10. Admin API

```
## 10. Admin API

The Gateway should provide an Admin API for operational management:

### 10.1 Backend Management
- POST   /admin/backends          — Register new backend
- GET    /admin/backends          — List all backends
- PUT    /admin/backends/{name}   — Update backend configuration
- DELETE /admin/backends/{name}   — Remove backend
- GET    /admin/backends/{name}/health — View backend health status

### 10.2 Rate Limit Management
- GET    /admin/rate-limits          — View current rate limit rules
- PUT    /admin/rate-limits/{key}    — Update rate limit quota
- GET    /admin/rate-limits/{key}/usage — View current usage

### 10.3 Cache Management
- DELETE /admin/cache              — Clear all cache
- GET    /admin/cache/stats        — Cache statistics

### 10.4 Operations
- GET    /health                   — Gateway health check
- GET    /ready                    — Readiness check
- GET    /metrics                  — Prometheus metrics endpoint
- POST   /admin/config/reload      — Hot reload configuration
```

### 11. Implementation Recommendations

```
## 11. Implementation Recommendations

### 11.1 Minimum Viable Product (MVP)
Recommended first phase:
1. Unified OpenAI-compatible entry point
2. Multi-model routing + simple round-robin load balancing
3. API Key authentication
4. Basic token counting and logging
5. Health checks and automatic backend removal

### 11.2 Phase 2: Enhanced
6. Token rate limiting (sliding window)
7. Circuit breaker and fallback
8. Prometheus metrics
9. Admin API

### 11.3 Phase 3: Advanced
10. Semantic caching
11. Content safety moderation
12. Multi-tenant quota management
13. Dashboards
14. Hot reload configuration

### 11.4 Key Interface Contract
The Gateway's external API must be 100% compatible with the OpenAI Chat Completions API:
- POST /v1/chat/completions (streaming + non-streaming)
- POST /v1/embeddings
- GET  /v1/models

Response format, error codes, and SSE format must all match OpenAI's specification, ensuring zero client-side changes for integration.
```

---

### Step 3: Output & Delivery

1. **Tailor** the design document by removing chapters for modules the user did not select
2. **Adjust complexity** based on the user's selected scale/scenario (remove multi-tenant, RBAC, and other enterprise features for personal scenarios)
3. **Use corresponding provider examples** in the backend configuration based on the user's selected model providers
4. **Provide matching architecture descriptions** in the deployment topology section based on the user's selected deployment environment
5. Output as a complete Markdown document
6. Remind the user: this document can be used directly as a prompt for an LLM — specify a tech stack and generate concrete implementation code
