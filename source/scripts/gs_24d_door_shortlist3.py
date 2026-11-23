# LONG PIG — third shortlist: replacement for the D3 back door (opening 1.219 x 2.389), internal reference only.
#   exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_24d_door_shortlist3.py", encoding="utf-8").read())
import os
os.environ["GS_DOOR_SHORTLIST"] = ",".join([
    "v_ilev_serv_door01.ydr", "v_ilev_cor_firedoor.ydr", "prop_hw1_23_door.ydr", "prop_cs6_03_door_l.ydr",
    "v_ilev_ra_door3.ydr", "ch_prop_ch_service_door_03b.ydr", "prop_cs4_11_door.ydr", "v_ilev_sol_off_door01.ydr",
    "v_ilev_arm_secdoor.ydr", "prop_mine_doorng_l.ydr", "kt1_11_mp_door.ydr", "v_61_hlw_mesh_cdoor.ydr",
])
exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_24_vanilla_doors.py", encoding="utf-8").read())
os.environ.pop("GS_DOOR_SHORTLIST", None)
