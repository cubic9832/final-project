"""Generate exactly the requested accepted profiles in independently audited shards."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import time

from vehicle_matching.catalog import read_catalog, save_catalog
from tools.data.households.generate_behavioral_choices import (
    ROLES, audit_saved, canonical, derived_seed, financial_key, generate,
    read_registered_catalog, sha256, write_json, DEFAULT_URL,
)
from vehicle_matching.finance import Profile


def generate_shard(task):
    output, catalog, count, seed, index, split_seed, source = task
    report_path = output / 'generation_report.json'
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding='utf-8'))
        if report.get('target_profiles') != count or report['seed'] != seed:
            raise ValueError('Resume configuration mismatch')
        write_json(output / 'saved_data_audit.json', audit_saved(output))
    else:
        report = generate(output, read_catalog(catalog), groups=max(100, count * 2),
                          target_profiles=count, seed=seed, shard_index=index,
                          split_seed=split_seed, source=source)
    return index, report['partitions'], sha256(report_path)


def audit_population(output, manifest):
    groups, signatures, ids = {}, set(), set()
    counts = {role: 0 for role in ROLES}
    for shard in manifest['shards']:
        directory = output / shard['directory']
        if sha256(directory / 'generation_report.json') != shard['report_sha256']:
            raise ValueError('Shard report mismatch')
        for role in ROLES:
            with (directory / f'{role}_profiles.jsonl').open(encoding='utf-8') as stream:
                for line in stream:
                    record = json.loads(line)
                    key = financial_key(Profile(**record['profile']))
                    signature = canonical(record['profile'])
                    if groups.setdefault(key, role) != role or signature in signatures or record['id'] in ids:
                        raise ValueError('Cross-shard duplicate or split leakage')
                    signatures.add(signature)
                    ids.add(record['id'])
                    counts[role] += 1
    if sum(counts.values()) != manifest['profiles_requested']:
        raise ValueError('Accepted profile count mismatch')
    result = {'status': 'passed', 'profiles': sum(counts.values()), 'partitions': counts,
              'financial_groups': len(groups), 'cross_shard_duplicates': 0, 'split_leakage': 0}
    write_json(output / 'population_audit.json', result)
    return result


def run(output, count, shard_size, workers, seed, catalog=None, url=DEFAULT_URL, resume=False):
    if min(count, shard_size, workers) <= 0:
        raise ValueError('Counts and workers must be positive')
    if output.exists() and not resume:
        raise FileExistsError(output)
    output.mkdir(parents=True, exist_ok=resume)
    snapshot = output / 'catalog.json'
    config = {'profiles': count, 'shard_size': shard_size, 'seed': seed,
              'source': str(catalog.resolve()) if catalog else url}
    if resume:
        if json.loads((output / 'configuration.json').read_text(encoding='utf-8')) != config:
            raise ValueError('Population resume configuration mismatch')
    else:
        vehicles = read_catalog(catalog) if catalog else read_registered_catalog(url)
        save_catalog(snapshot, sorted(vehicles, key=lambda car: car.id))
        write_json(output / 'configuration.json', config)
    tasks = []
    for index, offset in enumerate(range(0, count, shard_size)):
        amount = min(shard_size, count - offset)
        tasks.append((output / f'shard-{index:04d}', snapshot, amount,
                      derived_seed(seed, f'shard-{index}'), index,
                      derived_seed(seed, 'population-split'), config['source']))
    started = time.monotonic()
    shards = []
    # map preserves deterministic shard ordering regardless of process scheduling.
    with ProcessPoolExecutor(max_workers=workers) as executor:
        for index, partitions, digest in executor.map(generate_shard, tasks):
            shards.append({'directory': f'shard-{index:04d}', 'partitions': partitions, 'report_sha256': digest})
            accepted = sum(sum(part['profiles'] for part in item['partitions'].values()) for item in shards)
            print(json.dumps({'stage': 'generated-and-audited', 'shards': len(shards), 'profiles': accepted,
                              'target': count, 'elapsed_seconds': round(time.monotonic() - started, 1)}), flush=True)
    manifest = {'schema': 'behavioral-population-v1', 'profiles_requested': count,
                'catalog_sha256': sha256(snapshot), 'configuration': config, 'shards': shards,
                'partitions': {role: {name: sum(s['partitions'][role][name] for s in shards)
                                     for name in ('profiles', 'comparisons', 'features')} for role in ROLES}}
    write_json(output / 'manifest.json', manifest)
    print(json.dumps({'stage': 'global-audit', **audit_population(output, manifest)}), flush=True)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--profiles', type=int, default=1000000)
    parser.add_argument('--shard-size', type=int, default=10000)
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--seed', type=int, default=20261028)
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--catalog', type=Path)
    source.add_argument('--catalog-url', default=DEFAULT_URL)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    run(args.output, args.profiles, args.shard_size, args.workers, args.seed,
        args.catalog, args.catalog_url, args.resume)


if __name__ == '__main__':
    main()
