local _RegCmd = RegisterCommand
local function RegisterCommand(name, fn, restricted)   -- 1.7.0: LPR_CFG.Commands switch
    if LPR_CFG and LPR_CFG.Commands and LPR_CFG.Commands[name] == false then return end
    return _RegCmd(name, fn, restricted)
end
-- LONG PIG 2.9.0: roller blinds of the hall. The server owns the state: GlobalState.lp_rollers = { f1 .. f5 } with
-- f = 0 fully up .. 1 fully down, kept in the resource KVP so it survives restarts; clients move the fabric.
-- No permissions (owner 2026-11-12), but every change is clamped, distance-checked and rate-limited.
local KEY = 'lp_rollers_state'
local N = 5
local MIX = { 0.55, 0.20, 1.00, 0.35, 0.75 }           -- same defaults as client/blinds_data.lua
local ORIGIN = vector3(411.655, -1912.045, 24.45)     -- MLO instance position (client/config.lua GS.ORIGIN); distance check only

local function clamp(v) if v < 0.0 then return 0.0 elseif v > 1.0 then return 1.0 end return v end

local state = {}
do
    local ok, t = pcall(function() return json.decode(GetResourceKvpString(KEY) or '') end)
    for i = 1, N do
        local v = ok and type(t) == 'table' and tonumber(t[i]) or nil
        state[i] = v and clamp(v + 0.0) or MIX[i]
    end
    GlobalState.lp_rollers = state
end

local function publish()
    local copy = {}
    for i = 1, N do copy[i] = state[i] end
    GlobalState.lp_rollers = copy
    SetResourceKvp(KEY, json.encode(copy))
end

local function setAll(v)
    for i = 1, N do state[i] = type(v) == 'table' and v[i] or v end
    publish()
end

-- arrow keys in the adjust mode (/pig_blind on the client)
local lastBy = {}
RegisterNetEvent('lp_rollers:set', function(i, f)
    local src = source
    i, f = tonumber(i), tonumber(f)
    if not i or not f or i < 1 or i > N or i ~= math.floor(i) then return end
    local now = GetGameTimer()
    if lastBy[src] and now - lastBy[src] < 150 then return end
    lastBy[src] = now
    local ped = GetPlayerPed(src)
    if ped and ped ~= 0 then
        local p = GetEntityCoords(ped)
        if #(p - ORIGIN) > 40.0 then return end
    end
    state[i] = clamp(f + 0.0)
    publish()
end)

AddEventHandler('playerDropped', function() lastBy[source] = nil end)

-- /pig_blinds                 toggle: all up <-> all down
-- /pig_blinds open | close    all up / all down
-- /pig_blinds mix             the default mixed heights
-- /pig_blinds 0..100          all blinds to that percentage (100 = fully down)
local last = 0
RegisterCommand('pig_blinds', function(src, args)
    local now = GetGameTimer()
    if now - last < 1500 then return end
    last = now
    local a = args[1]
    local n = tonumber(a)
    if n then setAll(clamp(n / 100.0))
    elseif a == 'open' or a == 'up' or a == 'spread' or a == 'draw' then setAll(0.0)
    elseif a == 'close' or a == 'closed' or a == 'down' then setAll(1.0)
    elseif a == 'mix' then setAll(MIX)
    else
        local sum = 0.0
        for i = 1, N do sum = sum + state[i] end
        setAll(sum / N > 0.5 and 0.0 or 1.0)
    end
    if src == 0 then print('[LONG PIG] blinds: ' .. json.encode(state)) end
end, false)

-- the blinds follow the roller shutters: /close_pig -> all down, /open_pig -> back to the mixed heights.
CreateThread(function()
    local lastTarget = nil
    while true do
        local sh = GlobalState.lp_shutters
        local tg = type(sh) == 'table' and tonumber(sh.target) or nil
        if tg ~= nil then
            if lastTarget ~= nil and tg ~= lastTarget then
                if tg >= 0.999 then setAll(1.0) elseif tg <= 0.001 then setAll(MIX) end
            end
            lastTarget = tg
        end
        Wait(2000)
    end
end)
