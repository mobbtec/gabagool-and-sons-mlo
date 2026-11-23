local _RegCmd = RegisterCommand
local function RegisterCommand(name, fn, restricted)   -- 1.7.0: LPR_CFG.Commands switch
    if LPR_CFG and LPR_CFG.Commands and LPR_CFG.Commands[name] == false then return end
    return _RegCmd(name, fn, restricted)
end
-- Prototype test helpers (client only, nothing is changed for other players).
--   /gs_tp <view>                                   teleport to a test viewpoint (list: /gs_tp help)
--   /gs_time <hour|off>                             local clock override for day / night screenshots
--   /gs_info                                        interior / room / door diagnostics into F8 console
--   /gs_cam <V01..VC|off> [fov]                     0.2.1: fixed scripted camera for matched before/after screenshots
--                                                   (same eye / target as the offline previews; the ped is parked hidden
--                                                   at the eye so the interior streams; /gs_cam off gives control back)
--   automatic "[gs] trace" lines (F8 + CitizenFX.log): streaming state of the shop while within 250 m,
--   printed only when it changes. Read-only (requests nothing), so it can't change what the game streams.
local timeOverride = nil

local TRACE_MODELS = { 'gs_proto_shell', 'gs_proto_glass_w1', 'gs_proto_glass_w2', 'v_ilev_csr_door_l', 'v_ilev_csr_door_r', 'prop_map_door_01' }

CreateThread(function()
    local last = ''
    local probe = GS.toWorld(6.5, 5.0, 1.0)
    while true do
        local dist = #(GetEntityCoords(PlayerPedId()) - probe)
        if dist < 250.0 then
            local interior = GetInteriorAtCoords(probe.x, probe.y, probe.z)
            local parts = { ('int=%d ready=%s'):format(interior, tostring(interior ~= 0 and IsInteriorReady(interior))) }
            for _, m in ipairs(TRACE_MODELS) do
                local h = joaat(m)
                -- K = archetype known (ytyp loaded), L = drawable loaded
                parts[#parts + 1] = ('%s=%s%s'):format(m:sub(10), IsModelInCdimage(h) and 'K' or '-', HasModelLoaded(h) and 'L' or '-')
            end
            local s = table.concat(parts, ' ')
            if s ~= last then
                print(('[gs] trace d=%.0f %s'):format(dist, s))
                last = s
            end
            Wait(250)
        else
            if last ~= '' then
                print('[gs] trace: left the 250 m zone')
                last = ''
            end
            Wait(1000)
        end
    end
end)

RegisterCommand('gs_tp', function(_, args)
    local v = GS.VIEWS[args[1] or 'out_w1']
    if not v then
        local names = {}
        for k, _ in pairs(GS.VIEWS) do names[#names + 1] = k end
        table.sort(names)
        print('[gs] views: ' .. table.concat(names, ', '))
        return
    end
    local ped = PlayerPedId()
    local w = GS.toWorld(v.pos.x, v.pos.y, v.pos.z)
    SetEntityCoords(ped, w.x, w.y, w.z, false, false, false, false)
    SetEntityHeading(ped, GS.heading(v.look.x, v.look.y))
    SetGameplayCamRelativeHeading(0.0)
    SetGameplayCamRelativePitch(0.0, 1.0)
    print(('[gs] tp %s -> %.2f %.2f %.2f heading %.1f (%s)'):format(args[1] or 'out_w1', w.x, w.y, w.z, GS.heading(v.look.x, v.look.y), v.label))
end, false)

RegisterCommand('gs_time', function(_, args)
    local h = tonumber(args[1] or '')
    if h then timeOverride = math.floor(h) % 24 else timeOverride = nil end
    print('[gs] local time override: ' .. tostring(timeOverride))
end, false)

CreateThread(function()
    while true do
        if timeOverride then
            NetworkOverrideClockTime(timeOverride, 0, 0)
            Wait(0)
        else
            Wait(500)
        end
    end
end)

RegisterCommand('gs_info', function()
    local ped = PlayerPedId()
    local p = GetEntityCoords(ped)
    local interior = GetInteriorAtCoords(GS.ORIGIN.x + 5.0, GS.ORIGIN.y + 2.0, GS.ORIGIN.z + 1.0)
    local cur = GetInteriorFromEntity(ped)
    local room = GetRoomKeyFromEntity(ped)
    print(('[gs] player %.2f %.2f %.2f | interior@shop=%d valid=%s ready=%s | ped interior=%d roomKey=%d'):format(
        p.x, p.y, p.z, interior, tostring(IsValidInterior(interior)), tostring(IsInteriorReady(interior)), cur, room))
    for _, d in ipairs(GS.DOORS) do
        local w = GS.toWorld(d.pos.x, d.pos.y, d.pos.z)
        local obj = GetClosestObjectOfType(w.x, w.y, w.z, 1.5, d.model or GS.DOOR_MODEL, false, false, false)
        print(('[gs] %s hinge %.3f %.3f %.3f -> object=%d heading=%.1f registered=%s'):format(
            d.id, w.x, w.y, w.z, obj, obj ~= 0 and GetEntityHeading(obj) or -1.0, tostring(IsDoorRegisteredWithSystem(joaat(d.id)))))
    end
end, false)


-- 0.2.1: matched screenshot cameras (art direction V3 §13.2 / LP-017)
local gsCam, gsCamPed = nil, nil
local function camOff()
    if gsCam then
        RenderScriptCams(false, false, 0, true, true)
        DestroyCam(gsCam, false)
        gsCam = nil
    end
    if gsCamPed then
        local ped = PlayerPedId()
        SetEntityVisible(ped, true, false)
        FreezeEntityPosition(ped, false)
        gsCamPed = nil
    end
    ClearFocus()
end

RegisterCommand('gs_cam', function(_, args)
    local k = args[1]
    if not k or k == 'off' then
        camOff()
        print('[gs] cam off')
        return
    end
    local v = GS.CAMS and GS.CAMS[k]
    if not v then
        local names = {}
        for n, _ in pairs(GS.CAMS or {}) do names[#names + 1] = n end
        table.sort(names)
        print('[gs] cams: ' .. table.concat(names, ', ') .. ', off')
        return
    end
    local e = GS.toWorld(v.eye.x, v.eye.y, v.eye.z)
    local a = GS.toWorld(v.at.x, v.at.y, v.at.z)
    local ped = PlayerPedId()
    local feet = GS.toWorld(v.eye.x, v.eye.y, 1.0)
    SetEntityCoords(ped, feet.x, feet.y, feet.z, false, false, false, false)
    FreezeEntityPosition(ped, true)
    SetEntityVisible(ped, false, false)
    gsCamPed = true
    if not gsCam then gsCam = CreateCam('DEFAULT_SCRIPTED_CAMERA', true) end
    SetCamCoord(gsCam, e.x, e.y, e.z)
    PointCamAtCoord(gsCam, a.x, a.y, a.z)
    SetCamFov(gsCam, tonumber(args[2] or '') or 50.0)
    SetCamActive(gsCam, true)
    RenderScriptCams(true, false, 0, true, true)
    SetFocusPosAndVel(e.x, e.y, e.z, 0.0, 0.0, 0.0)
    print(('[gs] cam %s (%s) eye %.2f %.2f %.2f'):format(k, v.label, e.x, e.y, e.z))
end, false)

AddEventHandler('onResourceStop', function(res)
    if res == GetCurrentResourceName() then camOff() end
end)
