local _RegCmd = RegisterCommand
local function RegisterCommand(name, fn, restricted)   -- 1.7.0: LPR_CFG.Commands switch
    if LPR_CFG and LPR_CFG.Commands and LPR_CFG.Commands[name] == false then return end
    return _RegCmd(name, fn, restricted)
end
-- LONG PIG — security roller shutters, CLIENT.
-- Own models (stream/shutters, lp_shutters.ytyp): 2 guide rails per opening (static), a bottom bar and N curtain panels
-- (4 slats each) per opening. LOCAL objects only (nothing networked). The curtain rolls out of the facade's own shutter
-- boxes: every panel moves with the bar, a panel is drawn only while it is below the box bottom (above it, it is inside
-- the box). The server sends one motion per command; this client animates it every frame with the same easing.
-- Collision: OFF while anything moves (nobody gets crushed or pushed), ON when the curtain stands still and is not open;
-- if the local player stands in the curtain line at that moment, collision waits until he has stepped away.
if not LPS_CFG or not LPS_CFG.Enabled then return end

local D, C = LPS_DATA, LPS_CFG
local E = nil                 -- spawned entities: { rails = {...}, [i] = { bar = ent, pnl = { ent, ... } } }
local motion = { from = 0.0, to = 0.0, t0 = 0, dur = 0, seq = -1, known = false }
local current = 0.0
local animating = false
local colOn = {}              -- per opening index: collision currently enabled
local debugOn = false
local missing = {}

local function ease(x)
    x = math.min(1.0, math.max(0.0, x))
    return x * x * x * (x * (6.0 * x - 15.0) + 10.0)
end

local function motionProgress()
    if motion.dur <= 0 then return motion.to, true end
    local x = (GetGameTimer() - motion.t0) / motion.dur
    if x >= 1.0 then return motion.to, true end
    return motion.from + (motion.to - motion.from) * ease(x), false
end

-- ------------------------------------------------------------------------ geometry helpers (MLO-local -> world)
local function curtainPoint(o)
    return o.c.x + o.N.x * D.CURTAIN_D, o.c.y + o.N.y * D.CURTAIN_D
end

local function inwardHeading(o)
    return GS.heading(-o.N.x, -o.N.y)              -- model +Y points into the building, model front (-Y) to the street
end

local function barZ(o, p)
    return D.Z_OPEN + (o.z_closed - D.Z_OPEN) * p
end

