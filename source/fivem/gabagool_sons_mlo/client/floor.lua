local _RegCmd = RegisterCommand
local function RegisterCommand(name, fn, restricted)   -- 1.7.0: LPR_CFG.Commands switch
    if LPR_CFG and LPR_CFG.Commands and LPR_CFG.Commands[name] == false then return end
    return _RegCmd(name, fn, restricted)
end
-- 0.2.6 (brief section 6): floor A / B comparison for screenshots ONLY. A (default) is the aged checker built into the
-- shell. /gs_floor b swaps the shell's floor textures at runtime for the optional gray-beige quarry tile (B);
-- /gs_floor a restores A. Local to your client, nothing is saved. EXPERIMENTAL: if the game does not apply the swap to
-- the embedded shell texture, the floor simply stays A.
local TXD = 'gs_lp_floor_b'
local made = false

local function makeTxd()
    if made then return end
    local txd = CreateRuntimeTxd(TXD)
    for i, e in ipairs(GS.FLOOR_B or {}) do
        CreateRuntimeTextureFromImage(txd, 'floor_b_' .. i, e.file)
    end
    made = true
end

local function setB(on)
    for i, e in ipairs(GS.FLOOR_B or {}) do
        if on then
            AddReplaceTexture(GS.FLOOR_B.ydr, e.orig, TXD, 'floor_b_' .. i)
        else
            RemoveReplaceTexture(GS.FLOOR_B.ydr, e.orig)
        end
    end
end

RegisterCommand('gs_floor', function(_, args)
    local v = (args[1] or ''):lower()
    if v == 'b' then
        makeTxd()
        setB(true)
        print('[gs] floor B (comparison only) - /gs_floor a to restore')
    elseif v == 'a' then
        setB(false)
        print('[gs] floor A (default)')
    else
        print('[gs] /gs_floor a | b')
    end
end, false)

AddEventHandler('onResourceStop', function(res)
    if res == GetCurrentResourceName() and made then setB(false) end
end)
