# LONG PIG — second shortlist: double-door leaves ~0.95 m wide for D1 (internal reference only, never shipped).
#   exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_24c_door_shortlist2.py", encoding="utf-8").read())
import os
os.environ["GS_DOOR_SHORTLIST"] = ",".join([
    "v_ilev_csr_door_l.ydr", "v_ilev_csr_door_r.ydr", "v_ilev_roc_door1_l.ydr", "v_ilev_roc_door1_r.ydr",
    "prop_grumandoor_l.ydr", "prop_grumandoor_r.ydr",
])
exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_24_vanilla_doors.py", encoding="utf-8").read())
os.environ.pop("GS_DOOR_SHORTLIST", None)
