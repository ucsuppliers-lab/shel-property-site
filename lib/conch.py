P = {
 'spire': "M50 5 L36.5 33.5 M50 5 L63.5 33.5",
 'tiers': "M46.6 12.5 Q50 14.2 53.4 12.5 M43.3 19.5 Q50 22.6 56.7 19.5 M39.9 26.5 Q50 31 60.1 26.5 M36.5 33.5 Q50 39.5 63.5 33.5",
 'left': "M36.5 33.5 C29 45 28.5 63 38 77 C42 83 46.5 89 50 96",
 'lip': "M63.5 33.5 C76 37 86 47 86 60 C86 74 72 85 50 96",
 'aperture': "M61 42 C69.5 50 70.5 64 62.5 74 C59 78.5 55 81.5 51 84",
 'body': "M34 52 C41.5 47.5 50.5 46 58.5 47.5",
}
def conch(color, w=1.6, extra=''):
    return (f'<g fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round" {extra}>'
            + ''.join(f'<path d="{d}"/>' for d in P.values()) + '</g>')
