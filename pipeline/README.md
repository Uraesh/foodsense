# Pipeline

Le pipeline prepare les donnees pour la recherche semantique :

1. nettoyer les reviews ;
2. construire les documents produits agreges ;
3. generer les embeddings ;
4. indexer les documents dans Qdrant.

Scripts principaux :

- `01_clean.py`
- `02_build_product_docs.py`
- `03_generate_embeddings.py`
- `04_index_qdrant.py`
