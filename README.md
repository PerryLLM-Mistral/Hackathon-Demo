<p align="center">
  <img src="img/perry_sphere_logo.png" alt="Perry Sphere" width="200"/>
</p>

# PerrySphere

This repository contains our project developed for the **Mistral Datathon (February 2026)**.

The goal of the project is to explore and prototype a **multi-agent geopolitical simulation powered by Large Language Models (LLMs)**, using Mistral models as the reasoning backbone.

The system models countries as autonomous agents capable of making strategic decisions (e.g., war declarations, alliances, trade, sanctions) within a structured world state. Actions have **quantitative effects** on inter-country relationships and internal metrics, enabling controlled simulation dynamics.


## Purpose

The main objectives of this project are:

* Design a **multi-agent architecture** driven by LLM-based decision-making.
* Define a structured **world state representation** with measurable metrics.
* Implement a **rule-based simulation engine** with quantitative effects.
* Build an interactive **React frontend with map visualization** to explore the simulation state in real time.
* Experiment with hybrid control:

  * LLM-driven strategic reasoning
  * Deterministic, auditable simulation rules
* Explore negotiation dynamics such as alliance proposals and responses.

The project emphasizes architectural clarity and modularity rather than production-ready deployment.


## High-Level Architecture

The system is organized into three layers:

1. **Frontend (React + Maps)**
   
   Visualizes the world state (countries, relations, events) and provides a UI to run turns / trigger actions.

3. **API Layer (FastAPI)**
   
   Bridges the frontend with the backend logic, exposing endpoints to:

   * fetch world state
   * step the simulation (turn-based loop)
   * return updated state for visualization

5. **Multi-LLM + Simulation Core**

   * **Multi-LLM layer**: country agents select structured actions using Mistral models
   * **Simulation engine**: applies deterministic rules and quantitative effects to update the world


## Core Concepts

* **WorldState**: global representation of the simulation.
* **CountryState**: per-country metrics (economy, military power, technology, etc.).
* **RelationState**: bilateral relationship scores between countries.
* **ActionType**: structured action space (e.g., propose alliance, respond to alliance, war, sanction, trade, pass).
* **Quantitative Effects**: diplomatic actions translate into bounded numerical changes.


## Tech Stack

* React
* Python
* FastAPI
* Pydantic
* Asyncio

* Mistral LLM API