-- ------------------------------------------------------------------------ sound (NUI, distance-scaled volume)
local function nearestOpeningDist()
    local ped = GetEntityCoords(PlayerPedId())
    local best = 1e9
    for _, o in ipairs(D.OPENINGS) do
        local w = GS.toWorld(o.c.x, o.c.y, 1.3)
        best = math.min(best, #(ped - w))
    end
    return best
end

local function volume()
    local d = nearestOpeningDist()
    local v = 1.0 - d / C.SoundDist
    if v <= 0.0 then return 0.0 end
    return C.SoundVolume * v ^ 1.5
end

local function sound(kind, id, file, vol)
    SendNUIMessage({ type = kind, id = id, src = file, volume = vol or 0.0 })
end

-- ------------------------------------------------------------------------ entities
local function loadModel(m)
    if not IsModelInCdimage(m) then
        if not missing[m] then print(('[LONG PIG shutters] model %s not found (stream/shutters missing?)'):format(m)) end
        missing[m] = true
        return false
    end
    RequestModel(m)
    local t = GetGameTimer()
    while not HasModelLoaded(m) and GetGameTimer() - t < 8000 do Wait(0) end
    return HasModelLoaded(m)
end

local function make(m, x, y, z, h)
    local w = GS.toWorld(x, y, z)
    local e = CreateObjectNoOffset(m, w.x, w.y, w.z, false, false, false)
    SetEntityHeading(e, h)
    FreezeEntityPosition(e, true)
    SetEntityAsMissionEntity(e, true, true)
    SetEntityCollision(e, false, false)
    return e
end

local function setCollision(i, on)
    local s = E and E[i]
    if not s then return end
    SetEntityCollision(s.bar, on, on)
    for _, e in ipairs(s.pnl) do
        SetEntityCollision(e, on and IsEntityVisible(e), on and IsEntityVisible(e))
    end
    colOn[i] = on
end

local function apply(p)
    current = p
    if not E then return end
    for i, o in ipairs(D.OPENINGS) do
        local s = E[i]
        local cx, cy = curtainPoint(o)
        local zb = barZ(o, p)
        local w = GS.toWorld(cx, cy, zb)
        SetEntityCoordsNoOffset(s.bar, w.x, w.y, w.z, false, false, false)
        for k, e in ipairs(s.pnl) do
            local z = zb + D.BAR_H + (k - 1) * D.PANEL_H
            local vis = z < D.BOX_BOTTOM - 0.002
            if vis then
                local wp = GS.toWorld(cx, cy, z)
                SetEntityCoordsNoOffset(e, wp.x, wp.y, wp.z, false, false, false)
            else
                local wp = GS.toWorld(cx, cy, D.BOX_BOTTOM + 0.01)       -- parked inside the box, not drawn
                SetEntityCoordsNoOffset(e, wp.x, wp.y, wp.z, false, false, false)
            end
            local isVis = IsEntityVisible(e); isVis = isVis == true or isVis == 1      -- BOOL natives return 1 / false
            if isVis ~= vis then SetEntityVisible(e, vis, false) end
        end
    end
end

local function despawn()
    if not E then return end
    for _, e in ipairs(E.rails) do if DoesEntityExist(e) then DeleteObject(e) end end
    for i = 1, #D.OPENINGS do
        local s = E[i]
        if s then
            if DoesEntityExist(s.bar) then DeleteObject(s.bar) end
            for _, e in ipairs(s.pnl) do if DoesEntityExist(e) then DeleteObject(e) end end
        end
    end
    E, colOn = nil, {}
end

local function spawn()
    local models = {}
    for _, o in ipairs(D.OPENINGS) do models[o.rail] = true; models[o.bar] = true; models[o.pnl] = true end
    for m in pairs(models) do if not loadModel(m) then return false end end
    E = { rails = {} }
    for i, o in ipairs(D.OPENINGS) do
        local h = inwardHeading(o)
        for _, sg in ipairs({ -1.0, 1.0 }) do
            local u = sg * (o.hw + D.RAIL_W / 2)
            E.rails[#E.rails + 1] = make(o.rail, o.c.x + o.R.x * u, o.c.y + o.R.y * u, o.rail_bottom, h)
        end
        local cx, cy = curtainPoint(o)
        local s = { bar = make(o.bar, cx, cy, D.Z_OPEN, h), pnl = {} }
        for k = 1, o.n_panels do s.pnl[k] = make(o.pnl, cx, cy, D.BOX_BOTTOM + 0.01, h) end
        E[i] = s
        colOn[i] = false
    end
    for m in pairs(models) do SetModelAsNoLongerNeeded(m) end
    local p = motionProgress()
    apply(p)
    return true
end

-- ------------------------------------------------------------------------ collision only when standing still + safe
local function pedInCurtainLine(o)
    local ped = PlayerPedId()
    local pw = GetEntityCoords(ped)
    local r = math.rad(GS.YAW)
    local cs, sn = math.cos(r), math.sin(r)
    local dx, dy = pw.x - GS.ORIGIN.x, pw.y - GS.ORIGIN.y
    local ls, lt = dx * cs + dy * sn, -dx * sn + dy * cs            -- world -> MLO-local
    local rx, ry = ls - o.c.x, lt - o.c.y
    local u = rx * o.R.x + ry * o.R.y
    local d = rx * o.N.x + ry * o.N.y
    local z = pw.z - GS.ORIGIN.z
    return math.abs(u) < o.hw + 0.25 and math.abs(d - D.CURTAIN_D) < C.SafeZone and z > o.z_closed - 1.2 and z < D.BOX_BOTTOM + 1.0
end

local function settleCollision()
    if not E then return end
    local want = current > 0.02
    for i, o in ipairs(D.OPENINGS) do
        if not want then
            if colOn[i] then setCollision(i, false) end
        elseif not colOn[i] and not pedInCurtainLine(o) then
            setCollision(i, true)
        end
    end
end

-- ------------------------------------------------------------------------ animation
local function runAnimation()
    if animating then return end
    animating = true
    CreateThread(function()
        for i = 1, #D.OPENINGS do setCollision(i, false) end
        local v = volume()
        if v > 0.01 then sound('play', 'run', 'sfx/lp_shutter_run.ogg', v) end
        local nextVol = GetGameTimer() + 150
        local seq = motion.seq
        while true do
            local p, done = motionProgress()
            apply(p)
            if GetGameTimer() > nextVol then
                sound('vol', 'run', nil, volume())
                nextVol = GetGameTimer() + 150
            end
            if done or seq ~= motion.seq then
                if done then
                    sound('stop', 'run', nil, 0)
                    local vs = volume()
                    if vs > 0.01 then sound('play', 'stop', 'sfx/lp_shutter_stop.ogg', vs) end
                end
                if seq == motion.seq then break end
                seq = motion.seq                                -- retargeted mid-way: keep going without a stop clunk
                sound('vol', 'run', nil, volume())
            end
            Wait(0)
        end
        animating = false
        settleCollision()
    end)
end

RegisterNetEvent('lp_shutters:motion', function(m)
    if type(m) ~= 'table' then return end
    motion.from, motion.to, motion.dur, motion.seq = m.from + 0.0, m.to + 0.0, m.dur, m.seq
    motion.t0 = GetGameTimer() - (m.elapsed or 0)
    motion.known = true
    local p, done = motionProgress()
    if E then
        if done then
            if animating then return end                       -- the running loop finishes on its own
            apply(p)
            settleCollision()
        else
            runAnimation()
        end
    else
        current = p
    end
end)

RegisterNetEvent('lp_shutters:notify', function(msg)
    if GetResourceState('chat') == 'started' then
        TriggerEvent('chat:addMessage', { color = { 200, 60, 50 }, args = { 'LONG PIG', msg } })
    end
    print('[LONG PIG shutters] ' .. msg)
end)

-- spawn / despawn by distance, collision safety loop, first sync
CreateThread(function()
    while not NetworkIsSessionStarted() do Wait(500) end
    TriggerServerEvent('lp_shutters:sync')
    while true do
        local d = #(GetEntityCoords(PlayerPedId()) - GS.ORIGIN)
        if d < C.SpawnDist and not E then
            if spawn() then
                local p, done = motionProgress()
                if not done then runAnimation() else settleCollision() end
            end
        elseif d > C.SpawnDist + 25.0 and E then
            despawn()
        end
        if E and not animating then settleCollision() end
        Wait(E and 250 or 1500)
    end
end)

-- ------------------------------------------------------------------------ /pig_debug (local, read-only)
local function txt(x, y, s)
    SetTextFont(0); SetTextScale(0.30, 0.30); SetTextColour(255, 255, 255, 230); SetTextOutline()
    BeginTextCommandDisplayText('STRING'); AddTextComponentSubstringPlayerName(s); EndTextCommandDisplayText(x, y)
end

RegisterCommand('pig_debug', function()
    debugOn = not debugOn
    print(('[LONG PIG shutters] debug %s | spawned=%s position=%.3f motion seq=%s from=%.2f to=%.2f dur=%s animating=%s')
        :format(debugOn and 'on' or 'off', tostring(E ~= nil), current, tostring(motion.seq), motion.from, motion.to,
            tostring(motion.dur), tostring(animating)))
    if not debugOn then return end
    CreateThread(function()
        while debugOn do
            local y = 0.30
            txt(0.015, y, ('~y~LONG PIG shutters~s~  pos %.3f  target %.2f  %s'):format(current, motion.to,
                animating and 'moving' or 'still')); y = y + 0.022
            txt(0.015, y, ('objects %s | volume %.2f | dist %.1f m'):format(E and 'spawned' or 'none', volume(),
                nearestOpeningDist())); y = y + 0.022
            for i, o in ipairs(D.OPENINGS) do
                local vis = 0
                if E then for _, e in ipairs(E[i].pnl) do if IsEntityVisible(e) then vis = vis + 1 end end end
                txt(0.015, y, ('%s  bar z %.2f  panels %d/%d  collision %s  player-in-line %s'):format(o.id, barZ(o, current), vis,
                    o.n_panels, tostring(colOn[i]), tostring(pedInCurtainLine(o)))); y = y + 0.022
                local cx, cy = curtainPoint(o)
                local a = GS.toWorld(cx - o.R.x * o.hw, cy - o.R.y * o.hw, barZ(o, current))
                local b = GS.toWorld(cx + o.R.x * o.hw, cy + o.R.y * o.hw, barZ(o, current))
                DrawLine(a.x, a.y, a.z, b.x, b.y, b.z, 255, 60, 60, 255)
                local a2 = GS.toWorld(cx - o.R.x * o.hw, cy - o.R.y * o.hw, D.BOX_BOTTOM)
                local b2 = GS.toWorld(cx + o.R.x * o.hw, cy + o.R.y * o.hw, D.BOX_BOTTOM)
                DrawLine(a2.x, a2.y, a2.z, b2.x, b2.y, b2.z, 60, 200, 255, 255)
            end
            Wait(0)
        end
    end)
end, false)

AddEventHandler('onResourceStop', function(res)
    if res ~= GetCurrentResourceName() then return end
    debugOn = false
    sound('stop', 'run', nil, 0)
    despawn()
end)
