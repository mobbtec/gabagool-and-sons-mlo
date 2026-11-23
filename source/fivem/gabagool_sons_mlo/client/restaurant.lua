local _RegCmd = RegisterCommand
local function RegisterCommand(name, fn, restricted)   -- 1.7.0: LPR_CFG.Commands switch
    if LPR_CFG and LPR_CFG.Commands and LPR_CFG.Commands[name] == false then return end
    return _RegCmd(name, fn, restricted)
end
-- LONG PIG v0.2.9.1 — WORKING RESTAURANT / AFTER HOURS / FAMILY BUSINESS, CLIENT.
-- Reacts to GlobalState.lp_rest (server/restaurant.lua). Lightweight: one 1 s watcher for the interior entity sets, the
-- per-frame loop only runs while the player is within a few metres of a control or the hood is on next to him.
--   AFTER HOURS     ActivateInteriorEntitySet lp_open / lp_closed + RefreshInterior (lp_open is also the ymap default)
--   WORKING         prompts at the switch, bell, receipt printer, hood switch and order rail; hood lamps (DrawLight) +
--                   fan loop while the hood is on; order tickets = local objects on the rail
--   FAMILY BUSINESS hidden leaf of the office credenza = local object (lp_secret_door), opens / closes smoothly
if not LPR_CFG or not LPR_CFG.Enabled then return end
local C, D = LPR_CFG, LPR_DATA

local state = { afterHours = false, hood = false, secret = false, tickets = {}, seq = -1 }
local near = false                         -- player within 60 m of the shop
local interiorId = 0
local secretObj, secretAngle, secretTarget = nil, 0.0, 0.0
local tickets = {}                         -- spawned ticket objects, index = rail slot
local hoodPlaying = false

-- ------------------------------------------------------------------ helpers
local function W(p) return GS.toWorld(p.x, p.y, p.z) end
-- FiveM Lua: natives that return BOOL give 1 / false (not true / false) -> never compare their result with a boolean
local function B(v) return v == true or v == 1 end

local function localYawHeading(deg)        -- model local yaw in the MLO frame -> GTA heading of the model +Y axis
    local r = math.rad(deg)
    return GS.heading(-math.sin(r), math.cos(r))
end

local function nui(kind, id, file, vol, loop)
    SendNUIMessage({ type = kind, id = id, src = file, volume = vol or 0.0, loop = loop or false })
end

local function volAt(p, dist)
    local d = #(GetEntityCoords(PlayerPedId()) - W(p))
    local v = 1.0 - d / dist
    if v <= 0.0 then return 0.0 end
    return C.SoundVolume * v ^ 1.4
end

local SND = { bell = 'sfx/lp_bell.ogg', printer = 'sfx/lp_printer.ogg', switch = 'sfx/lp_switch.ogg', creak = 'sfx/lp_creak.ogg' }

RegisterNetEvent('lp_rest:sound', function(name, p)
    if not SND[name] then return end
    local v = volAt(vector3(p.x, p.y, p.z), C.SoundDist)
    if v > 0.01 then nui('play', 'lp_' .. name .. GetGameTimer(), SND[name], v, false) end
end)

local NOTE = { no_perm = 'Только для персонала.', wait = 'Подождите немного.', locked = 'Заперто.', empty = 'Нет заказов.' }
RegisterNetEvent('lp_rest:notify', function(code)
    local msg = NOTE[code]
    if not msg then return end
    BeginTextCommandThefeedPost('STRING'); AddTextComponentSubstringPlayerName(msg); EndTextCommandThefeedPostTicker(false, false)
end)

local function loadModel(m)
    if not IsModelInCdimage(m) then return false end
    RequestModel(m)
    local t = GetGameTimer()
    while not HasModelLoaded(m) and GetGameTimer() - t < 6000 do Wait(0) end
    return HasModelLoaded(m)
end

local function getInterior()
    local p = GS.toWorld(4.0, 3.0, 1.2)
    local id = GetInteriorAtCoords(p.x, p.y, p.z)
    if id ~= 0 and B(IsValidInterior(id)) then return id end
    return 0
end

local function placeInRoom(obj)
    if interiorId ~= 0 then ForceRoomForEntity(obj, interiorId, GetHashKey(D.room)) end
end

-- ------------------------------------------------------------------ AFTER HOURS: entity sets
-- 0.2.9.1 FIX (revision): the old check compared IsInteriorEntitySetActive() (returns 1) with true, never
-- matched, and called RefreshInterior every second -> the whole interior blinked. Now the sets are switched and the interior
-- refreshed ONLY when the wanted state differs from what this client last applied (state change, or the interior streamed
-- in again), the native result is read as a boolean, and RefreshInterior can never run more often than every 3 s.
local applied = { id = 0, closed = nil }
local lastRefresh = -100000

