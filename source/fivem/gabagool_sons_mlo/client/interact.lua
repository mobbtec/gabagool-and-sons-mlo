local _RegCmd = RegisterCommand
local function RegisterCommand(name, fn, restricted)   -- 1.7.0: LPR_CFG.Commands switch
    if LPR_CFG and LPR_CFG.Commands and LPR_CFG.Commands[name] == false then return end
    return _RegCmd(name, fn, restricted)
end
-- LONG PIG 0.3.1-j: sit and work places (revision). Points from client/interact_data.lua.
-- E = sit down / start working, E or any move key again = stand up. Uses vanilla scenarios only. Dining chairs are
-- offered only while the 'lp_open' entity set is active (at night the chairs are up on the tables).
-- No per-frame work unless the player is inside the shop; /lp_sit off | on disables the prompts.
local ENABLED = true
local REACH = 0.85
local active = nil
local lastToggle = 0

local function truthy(v) return v == true or v == 1 end

local function help(txt)
    BeginTextCommandDisplayHelp('STRING'); AddTextComponentSubstringPlayerName(txt); EndTextCommandDisplayHelp(0, false, false, -1)
end

local function shopInterior()
    local p = GS.toWorld(2.0, 3.0, 1.0)
    return GetInteriorAtCoords(p.x, p.y, p.z)
end

local function chairsOut(interior)
    if not IsInteriorEntitySetActive then return true end
    return truthy(IsInteriorEntitySetActive(interior, 'lp_open'))
end

local function stand(ped)
    ClearPedTasks(ped)
    active = nil
end

local function start(ped, p)
    local w = GS.toWorld(p.s, p.t, p.z)
    local h = (GS.YAW + p.h) % 360.0
    if p.kind == 'work' then
        local fw = GS.toWorld(p.s, p.t, 0.0)
        TaskStartScenarioAtPosition(ped, p.sc, fw.x, fw.y, fw.z + 1.0, h, 0, false, true)
    else
        TaskStartScenarioAtPosition(ped, p.sc, w.x, w.y, w.z, h, 0, true, true)
    end
    active = p
end

local MOVE = { 30, 31, 32, 33, 34, 35, 22 }

CreateThread(function()
    while true do
        local wait = 750
        local ped = PlayerPedId()
        local interior = shopInterior()
        if ENABLED and interior ~= 0 and GetInteriorFromEntity(ped) == interior then
            wait = 250
            local pos = GetEntityCoords(ped)
            if active then
                wait = 0
                local stop = IsControlJustReleased(0, 38)
                for _, c in ipairs(MOVE) do if IsControlJustPressed(0, c) then stop = true end end
                if stop and GetGameTimer() - lastToggle > 800 then
                    lastToggle = GetGameTimer()
                    stand(ped)
                elseif not IsPedUsingAnyScenario(ped) and GetGameTimer() - lastToggle > 2500 then
                    active = nil                                  -- scenario ended by itself
                end
            elseif not IsPedInAnyVehicle(ped, false) then
                local best, bestD = nil, REACH
                local open = nil
                for _, p in ipairs(GS_INTERACT or {}) do
                    local w = GS.toWorld(p.s, p.t, 0.0)
                    local dd = #(vector2(pos.x, pos.y) - vector2(w.x, w.y))
                    local PR = LPR_CFG and LPR_CFG.Prompts or {}
                    local off = (p.kind == 'work' and PR.work == false) or (p.kind ~= 'work' and PR.sit == false)
                    if dd < bestD and not off then
                        if p.kind == 'chair' and p.t < 8.4 then
                            if open == nil then open = chairsOut(interior) end
                            if open then best, bestD = p, dd end
                        else
                            best, bestD = p, dd
                        end
                    end
                end
                if best then
                    wait = 0
                    help('~INPUT_CONTEXT~ ' .. best.label)
                    if IsControlJustReleased(0, 38) and GetGameTimer() - lastToggle > 800 then
                        lastToggle = GetGameTimer()
                        start(ped, best)
                    end
                end
            end
        elseif active then
            active = nil
        end
        Wait(wait)
    end
end)

RegisterCommand('lp_sit', function(_, args)
    ENABLED = (args[1] ~= 'off')
    print('[LONG PIG] sit / work prompts ' .. (ENABLED and 'on' or 'off') .. ', points: ' .. #(GS_INTERACT or {}))
end, false)
