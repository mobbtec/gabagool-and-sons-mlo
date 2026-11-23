# LONG PIG v0.2.8 — HIGH-LOD bounds of the vanilla props used to finish the back of house (kitchen, storage, cooler,
# corridor, staff entry, back room, office, WC). Source: docs/_raw/vanilla_scan_boh.json (read-only gs_39 scan of the
# owner's game files). Names only are referenced; nothing of Rockstar is shipped.
import gs_proto_geometry as _PG
VB_V028 = {
    "prop_cooker_03": ((-0.7456, -0.4502, -0.0068), (0.7456, 0.4561, 0.9644)),  # v_kitchen.rpf
    "prop_ff_sink_02": ((-0.6733, -0.3975, 0.0005), (0.6733, 0.3975, 1.1323)),  # v_fastfood.rpf
    "prop_ff_sink_01": ((-0.2031, -0.1997, -0.1104), (0.2031, 0.1997, 0.1104)),  # v_fastfood.rpf
    "prop_fridge_01": ((-0.4795, -0.6011, -0.144), (0.3301, 0.4829, 2.2988)),  # v_kitchen.rpf
    "prop_fridge_03": ((-0.4258, -0.4487, 0.0098), (0.3472, 0.3555, 1.918)),  # v_kitchen.rpf
    "prop_ff_shelves_01": ((-1.2124, -0.3916, 0.0005), (1.2124, 0.4185, 2.3906)),  # v_fastfood.rpf
    "prop_kitch_pot_huge": ((-0.251, -0.2173, -0.123), (0.2476, 0.2173, 0.207)),  # v_kitchen.rpf
    "prop_kitch_pot_lrg": ((-0.1938, -0.1929, -0.1089), (0.4043, 0.1929, 0.1167)),  # v_kitchen.rpf
    "prop_kitch_pot_med": ((-0.165, -0.1631, -0.0933), (0.3521, 0.1631, 0.0938)),  # v_kitchen.rpf
    "prop_ladel": ((-0.0464, -0.1743, -0.0166), (0.0464, 0.1714, 0.0674)),  # v_kitchen.rpf
    "prop_micro_01": ((-0.2446, -0.1519, -0.0703), (0.2451, 0.2173, 0.2153)),  # v_kitchen.rpf
    "prop_cs_bin_02": ((-0.333, -0.333, 0.0), (0.333, 0.333, 0.877)),  # lev_des.rpf
    "prop_shelves_01": ((-1.3877, -0.4048, 0.0), (1.3945, 0.394, 1.8955)),  # v_storage.rpf
    "prop_shelves_02": ((-1.3877, -0.4048, 0.0), (1.3945, 0.394, 1.8955)),  # v_storage.rpf
    "prop_boxpile_01a": ((-0.3584, -0.3931, -0.1665), (0.7466, 0.4492, 0.3306)),  # v_storage.rpf
    "prop_boxpile_06a": ((-0.9624, -0.835, 0.0), (0.959, 0.8276, 1.0928)),  # v_storage.rpf
    "prop_cardbordbox_02a": ((-0.2246, -0.3125, -0.0005), (0.2246, 0.3125, 0.3813)),  # v_storage.rpf
    "prop_cardbordbox_03a": ((-0.3242, -0.4399, 0.001), (0.3242, 0.4399, 0.5142)),  # v_storage.rpf
    "prop_cardbordbox_04a": ((-0.481, -0.3462, 0.0005), (0.481, 0.3462, 0.6948)),  # v_storage.rpf
    "prop_cs_cardbox_01": ((-0.2153, -0.1724, -0.1743), (0.2153, 0.1724, 0.1743)),  # lev_des.rpf
    "prop_sacktruck_02a": ((-0.3086, -0.2983, 0.0), (0.3003, 0.2681, 1.4536)),  # v_storage.rpf
    "v_ind_cfbox": ((-0.1455, -0.1206, -0.1538), (0.1455, 0.1206, 0.1538)),  # v_storage.rpf
    "v_ind_cfbox2": ((-0.272, -0.1133, -0.2021), (0.272, 0.1133, 0.2021)),  # v_storage.rpf
    "prop_paper_box_01": ((-0.2173, -0.293, -0.1821), (0.2173, 0.293, 0.1821)),  # v_office.rpf
    "v_ind_cf_shelf": ((-1.4004, -0.4048, 0.0), (1.4111, 0.394, 1.8955)),  # int_industrial.rpf
    "prop_fruit_plas_crate_01": ((-0.3813, -0.3198, -0.1802), (0.3813, 0.3198, 0.1802)),  # lev_des.rpf
    "v_ind_cf_crate2": ((-0.25, -0.3501, 0.0), (0.25, 0.3501, 0.3999)),  # v_storage.rpf
    "prop_office_desk_01": ((-0.8452, -0.376, -0.3589), (0.8452, 0.376, 0.3589)),  # v_office.rpf
    "v_res_tre_officechair": ((-0.2651, -0.2905, -0.46), (0.2681, 0.291, 0.46)),  # int_residential.rpf
    "prop_monitor_03b": ((-0.2539, -0.2754, 0.0), (0.2583, 0.2222, 0.4731)),  # v_electrical.rpf
    "prop_keyboard_01a": ((-0.2544, -0.0864, -0.0005), (0.2505, 0.0928, 0.0317)),  # v_electrical.rpf
    "prop_office_phone_tnt": ((-0.0728, -0.0903, -0.0474), (0.1157, 0.1846, 0.0654)),  # v_office.rpf
    "v_res_desklamp": ((-0.2749, -0.0913, 0.0005), (0.2749, 0.0913, 0.6523)),  # int_residential.rpf
    "v_med_cor_filingcab": ((-0.2729, -0.4443, -0.0005), (0.2729, 0.4458, 1.8462)),  # int_medical.rpf
    "prop_ld_int_safe_01": ((-0.3418, -0.373, -0.4727), (0.3418, 0.3125, 0.4727)),  # lev_des.rpf
    "prop_coathook_01": ((-0.2734, -0.0591, 0.0), (0.2734, 0.0591, 0.166)),  # v_office.rpf
    "v_club_roc_jacket1": ((-0.3623, -0.0752, -0.8618), (0.3442, 0.0664, 0.0044)),  # int_club.rpf
    "v_club_roc_jacket2": ((-0.3628, -0.0801, -0.77), (0.3379, 0.043, 0.0044)),  # int_club.rpf
    "prop_cd_folder_pile1": ((-0.0483, -0.2192, -0.1919), (0.4292, 0.1616, 0.188)),  # v_minigame.rpf
    "prop_cs_documents_01": ((-0.1123, -0.1641, -0.0078), (0.1123, 0.1641, 0.0078)),  # v_minigame.rpf
    "v_ret_csr_bin": ((-0.1724, -0.1724, -0.231), (0.1724, 0.1724, 0.231)),  # int_retail.rpf
    "prop_toilet_01": ((-0.2124, -0.3364, 0.0005), (0.2124, 0.3223, 0.9604)),  # v_bathroom.rpf
    "prop_sink_06": ((-0.2949, -0.231, -0.0), (0.2949, 0.231, 1.0669)),  # v_bathroom.rpf
    "prop_toilet_roll_02": ((-0.1294, -0.1978, -0.1416), (0.1294, 0.001, 0.1416)),  # v_bathroom.rpf
    "prop_toilet_brush_01": ((-0.0942, -0.0942, 0.0205), (0.0942, 0.0942, 0.5552)),  # v_bathroom.rpf
    "prop_handdry_01": ((-0.1567, -0.126, -0.1899), (0.1567, -0.0054, 0.189)),  # v_bathroom.rpf
    "prop_soap_disp_01": ((-0.1143, -0.1353, -0.2129), (0.1143, 0.0054, 0.2129)),  # v_bathroom.rpf
    "prop_bin_07a": ((-0.3325, -0.3174, 0.0), (0.3311, 0.3174, 0.8643)),  # v_bins.rpf
    "prop_cs_trolley_01": ((-0.6934, -0.2441, -0.4907), (0.6172, 0.3579, 0.5088)),  # v_minigame.rpf
    "prop_micro_02": ((-0.2441, -0.186, -0.1479), (0.2441, 0.186, 0.1479)),  # v_kitchen.rpf
    "v_serv_metro_walllightcage": ((-0.229, -0.105, -0.1943), (0.2363, 0.0679, 0.1943)),  # catalogue (gs_28)
    "prop_map_door_01": (tuple(_PG.VDOORS["prop_map_door_01"]["min"]), tuple(_PG.VDOORS["prop_map_door_01"]["max"])),
}
