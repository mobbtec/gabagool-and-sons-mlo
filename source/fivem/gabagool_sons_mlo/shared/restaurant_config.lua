-- LONG PIG v0.2.9 — WORKING RESTAURANT / AFTER HOURS / FAMILY BUSINESS settings (server + client).
-- Positions come from shared/restaurant_data.lua (generated from the kit). Everything here is safe to edit.
LPR_CFG = {
    Enabled = true,
    Origin = vector3(411.655, -1912.045, 24.45),   -- MLO origin (same as client/config.lua GS.ORIGIN)
    Yaw = -45.94,                                  -- MLO rotation, degrees

    -- who may use the switches / printer / hood / order rail:
    --   RequireStaff = false -> anyone standing at the control (RP default: the place is open to whoever works there)
    --   RequireStaff = true  -> only ACE 'longpig.staff' or the job names below
    RequireStaff = false,
    StaffAce = 'longpig.staff',
    QBCoreJobs = {},                                -- e.g. { 'longpig' }
    ESXJobs = {},

    -- hidden compartment in the office credenza
    SecretRequirePerm = true,                       -- true: ACE 'longpig.family' or the jobs below; false: anyone
    SecretAce = 'longpig.family',
    SecretQBCoreJobs = {},
    SecretESXJobs = {},

    Reach = 1.4,                                    -- metres between the player and a control
    SecretReach = 1.0,
    Cooldown = 1200,                                -- ms between two actions of one player
    AfterHoursCooldown = 4000,                      -- ms between two After Hours switches (the interior is refreshed)
    MaxTickets = 4,                                 -- orders on the kitchen rail
    TicketLifetime = 30 * 60,                       -- seconds, then an order drops off the rail by itself
    Persist = true,                                 -- After Hours / hood / compartment state survives restarts (KVP)

    SoundDist = 22.0,                               -- metres, one-shot sounds (bell, printer, switch, creak)
    HoodSoundDist = 14.0,
    SoundVolume = 0.8,
    HoodLight = { range = 2.6, intensity = 6.0, color = { 255, 236, 206 } },   -- hood lamps (drawn while the hood is on)

    -- 1.7.0: switch single chat / console commands off (false). NOTE: the After Hours switch itself uses close_pig /
    -- open_pig to move the shutters - leave those two on if the shutters should follow the switch.
    Commands = {
        close_pig = true, open_pig = true, pig_status = true, pig_blinds = true,        -- shutters / blinds
        lp_afterhours = true, lp_rest_status = true,                                    -- restaurant state
        lp_sit = true, lp_night = true, lp_nightvar = true, lp_fx = true,               -- client settings
        gs_tp = true, gs_time = true, gs_info = true, gs_cam = true, gs_door = true, gs_floor = true,   -- debug
        lp_rest_debug = true, pig_debug = true,
    },
    -- 1.7.0: "press E" prompts. false = the prompt is not shown and that interaction is off.
    Prompts = {
        afterhours = true, bell = true, print = true, hood = true, orderup = true, secret = true,       -- 2.6.0: 1.9.3 counter / booths are back
        sit = true,                                  -- chairs, stools, booths
        work = true,                                 -- staff work spots (scenarios)
    },

    Text = {                                        -- help prompts (GTA help text, ~INPUT_CONTEXT~ = E)
        afterhours_on = '~INPUT_CONTEXT~ Закрыть зал (After Hours)',
        afterhours_off = '~INPUT_CONTEXT~ Открыть зал',
        bell = '~INPUT_CONTEXT~ Позвонить в звонок',
        print = '~INPUT_CONTEXT~ Пробить заказ',
        hood_on = '~INPUT_CONTEXT~ Включить вытяжку',
        hood_off = '~INPUT_CONTEXT~ Выключить вытяжку',
        orderup = '~INPUT_CONTEXT~ Заказ готов (снять чек)',
        secret = '~INPUT_CONTEXT~ Осмотреть шкаф',
        secret_close = '~INPUT_CONTEXT~ Закрыть',
    },
}

function LPR_toWorld(x, y, z)
    local r = math.rad(LPR_CFG.Yaw)
    local c, s = math.cos(r), math.sin(r)
    local o = LPR_CFG.Origin
    return vector3(o.x + x * c - y * s, o.y + x * s + y * c, o.z + (z or 0.0))
end
