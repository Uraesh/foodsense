# FoodSense — Frontend (Next.js)

Interface de recherche FoodSense recréée à l'identique du design fourni, prête à
remplacer le design existant de ton moteur de recherche.

## Stack

- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **lucide-react** (icônes)

## Démarrage

```bash
cd frontend
npm install
npm run dev
```

Ouvre http://localhost:3000

## Notes

- **Aucune image produit n'est générée.** Chaque emplacement produit affiche un
  placeholder neutre (`components/ProductPlaceholder.tsx`). Branche-y tes vraies
  images quand ton backend les fournit.
- Le logo se trouve dans `public/logo.png`.
- Les données affichées sont des mocks dans `lib/data.ts` — remplace-les par les
  résultats de ton moteur de recherche.

## Structure

```
frontend/
├── app/
│   ├── layout.tsx        # layout racine + métadonnées + police Inter
│   ├── page.tsx          # page de résultats (assemble tout)
│   └── globals.css
├── components/
│   ├── Header.tsx        # logo + navigation + Sign in
│   ├── Hero.tsx          # titre + barre de recherche + tags
│   ├── ResultCard.tsx    # carte de résultat
│   ├── ProductPlaceholder.tsx
│   ├── SearchInsights.tsx
│   ├── RefineSidebar.tsx # filtres (catégorie, régime, objectifs)
│   ├── AboutResults.tsx
│   └── Pagination.tsx
├── lib/
│   └── data.ts           
└── public/
    └── logo.png
```
