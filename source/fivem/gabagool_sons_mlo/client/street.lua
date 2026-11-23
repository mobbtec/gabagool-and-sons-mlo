-- LONG PIG 0.3.0 street (owner 2026-11-12): the taco kiosk next to the shop is removed (vanilla_override); the hole
-- is closed flush with the lot (parking tarmac). This script dresses the place with vanilla GTA props as LOCAL frozen objects (nothing
-- networked, game files untouched): tables + chairs + parasols like the ones in front of the shop, bins, a bench.
local ENABLED = true
local CENTRE = vector3(399.0, -1931.3, 23.84)
local Z = 23.84                                   -- patio top
local spawned = {}

-- 0.3.1 (revision):
-- everything is laid out on ONE grid parallel to the pavement edge: A = along the fence, B = from the fence into the patio.
local AX, AY = 0.756, -0.655
local BX, BY = 0.655, 0.756
local LINE_H = 319.1                              -- heading of the vanilla fence run this continues
local FX, FY = 393.30, -1931.60                   -- grid origin (north-west end of the fence line)

local function grid(a, b) return FX + AX * a + BX * b, FY + AY * a + BY * b end

local function tableSet(a, b)
    local x, y = grid(a, b)
    local t = { { m = `prop_table_03b`, x = x, y = y, h = LINE_H } }
    for _, o in ipairs({ { 0.85, 0.0 }, { -0.85, 0.0 }, { 0.0, 0.85 }, { 0.0, -0.85 } }) do
        local cx, cy = grid(a + o[1], b + o[2])
        t[#t + 1] = { m = `prop_table_03b_chr`, x = cx, y = cy, face = { x, y } }
    end
    local px, py = grid(a + 0.88, b + 0.88)
    t[#t + 1] = { m = `prop_parasol_04`, x = px, y = py, h = LINE_H }
    return t
end

local PROPS = {}
local function add(list) for _, e in ipairs(list) do PROPS[#PROPS + 1] = e end end
add(tableSet(2.0, 2.7))
add(tableSet(5.4, 2.7))
add(tableSet(2.0, 5.7))
add(tableSet(5.4, 5.7))
do
    local b1x, b1y = grid(0.3, 0.7)
    local b2x, b2y = grid(8.6, 0.7)
    local bx, by = grid(4.4, 0.75)
    local tx, ty = grid(4.4, 6.0)
    add({
        { m = `prop_bin_07a`, x = b1x, y = b1y, h = LINE_H },
        { m = `prop_bin_07a`, x = b2x, y = b2y, h = LINE_H },
        { m = `prop_bench_01a`, x = bx, y = by, face = { tx, ty } },
        -- the vanilla green fence continued in ONE straight line along the pavement edge (explicit z, upright)
        { m = `prop_fncsec_02a`, x = 398.82, y = -1936.39, z = 23.48, h = LINE_H },
        { m = `prop_fncsec_02a`, x = 397.32, y = -1935.09, z = 23.50, h = LINE_H },
        { m = `prop_fncsec_02a`, x = 395.82, y = -1933.79, z = 23.52, h = LINE_H },
        { m = `prop_fncsec_02a`, x = 394.32, y = -1932.49, z = 23.54, h = LINE_H },
        { m = `prop_fncsec_02a`, x = 392.82, y = -1931.19, z = 23.54, h = LINE_H },
        -- 0.3.1-l (revision): one more section on the same line up
        -- to the planter + the vanilla end pole (the kerb now runs on to the fence: vanilla_override sc1_14_grnd_02)
        { m = `prop_fncsec_02a`, x = 391.32, y = -1929.89, z = 23.54, h = LINE_H },
        { m = `prop_fncsec_02pole`, x = 390.544, y = -1929.213, z = 23.54, h = LINE_H },
    })
end

local function headingTo(x, y, tx, ty)             -- GTA heading of the direction (tx - x, ty - y)
    return (math.deg(math.atan(ty - y, tx - x)) - 90.0) % 360.0
end

local function spawnAll()
    for _, e in ipairs(PROPS) do
        if IsModelInCdimage(e.m) then
            RequestModel(e.m)
            local t = GetGameTimer()
            while not HasModelLoaded(e.m) and GetGameTimer() - t < 5000 do Wait(0) end
            if HasModelLoaded(e.m) then
                local obj = CreateObjectNoOffset(e.m, e.x, e.y, Z + 0.5, false, false, false)
                local h = e.h or 0.0
                if e.face then h = (headingTo(e.x, e.y, e.face[1], e.face[2]) + 180.0) % 360.0 end   -- model front = local -Y
                if e.z then
                    SetEntityCoordsNoOffset(obj, e.x, e.y, e.z, false, false, false)
                    SetEntityRotation(obj, 0.0, 0.0, h, 2, false)
                else
                    SetEntityHeading(obj, h)
                    PlaceObjectOnGroundProperly(obj)
                    local r = GetEntityRotation(obj, 2)
                    SetEntityRotation(obj, 0.0, 0.0, r.z, 2, false)       -- upright: no leaning on the slope / kerb
                end
                FreezeEntityPosition(obj, true)
                SetEntityLodDist(obj, 350)                             -- 0.3.1-o: tables / parasols / fence visible from afar
                SetEntityAsMissionEntity(obj, true, true)
                spawned[#spawned + 1] = obj
                SetModelAsNoLongerNeeded(e.m)
            end
        end
    end
end

local function removeAll()
    for _, obj in ipairs(spawned) do
        if DoesEntityExist(obj) then DeleteObject(obj) end
    end
    spawned = {}
end

CreateThread(function()
    while true do
        local near = ENABLED and #(GetEntityCoords(PlayerPedId()) - CENTRE) < 330.0   -- 0.3.1-o: was 110 m (patio seen from afar)
        if near and #spawned == 0 then spawnAll() elseif not near and #spawned > 0 then removeAll() end
        Wait(2500)
    end
end)

AddEventHandler('onResourceStop', function(res)
    if res == GetCurrentResourceName() then removeAll() end
end)
