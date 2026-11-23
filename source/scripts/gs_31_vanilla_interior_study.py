# LONG PIG — research (PATH B): how ROCKSTAR builds its own interiors. Read-only study of the vanilla GTA V files of the
# owner's installed game (no third-party MLO is read). Nothing is copied into the project: only statistics are written.
#   lights in interior drawables (type, colour, intensity, falloff, exponent, cone, flags, coronas, volumes),
#   shader usage + emissive multipliers + specular params, vertex-colour (CPV) channel statistics,
#   MLO archetypes (rooms, timecycles, flags, portals, entities, LOD distances, entity sets, extensions),
#   lights per MLO room (archetype lights mapped through the entities), and the vanilla timecycle modifiers they use.
# Blender 5.1 console on the PC:
#   exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_31_vanilla_interior_study.py", encoding="utf-8").read())
# Output: docs/_raw/vanilla_interior_study.json (+ docs/_raw/vanilla_timecycle_mods_used.json)
import os, json, time, re, traceback, math
from pathlib import Path
import numpy as np
import szio
from szio.vfs import VPath

ROOT = Path(os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons"))
GTA = Path(os.environ.get("GTA_ROOT", r"D:\Gamess\GTAV"))
OUT = ROOT / "docs" / "_raw" / "vanilla_interior_study.json"
OUT_TC = ROOT / "docs" / "_raw" / "vanilla_timecycle_mods_used.json"
BUDGET_S = float(globals().get("GS_BUDGET_S", 1800))
FLAGS = ["interior_only", "exterior_only", "dont_use_in_cutscene", "vehicle", "ignore_light_state", "texture_projection",
         "cast_shadows", "static_shadows", "dynamic_shadows", "calc_from_sun", "enable_buzzing", "force_buzzing", "draw_volume",
         "no_specular", "both_int_and_ext", "corona_only", "not_in_reflection", "only_in_reflection", "enable_culling_plane",
         "enable_vol_outer_color", "higher_res_shadows", "only_low_res_shadows", "far_lod_light", "dont_light_alpha",
         "cast_shadows_if_possible", "cutscene", "moving_light_source", "use_vehicle_twin", "force_medium_lod_light",
         "corona_only_lod_light", "delayed_render", "already_tested_for_occlusion"]
SPEC_PARAMS = ("specularIntensityMult", "specularFalloffMult", "bumpiness", "emissiveMultiplier", "specularFresnel")

t0 = time.time()
R = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "interior_rpfs": {}, "lights": [], "drawables": {}, "mlos": [],
     "errors": [], "notes": "statistics only; source = owner's installed GTA V (read-only)"}


def num(v):
    try:
        if hasattr(v, "value") and not isinstance(v, (int, float)):
            return int(v.value)
        if hasattr(v, "__len__") and not isinstance(v, str):
            return [round(float(x), 4) for x in v]
        return round(float(v), 4)
    except Exception:
        return str(v)


def is_interior(posix):
    p = posix.lower()
    return "/levels/gta5/interiors/" in p and not p.endswith("_lod.ydr")


# ------------------------------------------------------------------ 1. find interior archives
archives = sorted(GTA.glob("x64*.rpf")) + [GTA / "update" / "update.rpf"]
for base in (GTA / "update" / "x64" / "dlcpacks", GTA / "x64" / "dlcpacks"):
    if base.is_dir():
        archives += sorted(base.glob("*/dlc.rpf"))
ydrs, ytyps, tcs = {}, [], []
for a in archives:
    if not a.exists():
        continue
    try:
        for p in VPath(str(a)).rglob("*"):
            n = p.name.lower()
            pp = p.as_posix()
            if n.startswith("timecycle_mods") and n.endswith(".xml"):
                tcs.append(p)
            if not is_interior(pp):
                continue
            if n.endswith(".ydr"):
                ydrs[n[:-4]] = p              # later archives (update / dlc) override base names
            elif n.endswith(".ytyp"):
                ytyps.append(p)
    except Exception:
        R["errors"].append(f"scan {a.name}: " + traceback.format_exc()[-200:])
