# Journal De Bord Quotidien

Ce document sert de trace quotidienne du projet `FoodSense`.

Objectifs :
- garder un historique date par date ;
- faciliter la synthese finale ;
- pouvoir presenter l'avancement au professeur meme sans diaporama ;
- conserver les decisions, blocages et prochaines actions.

## Regle De Mise A Jour

- ajouter une nouvelle section par jour au format `YYYY-MM-DD` ;
- renseigner les actions reelles, pas les intentions vagues ;
- noter les blocages techniques ou organisationnels ;
- terminer chaque entree par les prochaines etapes.

## Note

Les entrees ci-dessous entre le 27 mars 2026 et le 2 avril 2026 ont ete reconstituees a partir des actions menees ensemble, des fichiers du projet, des pushes realises et des decisions prises pendant les sessions de travail.

## Modele A Copier

```md
## YYYY-MM-DD

### Objectifs Du Jour
- ...

### Realisations
- ...

### Decisions
- ...

### Blocages
- ...

### Prochaines Etapes
- ...
```

## 2026-03-27

### Objectifs Du Jour
- initialiser le depot GitHub du projet ;
- preparer une structure de branches exploitable par l'equipe ;
- poser une base propre pour demarrer rapidement.

### Realisations
- creation du depot `Uraesh/foodsense` ;
- initialisation de `main` avec un premier socle de repository ;
- creation des branches de travail `feature/*` pour separer l'infra, le pipeline, le backend, le frontend, les embeddings, la summarization et l'evaluation ;
- clarification des scopes GitHub necessaires pour l'administration du depot.

### Decisions
- travailler par lots fonctionnels avec des branches dediees ;
- garder `main` comme branche de reference stable ;
- privilegier une approche MLOps et non un simple depot de developpement brut.

### Blocages
- protection de branche `main` non activable a ce stade sur le plan GitHub disponible.

### Prochaines Etapes
- pousser une structure minimale recuperable par les autres contributeurs ;
- mettre en place une base de gouvernance et de CI.

## 2026-03-28

### Objectifs Du Jour
- rendre le depot exploitable par l'equipe ;
- poser une premiere base MLOps.

### Realisations
- push de la structure de projet sur `main` pour permettre aux contributeurs de recuperer une base commune ;
- ajout de fichiers de gouvernance : `CODEOWNERS`, template de PR, CI GitHub Actions ;
- mise en place d'un socle MLOps initial avec verification d'hygiene du depot et checks Python/frontend.

### Decisions
- integrer la qualite et la gouvernance des le debut du projet ;
- ne jamais versionner les datasets bruts ni les secrets.

### Blocages
- impossibilite d'activer effectivement la protection de `main` sur ce depot prive avec le plan actuel.

### Prochaines Etapes
- demarrer les fondations backend et frontend ;
- preparer les dependances du projet.

## 2026-03-29

### Objectifs Du Jour
- poser des fondations techniques viables pour le backend et le frontend ;
- recuperer le projet en local.

### Realisations
- creation d'un socle backend FastAPI avec configuration initiale ;
- creation d'un socle frontend Next.js minimal ;
- rapatriement du contenu du depot principal dans l'environnement local de travail ;
- configuration du remote GitHub local.

### Decisions
- utiliser des bibliotheques existantes et stables ;
- garder une separation claire entre backend, frontend et pipeline.

### Blocages
- l'historique Git local est reste imparfaitement aligne avec le depot distant.

### Prochaines Etapes
- attaquer le dataset et clarifier son adequation au cas d'usage.

## 2026-03-30

### Objectifs Du Jour
- choisir le bon fichier source du dataset ;
- comprendre la structure des donnees et leurs limites.

### Realisations
- choix explicite du fichier `Reviews.csv` comme source de travail pour le pipeline Polars ;
- premiere exploration du dataset Amazon Fine Food Reviews ;
- verification de points structurants : volume, colonnes disponibles, `ProductId`, distribution des scores, helpfulness, duplications et absence de vrai nom produit.

### Decisions
- travailler sur une indexation par produit reconstruit et non par review isolee ;
- garder le texte le plus naturel possible pour les embeddings ;
- utiliser `ProductId` comme unite de regroupement.

### Blocages
- le dataset ne contient pas de nom produit officiel fiable ;
- le dataset est desequilibre en faveur des avis 5 etoiles.

### Prochaines Etapes
- reformuler clairement la promesse V1 ;
- definir le nettoyage et l'agregation produit.

## 2026-03-31

