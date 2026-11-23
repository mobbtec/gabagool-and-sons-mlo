local _RegCmd = RegisterCommand
local function RegisterCommand(name, fn, restricted)   -- 1.7.0: LPR_CFG.Commands switch
    if LPR_CFG and LPR_CFG.Commands and LPR_CFG.Commands[name] == false then return end
    return _RegCmd(name, fn, restricted)
end
-- LONG PIG — security roller shutters, SERVER (authoritative state).
-- The server owns one motion: { from, to, dur, t0 } in server ms. Clients receive the motion ONCE per command (plus a
-- one-off sync on join) and animate locally with the same easing, so nothing is sent per frame and every client shows the
-- same curtain position. A command during a motion reverses / retargets it from the current position (no jump).
-- State survives resource restarts (resource KVP) and is mirrored in GlobalState.lp_shutters for other resources.
if not LPS_CFG or not LPS_CFG.Enabled then return end

local KVP = 'lp_shutters_target'
local M = { from = 0.0, to = 0.0, t0 = 0, dur = 0, seq = 0, by = 'start', at = os.time() }
local lastCmd = -1000000

local function ease(x)
    x = math.min(1.0, math.max(0.0, x))
    return x * x * x * (x * (6.0 * x - 15.0) + 10.0)
end

local function now() return GetGameTimer() end

local function progress()
    if M.dur <= 0 then return M.to end
    local x = (now() - M.t0) / M.dur
    if x >= 1.0 then return M.to end
    return M.from + (M.to - M.from) * ease(x)
end

local function moving() return M.dur > 0 and (now() - M.t0) < M.dur end

local function stateName()
    if moving() then return (M.to > M.from) and 'closing' or 'opening' end
    local p = progress()
    if p <= 0.001 then return 'open' elseif p >= 0.999 then return 'closed' end
    return ('partly closed (%d%%)'):format(math.floor(p * 100 + 0.5))
end

local function packet(elapsed)
    return { from = M.from, to = M.to, dur = M.dur, elapsed = elapsed or 0, seq = M.seq }
end

local function publish()
    GlobalState.lp_shutters = { target = M.to, state = stateName(), seq = M.seq, by = M.by, at = M.at }
end

local function persist()
    if LPS_CFG.Persist then SetResourceKvpFloat(KVP, M.to) end
end

local function startMotion(target, who)
    local p = progress()
    target = math.min(1.0, math.max(0.0, target))
    if math.abs(target - p) < 0.002 and not moving() then return false, 'already ' .. stateName() end
    if moving() and math.abs(target - M.to) < 0.002 then return false, 'already ' .. stateName() end
    M.seq = M.seq + 1
    M.from, M.to = p, target
    M.dur = math.floor(LPS_CFG.Duration * math.max(0.15, math.abs(target - p)) + 0.5)
    M.t0 = now()
    M.by, M.at = who, os.time()
    publish()
    TriggerClientEvent('lp_shutters:motion', -1, packet(0))
    local seq = M.seq
    SetTimeout(M.dur + 60, function()
        if seq ~= M.seq then return end                       -- superseded by a newer command
        M.from, M.dur = M.to, 0
        persist()
        publish()
    end)
    return true, (target > p) and 'closing' or 'opening'
end

-- ------------------------------------------------------------------------ permissions (ACE first, adapters optional)
local function jobAllowed(src)
    if #LPS_CFG.QBCoreJobs > 0 and GetResourceState('qb-core') == 'started' then
        local ok, QB = pcall(function() return exports['qb-core']:GetCoreObject() end)
        if ok and QB then
            local P = QB.Functions.GetPlayer(src)
            local job = P and P.PlayerData and P.PlayerData.job and P.PlayerData.job.name
            for _, j in ipairs(LPS_CFG.QBCoreJobs) do if job == j then return true end end
        end
    end
    if #LPS_CFG.ESXJobs > 0 and GetResourceState('es_extended') == 'started' then
        local ok, ESX = pcall(function() return exports['es_extended']:getSharedObject() end)
        if ok and ESX then
            local x = ESX.GetPlayerFromId(src)
            local job = x and x.job and x.job.name
            for _, j in ipairs(LPS_CFG.ESXJobs) do if job == j then return true end end
        end
    end
    return false
