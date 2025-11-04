export interface FactorCategory {
  id: string;
  name: string;
  description: string;
  details: string[];
  factors: string[];
}

export interface FactorSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (factor: string) => void;
}
