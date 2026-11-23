-- 0.1.6: vanilla map props whose leaves poke through the shop walls into the interior.
-- Hidden on the client with a model hide (the game files are not touched); restored when the resource stops.
local HIDES = {
    -- dry weeds right behind the NE wall (sc1_14_strm_0.ymap), seen through the floor / wall joint inside
    { model = `prop_weeddry_nxg02b`, pos = vector3(422.234, -1906.012, 24.650), radius = 0.75 },
    { model = `prop_weeddry_nxg01`,  pos = vector3(428.208, -1912.087, 24.586), radius = 0.75 },
    -- 0.3.0 street (owner 2026-11-12): the taco kiosk is gone (vanilla_override) - its billboard, roof vents, bunting,
    -- rubbish and the two bollards in front of it are hidden too (map props; game files untouched)
    { model = `prop_billboard_05`, pos = vector3(402.607, -1927.616, 21.468), radius = 2.50 },
    { model = `prop_bollard_02a`, pos = vector3(406.849, -1931.008, 23.499), radius = 0.75 },
    { model = `prop_bollard_02a`, pos = vector3(404.032, -1934.092, 23.507), radius = 0.75 },
    { model = `prop_roofvent_16a`, pos = vector3(402.295, -1930.432, 28.665), radius = 0.75 },
    { model = `prop_roofvent_16a`, pos = vector3(396.169, -1932.025, 28.665), radius = 0.75 },
    { model = `prop_rub_binbag_06`, pos = vector3(394.771, -1927.127, 23.853), radius = 0.75 },
    { model = `prop_rub_boxpile_08`, pos = vector3(393.272, -1931.007, 23.835), radius = 0.75 },
    { model = `sc1_14_bunting1`, pos = vector3(402.488, -1934.532, 30.225), radius = 1.50 },
    { model = `sc1_14_bunting2`, pos = vector3(400.371, -1940.207, 30.185), radius = 1.50 },
    -- 0.3.1 (revision): the vanilla tables / chairs / parasols in front of the
    -- shop and the dumpster on the patio are hidden; the seating is re-laid on the patio by client/street.lua
    { model = `prop_table_03b`, pos = vector3(412.2, -1918.9, 24.5), radius = 6.0 },
    { model = `prop_table_03b_chr`, pos = vector3(412.2, -1918.9, 24.3), radius = 6.0 },
    { model = `prop_parasol_04`, pos = vector3(412.2, -1918.9, 24.3), radius = 6.0 },
    { model = `prop_dumpster_01a`, pos = vector3(397.031, -1925.291, 23.78), radius = 1.0 },
}

local active = false

local function apply()
    for _, h in ipairs(HIDES) do
        CreateModelHide(h.pos.x, h.pos.y, h.pos.z, h.radius, h.model, true)
    end
    active = true
end

local function restore()
    for _, h in ipairs(HIDES) do
        RemoveModelHide(h.pos.x, h.pos.y, h.pos.z, h.radius, h.model, false)
    end
    active = false
end

CreateThread(function()
    while true do
        local p = GetEntityCoords(PlayerPedId())
        local near = #(p - GS.ORIGIN) < 900.0      -- 0.3.1-o: was 150 m - the kiosk billboard / bollards popped back in from afar
        if near and not active then apply() elseif not near and active then restore() end
        Wait(3000)
    end
end)

AddEventHandler('onResourceStop', function(res)
    if res == GetCurrentResourceName() and active then restore() end
end)