### Objectifs Du Jour
- recadrer la V1 pour qu'elle soit honnete et defendable ;
- documenter la bonne interpretation produit du projet.

### Realisations
- clarification que la V1 est un moteur de recherche semantique sur documents produits agreges par `ProductId` ;
- analyse du risque produit autour de requetes sensibles du type `chocolat pour diabetique` ;
- decision de reporter hors V1 toute fonctionnalite de type `voir les produits adaptes` basee sur des sources externes ;
- mise a jour du README pour recadrer la promesse du projet et les priorites immediates.

### Decisions
- ne pas survendre le systeme comme outil de recommandation nutritionnelle ou medicale ;
- assumer un positionnement d'exploration semantique d'avis clients.

### Blocages
- perception projet a reexpliquer finement au professeur et a l'equipe.

### Prochaines Etapes
- accelerer sur le pipeline, Docker et l'architecture reelle du depot.

## 2026-04-01

### Objectifs Du Jour
- rattraper le retard structurel du projet ;
- mettre en place Docker, le pipeline et l'environnement local sur `D:`.

### Realisations
- creation du `docker-compose.yml` initial ;
- creation des Dockerfiles utiles, dont celui du notebook ;
- mise en place d'un script local pour orienter caches, environnement Python, Jupyter et autres dependances vers le disque `D:` ;
- creation des scripts de pipeline Polars pour le nettoyage, l'agregation des documents produit, la generation d'embeddings de travail et l'indexation Qdrant ;
- generation locale des artefacts preprocesses : `reviews_cleaned.parquet`, `product_documents.parquet`, `quality_report.json` ;
- creation d'un premier notebook de travail pour l'exploration des donnees.

### Decisions
- garder les donnees brutes hors Git ;
- travailler avec des fichiers `.parquet` preprocesses pour accelerer la suite ;
- poser d'abord la structure, puis avancer pas a pas sur le fonctionnel.

### Blocages
- execution locale Python perturbee par l'environnement Windows Store et la gestion du venv ;
- Docker non encore valide bout en bout sur cette machine.

### Prochaines Etapes
- realigner strictement le depot sur l'architecture definie ;
- supprimer les dossiers parasites et les doublons inutiles.

## 2026-04-02

### Objectifs Du Jour
- remettre le depot en ordre selon l'architecture cible ;
- clarifier la promesse V1 du projet ;
- poser les bases techniques minimales pour le backend, le frontend et le pipeline ;
- preparer une base de suivi presentable.

### Realisations
- creation et structuration des dossiers `backend`, `frontend`, `pipeline`, `evaluation`, `docker`, `scripts` et `data` ;
- ajout d'un `docker-compose.yml`, de Dockerfiles et des manifests de dependances ;
- mise en place du socle backend FastAPI avec configuration, routes, services, modeles et tests de base ;
- mise en place du socle frontend Next.js avec composants principaux et client API ;
- mise en place du pipeline Polars pour le nettoyage, la creation de documents produits, la preparation des embeddings et l'indexation Qdrant ;
- exploration initiale du dataset Amazon Fine Food Reviews ;
- production locale de fichiers preprocesses : `reviews_cleaned.parquet`, `product_documents.parquet`, `quality_report.json` ;
- clarification dans le README : la V1 est une recherche semantique sur des documents produits reconstruits par `ProductId`, et non un moteur de recommandation nutritionnelle certifiee ;
- push de l'alignement d'architecture sur la branche distante `feature/infra-setup` ;
- creation d'un journal de bord quotidien presentable ;
- creation d'un notebook d'exploration et de visualisation des donnees ;
- diagnostic des checks GitHub Actions `Frontend quality` et `Python quality` ;
- correction locale de causes probables de CI : imports inutiles signales par Ruff et configuration frontend du workflow.

### Decisions
- conserver l'architecture cible comme reference de travail ;
- ne pas pousser les donnees brutes ni les artefacts lourds de preprocessing ;
- repousser toute fonctionnalite de type `produits adaptes` hors de la V1 ;
- garder pour l'instant `polars` et `pyarrow` dans le backend tant que le backend lit encore les fichiers `.parquet`.

### Blocages
- le depot Git local n'etait pas aligne sur la branche distante et necessite encore une remise au propre locale ;
- Docker n'a pas ete verifie en execution reelle sur cette machine ;
- le backend n'est pas encore branche sur une vraie recherche Qdrant ;
- les services LLM et reranking restent encore au stade de squelette ;
- l'etat exact de la CI GitHub doit etre revalide apres push des corrections.

