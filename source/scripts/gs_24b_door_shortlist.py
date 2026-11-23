# LONG PIG — export the shortlisted vanilla door models as CWXML (internal reference only, never shipped).
# Blender 5.1 console on the PC:
#   exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_24b_door_shortlist.py", encoding="utf-8").read())
import os
os.environ["GS_DOOR_SHORTLIST"] = ",".join([
    # D1 — double front door candidates (glass shop doors)
    "v_ilev_247door.yft", "v_ilev_247door_r.yft", "v_ilev_gasdoor.yft", "v_ilev_gasdoor_r.yft", "v_ilev_ml_door1.yft",
    "prop_showroom_door_l.ydr", "prop_showroom_door_r.ydr", "prop_shop_front_door_l.ydr", "prop_shop_front_door_r.ydr",
    "v_ilev_cs_door01.ydr", "prop_grumandoor_l.ydr", "v_ilev_store_door.ydr",
    # D2 / D3 — single steel back doors
    "prop_map_door_01.ydr", "prop_sc1_12_door.ydr", "prop_sm1_11_doorl.ydr", "v_ilev_cor_firedoor.ydr",
    "prop_bs_map_door_01.ydr", "prop_ss1_08_mp_door_l.ydr", "prop_police_door_l.ydr", "v_ilev_ss_doorext.ydr",
    "prop_magenta_door.ydr", "v_ilev_fa_backdoor.ydr", "prop_bh1_48_backdoor_l.ydr",
])
exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_24_vanilla_doors.py", encoding="utf-8").read())
os.environ.pop("GS_DOOR_SHORTLIST", None)
