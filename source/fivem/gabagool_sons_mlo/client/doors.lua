local _RegCmd = RegisterCommand
local function RegisterCommand(name, fn, restricted)   -- 1.7.0: LPR_CFG.Commands switch
    if LPR_CFG and LPR_CFG.Commands and LPR_CFG.Commands[name] == false then return end
    return _RegCmd(name, fn, restricted)
end
-- Prototype door handling: entrance D1 (two glass leaves) and the back doors D2 / D3.
-- 0.1.5: all leaves are vanilla GTA V door models placed as MLO entities (v_ilev_csr_door_l/_r, prop_map_door_01,
-- prop_sc1_12_door); their own archetypes make GTA create them as real doors. Here they are only registered in the door system so their state can be
-- read / changed for testing; they stay UNLOCKED. (Server-authoritative locking comes with the next stage.)
local registered = false

local function doorHash(id) return joaat(id) end

local function registerDoors()
    for _, d in ipairs(GS.DOORS) do
        local w = GS.toWorld(d.pos.x, d.pos.y, d.pos.z)
        local h = doorHash(d.id)
        if not IsDoorRegisteredWithSystem(h) then
            AddDoorToSystem(h, d.model or GS.DOOR_MODEL, w.x, w.y, w.z, false, false, false)
        end
        DoorSystemSetDoorState(h, 0, false, false) -- 0 = unlocked
    end
    registered = true
end

CreateThread(function()
    while true do
        local ped = PlayerPedId()
        local p = GetEntityCoords(ped)
        if #(p - GS.ORIGIN) < 80.0 then
            if not registered then registerDoors() end
        end
        Wait(2000)
    end
end)

-- 0.1.6: unlocked GTA doors sometimes come to rest a few degrees open (a light slit along the free edge).
-- When nobody stands next to a door and it is only slightly ajar, close it.
CreateThread(function()
    while true do
        local wait = 2000
        if registered then
            local p = GetEntityCoords(PlayerPedId())
            if #(p - GS.ORIGIN) < 40.0 then
                wait = 1000
                for _, d in ipairs(GS.DOORS) do
                    local h = doorHash(d.id)
                    local w = GS.toWorld(d.pos.x, d.pos.y, d.pos.z)
                    local r = DoorSystemGetOpenRatio(h)
                    if math.abs(r) > 0.003 and math.abs(r) < 0.15 and #(p - w) > 2.5 then
                        DoorSystemSetOpenRatio(h, 0.0, false, true)
                    end
                end
            end
        end
        Wait(wait)
    end
end)

RegisterCommand('gs_door', function(_, args)
    local mode = args[1] or 'state'
    if not registered then registerDoors() end
    for _, d in ipairs(GS.DOORS) do
        local h = doorHash(d.id)
        if mode == 'lock' then DoorSystemSetDoorState(h, 1, false, false)
        elseif mode == 'unlock' then DoorSystemSetDoorState(h, 0, false, false) end
        print(('[gs_door] %s state=%s open_ratio=%.2f'):format(d.id, tostring(DoorSystemGetDoorState(h)), DoorSystemGetOpenRatio(h)))
    end
end, false)
