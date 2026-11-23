"""Build LONG PIG from project sources plus a local copy of GTA V Legacy."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gta', type=Path, required=True, help='GTA V Legacy installation')
    parser.add_argument('--blender', required=True, help='Blender 5.1 executable with Sollumz and native Gen8 export')
    parser.add_argument('--output', type=Path, required=True, help='New output directory, including intermediate Blender scenes')
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    output, game = args.output.resolve(), args.gta.resolve()
    if not (game/'x64k.rpf').is_file():
        parser.error('The game folder must contain x64k.rpf (GTA V Legacy)')
    binary = shutil.which(args.blender)
    if binary is None:
        parser.error('Blender executable was not found')
    if any(output.is_relative_to(path) for path in (repository/'source', repository/'tools', repository/'docs', game)):
        parser.error('Choose a new build directory outside the inputs')
    if output.exists():
        parser.error('Choose a new output directory')
    output.mkdir(parents=True)
    project = output/'project'
    for key in ('source/scripts','source/textures','source/fivem/gabagool_sons_mlo','docs/_raw'):
        shutil.copytree(repository/key, project/key, ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    env = dict(os.environ, GS_ROOT=str(project), GTA_ROOT=str(game), GS_KIT='gs_v302_kit')

    def blender(script, *extra):
        cmd = [binary, '-b', '--offline-mode', '--python-exit-code', '1', '--python', str(script)]
        if extra:
            cmd.extend(['--', *(str(p) for p in extra)])
        subprocess.run(cmd, env=env, cwd=project, check=True)

    blender(repository/'tools/read_game_inputs.py')
    for script, report in (
        ('gs_52_lod_override', 'lod_override_result'),
        ('gs_38_build_shutters','shutters_build_result'),
        ('gs_44_build_props','props_build_result'),
        ('gs_build_v302','prototype_build_result'),
    ):
        blender(project/'source/scripts'/(script+'.py'))
        path = project/'docs/_raw'/(report+'.json')
        content = json.loads(path.read_text(encoding='utf8'))
        if not content.get('go') or content.get('errors'):
            raise RuntimeError(f'Build checks failed. See {path}')
    native = project/'build/gabagool_sons_mlo'
    final = output/'gabagool_sons_mlo'
    blender(repository/'tools/rebuild_resource.py', native, native, final)
    names = (repository/'tools/resource_files.txt').read_text(encoding='utf8').splitlines()
    built = {p.relative_to(final).as_posix() for p in final.rglob('*') if p.is_file()}
    if set(names) != built:
        raise ValueError(f'Unexpected resource inventory. Missing {set(names)-built}, extra {built-set(names)}')
    blender(repository/'tools/check_output.py', final, output/'verification.json')
    print(f'Built {len(built)} files in {final}')


if __name__ == '__main__':
    main()