print("[gs31] interior ydr", len(ydrs), "ytyp", len(ytyps), "timecycle files", len(tcs), round(time.time() - t0), "s", flush=True)

# ------------------------------------------------------------------ 2. MLO archetypes (first, cheap): which drawables matter
mlo_arch = {}
for y in ytyps:
    try:
        yt = szio.try_load_asset(y)
        for a in getattr(yt, "archetypes", []) or []:
            if getattr(a, "type", None) is not None and a.type.name == "MLO":
                rooms = []
                for i, r in enumerate(a.rooms):
                    rooms.append({"name": r.name, "timecycle": r.timecycle, "secondary": r.secondary_timecycle, "flags": num(r.flags),
                                  "blend": num(r.blend), "ext_vis_depth": num(r.exterior_visibility_depth),
                                  "objects": len(r.attached_objects or []), "bb": [num(r.bb_min), num(r.bb_max)]})
                ents = []
                for e in a.entities:
                    ents.append({"a": e.archetype_name, "lod": num(e.lod_dist), "flags": num(e.flags),
                                 "ao": num(e.ambient_occlusion_multiplier), "aao": num(e.artificial_ambient_occlusion)})
                room_of = {}
                for ri, r in enumerate(a.rooms):
                    for oi in (r.attached_objects or []):
                        room_of[int(oi)] = ri
                for pi, p in enumerate(a.portals):
                    for oi in (p.attached_objects or []):
                        room_of.setdefault(int(oi), -1 - pi)
                mlo_arch[a.name] = {"ytyp": y.name, "rpf": y.as_posix().split("/")[-2], "rooms": rooms, "entities": ents,
                                    "room_of": room_of, "portals": [{"flags": num(p.flags), "opacity": num(p.opacity),
                                                                     "objects": len(p.attached_objects or [])} for p in a.portals],
                                    "entity_sets": len(a.entity_sets or []), "timecycle_modifiers": len(a.timecycle_modifiers or []),
                                    "mlo_flags": num(a.mlo_flags)}
            ext = getattr(a, "extensions", None) or []
            for x in ext:
                R.setdefault("archetype_extensions", {}).setdefault(type(x).__name__, 0)
                R["archetype_extensions"][type(x).__name__] += 1
    except Exception:
        R["errors"].append(f"ytyp {y.name}: " + traceback.format_exc()[-200:])
print("[gs31] MLO archetypes", len(mlo_arch), round(time.time() - t0), "s", flush=True)

# drawables referenced by MLO entities first (ordered), then the rest of the interior drawables
wanted = []
for m in mlo_arch.values():
    for e in m["entities"]:
        k = e["a"].lower()
        if k in ydrs and k not in wanted:
            wanted.append(k)
rest = [k for k in ydrs if k not in set(wanted)]

