# FoodSense V2 - Processus ETL MVP

Ce document detaille le processus ETL V2 pour integrer Open Food Facts, ESCI et USDA dans PostgreSQL, en gardant un perimetre compatible avec un MVP et avec les ressources locales du PC.

## Objectif V2

La V1 travaillait surtout sur des avis agreges. La V2 vise une base produit plus solide :

- Open Food Facts devient la source principale des fiches produits.
- ESCI sert de base d'evaluation `query -> produit -> label`.
- USDA sert d'enrichissement nutritionnel institutionnel.
- PostgreSQL devient la couche relationnelle de reference avant vectorisation et indexation Qdrant.

## Sources retenues

### Open Food Facts

Source : `https://world.openfoodfacts.org`

Usage :

- import bulk depuis le dump CSV officiel (`fr.openfoodfacts.org.products.csv`) via `--off-csv` ;
- ou import par code-barres via l'API v3.6 via `--off-barcode` (tests unitaires uniquement) ;
- stockage des champs utiles dans `foodsense_v2.openfoodfacts_products` ;
- reconstruction de `products_master` et `product_search_documents`.

Champs principaux :

- `code`
- `product_name`
- `brands`
- `categories`
- `ingredients_text`
- `allergens`
- `nutriscore_grade`
- `nutriments`

Colonnes nutritionnelles extraites du dump CSV :

- `energy-kcal_100g`
- `energy_100g`
- `fat_100g`
- `saturated-fat_100g`
- `carbohydrates_100g`
- `sugars_100g`
- `fiber_100g`
- `proteins_100g`
- `salt_100g`
- `sodium_100g`

### ESCI

Chemin :

```text
data/raw/esci/shopping_queries_dataset_examples.parquet
```

Usage :

- importer les exemples de recherche ;
- conserver `query`, `product_id`, `esci_label`, `split` ;
- servir de base au benchmark V2.

Limite actuelle :

- le fichier present est le fichier d'exemples ESCI ;
- il ne contient pas les metadonnees produit completes ;
- il reste donc principalement une source d'evaluation.

### USDA

Chemin :

```text
data/raw/usda/FoodData_Central_foundation_food_csv_2026-04-30
```

Fichiers retenus pour le MVP :

- `food.csv`
- `foundation_food.csv`
- `food_category.csv`
- `food_nutrient.csv`
- `food_portion.csv`
- `measure_unit.csv`
- `nutrient.csv`

Raison du choix :

- `food.csv` identifie les aliments USDA.
- `foundation_food.csv` limite le contexte au dataset Foundation Food.
- `food_category.csv` donne les categories.
- `food_nutrient.csv` donne les valeurs nutritionnelles.
- `nutrient.csv` donne les noms et unites des nutriments.
- `food_portion.csv` donne les portions et poids en grammes.
- `measure_unit.csv` donne les libelles d'unites.

Fichiers non retenus dans le MVP :

- fichiers d'acquisition et de marche ;
- fichiers de sous-echantillons ;
- fichiers de methodes laboratoire ;
- logs de mise a jour ;
- facteurs de conversion avances.

Ces fichiers peuvent etre utiles en V2 avancee, mais ils alourdissent inutilement l'import initial.

## Base PostgreSQL

Parametres locaux :

```text
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=Foodsense
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yusuke
```

Le schema cree est :

```text
foodsense_v2
```

Tables principales :

- `ingestion_runs`
- `openfoodfacts_products`
- `products_master`
- `product_search_documents`
- `usda_food_categories`
- `usda_foods`
- `usda_foundation_foods`
- `usda_nutrients`
- `usda_food_nutrients`
- `usda_measure_units`
- `usda_food_portions`
- `esci_examples`

Pour afficher les tables et leur nombre de lignes :

```powershell
$env:PGPASSWORD = "yusuke"
psql -U postgres -d Foodsense -c "
SELECT relname AS table_name, n_live_tup AS row_count
FROM pg_stat_user_tables
WHERE schemaname = 'foodsense_v2'
ORDER BY relname;
"
```

## Regles ETL appliquees

### Extract

- Open Food Facts est extrait depuis le dump CSV officiel (mode recommande, `--off-csv`).
- Open Food Facts peut aussi etre extrait via API par code-barres (`--off-barcode`) pour les tests.
- ESCI est lu depuis un fichier `.parquet`.
- USDA est lu depuis les CSV Foundation Food.

### Transform

Les transformations MVP appliquent :

- nettoyage des espaces sur tous les champs texte ;
- conversion des types numeriques ;
- suppression des identifiants nuls ;
- suppression des textes vides ;
- suppression des doublons par cle primaire logique ;
- filtrage des montants nutritionnels negatifs ;
- filtrage des valeurs nutritionnelles trop extremes ;
- filtrage des portions avec `gram_weight <= 0` ;
- conservation des payloads JSON pour audit.

