-- 0.2.5 STYLE RESET (LP-006): the gumball / candy machines moved OUT of the hall. They are vanilla GTA models spawned as
-- LOCAL objects on every client (nothing networked, nothing written to the map) and frozen.
-- 0.2.6: grouped on the blank NW facade just past window W2; each one is ray-cast onto the real facade behind it so its
-- back stands GS.EXTERIOR_GAP from the wall, then put on the sidewalk. Toggle / positions: client/config.lua.
local spawned = {}

-- distance from the model origin to its back face (model front = local -Y, back = +Y)
local function backDepth(model)
    local mn, mx = GetModelDimensions(model)
    return mx.y
end

local function snapToFacade(e, model)
    -- start 1.5 m out on the street side, cast towards the building (opposite to the front direction)
    local base = GS.toWorld(e.s, e.t, 0.85)
    local fwd = GS.toWorld(e.s + e.fx, e.t + e.fy, 0.85) - base             -- world front direction (unit, horizontal)
    local from = base + fwd * 1.5
    local to = base - fwd * 1.5
    local ray = StartShapeTestRay(from.x, from.y, from.z, to.x, to.y, to.z, 1, PlayerPedId(), 7)
    local status, hit, hitPos
    local t0 = GetGameTimer()
    repeat
        status, hit, hitPos = GetShapeTestResult(ray)
        if status == 1 then Wait(0) end
    until status ~= 1 or GetGameTimer() - t0 > 500
    if hit == 1 or hit == true then
        local p = hitPos + fwd * (backDepth(model) + (GS.EXTERIOR_GAP or 0.03))
        return vector3(p.x, p.y, base.z - 0.45), true
    end
    return GS.toWorld(e.s, e.t, 0.40), false
end

local function spawnAll()
    for _, e in ipairs(GS.EXTERIOR_PROPS or {}) do
        RequestModel(e.model)
        local t = GetGameTimer()
        while not HasModelLoaded(e.model) and GetGameTimer() - t < 5000 do Wait(0) end
        if HasModelLoaded(e.model) then
            local p, snapped = GS.toWorld(e.s, e.t, 0.40), false
            if GS.EXTERIOR_SNAP then p, snapped = snapToFacade(e, e.model) end
            local obj = CreateObjectNoOffset(e.model, p.x, p.y, p.z, false, false, false)
            SetEntityHeading(obj, GS.heading(-e.fx, -e.fy))     -- model front = local -Y
            PlaceObjectOnGroundProperly(obj)
            FreezeEntityPosition(obj, true)
            SetEntityAsMissionEntity(obj, true, true)
            spawned[#spawned + 1] = obj
            SetModelAsNoLongerNeeded(e.model)
            if GS.DEBUG_EXTERIOR then print(('[gs] gumball %s snapped=%s'):format(tostring(e.model), tostring(snapped))) end
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
        if GS.EXTERIOR_ENABLED then
            local near = #(GetEntityCoords(PlayerPedId()) - GS.ORIGIN) < 120.0
            if near and #spawned == 0 then spawnAll() elseif not near and #spawned > 0 then removeAll() end
        elseif #spawned > 0 then
            removeAll()
        end
        Wait(2500)
    end
end)

AddEventHandler('onResourceStop', function(res)
    if res == GetCurrentResourceName() then removeAll() end
end)
