-- 2.6.0: 1.9.3 restaurant layout (booths, deli line, back counter) with the 2.5.0 walls, floor, coolers and gondolas.
-- 2.1.0-blockout: South LA mini market x Bronx bodega rebuild, BLOCKOUT for the composition check (plain volumes, no final
--   textures, no dressing). Ceiling, lights, fans and the overhead menu boards are the 1.9.3 ones.
-- LONG PIG — MLO interior inside the vanilla Long Pig Mini Market (Jamestown St / Little Bighorn Ave, Rancho)
-- (resource id gabagool_sons_mlo kept for compatibility)
-- 0.2.1 HERO BUILD (art direction V2/V3): new front-hall joinery, coffered ceiling + practical fixtures, rebuilt booths,
--        deli cases + food, salumi rail, slicer, tricolore — Hero Zones A/B for the in-game quality gate.
-- 0.1.1: MLO archetype + placement ymap reference the interior collision (physics dictionary), ymap renamed
--        to gs_longpig_int_milo_, MLO instance at LOD level HD, _manifest.ymf added (fixes the 0.1.0 crash
--        GTA5_b3258.exe+93419F: interior proxy == null).
-- 0.1.2: the MLO .ytyp is NOT a data_file DLC_ITYP_REQUEST any more. _manifest.ymf already declares it as the
--        dependency of gs_longpig_int_milo_.ymap (having both made FiveM unload the ytyp slot, "Fixing
--        manifest-required #typ dependency"). Same layout as the working dealer_map MLO on this server.
--        The "Streamer crashed" of 0.1.1/0.1.2 came from a server copy of sc1_14_build2.ydr corrupted by a
--        resumed upload (zeros instead of the header); replaced and verified by SHA-1.
-- 0.1.3: portals W1 / W2 / D1 face out of the room (were reversed: from inside the street was not drawn, and
--        leaving the shop was not tracked -> grey ground outside). Interior lights 3.0 -> 1.0, falloff 7.5 -> 6 m
--        (room overexposed, windows white at night).
-- 0.1.4: posters removed from W1/W2, interior window frames aligned to the vanilla frames, back doors D2 (steps)
--        and D3 (bins) working (steel leaves, portals, interior landings), MLO wall collision on the visible wall
--        faces (audit 05), vertex colours instead of all-white (night glow), new /gs_tp check views.
-- 0.1.5: every door is a vanilla GTA V door (v_ilev_csr_door_l/_r glass doors at D1, prop_map_door_01 at D2,
--        prop_sc1_12_door at D3) referenced by name — no own door models; leaves sit behind the vanilla frame stops,
--        dark wood casings around doors and windows, window stools, tiled landings, portals outside the handles.
-- 0.1.6: D3 = prop_map_door_01 (like D2), leaves 1.5 cm higher (they rubbed and stayed ajar), reveals up to the vanilla
--        stops (no light slits), auto-close of ajar doors; vanilla overrides: block occluder without the shop's street
--        faces (sc1_occl_01 / hei_ / lr_: the city behind the shop was culled when looking through two windows),
--        sc1_14_grnd_02 without the decal / sidewalk pieces inside the shop (smudge on the floor); 2 dry weeds behind the
--        NE wall hidden client-side (client/world.lua).
-- 0.2.0: Vertical Slice — CC0 PBR materials (Poly Haven / ambientCG, see assets/registry.json), partitions P1 / P2,
--        3 burgundy booths at W1, 2 refrigerated deli cases, register / coffee bar, back counter with slicers, meat rail,
--        pendants + globes; vanilla GTA props by archetype name only (till, scale, espresso machine, condiments, stools,
--        "Today's Specials" menus, chalkboard).
-- 0.2.1: HERO BUILD — gs_slice_furniture replaced by gs_v021_hall: frame-and-panel wainscot, baseboard, cap / picture
--        rails, cove cornice; coffered walnut beams, counter soffit with recessed cans, opal pendants / flush domes,
--        vanilla ceiling fans + enamel pendants; rebuilt booths (channel-tufted backs, piped cushions, walnut end caps),
--        terrazzo tables on cast-iron pedestals; curved-glass deli cases with sculpted food (original atlas), hanging
--        salumi rail, slicer, deli-paper roll, prosciutto stand; Italian tricolore flag; lights matched to fixtures
--        (29); chalkboard removed (walnut stock shelf instead); /gs_cam matched screenshot cameras.
-- 0.2.2: LIGHTING PASS (research: Rockstar interiors + reference study, methods only) — key SPOT lights with shadows on
--        the booth / queue pendants, weak no-specular fills, corona-only bulbs, festoon string lights at the window heads
--        (visible from the street), soffit can accents, picture light; own interior timecycle modifier lp_longpig_hall
--        (lp_timecycle.xml); baked artificial-ambient vertex-colour gradient (darker ceiling, floor contact).
-- 0.2.3: 90s LOBBY REBUILD to match the Long Pig Mini Market exterior — no wood any more: oxblood glazed tile wainscot
--        with aluminium cap + black cove base, cream painted brick, suspended tile ceiling with T-bar grid, 2x4 troffers
--        and recessed cans; red vinyl booths + 2 banquettes with laminate tables, window bar ledge at W2 (26 seats);
--        own backlit menu boards, LONG PIG entry mat, grime decals; 116 vanilla props by name (ATM, drinks cooler,
--        beer neons in the windows, condiments, ashtrays, photo wall, smoke detectors, sprinklers ...).
-- 0.2.4: RED ARMCHAIR LOUNGE in the middle of the hall: tiled pony wall with chrome rail, 6 own red vinyl tub armchairs
--        around 2 round coffee tables + side table with drum lamp, opal globe pendants, own 90s confetti rug; jukebox,
--        gumball machines, tall plant by name (32 seats). Food atlas 1024 px + flag textures dropped: hall < 16 MiB.

-- 0.2.5: STYLE RESET slice (docs/style_reset): worn South Los Santos deli 1995-2001. Removed ATM, drinks fridge, big plants,
--        candle sconces, gallery paintings, glass neons, jukebox, lounge; gumball machines outside (client/exterior.lua);
--        aged materials (faded oxblood tile, cream paint, dull vinyl, aged checker, yellowed ceiling), wear decals;
--        dressed cashier back wall (supply shelf, letterboards, permit, grade card, calendar, schedule, wall phone);
--        faded tricolore + family photo wall, community cork board; 2 utility tables with mismatched chairs (31 seats).
-- 0.2.6: FINISH-AND-REFINE pass (owner brief v0.2.6, non-destructive): hanging dome / globe lamps, small flag and the
--        black-and-white portraits removed; 15 recessed prismatic troffers each matched to its own light (lamp age
--        variation), diffusers / return grille with soot halos, replaced tiles, wall-top grime; day-only window fills;
--        original vertical PVC blinds in W1 / W2; P2 wall story (supplier poster, photos, sponsor plaque, ghosts,
--        anchors, patches); refined booth vinyl; till / staff mat / deli-prep details; cleaning corner in the back room;
--        floor A aged on a 4 m repeat; 2 vanilla ceiling fans + gumball facade snap (client side); /gs_floor a|b test.
-- 0.2.7  owner's in-game test: night lighting (every interior light twice with hour masks: day 07-19 as approved,
--        night 20-06 at ~half; softer troffer cones, soft ledge cans, ceiling bounce, lighter ceiling CPV, timecycle
--        up-ambient 0.28); COLD CUTS thermometer sign; 6 x 4 ft logo mat; gate counter dressing; floor litter + puddles;
--        P2 roof leak + import shelves; W1 banner + CRT TV; tray / trash station on the NW pier.
-- 0.2.7  exterior security roller shutters on W1, W2 and D1 (own models in the facade's existing shutter boxes, server-
--        synced: /close_pig [percent], /open_pig, /pig_status, /pig_debug; ACE longpig.shutters; see shared/shutters_config.lua)
-- 0.2.8  back of house per concept plan v2 (own drawable gs_boh): kitchen (range + hood, sinks, fridges, prep tables, quarry
--        tile), storage, walk-in cooler, corridor, staff entry (D3), staff back room, office, staff WC; 3 steel doors.
-- 0.2.9  PREMIUM FINAL PASS: doors in every doorway that needs one (kitchen door with vision panel, EMPLOYEES ONLY staff
--        door, staff room, storage, office = solid wood, WC = private), kitchen rebuilt as a working line (hood, griddle,
--        range, fryer, dish station, prep, rack, reach-ins, task lights), office re-planned + hidden credenza compartment,
--        AFTER HOURS entity sets (lp_open default / lp_closed: OPEN neon <-> CLOSED, public troffers off, chairs up),
--        working bell / receipt printer / hood switch / order rail (GlobalState.lp_rest), layout-audit fixes.
-- 0.2.9.1 FIX interior blinking: client/restaurant.lua called RefreshInterior every second (BOOL native returned 1 and
--        was compared with true); now only on an After Hours change, max once per 3 s. shutters.lua: same BOOL check.
--
-- stream/vanilla_override/*  are minimal edits of the shop's own vanilla files (sc1_14_build2.ydr,
--   sc1_14_sc1_emissive_sc1_14b.ydr, sc1_14_0.ybn, hi@sc1_14_0.ybn, sc1_14_grnd_02.ydr, sc1_occl_01.ymap,
--   hei_sc1_occl_01.ymap, lr_sc1_occl_01.ymap): only the painted glass / door leaves, the collision of the doorway,
--   the ground decals inside the shop and the shop's street faces of the block occluder are removed. They are derived from Rockstar game data: use on your own server,
--   do not redistribute them as a public download.
fx_version 'cerulean'
game 'gta5'
lua54 'yes'
this_is_a_map 'yes'

name 'gabagool_sons_mlo'
author 'Pryir'
description 'LONG PIG deli and mini market in Rancho, with a working kitchen, retail counters and After Hours mode'
version '3.0.2'

shared_scripts {
    'shared/shutters_config.lua',      -- 0.2.7 security shutters: settings (server + client)
    'shared/restaurant_config.lua',    -- 0.2.9 After Hours / working restaurant / hidden compartment: settings
    'shared/restaurant_data.lua',      -- 0.2.9 generated by gs_45_write_rest_data.py (interaction points from the kit)
}

client_scripts {
    'client/config.lua',
    'client/doors.lua',
    'client/debug.lua',
    'client/world.lua',
    'client/exterior.lua',
    'client/night.lua',                -- 0.3.0 extra timecycle modifier inside at night (no overexposure)
    'client/street.lua',               -- 0.3.0 patio on the removed kiosk's plinth (vanilla props, local objects)
    'client/fans.lua',
    'client/blinds_data.lua',          -- 2.9.0 roller blind bays (was: slats of the vertical blinds)
    'client/blinds.lua',               -- 2.9.0 roller blinds (/pig_blind adjust mode, arrows)
    'client/interact_data.lua',        -- 0.3.1 generated by gs_50_interact_data.py (sit / work places)
    'client/interact.lua',             -- 0.3.1 sit at tables / booths / stools, cook, wash up, coffee, mop (E)
    -- 'client/saloon.lua',  -- 3.0.0: saloon doors removed (owner)               -- 1.9.1 swinging staff saloon doors (own prop lp_saloon_leaf); back in 2.6.0
    'client/signs.lua',                -- 0.3.1 swinging blade sign + pavement A-frame (own props)
    'client/ambience.lua',             -- 0.3.1 drips, flies, bucket (vanilla ptfx, local)
    'client/floor.lua',
    'client/shutters_data.lua',        -- 0.2.7 generated by gs_shutter_geometry.py (measured openings)
    'client/shutters.lua',
    'client/restaurant.lua',           -- 0.2.9 After Hours entity sets, bell / printer / hood / order rail, hidden compartment
}

server_scripts {
    'server/shutters.lua',             -- 0.2.7 authoritative shutter state, ACE longpig.shutters, KVP persistence
    'server/blinds.lua',               -- 2.9.0 roller blinds state (GlobalState.lp_rollers), /pig_blinds
    'server/restaurant.lua',           -- 0.2.9 authoritative restaurant state (GlobalState.lp_rest), KVP persistence
}

ui_page 'html/shutters.html'          -- 0.2.7 shutter motor / stop sounds (original synthesized audio)

-- 0.2.2: own interior timecycle modifier (room gs_front -> lp_longpig_hall)
files {
    'lp_timecycle.xml',
    'textures/lp5_floor_b.png',       -- 0.2.6 floor B comparison (runtime texture, /gs_floor b)
    'textures/lp5_floor_b_n.png',
    'html/shutters.html',
    'html/sfx/lp_shutter_run.ogg',
    'html/sfx/lp_shutter_stop.ogg',
    'html/sfx/lp_bell.ogg',            -- 0.2.9 original synthesized restaurant sounds
    'html/sfx/lp_printer.ogg',
    'html/sfx/lp_hood.ogg',
    'html/sfx/lp_switch.ogg',
    'html/sfx/lp_creak.ogg',
    'html/sfx/lp_drip1.ogg',           -- 0.3.1-l own synthesized water drops (client/ambience.lua)
    'html/sfx/lp_drip2.ogg',
    'html/sfx/lp_drip3.ogg',
}
data_file 'TIMECYCLEMOD_FILE' 'lp_timecycle.xml'
data_file 'DLC_ITYP_REQUEST' 'stream/shutters/lp_shutters.ytyp'   -- 0.2.7 own shutter models (spawned client-side)
data_file 'DLC_ITYP_REQUEST' 'stream/props/lp_props.ytyp'         -- 0.2.9 hidden credenza leaf + order tickets (client-side)