Filtres specifiques au dump OFF CSV :

1. `code` et `product_name` obligatoires et non vides.
2. Code EAN valide : uniquement des chiffres, longueur 8 ou 13.
3. `product_name` de 3 caracteres minimum.
4. Au moins un champ utile parmi `categories`, `ingredients_text` ou `nutriscore_grade`.
5. Deduplication sur `code`.

Le script lit `limit * 5` lignes brutes pour garantir `limit` lignes propres apres filtrage.

Seuils actuels :

- `NUTRIENT_AMOUNT_MAX = 1000000`
- `PORTION_GRAMS_MAX = 10000`

Ces seuils sont volontairement larges : ils evitent les valeurs aberrantes evidentes sans supprimer trop agressivement des cas nutritionnels rares.

### Load

Le chargement PostgreSQL est idempotent :

- les tables sont creees si elles n'existent pas ;
- les imports utilisent `ON CONFLICT` ;
- relancer le pipeline ne cree pas de doublons ;
- chaque execution est tracee dans `ingestion_runs`.

## Commandes

Demarrer PostgreSQL et Qdrant :

```powershell
.\scripts\start_docker_stack.ps1 -IncludePostgres -QdrantOnly
```

Importer USDA et ESCI seulement :

```powershell
.\.venv\Scripts\python.exe pipeline\05_ingest_v2_to_postgres.py --skip-off
```

Importer Open Food Facts depuis le dump CSV :

```powershell
.\.venv\Scripts\python.exe pipeline\05_ingest_v2_to_postgres.py `
  --skip-usda --skip-esci `
  --off-csv "D:\Licience 3 IA-BD\Semantic-search\data\raw\openfoodfacts\fr.openfoodfacts.org.products.csv" `
  --off-limit 10000
```

Importer Open Food Facts par code-barres (tests unitaires) :

```powershell
.\.venv\Scripts\python.exe pipeline\05_ingest_v2_to_postgres.py `
  --skip-usda --skip-esci `
  --off-barcode 3274080005003,3017620422003
```

Exporter les artefacts Parquet V2 depuis PostgreSQL :

```powershell
.\.venv\Scripts\python.exe pipeline\06_export_v2_parquets.py
```

Generer les embeddings V2 :

```powershell
.\.venv\Scripts\python.exe pipeline\03_generate_embeddings.py `
  --id-column source_product_id `
  --text-column search_text `
  --model bge-m3 `
  --max-chars 1200 `
  --limit 15000
```

Indexer dans Qdrant V2 :

```powershell
.\.venv\Scripts\python.exe pipeline\04_index_qdrant.py `
  --embeddings-path data\processed\product_embeddings_bge_m3.parquet `
  --collection foodsense_products_v2 `
  --id-column source_product_id
```

Lister les fichiers USDA retenus :

```powershell
.\.venv\Scripts\python.exe pipeline\05_ingest_v2_to_postgres.py `
  --print-usda-keep-files --skip-usda --skip-esci --skip-off
```

## Nettoyage USDA

Les fichiers CSV a conserver sont :

```text
food.csv
foundation_food.csv
food_category.csv
food_nutrient.csv
food_portion.csv
measure_unit.csv
nutrient.csv
```

Dry-run pour voir ce qui sera supprime sans rien toucher :

```powershell
$keep = @(
    "food.csv", "foundation_food.csv", "food_category.csv",
    "food_nutrient.csv", "food_portion.csv", "measure_unit.csv", "nutrient.csv"
)
$dir = "D:\Licience 3 IA-BD\Semantic-search\data\raw\usda\FoodData_Central_foundation_food_csv_2026-04-30"

Get-ChildItem -Path $dir -Filter "*.csv" |
    Where-Object { $_.Name -notin $keep } |
    Select-Object Name, Length
```

Suppression effective :

```powershell
Get-ChildItem -Path $dir -Filter "*.csv" |
    Where-Object { $_.Name -notin $keep } |
    Remove-Item -Verbose
```

## Prochaine etape

Une fois PostgreSQL alimente avec les 10 000 produits OFF :

1. lancer `06_export_v2_parquets.py` pour produire `products_master_v2.parquet` et `product_search_documents_v2.parquet` ;
2. vectoriser `search_text` avec `bge-m3` via `03_generate_embeddings.py` ;
3. creer la collection Qdrant `foodsense_products_v2` via `04_index_qdrant.py` ;
4. adapter le backend pour afficher `product_name`, `brand`, `nutriscore`, `ingredients` et `allergens` ;
5. brancher les filtres frontend V2 (categorie, dietary preferences, health goals).