end

local function near(src)
    if (LPS_CFG.MaxCommandDist or 0) <= 0 then return true end
    local ped = GetPlayerPed(src)
    if not ped or ped == 0 then return true end               -- no OneSync position: do not block on distance
    local c = GetEntityCoords(ped)
    if c.x == 0.0 and c.y == 0.0 then return true end
    return #(c - LPS_CFG.Origin) <= LPS_CFG.MaxCommandDist
end

local function allowed(src)
    if src == 0 then return true end
    local perm = (not LPS_CFG.RequireAce) or IsPlayerAceAllowed(src, LPS_CFG.Ace) or jobAllowed(src)
    if not perm then return false, 'no permission (' .. LPS_CFG.Ace .. ')' end
    if not near(src) then return false, ('too far from the shop (max %d m)'):format(math.floor(LPS_CFG.MaxCommandDist)) end
    return true
end

local function reply(src, msg)
    if src == 0 then print('[LONG PIG shutters] ' .. msg) return end
    TriggerClientEvent('lp_shutters:notify', src, msg)
end

local function who(src)
    if src == 0 then return 'console' end
    return ('%s (#%d)'):format(GetPlayerName(src) or '?', src)
end

local function command(src, target)
    local ok, why = allowed(src)
    if not ok then reply(src, why) return end
    if now() - lastCmd < LPS_CFG.Cooldown then reply(src, 'wait a moment') return end
    lastCmd = now()
    local started, msg = startMotion(target, who(src))
    reply(src, started and ('shutters ' .. msg) or msg)
    if started then print(('[LONG PIG shutters] %s by %s'):format(msg, who(src))) end
end

RegisterCommand('close_pig', function(src, args)
    local pct = tonumber(args[1] or '')                       -- optional: /close_pig 50  (test position)
    command(src, pct and math.min(100, math.max(0, pct)) / 100.0 or 1.0)
end, false)

RegisterCommand('open_pig', function(src)
    command(src, 0.0)
end, false)

RegisterCommand('pig_status', function(src)
    local p = progress()
    local msg = ('state: %s | position %d%% closed | target %d%% | last: %s at %s | saved: %s'):format(
        stateName(), math.floor(p * 100 + 0.5), math.floor(M.to * 100 + 0.5), M.by, os.date('%H:%M:%S', M.at),
        LPS_CFG.Persist and tostring(GetResourceKvpFloat(KVP)) or 'off')
    reply(src, msg)
end, false)

-- late joiners / clients that (re)started: send the current motion with the time already elapsed
RegisterNetEvent('lp_shutters:sync', function()
    local src = source
    local el = M.dur > 0 and math.min(M.dur, now() - M.t0) or 0
    TriggerClientEvent('lp_shutters:motion', src, packet(el))
end)

-- ------------------------------------------------------------------------ start: restore the saved state
CreateThread(function()
    local saved = LPS_CFG.Persist and GetResourceKvpFloat(KVP) or nil
    local hasSaved = saved ~= nil and GetResourceKvpString(KVP .. '_set') == '1'
    local start = hasSaved and saved or ((LPS_CFG.StartState == 'closed') and 1.0 or 0.0)
    M.from, M.to, M.dur, M.seq = start, start, 0, 1
    if LPS_CFG.Persist then SetResourceKvp(KVP .. '_set', '1'); SetResourceKvpFloat(KVP, start) end
    publish()
    print(('[LONG PIG shutters] ready, %s (saved state: %s)'):format(stateName(), hasSaved and 'yes' or 'no'))
    TriggerClientEvent('lp_shutters:motion', -1, packet(0))   -- clients already in game after a resource restart
end)