local function applySets()
    local id = getInterior()
    if id == 0 or not B(IsInteriorReady(id)) then return end
    interiorId = id
    local wantClosed = state.afterHours == true
    if applied.id == id and applied.closed == wantClosed then return end
    local o, c = D.sets.open, D.sets.closed
    local isOpen, isClosed = B(IsInteriorEntitySetActive(id, o)), B(IsInteriorEntitySetActive(id, c))
    if isOpen == (not wantClosed) and isClosed == wantClosed then
        applied.id, applied.closed = id, wantClosed                 -- already right (ymap default lp_open): no refresh
        return
    end
    if GetGameTimer() - lastRefresh < 3000 then return end           -- hard limit, retried by the 1 s watcher
    if wantClosed then
        DeactivateInteriorEntitySet(id, o); ActivateInteriorEntitySet(id, c)
    else
        DeactivateInteriorEntitySet(id, c); ActivateInteriorEntitySet(id, o)
    end
    RefreshInterior(id)
    lastRefresh = GetGameTimer()
    applied.id, applied.closed = id, wantClosed                     -- applied once; not re-checked until the state changes
end

-- ------------------------------------------------------------------ order tickets on the kitchen rail
local function slotPos(i)
    local r = D.ticket_rail
    return vector3(r.s1 - 0.42 - (i - 1) * 0.085, r.t + 0.004, r.z - 0.02)
end

local function syncTickets()
    -- remove objects without a ticket, spawn missing ones (slot = position in the server list)
    for i, tk in pairs(tickets) do                                    -- pairs: the slot table may have holes
        local t = (state.tickets or {})[i]
        if not t or not near or tk.n ~= t.n then
            if DoesEntityExist(tk.obj) then DeleteObject(tk.obj) end
            tickets[i] = nil
        end
    end
    if not near then return end
    for i, t in ipairs(state.tickets or {}) do
        if not tickets[i] then
            local m = GetHashKey(('lp_ticket_%d'):format(t.v or 1))
            if loadModel(m) then
                local p = GS.toWorld(slotPos(i).x, slotPos(i).y, slotPos(i).z)
                local obj = CreateObjectNoOffset(m, p.x, p.y, p.z, false, false, false)
                SetEntityCollision(obj, false, false); FreezeEntityPosition(obj, true)
                SetEntityHeading(obj, GS.heading(0.0, -1.0))           -- text (model -Y) towards the kitchen (+t)
                placeInRoom(obj)
                tickets[i] = { n = t.n, obj = obj }
                SetModelAsNoLongerNeeded(m)
            end
        end
    end
end

-- ------------------------------------------------------------------ FAMILY BUSINESS: hidden credenza leaf
local function secretPose(angle)
    -- closed: model +X along +t (leaf towards -t from the hinge), outer face -Y towards the room (+s); opens by +100 deg
    return localYawHeading(90.0 + angle)
end

local function ensureSecret()
    if not near then
        if secretObj and DoesEntityExist(secretObj) then DeleteObject(secretObj) end
        secretObj = nil
        return
    end
    if secretObj and DoesEntityExist(secretObj) then return end
    local m = `lp_secret_door`
    if not loadModel(m) then return end
    local p = W(D.secret_hinge)
    secretObj = CreateObjectNoOffset(m, p.x, p.y, p.z, false, false, false)
    SetEntityCollision(secretObj, false, false); FreezeEntityPosition(secretObj, true)
    secretAngle = state.secret and 100.0 or 0.0
    SetEntityHeading(secretObj, secretPose(secretAngle))
    placeInRoom(secretObj)
    SetModelAsNoLongerNeeded(m)
end

-- ------------------------------------------------------------------ state
local function onState(v)
    if type(v) ~= 'table' then return end
    local prevAfter = state.afterHours
    state = v
    secretTarget = state.secret and 100.0 or 0.0
    if near then
        if prevAfter ~= state.afterHours then applySets() end
        syncTickets()
    end
end

AddStateBagChangeHandler('lp_rest', 'global', function(_, _, value) onState(value) end)
CreateThread(function()
    Wait(1000)
    onState(GlobalState.lp_rest)
end)

-- 1 s watcher: distance, entity sets (the interior may have streamed out and in), local objects
CreateThread(function()
    while true do
        local d = #(GetEntityCoords(PlayerPedId()) - C.Origin)
        local wasNear = near
        near = d < 60.0
        if near then
            applySets()
            ensureSecret()
            if not wasNear then syncTickets() end
        elseif wasNear then
            applied.id = 0                                          -- re-check once when the player comes back
            ensureSecret(); syncTickets()
            if hoodPlaying then nui('stop', 'lp_hood'); hoodPlaying = false end
        end
        Wait(near and 1000 or 3000)
    end
end)

