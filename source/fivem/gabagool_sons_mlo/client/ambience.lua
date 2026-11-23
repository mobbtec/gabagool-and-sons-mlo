local _RegCmd = RegisterCommand
local function RegisterCommand(name, fn, restricted)   -- 1.7.0: LPR_CFG.Commands switch
    if LPR_CFG and LPR_CFG.Commands and LPR_CFG.Commands[name] == false then return end
    return _RegCmd(name, fn, restricted)
end
-- LONG PIG 0.3.1-b: small living details (revision).
-- 0.3.1-l (revision):
-- two leaks with a bucket under each (corridor pipe, broken kitchen ceiling tile), layered drip effects + own drip sounds
-- (html/sfx/lp_drip1..3.ogg, distance volume), more flies (storage, WC). Vanilla particle effects from the "core" asset
-- as LOCAL looped effects, vanilla buckets as LOCAL frozen objects. Started near the shop, removed when far / on stop.
-- Nothing networked, no interior refresh. /lp_fx off | on
local ENABLED = true
local RANGE = 45.0
local ASSET = 'core'
local BUCKETS = { `prop_bucket_01a`, `prop_bucket_02a`, `prop_cs_mopbucket_01`, `prop_buck_spade_05` }
local CEIL = 3.40
local LEAKS = {                                    -- MLO-local (s, t); drops fall from z0 into a bucket on the floor
    { s = 2.75,  t = 7.35,  z0 = 3.15, room = 'corridor' },          -- under the corridor water pipe
    -- 1.9.0 (owner): no bucket / drip in the kitchen any more; the hall leak below stays
    { s = 4.828, t = 6.116, z0 = CEIL - 0.05, room = 'hall' },   -- 1.2.0: hall, under the missing ceiling tile (gs_v030_kit.HALL_HOLE)
}

