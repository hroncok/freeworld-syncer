import contextlib
import functools
import os
import pathlib
import subprocess

from .koji import split_nevr

SCM = pathlib.Path.cwd() / 'scm'


@contextlib.contextmanager
def cd(path):
    prev_cwd = pathlib.Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def stdout(*command, check=True):
    return subprocess.run(command,
                          check=check,
                          universal_newlines=True,
                          stdout=subprocess.PIPE).stdout.strip()


def run(*command, check=True):
    return subprocess.run(command, check=check)


def gitout(*command, check=True):
    return stdout('git', *command, check=check)


def git(*command, check=True):
    return run('git', *command, check=check)


def fedpkg_clone(pkgname):
    return run('fedpkg', 'clone', pkgname)


def rfpkg_clone(pkgname, *, free):
    namespace = 'free' if free else 'nonfree'
    return run('rfpkg', 'clone', f'{namespace}/{pkgname}')


def clone_or_reset(pkgname, freeworldname, *, rffree):
    SCM.mkdir(exist_ok=True)
    repo = SCM / freeworldname
    if not repo.exists():
        with cd(SCM):
            rfpkg_clone(freeworldname, free=rffree)
    with cd(repo):
        setup_remotes(pkgname, freeworldname)
        git('fetch', '--all')
        git('checkout', 'master')
        git('reset', '--hard', 'origin/master')
        git('clean', '-f')


def setup_remotes(pkgname, freeworldname):
    remotes = gitout('remote').split()

    if 'origin' in remotes:
        fusion_url = gitout('config', '--get', 'remote.origin.url',
                            check=False)
        if not fusion_url.endswith((freeworldname, freeworldname + '.git')):
            raise RuntimeError(f'Weird remote origin URL {fusion_url}')
    else:
        raise RuntimeError('No origin remote')

    if 'fedora' in remotes:
        fedora_url = gitout('config', '--get', 'remote.fedora.url',
                            check=False)
        if not fedora_url.endswith((pkgname, pkgname + '.git')):
            raise RuntimeError(f'Weird remote fedora URL {fedora_url}')
    else:
        git('remote', 'add', 'fedora',
            f'https://src.fedoraproject.org/rpms/{pkgname}.git')


@functools.lru_cache(maxsize=2)
def resolve(merge_branch):
    try:
        gitout('rev-parse', f'fedora/{merge_branch}')
        # it's a branch/tag
        return f'fedora/{merge_branch}'
    except subprocess.CalledProcessError:
        # it's a hash (or it's bogus)
        return merge_branch


def git_merge(pkgname, freeworldname, branch, merge_branch):
    repo = SCM / freeworldname
    with cd(repo):
        git('checkout', branch)
        # merge the branch, keep our sources and .gitignore
        git('merge', resolve(merge_branch), '-X', 'ours', '-m', 'XXX merge')


def sources_magic(pkgname, freeworldname, branch, merge_branch):
    repo = SCM / freeworldname
    with cd(repo):
        sources_path = pathlib.Path('./sources')
        head = gitout('rev-parse', 'HEAD')
        try:
            # download possibly new Fedora sources
            git('reset', '--hard', resolve(merge_branch))

            # HACK alert 1/3
            # This works for chromium, but might fail somewhere else
            sources = sources_path.read_text().strip().splitlines()
            altered_sources = [l for l in sources if pkgname not in l]
            sources_path.write_text('\n'.join(altered_sources) + '\n')

            run('fedpkg', '--module-name', pkgname, 'sources')
        finally:
            # back to original HEAD
            git('reset', '--hard', head)

        # download remaining sources from their URLs
        run('spectool', '-g', f'{freeworldname}.spec')

        sources = sources_path.read_text().strip().splitlines()
        new_sources = []
        for source in sources:
            if ' = ' in source:
                raise NotImplementedError('new source format in RPM Fusion')
            *_, source = source.strip().rpartition(' ')
            # HACK alert (part 2/3)
            if not source.startswith(pkgname):
                new_sources.append(source)

        # HACK alert (part 3/3)
        untracked = gitout('ls-files', '--others',
                           '--exclude-standard').splitlines()
        if len(untracked) != 1:
            raise RuntimeError('Hack in sources_magic() failed. '
                               f'Found {len(untracked)} untracked files.')
        new_sources.append(untracked[0])

        run('rfpkg', 'new-sources', *new_sources)


def nevr(pkgname, freeworldname):
    out = stdout('rpm', '--specfile', f'{freeworldname}.spec')
    nevra = out.splitlines()[0].strip()
    nevr, *_ = nevra.rpartition('.')
    _, epoch, version, release = split_nevr(nevr)
    release, *_ = release.rpartition('.')
    if epoch:
        return f'{pkgname}-{epoch}:{version}-{release}'
    return f'{pkgname}-{version}-{release}'


def squash(pkgname, freeworldname):
    repo = SCM / freeworldname
    with cd(repo):
        msg = f'Merge Fedora, {nevr(pkgname, freeworldname)}'
        git('commit', '--amend', '-m', msg)
