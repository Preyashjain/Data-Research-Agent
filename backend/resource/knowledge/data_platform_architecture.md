# Data Research Agent Architecture

The Data Research Agent is a LangGraph workflow for analytical questions. It combines retrieval, SQL-based analysis, and lightweight computation.

## Architecture Overview

- User question enters the LangGraph router.
- The router decides if the request needs retrieval, SQL analysis, or calculator logic.
- Retrieval searches the curated knowledge base for architecture and deployment context.
- SQL queries use a safe SQLite business dataset for revenue and performance metrics.
- Calculator functions compute growth, percentage change, averages, and deltas.
- The final node synthesizes the evidence and returns a concise answer with source references.

## Deployment Architecture

The application is designed for a simple deployment model:

1. Backend: FastAPI service.
2. Frontend: Next.js application.
3. Data layer: SQLite for a small business dataset and metadata.
4. Retrieval layer: markdown knowledge documents.
5. Observability: optional Langfuse tracing via environment variables.
6. Evaluation: automated suite that measures tool selection, success, and latency.

## Data Model

The analytical dataset contains product revenue, customer counts, conversion rate, and cost metrics. The table name is revenue_metrics. This allows year-over-year analysis and comparison across regions.

## Reliability Principles

- Restrict SQL to read-only operations.
- Validate tool inputs before execution.
- Return source references and error context to the user.
- Keep the graph explicit and state-driven.
