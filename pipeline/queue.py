#!/usr/bin/env python3
"""Local durable queue. All mutations use a process lock and atomic replacement."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parent
STATE = ROOT / 'state' / 'queue.json'
LOCK = ROOT / 'state' / '.queue.lock'


def initial():
    return {'version': 1, 'paused': True, 'stopped': False, 'jobs': []}


def save(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.queue-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as out:
            json.dump(state, out, indent=2, sort_keys=True)
            out.write('\n')
            out.flush()
            os.fsync(out.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def recover(state, now):
    count = 0
    for job in state['jobs']:
        if job['status'] == 'leased' and job['lease']['expires_at'] <= now:
            job['receipts'].append({'attempt': job['attempts'], 'at': now, 'success': False, 'details': {'event': 'lease_expired'}})
            job['status'] = 'queued'
            job['lease'] = None
            count += 1
    return count


def transact(operation, path=STATE, lock=LOCK, now=None):
    path, lock = Path(path), Path(lock)
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open('a+') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        state = json.loads(path.read_text()) if path.exists() else initial()
        before = json.dumps(state, sort_keys=True)
        result = operation(state, time.time() if now is None else now)
        if before != json.dumps(state, sort_keys=True) or not path.exists():
            save(path, state)
        return result


def enqueue(state, now, key, payload):
    if not key.strip():
        raise ValueError('A nonempty idempotency key is required')
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    for job in state['jobs']:
        if job['key'] == key:
            if job['payload_sha256'] != digest:
                raise ValueError('Idempotency key already used for different payload')
            return job['id']
    job = {'id': str(uuid.uuid4()), 'key': key, 'payload': payload, 'payload_sha256': digest,
           'status': 'queued', 'created_at': now, 'attempts': 0, 'lease': None, 'receipts': []}
    state['jobs'].append(job)
    return job['id']


def claim(state, now, worker, lease_seconds, storage, budget_bytes, minimum_free_bytes=0):
    if budget_bytes <= 0 or minimum_free_bytes < 0:
        raise ValueError('Disk budget must be positive and minimum free space nonnegative')
    recover(state, now)
    if state['paused'] or state['stopped']:
        return None
    if not worker or lease_seconds <= 0:
        raise ValueError('Worker and positive lease duration required')
    # A single active lease globally prevents concurrent voice-model loading.
    if any(j['status'] == 'leased' for j in state['jobs']):
        return None
    storage = Path(storage)
    storage.mkdir(parents=True, exist_ok=True)
    used = sum(p.stat().st_size for p in storage.rglob('*') if p.is_file() and not p.is_symlink())
    if used >= budget_bytes or shutil.disk_usage(storage).free < minimum_free_bytes:
        return None
    for job in state['jobs']:
        if job['status'] == 'queued':
            token = uuid.uuid4().hex
            job.update(status='leased', attempts=job['attempts'] + 1,
                       lease={'worker': worker, 'token_sha256': hashlib.sha256(token.encode()).hexdigest(), 'expires_at': now + lease_seconds})
            return {'id': job['id'], 'payload': job['payload'], 'token': token,
                    'expires_at': job['lease']['expires_at']}
    return None


def finish(state, now, job_id, token, success, receipt):
    for job in state['jobs']:
        if job['id'] == job_id:
            # Do not allow late workers to report success after expiration or re-lease.
            if job['status'] != 'leased' or job['lease']['token_sha256'] != hashlib.sha256(token.encode()).hexdigest() or job['lease']['expires_at'] <= now:
                raise ValueError('Lease is missing, expired, or owned by another worker')
            if not isinstance(receipt, dict) or not receipt:
                raise ValueError('A nonempty receipt object is required')
            job['receipts'].append({'attempt': job['attempts'], 'at': now, 'success': success, 'details': receipt})
            job['status'] = 'completed' if success else 'failed'
            job['lease'] = None
            return job['status']
    raise ValueError('Unknown job')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    add = sub.add_parser('enqueue'); add.add_argument('--key', required=True); add.add_argument('--payload', required=True, help='JSON object; public metadata only')
    heartbeat = sub.add_parser('heartbeat'); heartbeat.add_argument('--public-status', help='Write a public status snapshot to this path')
    sub.add_parser('status')
    for name in ('pause', 'resume', 'stop', 'reset-stop'):
        sub.add_parser(name)
    take = sub.add_parser('claim'); take.add_argument('--worker', required=True); take.add_argument('--lease-seconds', type=int, default=1800); take.add_argument('--storage', required=True); take.add_argument('--budget-bytes', type=int, required=True); take.add_argument('--minimum-free-bytes', type=int, default=0)
    done = sub.add_parser('finish'); done.add_argument('--id', required=True); done.add_argument('--token', required=True); done.add_argument('--receipt', required=True, help='JSON object; public metadata only'); done.add_argument('--failed', action='store_true')
    args = parser.parse_args()
    def run(state, now):
        if args.command == 'heartbeat':
            count = recover(state, now)
            return {'recovered': count, 'paused': state['paused'], 'stopped': state['stopped'], 'counts': {s: sum(j['status'] == s for j in state['jobs']) for s in ('queued', 'leased', 'completed', 'failed')}}
        if args.command == 'status': return state
        if args.command in ('pause', 'resume', 'stop', 'reset-stop'):
            if args.command == 'pause': state['paused'] = True
            if args.command == 'resume': state['paused'] = False
            if args.command == 'stop': state['stopped'] = True
            if args.command == 'reset-stop': state['stopped'] = False
            return {'paused': state['paused'], 'stopped': state['stopped']}
        if args.command == 'enqueue':
            payload = json.loads(args.payload)
            if not isinstance(payload, dict): raise ValueError('Payload must be an object')
            return {'id': enqueue(state, now, args.key, payload)}
        if args.command == 'claim': return claim(state, now, args.worker, args.lease_seconds, args.storage, args.budget_bytes, args.minimum_free_bytes)
        return {'status': finish(state, now, args.id, args.token, not args.failed, json.loads(args.receipt))}
    try:
        result = transact(run)
        if args.command == 'heartbeat' and args.public_status:
            blocked = ['Production backend is not configured']
            if result['paused']: blocked.append('Queue is paused')
            if result['stopped']: blocked.append('Queue is stopped')
            snapshot = {'lastCheck': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                        'monitorStatus': 'ok', 'producerStatus': 'not_configured', 'blockedReasons': blocked,
                        'queued': result['counts']['queued'], 'leased': result['counts']['leased'],
                        'paused': result['paused'], 'stopped': result['stopped']}
            save(Path(args.public_status), snapshot)
        print(json.dumps(result, indent=2))
    except (ValueError, json.JSONDecodeError) as exc:
        parser.exit(2, f'{exc}\n')


if __name__ == '__main__': main()
