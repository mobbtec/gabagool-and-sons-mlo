-- LONG PIG 0.3.1-e: own sign props (revision).
--   lp_sign_bracket + lp_sign_board  blade sign on the street wall: the board hangs crooked on one hanger and sways
--   lp_aframe                        pavement A-frame board at the patio
-- LOCAL frozen objects without collision, spawned within RANGE; the board is turned only while the player is near.
local RANGE, NEAR = 90.0, 45.0
local objs, board, boardH = {}, nil, 0.0
local BR = { s = 5.78, t = -1.35, z = 2.55 }          -- 0.3.1-i: 17 cm off the return wall (the board was sunk into it)          -- bracket on the wall pier right of the big window (MLO-local)
local AFRAME = vector3(400.14, -1935.01, 23.75)     -- 0.3.1-j: on the new tiled corner by the fence

local function load(m)
    if not IsModelInCdimage(m) then return false end
    RequestModel(m)
    local t = GetGameTimer()
    while not HasModelLoaded(m) and GetGameTimer() - t < 5000 do Wait(0) end
    return HasModelLoaded(m)
end

local function make(m, p, h)
    local o = CreateObjectNoOffset(m, p.x, p.y, p.z, false, false, false)
    SetEntityCollision(o, false, false)
    FreezeEntityPosition(o, true)
    SetEntityRotation(o, 0.0, 0.0, h, 2, false)
    SetEntityLodDist(o, 150)
    objs[#objs + 1] = o
    SetModelAsNoLongerNeeded(m)
    return o
end

local function spawn()
    if load(`lp_sign_bracket`) then make(`lp_sign_bracket`, GS.toWorld(BR.s, BR.t, BR.z), GS.YAW) end
    if load(`lp_sign_board`) then
        boardH = GS.YAW + 90.0
        board = make(`lp_sign_board`, GS.toWorld(BR.s, BR.t - 0.58, BR.z - 0.02), boardH)
    end
    if load(`lp_aframe`) then
        local o = make(`lp_aframe`, AFRAME, 274.0)
        PlaceObjectOnGroundProperly(o)
        local r = GetEntityRotation(o, 2)
        SetEntityRotation(o, 0.0, 0.0, r.z, 2, false)
    end
end

local function remove()
    for _, o in ipairs(objs) do
        if DoesEntityExist(o) then DeleteObject(o) end
    end
    objs, board = {}, nil
end

CreateThread(function()
    while true do
        local d = #(GetEntityCoords(PlayerPedId()) - GS.ORIGIN)
        if d < RANGE and #objs == 0 then spawn() elseif d >= RANGE and #objs > 0 then remove() end
        if board and d < NEAR and DoesEntityExist(board) then
            local t = GetGameTimer() / 1000.0
            local sway = 2.5 * math.sin(t * 1.7) + 1.0 * math.sin(t * 0.63 + 1.0)
            SetEntityRotation(board, sway, 11.0, boardH, 2, false)      -- 11 deg crooked: one hanger gone
            Wait(0)
        else
            Wait(1500)
        end
    end
end)

AddEventHandler('onResourceStop', function(res)
    if res == GetCurrentResourceName() then remove() end
end)
