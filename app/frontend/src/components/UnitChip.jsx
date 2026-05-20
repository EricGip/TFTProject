function formatChampionName(characterId) {
  const parts = characterId.split('_')
  const raw = parts.length > 1 ? parts.slice(1).join(' ') : parts[0]
  return raw.replace(/([A-Z])/g, ' $1').trim()
}

function formatItemName(itemName) {
  const raw = itemName.split('_').pop()
  return raw.replace(/([A-Z])/g, ' $1').trim()
}

export default function UnitChip({ unit }) {
  const name = formatChampionName(unit.character_id)
  const rarity = Math.min(Math.max(unit.rarity || 1, 1), 5)
  const stars = '★'.repeat(Math.min(unit.tier || 1, 3))
  const items = unit.item_names || []

  return (
    <div className="unit-chip">
      <div className="unit-stars">{stars}</div>
      <div className={`unit-portrait rarity-${rarity}`}>{name}</div>
      <div className="unit-name">{name}</div>
      {items.length > 0 && (
        <div className="unit-items">
          {items.slice(0, 3).map((item, i) => (
            <div key={i} className="item-dot" title={formatItemName(item)}>
              {formatItemName(item).charAt(0)}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