local FX = {                                       -- local (s, t, z above the floor) unless world = true
    { name = 'ent_amb_tap_drip',  s = 12.10,  t = 4.72,   z = 1.12, scale = 0.8 },   -- dripping tap of the 3-bay sink
    { name = 'ent_amb_fly_swarm', s = 13.42,  t = -0.20,  z = 0.95, scale = 0.5 },   -- kitchen bin
    -- 1.9.3 (owner): faint dust motes hanging in the hall air (vanilla 'core' effect, 6 small emitters)
    { name = 'ent_amb_dust_motes', s = 0.60,  t = 1.60,   z = 1.60, scale = 1.0 },
    { name = 'ent_amb_dust_motes', s = 3.10,  t = 0.40,   z = 1.50, scale = 1.0 },
    { name = 'ent_amb_dust_motes', s = 5.40,  t = 2.20,   z = 1.60, scale = 1.0 },
    { name = 'ent_amb_dust_motes', s = -1.60, t = 4.60,   z = 1.50, scale = 1.0 },
    { name = 'ent_amb_dust_motes', s = 2.60,  t = 5.60,   z = 1.60, scale = 1.0 },
    { name = 'ent_amb_dust_motes', s = 8.60,  t = 3.20,   z = 1.70, scale = 0.8 },
    { name = 'ent_amb_fly_swarm', s = 12.10,  t = 4.40,   z = 1.05, scale = 0.4 },   -- 1.1.1: kitchen, over the 3-bay sink
    { name = 'ent_amb_fly_swarm', s = 11.30,  t = 9.90,   z = 1.10, scale = 0.45 },  -- storage, by the cartons
    { name = 'ent_amb_fly_swarm', s = 9.15,   t = 10.85,  z = 0.95, scale = 0.35 },  -- staff WC
    { name = 'ent_amb_fly_swarm', world = vector3(393.99, -1931.27, 24.55), scale = 0.7 },   -- patio bin
    { name = 'ent_amb_fly_swarm', world = vector3(414.5, -1903.8, 25.6), scale = 0.8 },      -- dumpster behind the shop
}
for _, l in ipairs(LEAKS) do                       -- layered: a thin roof drip + a tap drip at the source, ripples at the bucket
    if l.light then                                -- 1.2.0: a slow single drip only
        FX[#FX + 1] = { name = 'ent_amb_tap_drip', s = l.s, t = l.t, z = l.z0, scale = 0.9 }
    else
        FX[#FX + 1] = { name = 'ent_amb_tap_drip', s = l.s, t = l.t, z = l.z0, scale = 1.25 }
        FX[#FX + 1] = { name = 'ent_amb_water_roof_drips_thin', s = l.s, t = l.t, z = l.z0, scale = 0.35 }
        FX[#FX + 1] = { name = 'ent_amb_water_drips_sm', s = l.s, t = l.t, z = l.z0 - 0.02, scale = 0.6 }
    end
end

local DRIP_SND = { 'sfx/lp_drip1.ogg', 'sfx/lp_drip2.ogg', 'sfx/lp_drip3.ogg' }
local DRIP_RANGE = 0.0                             -- 1.2.0 (owner): drip sounds off - nothing is ever within range
local DRIP_VOL = 0.35
local handles, buckets, active = {}, {}, false

local function start()
    RequestNamedPtfxAsset(ASSET)
    local t = GetGameTimer()
    while not HasNamedPtfxAssetLoaded(ASSET) and GetGameTimer() - t < 5000 do Wait(0) end
    if not HasNamedPtfxAssetLoaded(ASSET) then return end
    for _, f in ipairs(FX) do
        local p = f.world or GS.toWorld(f.s, f.t, f.z)
        UseParticleFxAssetNextCall(ASSET)
        local h = StartParticleFxLoopedAtCoord(f.name, p.x, p.y, p.z, 0.0, 0.0, 0.0, f.scale + 0.0, false, false, false, false)
        if h and h ~= 0 then handles[#handles + 1] = h end
    end
    local probe = GS.toWorld(2.0, 3.0, 1.0)
    local interior = GetInteriorAtCoords(probe.x, probe.y, probe.z)
    for _, l in ipairs(LEAKS) do
        for _, m in ipairs(BUCKETS) do
            if IsModelInCdimage(m) then
                RequestModel(m)
                local t0 = GetGameTimer()
                while not HasModelLoaded(m) and GetGameTimer() - t0 < 4000 do Wait(0) end
                if HasModelLoaded(m) then
                    local p = GS.toWorld(l.s, l.t, 0.02)
                    local b = CreateObjectNoOffset(m, p.x, p.y, p.z, false, false, false)
                    PlaceObjectOnGroundProperly(b)
                    FreezeEntityPosition(b, true)
                    if interior ~= 0 then ForceRoomForEntity(b, interior, GetHashKey('gs_front')) end
                    buckets[#buckets + 1] = b
                    break
                end
            end
        end
    end
    for _, m in ipairs(BUCKETS) do SetModelAsNoLongerNeeded(m) end
    active = true
end

local function stop()
    for _, h in ipairs(handles) do StopParticleFxLooped(h, false) end
    handles = {}
    for _, b in ipairs(buckets) do
        if DoesEntityExist(b) then DeleteObject(b) end
    end
    buckets = {}
    for i = 1, #LEAKS do SendNUIMessage({ type = 'stop', id = 'lp_drip' .. i }) end
    active = false
end

-- drip sounds: one drop every 0.9 .. 1.7 s per leak, volume by distance, only near a leak (cheap: one thread, 250 ms)
CreateThread(function()
    local nextAt = {}
    while true do
        if active then
            local pp = GetEntityCoords(PlayerPedId())
            local now = GetGameTimer()
            for i, l in ipairs(LEAKS) do
                local d = #(pp - GS.toWorld(l.s, l.t, 0.3))
                if d < DRIP_RANGE and now >= (nextAt[i] or 0) then
                    local v = DRIP_VOL * (1.0 - d / DRIP_RANGE) ^ 1.5
                    SendNUIMessage({ type = 'play', id = 'lp_drip' .. i, src = DRIP_SND[math.random(#DRIP_SND)], volume = v, loop = false })
                    nextAt[i] = now + math.random(900, 1700)
                end
            end
            Wait(250)
        else
            Wait(1500)
        end
    end
end)

CreateThread(function()
    while true do
        local near = ENABLED and #(GetEntityCoords(PlayerPedId()) - GS.ORIGIN) < RANGE
        if near and not active then start() elseif not near and active then stop() end
        Wait(2000)
    end
end)

AddEventHandler('onResourceStop', function(res)
    if res == GetCurrentResourceName() and active then stop() end
end)

RegisterCommand('lp_fx', function(_, args)
    ENABLED = (args[1] ~= 'off')
    if not ENABLED and active then stop() end
    print('[LONG PIG] ambience effects ' .. (ENABLED and 'on' or 'off') .. ', running: ' .. #handles)
end, false)
