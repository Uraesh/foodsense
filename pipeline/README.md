# Pipeline

Ce dossier prepare les donnees de FoodSense pour la recherche semantique.

Le flux cible est :

`sources brutes -> PostgreSQL -> Parquet -> embeddings -> indexation Qdrant`

## Scripts principaux

- `01_clean.py` : nettoyage de la table source V1
- `02_build_product_docs.py` : aggregation par `ProductId`
- `03_generate_embeddings.py` : generation des vecteurs
- `04_index_qdrant.py` : envoi des vecteurs dans Qdrant
- `05_ingest_v2_to_postgres.py` : import V2 Open Food Facts / ESCI / USDA dans PostgreSQL
- `06_export_v2_parquets.py` : export PostgreSQL V2 vers `products_master_v2.parquet` et `product_search_documents_v2.parquet`
- `reviews_polars.py` : logique Polars et rapports de qualite
- `utils/qdrant_client.py` : client Qdrant local ou cloud

La V2 alimente la collection Qdrant `foodsense_products_v2`. Si tu dois reutiliser la V1 temporairement, garde `foodsense_products_bge_m3` et redefinis `QDRANT_COLLECTION` cote backend.

## Artefacts produits

Les sorties typiques vont dans `data/processed/` :

- `reviews_cleaned.csv`
- `reviews_cleaned.parquet`
- `product_documents.parquet`
- `product_embeddings_bge_m3.parquet`
- `quality_report.json`
- `products_master_v2.parquet`
- `product_search_documents_v2.parquet`
- `product_embeddings_v2_bge_m3.parquet`

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

Execution pas a pas V1 :

```powershell
python pipeline\01_clean.py
python pipeline\02_build_product_docs.py
python pipeline\03_generate_embeddings.py
python pipeline\04_index_qdrant.py
```

Pipeline V2 PostgreSQL - import USDA et ESCI :

```powershell
.\.venv\Scripts\python.exe pipeline\05_ingest_v2_to_postgres.py --skip-off
```

Pipeline V2 PostgreSQL - import Open Food Facts depuis dump CSV (recommande) :

```powershell
.\.venv\Scripts\python.exe pipeline\05_ingest_v2_to_postgres.py `
  --skip-usda --skip-esci `
  --off-csv "D:\Licience 3 IA-BD\Semantic-search\data\raw\openfoodfacts\fr.openfoodfacts.org.products.csv" `
  --off-limit 10000
```

Pipeline V2 PostgreSQL - export, embeddings et indexation :

```powershell
.\.venv\Scripts\python.exe pipeline\06_export_v2_parquets.py
.\.venv\Scripts\python.exe pipeline\03_generate_embeddings.py `
  --input-path data\processed\product_search_documents_v2.parquet `
  --output-path data\processed\product_embeddings_v2_bge_m3.parquet `
  --id-column product_id --text-column search_text --model bge-m3 `
  --progress-every 10
.\.venv\Scripts\python.exe pipeline\04_index_qdrant.py `
  --embeddings-path data\processed\product_embeddings_v2_bge_m3.parquet `
  --collection foodsense_products_v2 --id-column product_id
```

Documentation detaillee :

- [V2_ETL_README.md](../docs/V2_ETL_README.md)

## Embeddings

Le projet cible `bge-m3` sur un lot de `10 000` produits Open Food Facts (dump CSV francais).

Points a retenir :

- `bge-m3` est multilingue et pertinent pour les requetes en francais
- la troncation des textes reste importante pour stabiliser Ollama sur machine limitee
- les embeddings peuvent ensuite etre indexes localement dans Qdrant ou pousses vers Qdrant Cloud

## Suivi temps reel

Le fichier `embedding_status.json` est mis a jour pendant la vectorisation. Tu peux le surveiller depuis le notebook pour suivre l'avancement sans ouvrir les logs.

## Ordre d'execution recommande

1. lancer `06_export_v2_parquets.py` pour generer `product_search_documents_v2.parquet` ;
2. lancer `03_generate_embeddings.py` avec `--progress-every 10` pour suivre l'avancee plus finement ;
3. ouvrir la cellule de suivi temps reel pour voir `embedding_status.json` se rafraichir ;
4. une fois `stage = completed`, lancer `04_index_qdrant.py` pour pousser les vecteurs dans Qdrant.

```python
from pathlib import Path
import json
import time
from IPython.display import clear_output, display

status_path = PROJECT_ROOT / 'embedding_status.json'
last_snapshot = None
print(f'Suivi du statut: {status_path}')

while True:
    if status_path.exists():
        snapshot = json.loads(status_path.read_text(encoding='utf-8'))
        if snapshot != last_snapshot:
            clear_output(wait=True)
            display(snapshot)
            last_snapshot = snapshot
        if snapshot.get('stage') in {'completed', 'failed'}:
            break
    time.sleep(1)
```

## Qdrant local ou cloud

Le pipeline lit :

- `QDRANT_HOST` et `QDRANT_PORT` pour le mode local
- `QDRANT_URL` et `QDRANT_API_KEY` pour Qdrant Cloud

Cela permet de garder la meme logique d'indexation en V1 locale puis en V2/deploiement.
