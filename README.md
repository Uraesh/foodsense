# FoodSense

FoodSense est un moteur de recherche semantique pour produits alimentaires construit autour de Next.js, FastAPI, Qdrant et Ollama.

## Objectif

Permettre a un utilisateur de rechercher un produit en langage naturel, retrouver les resultats les plus pertinents par le sens, puis demander un resume structure des avis a la demande.

## Structure du depot

- `backend/` : API FastAPI, logique metier, cache et tests.
- `frontend/` : application Next.js et composants UI.
- `pipeline/` : nettoyage, transformation, embeddings et indexation.
- `data/` : jeux de donnees locaux, echantillons et sorties traitees.
- `evaluation/` : mesures comparatives et resultats d'experience.
- `docs/` : notes de conception, soutenance et documentation projet.

## Regles de travail

- `main` doit rester stable et servir de base commune.
- Le travail quotidien se fait sur des branches `feature/*`.
- Les changements passent par Pull Request.
- Les donnees brutes ne sont jamais versionnees dans Git.
- Les secrets restent hors depot ; utiliser `.env.example` comme reference.

## Base MLOps mise en place

- GitHub Actions execute une CI legere sur `main` et `feature/*`.
- La CI verifie l'hygiene du depot, les chemins Python et le frontend quand les manifests existent.
- Le template de PR demande explicitement l'impact sur donnees, index, variables d'environnement et evaluation.
- `CODEOWNERS` centralise la responsabilite de revue en attendant les handles definitifs de toute l'equipe.

## Prochaines etapes recommandees

1. Ajouter `backend/requirements.txt` ou `backend/pyproject.toml`.
2. Ajouter `frontend/package.json` et les scripts `lint` et `build`.
3. Ajouter les dependances du pipeline et les premiers tests.
4. Ajouter `docker-compose.yml` et documenter le demarrage local.
5. Ajouter une evaluation comparative semantique vs keyword dans `evaluation/`.
