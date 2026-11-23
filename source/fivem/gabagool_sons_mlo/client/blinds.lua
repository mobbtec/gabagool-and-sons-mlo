-- LONG PIG 2.9.0: ROLLER BLINDS (owner 2026-11-21: "blinds that come down from the top, some half down, some up, some fully
-- down; adjust them with the arrow keys"). Replaces the vertical slats of 0.3.1.
-- One local, frozen, collision-free object per window bay (own model lp_roller: fabric + bottom bar, origin = bottom bar).
-- The fabric is one full-length panel that slides up behind the wall above the window, so it looks like it rolls up.
-- State: GlobalState.lp_rollers = { f1 .. f5 }, f = 0 fully up .. 1 fully down (owned by server/blinds.lua).
--   /pig_blind          adjust mode on / off: stand near a window, ARROW UP / ARROW DOWN move the nearest blind,
--                       BACKSPACE (or the command again) leaves the mode
--   /pig_blinds ...     server command: open | close | mix | <0-100> (all blinds)
-- Work is done only while a blind is moving or the adjust mode is on.
local MODEL = `lp_roller`
local RANGE = 70.0
local SPEED = 0.45                                   -- fraction per second
local objs, cur, target = {}, {}, {}
local animating, adjusting = false, false
local lastSent, lastMine = 0, {}

local function clamp(v) if v < 0.0 then return 0.0 elseif v > 1.0 then return 1.0 end return v end

local function wanted(i)
    local st = GlobalState.lp_rollers
    local d = GS_ROLLERS[i]
    if type(st) == 'table' and tonumber(st[i]) then return clamp(tonumber(st[i]) + 0.0) end
    return d.def
end

local function place(i, f)
    local d, o = GS_ROLLERS[i], objs[i]
    if not o or not DoesEntityExist(o) then return end
    local p = GS.toWorld(d.s, d.t, d.top - 0.05 - f * (d.len - 0.05))
    SetEntityCoordsNoOffset(o, p.x, p.y, p.z, false, false, false)
    cur[i] = f
end

local function animate()
    if animating then return end
    animating = true
    CreateThread(function()
        local last = GetGameTimer()
        while animating do
            local now = GetGameTimer()
            local dt = (now - last) / 1000.0
            last = now
            local busy = false
            for i = 1, #GS_ROLLERS do
                if objs[i] and cur[i] and target[i] and math.abs(cur[i] - target[i]) > 0.0005 then
                    local step = SPEED * dt
                    local d = target[i] - cur[i]
                    if math.abs(d) <= step then place(i, target[i]) else place(i, cur[i] + (d > 0 and step or -step)) end
                    busy = true
                end
            end
            if not busy and not adjusting then break end
            Wait(0)
        end
        animating = false
    end)
end

local function spawn()
    if not IsModelInCdimage(MODEL) then return end
    RequestModel(MODEL)
    local t = GetGameTimer()
    while not HasModelLoaded(MODEL) and GetGameTimer() - t < 5000 do Wait(0) end
    if not HasModelLoaded(MODEL) then return end
    local probe = GS.toWorld(2.0, 3.0, 1.0)
    local interior = GetInteriorAtCoords(probe.x, probe.y, probe.z)
    local room = GetHashKey('gs_front')
    for i, d in ipairs(GS_ROLLERS) do
        local p = GS.toWorld(d.s, d.t, d.top - 0.05)
        local o = CreateObjectNoOffset(MODEL, p.x, p.y, p.z, false, false, false)
        SetEntityCollision(o, false, false)
        FreezeEntityPosition(o, true)
        SetEntityLodDist(o, 120)
        SetEntityRotation(o, 0.0, 0.0, GS.YAW + d.h, 2, false)
        if interior ~= 0 then ForceRoomForEntity(o, interior, room) end
        objs[i] = o
        target[i] = wanted(i)
        place(i, target[i])
    end
    SetModelAsNoLongerNeeded(MODEL)
end

local function remove()
    for _, o in pairs(objs) do
        if DoesEntityExist(o) then DeleteObject(o) end
    end
    objs, cur = {}, {}
end

CreateThread(function()
    while true do
        local near = #(GetEntityCoords(PlayerPedId()) - GS.ORIGIN) < RANGE
        local have = next(objs) ~= nil
        if near and not have then spawn() elseif not near and have and not animating then remove() end
        Wait(2000)
    end
end)

AddStateBagChangeHandler('lp_rollers', 'global', function(_, _, value)
    if type(value) ~= 'table' then return end
    local now = GetGameTimer()
    for i = 1, #GS_ROLLERS do
        local v = tonumber(value[i])
        if v and not (lastMine[i] and now - lastMine[i] < 1200) then target[i] = clamp(v + 0.0) end   -- do not fight my own key presses
    end
    if next(objs) ~= nil then animate() end
end)

-- ---------------------------------------------------------------------------------------------- adjust mode
local function text3d(p, s)
    local on, x, y = World3dToScreen2d(p.x, p.y, p.z)
    if not on then return end
    SetTextScale(0.34, 0.34); SetTextFont(4); SetTextProportional(true); SetTextColour(255, 240, 210, 235)
    SetTextOutline(); SetTextCentre(true)
    BeginTextCommandDisplayText('STRING'); AddTextComponentSubstringPlayerName(s); EndTextCommandDisplayText(x, y)
end

local function nearest()
    local me = GetEntityCoords(PlayerPedId())
    local best, bd = nil, 3.2
    for i, d in ipairs(GS_ROLLERS) do
        local dist = #(me - GS.toWorld(d.s, d.t, 1.3))
        if dist < bd then best, bd = i, dist end
    end
    return best
end

local function adjust()
    if adjusting then adjusting = false return end
    if next(objs) == nil then return end
    adjusting = true
    animate()
    CreateThread(function()
        local last = GetGameTimer()
        while adjusting do
            local now = GetGameTimer()
            local dt = (now - last) / 1000.0
            last = now
            DisableControlAction(0, 27, true); DisableControlAction(0, 172, true); DisableControlAction(0, 173, true)
            local i = nearest()
            if i then
                local d = GS_ROLLERS[i]
                local dir = 0
                if IsDisabledControlPressed(0, 172) then dir = -1 elseif IsDisabledControlPressed(0, 173) then dir = 1 end
                if dir ~= 0 then
                    target[i] = clamp((target[i] or cur[i] or d.def) + dir * SPEED * dt)
                    lastMine[i] = now
                    if now - lastSent > 250 then
                        lastSent = now
                        TriggerServerEvent('lp_rollers:set', i, target[i])
                    end
                elseif lastMine[i] and lastSent < lastMine[i] then
                    lastSent = now
                    TriggerServerEvent('lp_rollers:set', i, target[i])
                end
                text3d(GS.toWorld(d.s, d.t, 1.55), ('~y~UP~s~ / ~y~DOWN~s~   blind %d   %d%%~n~~c~BACKSPACE - done'):format(i, math.floor((cur[i] or 0.0) * 100 + 0.5)))
            end
            if IsControlJustPressed(0, 177) then adjusting = false end
            Wait(0)
        end
    end)
end

RegisterCommand('pig_blind', adjust, false)

AddEventHandler('onResourceStop', function(res)
    if res == GetCurrentResourceName() then adjusting = false; animating = false; remove() end
end)
