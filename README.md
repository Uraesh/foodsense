# FoodSense

FoodSense est un moteur de recherche semantique pour produits alimentaires construit avec Next.js, FastAPI, Qdrant, Ollama et un pipeline Polars.

La V1 travaille sur Amazon Fine Food Reviews. Comme ce dataset ne fournit pas un vrai catalogue produit riche, l'unite de recherche principale reste le `ProductId` et chaque resultat est reconstruit a partir des avis agregees.

## Etat actuel de la V1

Le projet couvre deja :

- nettoyage et preparation des donnees avec Polars ;
- construction de documents produits agreges ;
- embeddings `bge-m3` et indexation Qdrant ;
- recherche `semantic_hybrid` avec fallback lexical ;
- frontend de recherche branche sur `/search` ;
- bouton `Resume` centre sur les avis clients ;
- evaluation semantique vs baseline keyword.

Metriques actuellement versionnees :

- semantique : `Precision@3 = 0.75`, `Success@3 = 1.0`, `MRR = 0.8333`
- lexical : `Precision@3 = 0.6667`, `Success@3 = 0.75`, `MRR = 0.75`

Fichiers de reference :

- [evaluation/semantic_eval_report.json](d:/Licience%203%20IA-BD/Semantic-search/evaluation/semantic_eval_report.json)
- [evaluation/keyword_eval_report.json](d:/Licience%203%20IA-BD/Semantic-search/evaluation/keyword_eval_report.json)
- [docs/V1_V2_checklist.md](d:/Licience%203%20IA-BD/Semantic-search/docs/V1_V2_checklist.md)

## Cadrage fonctionnel V1

- L'unite de recherche principale est le `ProductId`.
- Chaque produit est represente par un document de recherche construit a partir des `Summary`, `Text`, de la note moyenne et du nombre d'avis.
- L'interface affiche un identifiant produit, un label infere, des extraits utiles et un score de pertinence.
- Le bouton `Resume` est central, mais il repose par defaut sur une synthese extractive stable.

Important :

- la V1 n'est pas un moteur de recommandation nutritionnelle certifie ;
- le RAG complet n'est pas le coeur de la V1, car le dataset actuel ne contient pas de noms de produits officiels fiables ni de vraies metadonnees nutritionnelles structurees ;
- l'ajout d'un dataset enrichi avec noms de produits et attributs metier reste une piste V2.

## Architecture du projet

```text
foodsense/
|-- README.md
|-- .env.example
|-- .gitignore
|-- docker-compose.yml
|-- requirements.txt
|
|-- backend/
|-- frontend/
|-- pipeline/
|-- evaluation/
|-- docs/
|-- scripts/
`-- data/
```

Sous-dossiers principaux :

- `backend/` : API FastAPI, routes `/search` et `/summarize`, services d'embedding et de resume
- `frontend/` : interface Next.js
- `pipeline/` : nettoyage, documents produits, embeddings, indexation Qdrant
- `evaluation/` : benchmark keyword vs semantic
- `scripts/` : bootstrap local, demarrage Docker, backend, Ollama, profil ressources reduites
- `data/processed/` : artefacts preprocesses et embeddings locaux

## Variables d'environnement

Le projet lit `.env` s'il existe, sinon `.env.example`.

Variables importantes :

- `QDRANT_HOST`, `QDRANT_PORT` : acces Qdrant local
- `QDRANT_URL`, `QDRANT_API_KEY` : acces Qdrant Cloud
- `OLLAMA_HOST` : endpoint Ollama
- `EMBEDDING_MODEL` : modele d'embedding, actuellement `bge-m3`
- `SUMMARY_MODEL` : modele LLM de resume
- `SUMMARY_STRATEGY` : `extractive` ou `ollama`
- `OLLAMA_KEEP_ALIVE` : duree de maintien en memoire des modeles

## Installation locale

```powershell
.\scripts\bootstrap_local_env.ps1 -Install
```

Ce script prepare le projet sur `D:` pour limiter la pression sur `C:`.

## Demarrage rapide

### 1. Ollama

Demarrage standard :

```powershell
.\scripts\start_ollama.ps1
```

Demarrage plus sobre en ressources :

```powershell
.\scripts\start_ollama.ps1 -LowMemory
```

### 2. Qdrant / Docker

```powershell
.\scripts\start_docker_stack.ps1 -QdrantOnly
```

Ou avec services supplementaires :

- `.\scripts\start_docker_stack.ps1`
- `.\scripts\start_docker_stack.ps1 -IncludeUI`
- `.\scripts\start_docker_stack.ps1 -IncludeData`
- `.\scripts\start_docker_stack.ps1 -IncludeLLM`

### 3. Backend

```powershell
.\scripts\start_backend.ps1
```

### 4. Frontend

```powershell
cd frontend
npm install
npm run dev
```

## Mode ressources reduites

Pour la prod locale, la demo ou une machine limitee, un script applique un profil plus sobre :

```powershell
.\scripts\enable_low_resource_mode.ps1
```

Ce profil :

- force `SUMMARY_STRATEGY=extractive`
- prepare `SUMMARY_MODEL=llama3.2:1b` pour une future activation LLM plus legere
- reduit `OLLAMA_KEEP_ALIVE`
- raccourcit `EMBEDDING_QUERY_MAX_CHARS`
- diminue `SEARCH_TOP_K` et `SEARCH_CANDIDATE_POOL`
- garde un seul modele charge a la fois via `start_ollama.ps1 -LowMemory`

Commande conseillee :

```powershell
.\scripts\enable_low_resource_mode.ps1
.\scripts\start_ollama.ps1 -LowMemory
.\scripts\start_docker_stack.ps1 -QdrantOnly
.\scripts\start_backend.ps1
```

## Resume et stabilite

Par defaut, le resume produit reste stable grace a `SUMMARY_STRATEGY=extractive`.

Pourquoi :

- le resume LLM local est possible, mais depend encore de la stabilite RAM d'Ollama sur cette machine ;
- la V1 privilegie donc une synthese fiable des avis clients plutot qu'une generation fragile.

La route utile est :

- `GET /summarize/{product_id}`
- `POST /summarize/{product_id}`

## Qdrant Cloud

Le code supporte deja Qdrant Cloud. Pour l'activer, renseigner :

- `QDRANT_URL`
- `QDRANT_API_KEY`

Le backend et le pipeline basculeront alors vers cette cible sans changer le code metier.

## Evaluation

Pour rejouer les benchmarks :

```powershell
python evaluation\eval_keyword_baseline.py
python evaluation\eval_semantic.py
```

Ou lancer la suite qualite :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_quality_suite.ps1
```

## Branches de travail

- `main` reste la reference stable
- le developpement se fait sur `feature/*`
- les donnees brutes et secrets ne doivent jamais etre commits

## Documentation associee

- [pipeline/README.md](d:/Licience%203%20IA-BD/Semantic-search/pipeline/README.md)
- [evaluation/README.md](d:/Licience%203%20IA-BD/Semantic-search/evaluation/README.md)
- [docs/README_journal_de_bord.md](d:/Licience%203%20IA-BD/Semantic-search/docs/README_journal_de_bord.md)
