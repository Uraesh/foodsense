export type Result = {
  id: number;
  topMatch?: boolean;
  title: string;
  rating: number;
  reviews: number;
  brand: string;
  category: string;
  description: string;
  keyPoints: string[];
  relevance: number;
};

export const results: Result[] = [
  {
    id: 1,
    topMatch: true,
    title: "Like Chocolate & Granola??? To me, 'tis a Match Made in Heaven!!",
    rating: 4.2,
    reviews: 216,
    brand: "Farines",
    category: "Beverages",
    description:
      "Heaven... I'm in heaven... OOOPS!! If you love \"All Things Chocolate\" and/or \"All Things Granola\", you simply have to try this dee-lish-us cereal.",
    keyPoints: ['"YUMMY" But', "chewy and totally chocolate – dark chocolate"],
    relevance: 98,
  },
  {
    id: 2,
    title: "Yummy, tempting dark chocolate chunks",
    rating: 3.8,
    reviews: 91,
    brand: "Farines",
    category: "Cereals & Granola",
    description:
      "These granola bars combine dark chocolate with crispy cereal. More specifically, they have chocolate layer on the bottom, cereal in the middle, and chocolate chunks on the top.",
    keyPoints: [
      "Reasonably good for quick, low calorie energy",
      "Great! Just wish it was bigger!",
    ],
    relevance: 92,
  },
  {
    id: 3,
    title: "Nestle Nido from Chile best powder milk in 48 years of milk drinking",
    rating: 4.4,
    reviews: 45,
    brand: "Farines",
    category: "Dairy & Eggs",
    description:
      "Nestle Nido made in Chile Ingredients, Whole milk, soy Lecithin ( emulsification properties ), Vitamin A Acetate, Vitamin D3. I did a three milk blind taste test. I mixed nonfat...",
    keyPoints: ["Thank You Nestle!!!", "Product of Chile or Mexico?"],
    relevance: 89,
  },
  {
    id: 4,
    title: "Yummy smooth dark chocolate that is also good for your health!",
    rating: 3.9,
    reviews: 260,
    brand: "Chocolats",
    category: "Chocolate",
    description:
      "Fuzzy Wuzzy's Summary: **** Recommended with warm fuzzies. I just received my single 25-ounce bar this morning and it was a good thing that I already ate breakfast...",
    keyPoints: [
      "Disappointing on a number of levels",
      "I didn't think I would fall in love with it, but I did",
    ],
    relevance: 85,
  },
  {
    id: 5,
    title: "Hardly any different than dark chocolate variety",
    rating: 3.8,
    reviews: 94,
    brand: "Farines",
    category: "Beverages",
    description:
      "Crunchy-crisp at the same time chewy. For most food that's a sin. That usually is a signal to run from high fat, salt, calories, and sweetness. Bottom line, it's as reasonably...",
    keyPoints: [
      "Tasty but small portion",
      "Good Taste with Hints of Coffee vs. Peanut Butter",
    ],
    relevance: 84,
  },
];

export const popularSearches = [
  "High protein snacks",
  "Low sugar cereals",
  "Gluten-free pasta",
  "Vegan alternatives",
];

export const categoryFilters = [
  { label: "Cereals & Granola", count: "1,245", checked: false },
  { label: "Beverages", count: "982", checked: true },
  { label: "Snacks", count: "756", checked: false },
  { label: "Dairy & Eggs", count: "532", checked: false },
  { label: "Chocolate", count: "485", checked: false },
];

export const dietaryFilters = [
  { label: "Low Sugar", count: "1,892", checked: false },
  { label: "High Protein", count: "1,456", checked: false },
  { label: "Gluten Free", count: "1,234", checked: false },
  { label: "Vegan", count: "987", checked: false },
  { label: "Keto Friendly", count: "643", checked: false },
];

export const healthGoals = [
  { label: "Weight Management", count: "1,234", checked: false },
  { label: "Heart Health", count: "987", checked: false },
  { label: "Energy Boost", count: "756", checked: false },
  { label: "Muscle Building", count: "532", checked: false },
  { label: "Digestive Health", count: "423", checked: false },
];
