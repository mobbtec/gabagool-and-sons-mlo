-- LONG PIG — exterior security roller shutters: settings shared by server and client.
-- Commands:  /close_pig  /open_pig  /pig_status  /pig_debug
-- Permission (server side, authoritative): ACE  "longpig.shutters"  e.g. in server.cfg:
--     add_ace group.admin longpig.shutters allow
--     add_ace identifier.license:xxxxxxxx longpig.shutters allow
-- The server console (and txAdmin console) may always run /close_pig and /open_pig.
LPS_CFG = {
    Enabled        = true,
    Origin         = vector3(411.655, -1912.045, 24.45),   -- shop (MLO) origin, same as GS.ORIGIN
    Ace            = 'longpig.shutters',   -- ACE that may open / close
    RequireAce     = false,                -- 0.3.0 (owner 2026-11-12): no permission needed, anyone near the shop may use /close_pig /open_pig
    MaxCommandDist = 40.0,                 -- players must be within this many metres of the shop (0 = anywhere)
    Duration       = 6500,                 -- ms for a full open or close (5-8 s per the brief)
    Cooldown       = 600,                  -- ms: repeated commands inside this window are ignored
    Persist        = true,                 -- remember open / closed across resource and server restarts (resource KVP)
    StartState     = 'open',               -- first start ever (no saved state): 'open' or 'closed'

    -- optional framework adapters, used only when RequireAce passes OR as an extra allow path
    QBCoreJobs     = {},                   -- e.g. { 'longpig' }  (qb-core job names that may also use the commands)
    ESXJobs        = {},                   -- e.g. { 'longpig' }  (es_extended job names)

    -- client
    SpawnDist      = 160.0,                -- shutter objects exist only while a player is this close
    SoundDist      = 45.0,                 -- motor / stop sounds audible up to this distance
    SoundVolume    = 0.75,                 -- master volume 0..1
    SafeZone       = 0.55,                 -- m: a player this close to a closing curtain keeps no collision until he steps away
}
