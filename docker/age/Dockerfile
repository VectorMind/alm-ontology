ARG AGE_BASE=apache/age@sha256:4241e2d8bb86a6b2ea44e9ad06c73856e12b209de295124603a599dd7feb70eb
FROM ${AGE_BASE}

USER root

# Keep the project graph/search/semantic substrate in one Postgres image:
# Apache AGE comes from the base image; pgvector is installed for Phase 4.
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-18-pgvector \
    && rm -rf /var/lib/apt/lists/*