# ------------------------------------------------------------------ 3. drawables: lights, shaders, CPV
shader_count, spec_vals, cpv_by_shader = {}, {}, {}
done = 0
for k in wanted + rest:
    if time.time() - t0 > BUDGET_S:
        R["truncated_at"] = done
        break
    p = ydrs[k]
    try:
        a = szio.try_load_asset(p)
        d = a.drawable if hasattr(a, "drawable") and a.drawable is not None else a
        info = {"lights": 0, "tris": 0, "shaders": []}
        for L in (getattr(d, "lights", None) or []):
            f = int(num(L.flags)) if not isinstance(num(L.flags), str) else 0
            rec = {"d": k, "rpf": p.as_posix().split("/")[-2], "type": L.light_type.name, "color": num(L.color),
                   "intensity": num(L.intensity), "falloff": num(L.falloff), "exp": num(L.falloff_exponent),
                   "cone_in": num(L.cone_inner_angle), "cone_out": num(L.cone_outer_angle), "flags": f,
                   "flag_names": [FLAGS[b] for b in range(32) if f >> b & 1], "time_flags": num(L.time_flags),
                   "corona_size": num(L.corona_size), "corona_int": num(L.corona_intensity), "vol_int": num(L.volume_intensity),
                   "vol_size": num(L.volume_size_scale), "extent": num(L.extent), "fade": num(L.light_fade_distance),
                   "shadow_fade": num(L.shadow_fade_distance), "spec_fade": num(L.specular_fade_distance),
                   "pos": num(L.position), "dir": num(L.direction), "flash": str(L.flashiness)}
            R["lights"].append(rec)
            info["lights"] += 1
        if d.shader_group:
            for sh in d.shader_group.shaders:
                nm = sh.preset_filename or sh.name
                shader_count[nm] = shader_count.get(nm, 0) + 1
                info["shaders"].append(nm)
                for prm in sh.parameters:
                    if prm.name in SPEC_PARAMS:
                        v = prm.value
                        try:
                            v = float(v[0]) if hasattr(v, "__len__") else float(v)
                        except Exception:
                            continue
                        spec_vals.setdefault(f"{nm}:{prm.name}", []).append(v)
        if getattr(d, "models", None):
            lod = min(d.models.keys(), key=lambda q: int(q))
            for mdl in d.models[lod]:
                for gi, g in enumerate(mdl.geometries):
                    info["tris"] += len(g.index_buffer) // 3
                    names = g.vertex_buffer.dtype.names or ()
                    if "Colour0" in names and len(g.vertex_buffer) > 0:
                        c = np.asarray(g.vertex_buffer["Colour0"]).reshape(len(g.vertex_buffer), -1)[:2000].astype(float)
                        shn = info["shaders"][g.shader_index] if hasattr(g, "shader_index") and g.shader_index < len(info["shaders"]) else "?"
                        acc = cpv_by_shader.setdefault(shn, {"n": 0, "mean": np.zeros(4), "p10": [], "p90": []})
                        acc["n"] += len(c)
                        acc["mean"] += c.sum(0)[:4] if c.shape[1] >= 4 else np.pad(c.sum(0), (0, 4 - c.shape[1]))
                        acc["p10"].append(np.percentile(c, 10, axis=0)[:4].tolist())
                        acc["p90"].append(np.percentile(c, 90, axis=0)[:4].tolist())
        R["drawables"][k] = info
    except Exception:
        R["errors"].append(f"ydr {k}: " + traceback.format_exc()[-160:])
    done += 1
    if done % 300 == 0:
        print("[gs31] drawables", done, "/", len(wanted) + len(rest), "lights", len(R["lights"]), round(time.time() - t0), "s", flush=True)

# ------------------------------------------------------------------ 4. aggregates
def stats(vals):
    a = np.asarray(vals, float)
    if a.size == 0:
        return None
    return {"n": int(a.size), "min": round(float(a.min()), 3), "p10": round(float(np.percentile(a, 10)), 3),
            "median": round(float(np.median(a)), 3), "p90": round(float(np.percentile(a, 90)), 3), "max": round(float(a.max()), 3)}

R["shader_usage"] = dict(sorted(shader_count.items(), key=lambda kv: -kv[1]))
R["shader_param_stats"] = {k: stats(v) for k, v in spec_vals.items()}
R["cpv_by_shader"] = {k: {"n": v["n"], "mean_rgba": (v["mean"] / max(1, v["n"])).round(1).tolist(),
                          "p10_mean": np.mean(v["p10"], 0).round(1).tolist() if v["p10"] else None,
                          "p90_mean": np.mean(v["p90"], 0).round(1).tolist() if v["p90"] else None}
                      for k, v in cpv_by_shader.items() if v["n"] > 500}
