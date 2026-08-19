# ServiceNow Logic Lab

Study project created to practice and explain ServiceNow-style concepts such as incident lifecycle, reusable server-side logic, before/after business rules, client-side validation and outbound REST integrations.

## Purpose

This project was built as a learning and interview-preparation artifact to simulate how workflow automation and incident logic can be structured in a platform-oriented environment.

It does not run inside ServiceNow, but it was designed to mirror important concepts that are commonly discussed in ServiceNow scripting interviews.

## Concepts Covered

- Incident records
- Reusable logic layer similar to Script Includes
- Before business rules
- After business rules
- Client-side validation logic
- Outbound REST integration
- End-to-end incident flow simulation

## Project Structure

- `src/servicenow-mini-app.js` — main implementation
- `test/servicenow-mini-app.test.js` — automated tests

## How It Maps to ServiceNow Concepts

| Project Component | Conceptual Equivalent |
|---|---|
| IncidentDB | Table / record storage |
| IncidentUtils | Script Include |
| beforeInsertBusinessRule | Before Business Rule |
| afterInsertBusinessRule | After Business Rule |
| clientScriptOnChangeCategory | Client Script |
| outboundRESTIntegration | REST integration |
| demo() | End-to-end flow test |

## How to Run

Requires Node.js 18+.

```bash
node src/servicenow-mini-app.js
```

## Automated Tests

```bash
node --test
```

## Why This Project Exists

This repository exists to demonstrate practical understanding of platform logic, workflow separation, validation, automation and system integration in a simplified environment.
