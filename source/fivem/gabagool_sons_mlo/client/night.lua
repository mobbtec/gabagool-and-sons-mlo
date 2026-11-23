-- A full night look uses the secondary slot so it can coexist with a primary effect.
-- GTA exposes weighted strength on the primary slot. The old extra-strength alias
-- actually selects the moon phase in the installed FiveM native bindings.
local MOD = 'lp_longpig_night'
local enabled, strength = true, 1.0
local hall = GS.toWorld(4.0, 3.0, 1.2)
local primary = {
    get = GetTimecycleModifierIndex, set = SetTimecycleModifier, clear = ClearTimecycleModifier
}
local secondary = {
    get = GetExtraTimecycleModifierIndex, set = SetExtraTimecycleModifier, clear = ClearExtraTimecycleModifier
}
local owned, appliedIndex, appliedStrength
local edits = {}

local function inside()
    local id = GetInteriorFromEntity(PlayerPedId())
    return id ~= 0 and id == GetInteriorAtCoords(hall.x, hall.y, hall.z)
end

local function release()
    if owned and owned.get() == appliedIndex then owned.clear() end
    owned, appliedIndex, appliedStrength = nil, nil, nil
end

local function update()
    local h = GetClockHours()
    local state = GlobalState.lp_rest
    local closed = type(state) == 'table' and state.afterHours == true
    local use = enabled and strength > 0 and (closed or h >= 20 or h < 7) and inside()
    if not use then
        if owned then release() end
        return
    end

    local target = primary
    if strength == 1.0 and secondary.get and secondary.set and secondary.clear then
        local index = secondary.get()
        if index == -1 or (owned == secondary and index == appliedIndex) then target = secondary end
    end
    if owned and (target ~= owned or owned.get() ~= appliedIndex) then release() end
    if not owned then
        if target.get() ~= -1 then return end
        local id = GetTimecycleModifierIndexByName(MOD)
        if id < 0 then return end
        target.set(MOD)
        if target.get() ~= id then return end
        owned, appliedIndex = target, id
    end
    if owned == primary and strength ~= appliedStrength then
        SetTimecycleModifierStrength(strength)
    end
    appliedStrength = strength
end

CreateThread(function()
    while true do
        update()
        Wait(1000)
    end
end)

local function command(name, callback)
    if LPR_CFG and LPR_CFG.Commands and LPR_CFG.Commands[name] == false then return end
    RegisterCommand(name, callback, false)
end

command('lp_night', function(_, args)
    local a = args[1]
    if a == 'off' then
        enabled = false
    elseif a == 'on' then
        enabled = true
    elseif tonumber(a) then
        strength = math.max(0.0, math.min(1.0, tonumber(a)))
        enabled = true
    end
    update()
    local mode = not owned and 'none' or owned == primary and 'main' or 'extra'
    print(('[LONG PIG] night enabled=%s strength=%.2f hour=%d inside=%s mode=%s'):format(
        tostring(enabled), strength, GetClockHours(), tostring(inside()), mode))
end)

command('lp_nightvar', function(_, args)
    local name, value = args[1], tonumber(args[2] or '')
    if not name or not value then
        print('[LONG PIG] /lp_nightvar <var> <value>')
        return
    end
    local present, v1, v2 = GetTimecycleModifierVar(MOD, name)
    if edits[name] == nil then edits[name] = present and { v1, v2 } or false end
    SetTimecycleModifierVar(MOD, name, value, present and v2 or 0.0)
    if DoesTimecycleModifierHasVar(MOD, name) then
        print(('[LONG PIG] %s.%s = %.3f (until restart)'):format(MOD, name, value))
    else
        print('[LONG PIG] unknown timecycle variable: ' .. name)
    end
end)

AddEventHandler('onResourceStop', function(res)
    if res ~= GetCurrentResourceName() then return end
    release()
    for name, original in pairs(edits) do
        if original then
            SetTimecycleModifierVar(MOD, name, original[1], original[2])
        else
            RemoveTimecycleModifierVar(MOD, name)
        end
    end
end)