L = R["lights"]
R["light_stats"] = {}
for typ in sorted({l["type"] for l in L}):
    s = [l for l in L if l["type"] == typ]
    fl = {}
    for l in s:
        for n in l["flag_names"]:
            fl[n] = fl.get(n, 0) + 1
    R["light_stats"][typ] = {"count": len(s), "intensity": stats([l["intensity"] for l in s]), "falloff": stats([l["falloff"] for l in s]),
                             "exponent": stats([l["exp"] for l in s]), "cone_out_deg": stats([math.degrees(l["cone_out"]) for l in s if isinstance(l["cone_out"], float)]),
                             "corona_size": stats([l["corona_size"] for l in s]), "corona_int": stats([l["corona_int"] for l in s]),
                             "with_corona": sum(1 for l in s if isinstance(l["corona_size"], float) and l["corona_size"] > 0),
                             "flags": dict(sorted(fl.items(), key=lambda kv: -kv[1])),
                             "colour_mean": np.mean([l["color"] for l in s], 0).round(1).tolist() if s else None}
# per MLO: entities, lights per room
light_count = {k: v["lights"] for k, v in R["drawables"].items()}
for name, m in mlo_arch.items():
    per_room = {}
    for i, e in enumerate(m["entities"]):
        ri = m["room_of"].get(i, None)
        rn = m["rooms"][ri]["name"] if (ri is not None and ri >= 0 and ri < len(m["rooms"])) else ("portal" if ri is not None else "?")
        pr = per_room.setdefault(rn, {"entities": 0, "lights": 0, "lit_entities": 0})
        pr["entities"] += 1
        lc = light_count.get(e["a"].lower(), 0)
        pr["lights"] += lc
        pr["lit_entities"] += 1 if lc else 0
    for r in m["rooms"]:
        if r["name"] in per_room:
            bb = r["bb"]
            try:
                area = max(0.0, (bb[1][0] - bb[0][0])) * max(0.0, (bb[1][1] - bb[0][1]))
            except Exception:
                area = None
            per_room[r["name"]]["area_m2_bb"] = round(area, 1) if area else None
            per_room[r["name"]]["timecycle"] = r["timecycle"]
    R["mlos"].append({"name": name, "ytyp": m["ytyp"], "rpf": m["rpf"], "rooms": len(m["rooms"]), "portals": len(m["portals"]),
                      "entities": len(m["entities"]), "entity_sets": m["entity_sets"], "tc_boxes": m["timecycle_modifiers"],
                      "lod_dist": stats([e["lod"] for e in m["entities"] if isinstance(e["lod"], float)]),
                      "entity_flags": sorted({e["flags"] for e in m["entities"] if not isinstance(e["flags"], str)})[:12],
                      "per_room": per_room, "room_timecycles": sorted({r["timecycle"] for r in m["rooms"] if r["timecycle"]}),
                      "portal_flags": sorted({p["flags"] for p in m["portals"] if not isinstance(p["flags"], str)})})
R["drawables_scanned"] = len(R["drawables"])
R["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(R, fh)

# ------------------------------------------------------------------ 5. vanilla timecycle modifiers used by those rooms
used = set()
for m in R["mlos"]:
    used |= set(m["room_timecycles"])
used |= {"int_gasstation"}
mods = {}
for p in tcs:
    try:
        txt = p.read_bytes().decode("utf-8", "replace")
        for mm in re.finditer(r'<modifier\s+name="([^"]+)"([^>]*)>(.*?)</modifier>', txt, re.S):
            nm = mm.group(1)
            if nm in used and nm not in mods:
                body = {}
                for v in re.finditer(r"<(\w+)>\s*([-0-9.eE]+)\s+([-0-9.eE]+)\s*</\1>", mm.group(3)):
                    body[v.group(1)] = [float(v.group(2)), float(v.group(3))]
                mods[nm] = {"file": p.name, "attrs": mm.group(2).strip(), "vars": body}
    except Exception:
        R["errors"].append(f"tc {p.name}: " + traceback.format_exc()[-160:])
with open(OUT_TC, "w", encoding="utf-8") as fh:
    json.dump({"used_by_rooms": sorted(used), "modifiers": mods}, fh, indent=1)
print("GS31_DONE drawables=%d lights=%d mlos=%d tc_mods=%d errors=%d %ds" % (len(R["drawables"]), len(R["lights"]), len(R["mlos"]),
                                                                              len(mods), len(R["errors"]), time.time() - t0))
