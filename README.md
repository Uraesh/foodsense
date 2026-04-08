# FoodSense

FoodSense est un moteur de recherche semantique pour produits alimentaires construit autour de Next.js, FastAPI, Qdrant, Ollama et Mistral.

## Vue d'ensemble

L'utilisateur saisit une requete en langage naturel, le systeme retrouve les produits les plus pertinents par le sens, puis il peut demander une synthese structuree des avis a la demande.

Flux vise :

`Requete libre -> Embedding -> Qdrant -> Reranking -> Top K -> Resume LLM`

## Cadrage V1

Le projet s'appuie sur le dataset Amazon Fine Food Reviews. Ce dataset contient des avis, mais pas un catalogue produit complet avec des noms officiels fiables ni des metadonnees nutritionnelles structurees.

La V1 doit donc etre comprise comme un moteur de recherche semantique sur des documents produits reconstruits a partir des avis, agreges par `ProductId`.

- L'unite de recherche principale est le `ProductId`.
- Chaque produit est represente par un document de recherche construit a partir des `Summary`, `Text`, de la note moyenne et du nombre d'avis.
- L'interface affiche un identifiant produit, un label infere, des extraits utiles et un score de pertinence.
- Le bouton `Resume` reste la fonctionnalite centrale du cahier des charges.

Cette V1 ne constitue pas une recommandation medicale, nutritionnelle ou reglementaire. Toute fonctionnalite de type `Voir les produits adaptes` basee sur des sources externes reste hors perimetre immediat.

## Architecture du projet

```text
foodsense/
|
|-- README.md
|-- docker-compose.yml
|-- .env.example
|-- .gitignore
|-- requirements.txt
|
|-- data/
|   |-- raw/
|   |-- processed/
|   `-- samples/
|
|-- pipeline/
|   |-- README.md
|   |-- requirements.txt
|   |-- 01_clean.py
|   |-- 02_build_product_docs.py
|   |-- 03_generate_embeddings.py
|   |-- 04_index_qdrant.py
|   |-- reviews_polars.py
|   `-- utils/
|       |-- __init__.py
|       `-- qdrant_client.py
|
|-- backend/
|   |-- Dockerfile
|   |-- requirements.txt
|   |-- pyproject.toml
|   |-- app/
|   |   |-- __init__.py
|   |   |-- main.py
|   |   |-- config.py
|   |   |-- routers/
|   |   |   |-- __init__.py
|   |   |   |-- search.py
|   |   |   `-- summarize.py
|   |   |-- services/
|   |   |   |-- __init__.py
|   |   |   |-- embedding_service.py
|   |   |   |-- search_service.py
|   |   |   |-- rerank_service.py
|   |   |   |-- summarize_service.py
|   |   |   `-- cache.py
|   |   `-- models/
|   |       |-- __init__.py
|   |       |-- search.py
|   |       `-- product.py
|   `-- tests/
|       |-- __init__.py
|       |-- test_health.py
|       |-- test_search.py
|       `-- test_summarize.py
|
|-- frontend/
|   |-- Dockerfile
|   |-- package.json
|   |-- next.config.js
|   |-- .env.local.example
|   |-- src/
|   |   |-- app/
|   |   |   |-- layout.tsx
|   |   |   |-- page.tsx
|   |   |   `-- globals.css
|   |   |-- components/
|   |   |   |-- SearchBar.tsx
|   |   |   |-- ResultCard.tsx
|   |   |   |-- SummaryPanel.tsx
|   |   |   `-- LoadingSpinner.tsx
|   |   `-- lib/
|   |       `-- api.ts
|   `-- public/
|
|-- evaluation/
|   |-- README.md
|   |-- queries_test.json
|   |-- eval_semantic.py
|   |-- eval_keyword_baseline.py
|   `-- results/
|
|-- docs/
|-- docker/
|   `-- notebook.Dockerfile
`-- scripts/
    `-- bootstrap_local_env.ps1
```

## Variables d'environnement

Copier `.env.example` en `.env` puis renseigner les valeurs necessaires :

Variables principales :

- `MISTRAL_API_KEY` : cle API de synthese.
- `OPENROUTER_API_KEY` : cle API pour le reranking.
- `QDRANT_HOST` et `QDRANT_PORT` : connexion vers Qdrant.
- `OLLAMA_HOST` : hote Ollama pour les embeddings.
- `BACKEND_PORT` : port FastAPI.
- `FRONTEND_PORT` : port Next.js.

## Installation locale sur D:

Le projet est configure pour garder les caches et dependances Python locales sur le disque `D:` via le script `scripts/bootstrap_local_env.ps1`.

```powershell
.\scripts\bootstrap_local_env.ps1 -Install
```

Ce script prepare :

- `.venv/`
- `.cache/pip`
- `.cache/uv`
- `.cache/npm`
- `.cache/tmp`
- `.jupyter/`
- `.ipython/`
- `.ollama/`

## Lancement rapide

### Pipeline de donnees

```powershell
python -m pip install -r pipeline\requirements.txt
python pipeline\01_clean.py
python pipeline\02_build_product_docs.py
python pipeline\03_generate_embeddings.py
python pipeline\04_index_qdrant.py
```

### Application complete

Demarrage recommande sur Windows :

```powershell
.\scripts\start_docker_stack.ps1
```

Options utiles :

- `.\scripts\start_docker_stack.ps1 -QdrantOnly`
- `.\scripts\start_docker_stack.ps1 -IncludeUI`
- `.\scripts\start_docker_stack.ps1 -IncludeData`
- `.\scripts\start_docker_stack.ps1 -IncludeLLM`

Ce script :

- cree un `DOCKER_CONFIG` local dans le projet pour eviter les blocages sur `C:\Users\...\ .docker\config.json` ;
- lance Docker Desktop si besoin ;
- attend que le daemon soit pret ;
- demarre automatiquement les services requis via `docker compose` ;
- s'appuie directement sur `.env.example` pour le demarrage standard du stack.

Commande compose directe si Docker est deja pret :

```powershell
docker-compose up --build
```

Services attendus :

- Frontend : `http://localhost:3000`
- Backend API : `http://localhost:8000`
- Swagger : `http://localhost:8000/docs`
- Qdrant : `http://localhost:6333/dashboard`
- Jupyter Lab : `http://localhost:8888`

## Regles de travail

- `main` reste stable.
- Le travail se fait sur des branches `feature/*`.
- Les changements passent par Pull Request.
- Les donnees brutes ne sont jamais versionnees.
- Les secrets ne doivent jamais etre commits.

## Base MLOps

- Une CI GitHub Actions valide l'hygiene du depot, Python et le frontend.
- `CODEOWNERS` et le template de PR structurent la revue.
- Le pipeline, le backend, le frontend et l'evaluation sont decoupes par responsabilite.

## Priorites immediates

- Finaliser le pipeline complet `clean -> docs -> embeddings -> qdrant`.
- Brancher la recherche backend sur les documents produits preprocesses.
- Connecter le frontend au backend.
- Mettre en place l'evaluation semantique vs baseline keyword.
- Stabiliser le demarrage par Docker pour la demo.
- Suivre la checklist de cloture V1 / cadrage V2 dans `docs/V1_V2_checklist.md`.
