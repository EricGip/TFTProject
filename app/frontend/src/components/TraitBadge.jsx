function formatTraitName(name) {
  const part = name.split('_').pop()
  return part.replace(/([A-Z])/g, ' $1').trim()
}

export default function TraitBadge({ trait }) {
  const tier = Math.min(trait.tier || 0, 4)
  return (
    <span className={`trait-badge tier-${tier}`}>
      <span className="trait-num">{trait.num_units}</span>
      {formatTraitName(trait.trait_name)}
    </span>
  )
}
