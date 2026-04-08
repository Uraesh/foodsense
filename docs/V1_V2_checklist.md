# Checklist V1 Et V2

Ce document sert de reference pratique pour finir proprement la V1, puis cadrer la V2 sans melanger les priorites.

## V1 A Cloturer

### Evaluation Et Verification
- [x] finaliser et rerun proprement le rapport semantique avec les nouvelles metriques `Precision@k`, `Success@k` et `MRR`
- [x] verifier noir sur blanc que la recherche hybride ameliore reellement le score par rapport au lexical
- [ ] stabiliser le benchmark de V1 avec quelques requetes representatives et defendables
- [ ] figer les rapports d'evaluation utilises pour la demonstration finale

### Backend Et Recherche
- [ ] confirmer que `/search` utilise bien la collection Qdrant `foodsense_products_bge_m3`
- [ ] verifier les cas de fallback lexical et documenter la cause si Ollama ou Qdrant est indisponible
- [ ] garder une execution fiable de la chaine `query -> embedding -> qdrant -> ranking -> response`

### Frontend Et Demo
- [ ] brancher ou finir de brancher le frontend sur le backend `/search`
- [ ] afficher clairement la strategie utilisee (`semantic_hybrid` ou `lexical_fallback`) si utile pour la demo
- [ ] produire une demo simple, fiable, avec quelques requetes bien choisies
- [ ] verifier que la demo fonctionne avec Docker/Qdrant/Ollama relances proprement

### Documentation Et Livraison
- [ ] mettre a jour le README avec l'etat final reel de la V1
- [ ] mettre a jour le journal de bord avec les decisions, resultats et limites finales
- [ ] pousser les derniers changements utiles sur les branches dediees
- [ ] preparer les captures et elements de rapport pour la soutenance

## V2 A Cadrer

### Qualite De Recherche
- [ ] remplacer le reranking placeholder par un reranking reel
- [ ] affiner la combinaison lexical + semantique avec calibration des poids
- [ ] construire un benchmark plus grand, mieux annote, et plus representatif
- [ ] tester plusieurs modeles d'embedding si le temps le permet

### Donnees Produit
- [ ] enrichir ou remplacer le dataset actuel avec un dataset comportant de vraies colonnes produit
- [ ] etudier en priorite un dataset de type recherche produit tel que Amazon ESCI
- [ ] envisager un enrichissement avec Open Food Facts ou FoodData Central pour recuperer noms, ingredients et attributs nutritionnels
- [ ] distinguer clairement les donnees d'avis et les metadonnees produit dans l'architecture

### Fonctionnalites Metier
- [ ] ajouter une verification nutritionnelle guidee si le besoin est confirme
- [ ] si cette verification est retenue, la baser sur des sources fiables et citees, pas sur des affirmations libres
- [ ] encadrer toute suggestion LLM comme une aide a l'interpretation et non comme une recommandation medicale
- [ ] etudier ton idee : partir des avis affiches, puis demander a un LLM de proposer des produits potentiellement adequats a partir de sources nutritionnelles externes

### Produit Et UX
- [ ] ameliorer le frontend et l'experience utilisateur
- [ ] mieux presenter les resultats, les extraits et les justifications
- [ ] ajouter un resume produit plus convaincant cote interface
- [ ] rendre le demarrage local et la demo encore plus reproductibles

### Extensions Eventuelles
- [ ] ajouter un classificateur si vous avez ensuite un besoin clair de categorisation ou de filtrage
- [ ] n'ajouter ce classificateur qu'apres stabilisation de la recherche, pas avant

## Decision De Cadrage

- La V1 reste une recherche semantique sur des documents produits reconstruits a partir des avis.
- L'ajout d'un dataset avec de vraies colonnes produit est une excellente piste, mais releve plutot d'une V2 ou d'une V1.5 si vous avez encore de la marge.
- L'idee d'un LLM qui propose des produits adequats a partir de sites nutritionnels peut etre interessante, mais elle doit etre presentee comme une fonctionnalite d'assistance guidee, pas comme un avis medical ou nutritionnel certifie.
