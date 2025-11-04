interface FilterGroupProps {
  items: { id: string; label: string }[];
  activeId: string;
  onChange: (id: string) => void;
}

export function FilterGroup({ items, activeId, onChange }: FilterGroupProps) {
  return (
    <div className="filter-group">
      {items.map((item) => (
        <button
          key={item.id}
          type="button"
          onClick={() => onChange(item.id)}
          className={`filter-item ${activeId === item.id ? "is-active" : ""}`}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
