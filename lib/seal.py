from conch import conch
OC='#0E4470'
def seal_g(color,w):   # w = stroke in 64-px space
    return (f'<circle cx="32" cy="32" r="26" fill="none" stroke="{color}" stroke-width="{w:.2f}"/>'
            f'<g transform="translate(32 32.5) scale(0.44) translate(-50 -50)">{conch(color, w/0.44)}</g>')
def icon_g(color,w):
    return f'<g transform="translate(32 32) scale(0.66) translate(-60 -50.5)">{conch(color, w/0.66)}</g>'
def mark(tile, color, w=2.0, rx=14, kind='seal'):
    t=f'<rect width="64" height="64" rx="{rx}" fill="{tile}"/>' if tile else ''
    g=seal_g(color,w) if kind=='seal' else icon_g(color,w)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" role="img" aria-label="Shel">{t}{g}</svg>\n'

def wave_path(y, x0, x1, amp, step):
    d=f"M{x0} {y}"; x=x0; up=True
    while x < x1:
        d+=f" q{step/2:.2f} {(-amp if up else amp):.2f} {step:.2f} 0"; x+=step; up=not up
    return d
_cid=[0]
WAVES={
 'swell2': [(48.2, 2.6, 8.5, 1.0, 64), (53.4, 2.2, 8.5, 5.25, 60)],
 'swell3': [(46.8, 2.5, 8.5, 1.0, 64), (51.6, 2.2, 8.5, 5.25, 64), (56.2, 1.8, 8.5, 1.0, 64)],
}
def wave_seal_g(color, w, style='swell2', conch_scale=0.38, conch_cy=27.6, ring=True, ring_color=None):
    ring_color = ring_color or color
    _cid[0]+=1; cid=f"shelclip{_cid[0]}"
    r=26
    paths=''.join(f'<path d="{wave_path(y, x0, x1, amp, step)}"/>' for (y,amp,step,x0,x1) in WAVES[style])
    return (f'<defs><clipPath id="{cid}"><circle cx="32" cy="32" r="{r - w*1.6:.2f}"/></clipPath></defs>'
         + (f'<circle cx="32" cy="32" r="{r}" fill="none" stroke="{ring_color}" stroke-width="{w:.2f}"/>' if ring else '')
         + f'<g clip-path="url(#{cid})" fill="none" stroke="{color}" stroke-width="{w*0.85:.2f}" stroke-linecap="round" stroke-linejoin="round">{paths}</g>'
         + f'<g transform="translate(32 {conch_cy}) scale({conch_scale}) translate(-50 -50)">{conch(color, w/conch_scale)}</g>')
