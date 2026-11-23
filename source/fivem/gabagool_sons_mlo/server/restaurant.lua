local _RegCmd = RegisterCommand
local function RegisterCommand(name, fn, restricted)   -- 1.7.0: LPR_CFG.Commands switch
    if LPR_CFG and LPR_CFG.Commands and LPR_CFG.Commands[name] == false then return end
    return _RegCmd(name, fn, restricted)
end
-- LONG PIG v0.2.9 — WORKING RESTAURANT / AFTER HOURS / FAMILY BUSINESS, SERVER.
-- One authoritative state, published as GlobalState.lp_rest (clients react to changes; nothing is sent per frame):
--   afterHours (bool)  -> clients switch the MLO entity sets lp_open / lp_closed
--   hood (bool)        -> clients draw the hood lamps + play the fan loop near the kitchen
--   secret (bool)      -> clients animate the hidden credenza leaf (their own local object)
--   tickets {...}      -> order tickets hanging on the kitchen rail (max LPR_CFG.MaxTickets)
-- One-shot sounds (bell, printer, switch, creak, order up) are broadcast once with their MLO-local position.
if not LPR_CFG or not LPR_CFG.Enabled then return end
local C, D = LPR_CFG, LPR_DATA

local S = { afterHours = false, hood = false, secret = false, tickets = {}, seq = 0, ticketNo = 117 }
local lastAct, lastAfterHours = {}, -1000000

local function publish()
    S.seq = S.seq + 1
    GlobalState.lp_rest = { afterHours = S.afterHours, hood = S.hood, secret = S.secret, tickets = S.tickets, seq = S.seq }
end

local function persist()
    if not C.Persist then return end
    SetResourceKvpInt('lp_rest_afterhours', S.afterHours and 1 or 0)
    SetResourceKvpInt('lp_rest_hood', S.hood and 1 or 0)
    SetResourceKvpInt('lp_rest_secret', S.secret and 1 or 0)
    SetResourceKvpInt('lp_rest_set', 1)
end

local function restore()
    if C.Persist and GetResourceKvpInt('lp_rest_set') == 1 then
        S.afterHours = GetResourceKvpInt('lp_rest_afterhours') == 1
        S.hood = GetResourceKvpInt('lp_rest_hood') == 1
        S.secret = GetResourceKvpInt('lp_rest_secret') == 1
    end
end

-- ------------------------------------------------------------------ permissions (ACE + optional QBCore / ESX jobs)
local function jobOf(src)
    if GetResourceState('qb-core') == 'started' then
        local ok, core = pcall(function() return exports['qb-core']:GetCoreObject() end)
        if ok and core then
            local p = core.Functions.GetPlayer(src)
            return p and p.PlayerData and p.PlayerData.job and p.PlayerData.job.name, 'qb'
        end
    end
    if GetResourceState('es_extended') == 'started' then
        local ok, esx = pcall(function() return exports['es_extended']:getSharedObject() end)
        if ok and esx then
            local p = esx.GetPlayerFromId(src)
            return p and p.job and p.job.name, 'esx'
        end
    end
    return nil
end

local function inList(name, list)
    if not name then return false end
    for _, v in ipairs(list or {}) do if v == name then return true end end
    return false
end

local function hasPerm(src, ace, qbJobs, esxJobs)
    if src == 0 then return true end
    if IsPlayerAceAllowed(src, ace) then return true end
    local job, fw = jobOf(src)
    if fw == 'qb' then return inList(job, qbJobs) end
    if fw == 'esx' then return inList(job, esxJobs) end
    return false
end

local function isStaff(src)
    if not C.RequireStaff then return true end
    return hasPerm(src, C.StaffAce, C.QBCoreJobs, C.ESXJobs)
end

local function near(src, p, reach)
    if src == 0 then return true end
    local ped = GetPlayerPed(src)
    if not ped or ped == 0 then return false end
    return #(GetEntityCoords(ped) - LPR_toWorld(p.x, p.y, p.z)) <= reach + 0.6     -- server position lags a little
end

local function sound(name, p)
    TriggerClientEvent('lp_rest:sound', -1, name, { x = p.x, y = p.y, z = p.z })
end

-- ------------------------------------------------------------------ actions
local ACTIONS = {}

