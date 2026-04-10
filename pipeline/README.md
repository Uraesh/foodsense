# Pipeline

Ce dossier prepare les donnees de FoodSense pour la recherche semantique.

Le flux cible est :

`reviews brutes -> nettoyage -> documents produits -> embeddings -> indexation Qdrant`

## Scripts principaux

- `01_clean.py` : nettoyage de la table source
- `02_build_product_docs.py` : aggregation par `ProductId`
- `03_generate_embeddings.py` : generation des vecteurs
- `04_index_qdrant.py` : envoi des vecteurs dans Qdrant
- `reviews_polars.py` : logique Polars et rapports de qualite
- `utils/qdrant_client.py` : client Qdrant local ou cloud

## Artefacts produits

Les sorties typiques vont dans `data/processed/` :

- `reviews_cleaned.csv`
- `reviews_cleaned.parquet`
- `product_documents.parquet`
- `product_embeddings_bge_m3.parquet`
- `quality_report.json`

## Hypothese de travail V1

Le dataset Amazon Fine Food Reviews ne fournit pas de catalogue produit riche.

Donc :

- l'unite de travail principale reste `ProductId`
- le document produit est reconstruit a partir des avis
- le pipeline V1 cherche des produits agreges, pas des fiches nutritionnelles officielles

## Commandes usuelles

Installation :

```powershell
python -m pip install -r pipeline\requirements.txt
```

Execution pas a pas :

```powershell
python pipeline\01_clean.py
python pipeline\02_build_product_docs.py
python pipeline\03_generate_embeddings.py
python pipeline\04_index_qdrant.py
```

## Embeddings

Le projet a ete valide localement avec `bge-m3` sur un lot de `3000` produits.

Points a retenir :

- `bge-m3` est multilingue et plus pertinent que Qwen pour les requetes en francais de la V1
- la troncation des textes reste importante pour stabiliser Ollama sur machine limitee
- les embeddings peuvent ensuite etre indexes localement dans Qdrant ou pousses vers Qdrant Cloud

## Qdrant local ou cloud

Le pipeline lit :

- `QDRANT_HOST` et `QDRANT_PORT` pour le mode local
- `QDRANT_URL` et `QDRANT_API_KEY` pour Qdrant Cloud

Cela permet de garder la meme logique d'indexation en V1 locale puis en V2/deploiement.