### Prochaines Etapes
- realigner le depot local sur `origin/feature/infra-setup` ;
- ajouter un notebook d'exploration et de visualisation des donnees ;
- finaliser la chaine `embeddings -> indexation Qdrant -> recherche backend` ;
- brancher le frontend sur les vrais endpoints ;
- preparer l'evaluation semantique vs baseline keyword.

## 2026-04-04

### Objectifs Du Jour
- demarrer concretement la phase d'embeddings ;
- installer et valider l'infrastructure locale Ollama + Qdrant ;
- choisir un modele d'embedding compatible avec le francais et soutenable sur une machine limitee.

### Realisations
- activation effective de la virtualisation, de WSL et de Docker Desktop sur la machine Dell ;
- lancement de Qdrant dans Docker et verification de son accessibilite locale ;
- installation d'Ollama et telechargement des modeles `qwen3-embedding:0.6b` puis `bge-m3` ;
- mesure pratique du temps d'embedding sur petits echantillons avec Qwen puis avec BGE-M3 ;
- identification des erreurs `500` d'Ollama avec `bge-m3` sur des textes trop longs ;
- ajout d'une troncation `max_chars=800` dans le pipeline d'embeddings pour stabiliser `bge-m3` ;
- ajout d'un fichier de suivi `embedding_status.json` a la racine pour suivre l'avancement sans lire les logs ;
- lancement d'un run de 3000 produits avec `bge-m3` en arriere-plan et logs dedies ;
- optimisation locale legere en fermant quelques applications non essentielles pendant le run.

### Decisions
- conserver l'ancienne base / collection pour comparaison et ne pas ecraser les artefacts Qwen deja produits ;
- utiliser `bge-m3` pour la suite car il est multilingue et plus pertinent pour des requetes en francais ;
- garder une collection Qdrant distincte pour chaque modele d'embedding utilise ;
- ne pas pousser les artefacts d'embedding locaux (`embedding_status.json`, manifests, logs, parquets de sortie) dans Git.

### Blocages
- l'executable Python du venv reste capricieux en lancement detache sous Windows, ce qui impose un contournement pour les longs runs en arriere-plan ;
- des erreurs `500` surviennent encore ponctuellement sur certains produits, meme apres troncation, ce qui devra etre surveille dans le rapport final ;
- l'indexation Qdrant n'a pas encore ete relancee sur la nouvelle sortie `bge-m3`.

### Prochaines Etapes
- laisser terminer le batch `bge-m3` sur 3000 produits ;
- indexer les embeddings BGE dans une collection Qdrant dediee ;
- comparer ensuite les comportements Qwen vs BGE-M3 sur quelques requetes de demonstration ;
- pousser le code propre de la phase embeddings sur la branche `feature/embeddings-qdrant`.

## 2026-04-05

### Objectifs Du Jour
- fiabiliser le backend de recherche ;
- verifier le chemin complet `backend -> Ollama -> Qdrant` ;
- renforcer les tests avant push sur la branche backend dediee.

### Realisations
- installation de `pytest` dans le `.venv` du projet ;
- execution des tests backend et ajout de cas supplementaires pour `/favicon.ico`, `GET /search` et la strategie semantique ;
- correction du backend pour accepter `GET /search` en plus du `POST` ;
- ajout d'une route `GET /favicon.ico` pour eliminer les `404` parasites dans les logs ;
- branchement du backend sur la collection Qdrant `foodsense_products_bge_m3` avec la bonne API SDK (`query_points`) ;
- ajout d'un retry cote Ollama pour les embeddings de requete ;
- amelioration de la reponse API avec `strategy` et `warning` afin de distinguer clairement recherche semantique et fallback lexical ;
- verification manuelle que la collection Qdrant contient bien `3000` points et que la recherche semantique repond a nouveau quand Docker et Ollama sont correctement lances.

### Decisions
- pousser les corrections backend sur `feature/backend-search` plutot que sur `main` ;
- garder le fallback lexical tant qu'Ollama peut encore etre instable localement ;
- exposer explicitement la strategie utilisee dans la reponse API pour faciliter la demo et le debug.

### Blocages
- la stabilite d'Ollama reste sensible a l'etat memoire de la machine et peut provoquer des `500` transitoires ;
- le depot local principal reste trop brouillon pour un push direct securise, ce qui impose un push via un clone temporaire propre.

### Prochaines Etapes
- pousser les correctifs backend sur la branche distante dediee ;
- brancher le frontend sur le `/search` backend ;
- evaluer quelques requetes de demo avec et sans fallback pour documenter les limites de la V1.
