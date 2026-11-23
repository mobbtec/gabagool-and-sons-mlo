"""Export the block needed for this interior from a local GTA V Legacy installation."""
import os
from pathlib import Path
from szio.vfs import VPath


def extract():
    game = Path(os.environ['GTA_ROOT']).resolve()
    project = Path(os.environ['GS_ROOT']).resolve()
    target = project / 'reference_vanilla/sc1_14'
    target.mkdir(parents=True, exist_ok=True)
    block = 'x64k.rpf/levels/gta5/_citye/scentral_01/sc1_14.rpf'
    paths = {name: f'{block}/{name}' for name in (
        'sc1_14_build2.ydr', 'sc1_14_sc1_emissive_sc1_14b.ydr', 'sc1_14_grnd_02.ydr',
        'sc1_14_0.ybn', 'hi@sc1_14_0.ybn', 'sc1_14_bb_meltdown.ydr',
        'sc1_14_nbill_lod.ytd', 'sc1_14_nbill_slod.ytd',
    )}
    paths.update({
        'sc1_occl_01.ymap': 'update/x64/dlcpacks/patchday2ng/dlc.rpf/x64/levels/gta5/_citye/scentral_01/sc1_occl.rpf/sc1_occl_01.ymap',
        'hei_sc1_occl_01.ymap': 'update/x64/dlcpacks/mpheist/dlc.rpf/x64/levels/gta5/_citye/scentral_01/sc1_occl.rpf/hei_sc1_occl_01.ymap',
        'lr_sc1_occl_01.ymap': 'update/update.rpf/dlc_patch/mplowrider/x64/levels/gta5/_citye/scentral_01/sc1_occl.rpf/lr_sc1_occl_01.ymap',
    })
    for name, path in paths.items():
        raw = VPath(str(game/path)).read_bytes()
        if not raw.startswith(b'RSC7'):
            raise ValueError(f'Expected a GTA V Legacy RSC7 resource at {path}')
        (target/name).write_bytes(raw)
        print(f'Extracted {name} ({len(raw)} bytes)')


if __name__ == '__main__':
    extract()