-- ------------------------------------------------------------------ prompts + E, hood lamps, hood sound, secret animation
local CONTROLS = {
    { key = 'afterhours', p = function() return D.switch_hall end, r = function() return C.Reach end,
      text = function() return state.afterHours and C.Text.afterhours_off or C.Text.afterhours_on end },
    { key = 'afterhours', p = function() return D.switch_office end, r = function() return C.Reach end,
      text = function() return state.afterHours and C.Text.afterhours_off or C.Text.afterhours_on end },
    { key = 'bell', p = function() return D.bell end, r = function() return C.Reach end, text = function() return C.Text.bell end },
    { key = 'print', p = function() return D.printer end, r = function() return C.Reach end, text = function() return C.Text.print end },
    { key = 'hood', p = function() return D.hood_switch end, r = function() return C.Reach end,
      text = function() return state.hood and C.Text.hood_off or C.Text.hood_on end },
    { key = 'orderup', p = function() local r = D.ticket_rail; return vector3((r.s0 + r.s1) / 2, r.t + 0.30, r.z - 0.2) end,
      r = function() return C.Reach + 0.3 end, text = function() return C.Text.orderup end,
      visible = function() return #(state.tickets or {}) > 0 end },
    { key = 'secret', p = function() return D.secret_point end, r = function() return C.SecretReach end,
      text = function() return state.secret and C.Text.secret_close or C.Text.secret end },
}

local function help(txt)
    BeginTextCommandDisplayHelp('STRING'); AddTextComponentSubstringPlayerName(txt); EndTextCommandDisplayHelp(0, false, false, -1)
end

CreateThread(function()
    local lastPress, lastVol = 0, 0
    while true do
        local wait = 500
        if near then
            local ped = PlayerPedId()
            local pos = GetEntityCoords(ped)
            local best, bestD = nil, 1e9
            for _, c in ipairs(CONTROLS) do
                if (not c.visible or c.visible()) and not (C.Prompts and C.Prompts[c.key] == false) then
                    local dd = #(pos - W(c.p()))
                    if dd < c.r() and dd < bestD then best, bestD = c, dd end
                end
            end
            local animating = secretObj and math.abs(secretAngle - secretTarget) > 0.05
            local hoodNear = state.hood and #(pos - W(D.hood_lamps[2])) < 30.0
            if best or animating or hoodNear then wait = 0 end
            if best and not IsPedInAnyVehicle(ped, false) then
                help(best.text())
                if IsControlJustReleased(0, 38) and GetGameTimer() - lastPress > 600 then
                    lastPress = GetGameTimer()
                    TriggerServerEvent('lp_rest:act', best.key)
                end
            end
            if hoodNear then
                local hl = C.HoodLight
                for _, lp in ipairs(D.hood_lamps) do
                    local w = W(lp)
                    DrawLightWithRange(w.x, w.y, w.z - 0.05, hl.color[1], hl.color[2], hl.color[3], hl.range, hl.intensity)
                end
            end
            if animating and secretObj then
                local step = 100.0 * (GetFrameTime() / 1.1)
                if secretAngle < secretTarget then secretAngle = math.min(secretTarget, secretAngle + step)
                else secretAngle = math.max(secretTarget, secretAngle - step) end
                SetEntityHeading(secretObj, secretPose(secretAngle))
            end
            -- hood fan loop, volume by distance (updated every frame while near, else every 0.5 s)
            if GetGameTimer() - lastVol > 250 then
                lastVol = GetGameTimer()
                local hv = state.hood and volAt(D.hood_lamps[2], C.HoodSoundDist) or 0.0
                if hv > 0.01 and not hoodPlaying then nui('play', 'lp_hood', 'sfx/lp_hood.ogg', hv, true); hoodPlaying = true
                elseif hv <= 0.01 and hoodPlaying then nui('stop', 'lp_hood'); hoodPlaying = false
                elseif hoodPlaying then nui('vol', 'lp_hood', nil, hv) end
            end
        end
        Wait(wait)
    end
end)

-- ------------------------------------------------------------------ cleanup
AddEventHandler('onResourceStop', function(res)
    if res ~= GetCurrentResourceName() then return end
    if secretObj and DoesEntityExist(secretObj) then DeleteObject(secretObj) end
    for _, t in pairs(tickets) do if DoesEntityExist(t.obj) then DeleteObject(t.obj) end end
    nui('stop', 'lp_hood')
end)

RegisterCommand('lp_rest_debug', function()
    local id = getInterior()
    print(('[LONG PIG rest] interior=%d ready=%s open=%s closed=%s | afterHours=%s hood=%s secret=%s tickets=%d'):format(
        id, tostring(id ~= 0 and B(IsInteriorReady(id))), tostring(id ~= 0 and B(IsInteriorEntitySetActive(id, D.sets.open))),
        tostring(id ~= 0 and B(IsInteriorEntitySetActive(id, D.sets.closed))), tostring(state.afterHours), tostring(state.hood),
        tostring(state.secret), #(state.tickets or {})))
end, false)
