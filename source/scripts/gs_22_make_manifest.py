# Gabagool & Sons — writes stream/_manifest.ymf (CPackFileMetaData, PSO big-endian) for the MLO resource.
#
# Why: a brand-new MLO needs the game to know, before the placement ymap streams in, that
#   * <mlo>_milo_.ymap is INTERIOR_DATA and depends on the MLO .ytyp,
#   * the interior's static collision is <bounds>.ybn.
# Without it the first test crashed in CInteriorInst init (interior proxy == null, GTA5_b3258.exe+93419F).
# Layout mirrors the _manifest.ymf of the working custom MLO already on the server (dealer_map, CodeWalker-made):
#   root CPackFileMetaData { MapDataGroups[], HDTxdBindingArray[], imapDependencies[],
#                            imapDependencies_2[CImapDependencies], itypDependencies_2[CItypDependencies],
#                            Interiors[CInteriorBoundsFiles] }
# The PSCH (schema) section below is the game's own type schema for these structures (no content of the
# other resource is reused: all names/hashes in PSIN are ours).
import struct
import sys
from pathlib import Path

PSCH_HEX = (
    "505343480000019c00000005c11f3ee1000000345a564e500000007c2c325290000000c493a68a2f000000f46452a05b00000190"
    "00000005000000180000000031af439f0b07000000000000000001000e0000006452a05b6452a05b0f00000400200001000001000b"
    "070000000000008fb42ae60d00000800000003000000050000001800000000ac4450640b07000000000000000001000e000000"
    "6452a05b6452a05b0f00000400200001000001000b070000000000008fb42ae60d000008000000030000000300000018000000"
    "00acec22be0b07000000000000000001000b07000000000000c496e4a80d000008000000010000000c00000060000000000000"
    "01000c000000c25b3923b52cae230d00000000000000000001000c00000059869c63f78afb230d00001000000002000001000c"
    "000000d0ad6e622bda143f0d00002000000004000001000c000000c11f3ee1dd4c5ccc0d00003000000006000001000c000000"
    "5a564e50d2611c990d00004000000008000001000c0000002c32529038767a8f0d0000500000000a010000012156909600000000"
)
T_HASHES = 0x00000006          # block of u32 name hashes
T_IMAPDEPS = 0xC11F3EE1        # CImapDependencies
T_ITYPDEPS = 0x5A564E50        # CItypDependencies
T_INTERIOR = 0x2C325290        # CInteriorBoundsFiles
T_ROOT = 0x93A68A2F            # CPackFileMetaData
INTERIOR_DATA = 1              # eManifestFlags bit 0


def joaat(s):
    h = 0
    for c in s.lower().encode():
        h = (h + c) & 0xFFFFFFFF
        h = (h + (h << 10)) & 0xFFFFFFFF
        h ^= h >> 6
    h = (h + (h << 3)) & 0xFFFFFFFF
    h ^= h >> 11
    h = (h + (h << 15)) & 0xFFFFFFFF
    return h


def ptr(block, offset=0):
    return (offset << 12) | block


def arr(block, offset, count):
    """PSO array: pointer(4) + unk(4) + count(2) + capacity(2) + pad(4) = 16 bytes"""
    if count == 0:
        return b"\0" * 16
    return struct.pack(">IIHHI", ptr(block, offset), 0, count, count, 0)


def build(imap_name, ityp_name, interior_name, bounds_name):
    # block 1: hashes [ityp, bounds]
    b1 = struct.pack(">II", joaat(ityp_name), joaat(bounds_name))
    # block 2: one CImapDependencies { imapName, manifestFlags, itypDepArray -> b1[0] x1 }
    b2 = struct.pack(">II", joaat(imap_name), INTERIOR_DATA) + arr(1, 0, 1)
    # block 3: one CItypDependencies { itypName, manifestFlags, itypDepArray (empty) }
    b3 = struct.pack(">II", joaat(ityp_name), INTERIOR_DATA) + arr(0, 0, 0)
    # block 4: one CInteriorBoundsFiles { Name, pad, Bounds -> b1[4] x1 }
    b4 = struct.pack(">II", joaat(interior_name), 0) + arr(1, 4, 1)
    # block 5: root
    b5 = (arr(0, 0, 0) + arr(0, 0, 0) + arr(0, 0, 0) + arr(2, 0, 1) + arr(3, 0, 1) + arr(4, 0, 1))
    blocks = [(T_HASHES, b1), (T_IMAPDEPS, b2), (T_ITYPDEPS, b3), (T_INTERIOR, b4), (T_ROOT, b5)]
    data = bytearray(b"\0" * 8)  # 8 bytes after the section header, first block at offset 16
    entries = []
    for h, b in blocks:
        off = 8 + len(data)
        entries.append((h, off, len(b)))
        data += b
    psin = b"PSIN" + struct.pack(">I", 8 + len(data)) + bytes(data)
    pmap = b"PMAP" + struct.pack(">IiHH", 16 + 16 * len(entries), len(entries), len(entries), 0x7070)
    for h, off, ln in entries:
        pmap += struct.pack(">IiiI", h, off, 0, ln)
    psch = bytes.fromhex(PSCH_HEX)
    assert psch[:4] == b"PSCH" and struct.unpack_from(">I", psch, 4)[0] == len(psch)
    return psin + pmap + psch


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("_manifest.ymf")
    mlo = "gs_longpig_int"
    data = build(imap_name=f"{mlo}_milo_", ityp_name=mlo, interior_name=mlo, bounds_name=mlo)
    out.write_bytes(data)
    print(out, len(data), "bytes")
