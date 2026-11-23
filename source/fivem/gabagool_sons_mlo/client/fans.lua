-- 0.2.6 (brief section 4.5): two ordinary ceiling fans over the centre tables. Vanilla prop_outdoor_fan_01, spawned as
-- LOCAL objects (not networked), assigned to the MLO room, slowly turned around their own axis only while the player is
-- within 35 m. The whole fan turns about its vertical axis; the canopy is round, so only the blades read as moving.
-- No per-frame work when nobody is near; everything is deleted on resource stop. Config: client/config.lua (GS.FANS*).
local fans = {}
local angle = 0.0

local function spawnFans()
    local model = GS.FANS_MODEL
    RequestModel(model)
    local t = GetGameTimer()
    while not HasModelLoaded(model) and GetGameTimer() - t < 5000 do Wait(0) end
    if not HasModelLoaded(model) then
        print('[gs] fan model did not load')
        return
    end
    local probe = GS.toWorld(2.0, 3.0, 1.0)
    local interior = GetInteriorAtCoords(probe.x, probe.y, probe.z)
    for _, f in ipairs(GS.FANS or {}) do
        local p = GS.toWorld(f.s, f.t, GS.FANS_Z)
        local obj = CreateObjectNoOffset(model, p.x, p.y, p.z, false, false, false)
        SetEntityCollision(obj, false, false)
        FreezeEntityPosition(obj, true)
        SetEntityHeading(obj, GS.YAW)
        if interior ~= 0 then ForceRoomForEntity(obj, interior, GetHashKey('gs_front')) end
        fans[#fans + 1] = obj
    end
    SetModelAsNoLongerNeeded(model)
end

local function removeFans()
    for _, obj in ipairs(fans) do
        if DoesEntityExist(obj) then DeleteObject(obj) end
    end
    fans = {}
end

CreateThread(function()
    while true do
        local wait = 1500
        if GS.FANS_ENABLED then
            local near = #(GetEntityCoords(PlayerPedId()) - GS.ORIGIN) < 35.0
            if near and #fans == 0 then spawnFans() elseif not near and #fans > 0 then removeFans() end
            if near and #fans > 0 and (GS.FANS_RPM or 0.0) > 0.0 then
                angle = (angle + GS.FANS_RPM * 6.0 * GetFrameTime()) % 360.0          -- rpm -> degrees per second
                for k, obj in ipairs(fans) do
                    SetEntityRotation(obj, 0.0, 0.0, GS.YAW + angle + k * 37.0, 2, false)
                end
                wait = 0
            end
        elseif #fans > 0 then
            removeFans()
        end
        Wait(wait)
    end
end)

AddEventHandler('onResourceStop', function(res)
    if res == GetCurrentResourceName() then removeFans() end
end)