-- 1.4.0: closing the hall also lowers the roller shutters (the blinds follow them, server/blinds.lua); opening raises them
local function followShop()
    SetTimeout(200, function() ExecuteCommand(S.afterHours and 'close_pig' or 'open_pig') end)
end

ACTIONS.afterhours = function(src)
    if not (near(src, D.switch_hall, C.Reach) or near(src, D.switch_office, C.Reach)) then return end
    if not isStaff(src) then return 'no_perm' end
    if GetGameTimer() - lastAfterHours < C.AfterHoursCooldown then return 'wait' end
    lastAfterHours = GetGameTimer()
    S.afterHours = not S.afterHours
    followShop()
    local p = near(src, D.switch_hall, C.Reach) and D.switch_hall or D.switch_office
    sound('switch', p)
    persist(); publish()
end

ACTIONS.hood = function(src)
    if not near(src, D.hood_switch, C.Reach) then return end
    if not isStaff(src) then return 'no_perm' end
    S.hood = not S.hood
    sound('switch', D.hood_switch)
    persist(); publish()
end

ACTIONS.bell = function(src)
    if not near(src, D.bell, C.Reach) then return end
    sound('bell', D.bell)
end

ACTIONS.print = function(src)
    if not near(src, D.printer, C.Reach) then return end
    if not isStaff(src) then return 'no_perm' end
    sound('printer', D.printer)
    S.ticketNo = S.ticketNo + 1
    table.insert(S.tickets, { n = S.ticketNo, v = (S.ticketNo % 3) + 1, at = os.time() })
    while #S.tickets > C.MaxTickets do table.remove(S.tickets, 1) end
    publish()
end

ACTIONS.orderup = function(src)
    local r = D.ticket_rail
    local mid = vector3((r.s0 + r.s1) / 2, r.t + 0.30, r.z - 0.2)
    if not near(src, mid, C.Reach + 0.3) then return end
    if not isStaff(src) then return 'no_perm' end
    if #S.tickets == 0 then return 'empty' end
    table.remove(S.tickets, 1)
    sound('bell', D.pickup_bell)
    publish()
end

ACTIONS.secret = function(src)
    if not near(src, D.secret_point, C.SecretReach) then return end
    if C.SecretRequirePerm and not hasPerm(src, C.SecretAce, C.SecretQBCoreJobs, C.SecretESXJobs) then return 'locked' end
    S.secret = not S.secret
    sound('creak', D.secret_point)
    persist(); publish()
end

RegisterNetEvent('lp_rest:act', function(action)
    local src = source
    if type(action) ~= 'string' or not ACTIONS[action] then return end
    local now = GetGameTimer()
    if lastAct[src] and now - lastAct[src] < C.Cooldown then return end
    lastAct[src] = now
    local res = ACTIONS[action](src)
    if res then TriggerClientEvent('lp_rest:notify', src, res) end
end)

AddEventHandler('playerDropped', function() lastAct[source] = nil end)

-- old tickets drop off the rail by themselves
CreateThread(function()
    while true do
        Wait(60000)
        local now, changed = os.time(), false
        for i = #S.tickets, 1, -1 do
            if now - S.tickets[i].at > C.TicketLifetime then table.remove(S.tickets, i); changed = true end
        end
        if changed then publish() end
    end
end)

RegisterCommand('lp_rest_status', function(src)
    local msg = ('[LONG PIG] afterHours=%s hood=%s secret=%s tickets=%d seq=%d'):format(tostring(S.afterHours), tostring(S.hood),
        tostring(S.secret), #S.tickets, S.seq)
    if src == 0 then print(msg) else TriggerClientEvent('chat:addMessage', src, { args = { 'LONG PIG', msg } }) end
end, false)

-- console / txAdmin: lp_afterhours [on|off]
RegisterCommand('lp_afterhours', function(src, args)
    if src ~= 0 and not IsPlayerAceAllowed(src, C.StaffAce) then return end
    local a = args[1]
    if a == 'on' then S.afterHours = true elseif a == 'off' then S.afterHours = false else S.afterHours = not S.afterHours end
    followShop()
    persist(); publish()
    print('[LONG PIG] after hours = ' .. tostring(S.afterHours))
end, false)

restore()
publish()
