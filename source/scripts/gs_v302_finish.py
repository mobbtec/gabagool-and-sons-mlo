"""Small finishing details for the end of the upright refrigerator run."""
import math


def finish_market(out, kit):
    # Folded sheet on the exposed end of the fridge bank. A 2 mm skin follows
    # the existing laminate and turns around the front without entering the door.
    x = kit.K26.COOL_END + .030
    y = kit.K26.FF
    base = kit.PG.FLOOR + .012
    cap = base + .152
    depth = kit.YN - y
    path = [(x-.024, y-.002), (x-.003, y-.002), (x+.002, y+.003),
            (x+.002, y+depth-.018)]
    def sheet(a,b,z0,z1,hint,mat='alu20'):
        w=math.dist(a,b)
        return kit.V.F([(a[0],a[1],z0),(b[0],b[1],z0),(b[0],b[1],z1),(a[0],a[1],z1)],mat,
                       [(0,0),(w/.4,0),(w/.4,(z1-z0)/.4),(0,(z1-z0)/.4)],hint=hint)
    for i,(a,b) in enumerate(zip(path,path[1:])):
        hint=((0,-1,0),(1,-1,0),(1,0,0))[i]
        out.append(sheet(a,b,base,cap,hint))
    # A narrow rounded corner angle at trolley height protects the end panel;
    # the lower plate sits clear of it. No coplanar overlay or closed box inside the cabinet.
    a=(x-.019,y-.0025); b=(x-.004,y-.0025); c=(x+.0025,y+.004); d=(x+.0025,y+.036)
    for p,q,n in ((a,b,(0,-1,0)),(b,c,(1,-1,0)),(c,d,(1,0,0))):
        out.append(sheet(p,q,cap+.004,.91,n))
    return out


def arrange_wear(kit):
    # The old 60 cm streak under the painted Deli overlaps the lettering by
    # 0.5 mm in depth. Crop the drip to the wall next to the lettering.
    adjusted = []
    for cell, c, width, low, high, normal in kit.GRIME:
        if cell == 'drips' and c == (7.60, kit.YS):
            adjusted.append((cell,(7.03,kit.YS),.28,1.15,1.57,normal))
        else:
            adjusted.append((cell,c,width,low,high,normal))
    kit.GRIME=tuple(adjusted)
