"""Build the final resource in a fresh folder with Blender 5.1 + Sollumz.

blender -b --python-exit-code 1 --python tools/rebuild_resource.py -- ORIGINAL NATIVE OUTPUT

ORIGINAL and NATIVE are the two gabagool_sons_mlo folders of release 3.0.1 and
the rebuilt 3.0.2 project. OUTPUT must be a new directory on disk.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cleanup import save_clean
from cooler_clearance import fix
from compact_materials import pack


def assemble(original, native, output):
    if output.exists():
        raise FileExistsError(output)
    for base in (original, native):
        if not (base/'fxmanifest.lua').is_file() or output.is_relative_to(base):
            raise ValueError(f'Check input and output paths: {base}, {output}')
    output.parent.mkdir(exist_ok=True, parents=True)
    with TemporaryDirectory(dir=output.parent) as temp:
        scratch = Path(temp)
        stage = scratch/'resource'
        shutil.copytree(original, stage)
        for name in ('stream/gabagool_sons_mlo.ytyp', 'fxmanifest.lua', 'lp_timecycle.xml', 'client/night.lua'):
            shutil.copy2(native/name, stage/name)
        subdir = Path('stream/mlo')
        target = stage/subdir
        save_clean(original/subdir, target)
        market = 'gs_v26_market.ydr'
        fix(native/subdir/market, target/market)
        for name in ('gs_ah_open', 'gs_boh', 'gs_v021_hall', 'gs_v26_market'):
            file = name + '.ydr'
            optimized = scratch/'optimized'/file
            if pack(target/file, optimized):
                optimized.replace(target/file)
        stage.rename(output)


if __name__ == '__main__':
    paths = [Path(s).resolve() for s in sys.argv[sys.argv.index('--')+1:]]
    if len(paths) != 3:
        raise SystemExit('Expected ORIGINAL NATIVE OUTPUT')
    assemble(*paths)
