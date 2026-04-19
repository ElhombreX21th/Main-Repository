# FPConnect RCA Copilot

SaaS platform for technical operations, incident tracking and Root Cause Analysis workflows in MedTech and healthcare environments.

## Overview

FPConnect RCA Copilot was designed to support operational visibility, technical workflows and structured incident analysis in environments where reliability, traceability and response time matter.

The platform combines a modern web interface, API backend, cloud database and production-ready infrastructure to support technical operations in a scalable way.

## Problem

Technical teams in healthcare and MedTech environments often deal with:

- fragmented incident records
- poor operational visibility
- weak traceability of technical actions
- limited support for structured RCA workflows
- disconnected tooling between field, support and management

## Solution

FPConnect provides a unified operational platform with:

- secure login and protected access
- dashboard with operational visibility
- ticket management workflows
- machine and asset visibility
- structured backend architecture for expansion
- foundation for AI-assisted RCA capabilities

## Key Features

- Authentication with JWT
- Operational dashboard
- Ticket management
- Machine management
- Responsive web interface
- Mobile-ready codebase
- Cloud deployment architecture
- Docker-based local development
- Expandable AI and semantic search foundation

## Architecture

### Frontend
- Next.js
- React
- TypeScript
- Tailwind CSS

### Backend
- FastAPI
- Uvicorn

### Data Layer
- PostgreSQL
- SQLAlchemy
- Alembic
- Neon Postgres

### Infrastructure
- Vercel
- Railway
- Docker Compose

### Security
- JWT
- Passlib / Bcrypt

## Production Status

- web frontend published
- backend deployed
- cloud database connected
- persistence validated
- responsive interface ready for desktop and mobile
- foundation prepared for expansion with AI, storage and queue/cache services

## Repository Structure

- `apps/web` — web frontend
- `apps/api` — backend API
- `apps/mobile` — mobile foundation
- `docs` / reports — technical and support materials

## Local Development

### Web
```bash
cd apps/web
npm install
npm run dev
```

### API

```bash
cd apps/api
# install dependencies according to project setup
```

### Full stack

```bash
make up
make logs
make migrate
make down
```

## Roadmap

- AI-assisted RCA workflows
- semantic search with vector support
- file attachments and storage layer
- queue/cache acceleration
- richer analytics and KPI modules
- stronger mobile operational workflows

## Commercial Note

This repository showcases the platform architecture, product direction and selected implementation details.

Sensitive production credentials, restricted assets and confidential operational configurations are not included.

## Why This Project Matters

FPConnect is not just a coding exercise. It is a practical product-oriented platform designed around real technical operations, reliability workflows and data-driven support in complex environments.
