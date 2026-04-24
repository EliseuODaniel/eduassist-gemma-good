# Repository Scope

This repo is the public Gemma 4 Good submission fork. It intentionally avoids
copying the entire EduAssist platform history and runtime surface.

Included:

- Gemma 4 E4B local runtime recipe through llama.cpp;
- Streamlit demo app;
- Python tool planner, policy layer, and grounded composer;
- synthetic public and protected school data;
- small regression evaluation;
- submission writeup and demo script.

Excluded:

- real student data;
- production secrets;
- Telegram gateway;
- Keycloak realm exports;
- Postgres, Qdrant, MinIO, and observability stack;
- experimental multi-orchestrator comparison artifacts.

The source platform remains useful as provenance, but the hackathon judges should
be able to understand and run this repository without navigating production
infrastructure.
