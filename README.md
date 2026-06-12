# FoodSense  — Plateforme de Recherche Sémantique & RAG

Bienvenue dans le dépôt officiel du projet **FoodSense**, développé dans le cadre de la certification en Intelligence Artificielle et Big Data (Licence 3 IA-BD, ESGIS Lomé).

Ce système complet de bout en bout illustre la transition d'un moteur de recherche sémantique textuel de base (V1) vers une architecture industrielle de Génération Augmentée par Récupération (RAG) hautement disponible et découplée (V2).

---

##  Navigation dans la Documentation

Pour faciliter l'évaluation modulaire de nos livrables par le jury, la documentation technique a été segmentée par domaines de compétences :

*  **[Documentation du Pipeline de Données & ETL (Data Engineering)](./pipeline/README.md)** : Stratégies de nettoyage, agrégation de volumes avec Polars et extraction d'embeddings complexes via `bge-m3`.
*  **[Rapport de Validation \u0026 Benchmarks (ML Engineering)](./evaluation/README.md)** : Comparaison mathématique rigoureuse (Precision@k, Success@k, MRR) entre les approches lexicales classiques et notre moteur sémantique.
* **[Guide de l'API Backend (FastAPI)](./backend/README.md)** : Spécifications des endpoints de recherche, gestion des pools de connexions et routage des requêtes.
* **[Guide de l'Interface Utilisateur (Frontend Next.js)](./frontend/README.md)** : Architecture des composants web en TypeScript, gestion des états asynchrones et affichage dynamique des insights.

---

## Comment tester les deux versions du projet ?

Notre projet est structuré de manière chronologique pour refléter fidèlement notre démarche scientifique d'ingénierie.

###  Version 1 : Moteur Sémantique Initial (Dataset Amazon Reviews)
* **Objectif** : Valider la supériorité de la recherche sémantique hybride par rapport aux mots-clés sur le dataset officiel *Amazon Fine Food Reviews*.
* **Commande de basculement** : Pour restaurer le code, les scripts (`01` à `04`) et la configuration exacte de notre première version stable, exécutez simplement :
  ```powershell
  git checkout tags\v1.0.0
