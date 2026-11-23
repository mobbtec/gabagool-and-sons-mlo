-- LONG PIG 1.9.1: staff saloon doors at the south end of the deli line (revision).
-- Two LOCAL props lp_saloon_leaf without collision (nobody gets stuck); a spring swings them away from whoever walks
-- through and lets them rock back to closed. Positions = gs_v030_kit.SALOON (MLO-local metres).
local ENABLED = true
local RANGE = 40.0
local HS, TA, TB, W = 7.0, -0.735, 0.405, 0.56
local MAXA, K_SPRING, DAMP = 78.0, 34.0, 2.6
local leaves = {}                                  -- { obj, h0, sgn, a, v }

local function load(m)
    if not IsModelInCdimage(m) then return false end
    RequestModel(m)
    local t = GetGameTimer()
    while not HasModelLoaded(m) and GetGameTimer() - t < 5000 do Wait(0) end
    return HasModelLoaded(m)
end

local function spawn()
    local m = `lp_saloon_leaf`
    if not load(m) then return end
    for _, d in ipairs({ { t = TA, h0 = GS.YAW + 90.0, sgn = -1.0 }, { t = TB, h0 = GS.YAW - 90.0, sgn = 1.0 } }) do
        local p = GS.toWorld(HS, d.t, 0.0)
        local o = CreateObjectNoOffset(m, p.x, p.y, p.z, false, false, false)
        SetEntityCollision(o, false, false)
        FreezeEntityPosition(o, true)
        SetEntityRotation(o, 0.0, 0.0, d.h0, 2, false)
        local int = GetInteriorAtCoords(p.x, p.y, p.z + 1.0)
        if int ~= 0 then ForceRoomForEntity(o, int, GetHashKey('gs_front')) end
        leaves[#leaves + 1] = { obj = o, h0 = d.h0, sgn = d.sgn, a = 0.0, v = 0.0 }
    end
    SetModelAsNoLongerNeeded(m)
end

local function remove()
    for _, l in ipairs(leaves) do
        if DoesEntityExist(l.obj) then DeleteObject(l.obj) end
    end
    leaves = {}
end

-- push = +1: somebody walks towards the staff side (+s), -1: towards the hall, 0: nobody in the doorway
local function pushFrom(ped, state)
    local c = GS.toWorld(HS, (TA + TB) / 2, 0.0)
    local r = math.rad(GS.YAW)
    local p = GetEntityCoords(ped)
    local dx, dy = p.x - c.x, p.y - c.y
    local ls = dx * math.cos(r) + dy * math.sin(r)             -- across the door line (+ = staff side)
    local lt = -dx * math.sin(r) + dy * math.cos(r)            -- along the door line
    if math.abs(lt) > (TB - TA) / 2 + 0.10 or math.abs(ls) > 0.80 or math.abs(p.z - c.z - 1.0) > 1.5 then
        state.side = nil
        return 0.0, 0.0
    end
    if not state.side then state.side = (ls < 0.0) and -1.0 or 1.0 end
    local amount = math.min(1.0, math.max(0.0, 1.0 - (math.abs(ls) - 0.20) / 0.60))
    return -state.side, amount
end

CreateThread(function()
    if not ENABLED then return end
    local state, last = {}, GetGameTimer()
    while true do
        local ped = PlayerPedId()
        local d = #(GetEntityCoords(ped) - GS.ORIGIN)
        if d < RANGE and #leaves == 0 then spawn() elseif d >= RANGE and #leaves > 0 then remove() end
        if #leaves > 0 and d < 14.0 then
            local now = GetGameTimer()
            local dt = math.min(0.05, (now - last) / 1000.0)
            last = now
            local dir, amount = pushFrom(ped, state)
            local busy = false
            for _, l in ipairs(leaves) do
                if amount > 0.0 then                                   -- held open by the body, eased
                    local target = l.sgn * dir * MAXA * amount
                    if math.abs(target) > math.abs(l.a) or (target * l.a) < 0.0 then
                        l.v = (target - l.a) * 9.0
                    else
                        l.v = l.v + (-K_SPRING * (l.a - target) - DAMP * 2.2 * l.v) * dt
                    end
                else                                                   -- free: rocks back and forth, settles closed
                    l.v = l.v + (-K_SPRING * l.a - DAMP * l.v) * dt
                end
                l.a = math.max(-MAXA - 6.0, math.min(MAXA + 6.0, l.a + l.v * dt))
                if math.abs(l.a) > 0.05 or math.abs(l.v) > 0.5 then
                    busy = true
                    if DoesEntityExist(l.obj) then SetEntityRotation(l.obj, 0.0, 0.0, l.h0 + l.a, 2, false) end
                elseif l.a ~= 0.0 then
                    l.a, l.v = 0.0, 0.0
                    if DoesEntityExist(l.obj) then SetEntityRotation(l.obj, 0.0, 0.0, l.h0, 2, false) end
                end
            end
            Wait((busy or amount > 0.0) and 0 or 120)
        else
            last = GetGameTimer()
            Wait(1000)
        end
    end
end)

AddEventHandler('onResourceStop', function(res)
    if res == GetCurrentResourceName() then remove() end
end)
