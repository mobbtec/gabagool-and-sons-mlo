import argparse, json, os, sys
from pathlib import Path
from shelf_geometry import read_actual_packs, inspect

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('before',type=Path);parser.add_argument('after',type=Path,nargs='?')
    parser.add_argument('--game',type=Path,default=os.environ.get('GTA_ROOT'),required='GTA_ROOT' not in os.environ)
    parser.add_argument('--json',type=Path);args=parser.parse_args()
    packs=read_actual_packs(args.game)
    report={'original':inspect(args.before,packs,False)}
    if args.after:
        report['updated']=inspect(args.after,packs,True)
    if args.json:
        args.json.write_text(json.dumps(report,indent=2),encoding='utf-8')
    for key,data in report.items(): print(key, {k:v for k,v in data.items() if k!='rows'})
    sys.stdout.flush();os._exit(0)
