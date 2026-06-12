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
