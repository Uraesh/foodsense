# Evaluation

Ce dossier contient les scripts et jeux de requetes utilises pour comparer :

- la recherche semantique de FoodSense
- une baseline keyword/lexicale

## Fichiers principaux

- `queries_test.json` : petit benchmark V1
- `eval_keyword_baseline.py` : baseline par mots-cles
- `eval_semantic.py` : evaluation du moteur semantique/hybride
- `eval_utils.py` : metriques communes
- `keyword_eval_report.json` : dernier rapport lexical versionne
- `semantic_eval_report.json` : dernier rapport semantique versionne

## Metriques suivies

- `Precision@k`
- `Success@k`
- `MRR`
- `avg_search_time_ms`
- `strategy` employee pendant la recherche

## Dernier constat versionne

Baseline keyword :

- `avg_precision_at_k = 0.6667`
- `success_rate_at_k = 0.75`
- `mrr = 0.75`

Recherche semantique :

- `avg_precision_at_k = 0.75`
- `success_rate_at_k = 1.0`
- `mrr = 0.8333`
- `fallback_runs = 0`

## Commandes

```powershell
python evaluation\eval_keyword_baseline.py
python evaluation\eval_semantic.py
```

Ou, pour un passage global :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_quality_suite.ps1
```

## Lecture correcte des rapports

- si `strategy = semantic_hybrid`, le moteur a bien utilise les embeddings ;
- si `strategy = lexical_fallback`, l'embedding de requete ou Ollama ont echoue ;
- si `relevance_percent` est absent cote frontend, cela indique generalement une chute en mode lexical pur ou un probleme de similarite vectorielle disponible.

## Limites

Le benchmark V1 reste volontairement petit.

En V2, il faudra :

- agrandir le jeu de requetes
- annoter plus proprement la pertinence attendue
- comparer aussi un vrai reranking plus pousse
