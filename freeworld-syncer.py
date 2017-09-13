import sys

import click

from syncer.koji import koji_builds, latest_complete_builds, compare_evr
from syncer.koji import FEDORA_KOJI, FUSION_KOJI
from syncer.git import clone_or_reset, git_merge, sources_magic, squash


FEDORA_PKGNAME = 'chromium'
SUFFIX = 'freeworld'
FUSION_PKGNAME = f'{FEDORA_PKGNAME}-{SUFFIX}'


def pkgname_freeworldname(ctx):
    pkgname = ctx.obj['pkgname']
    freeworldname = ctx.obj['freeworldname'] or f'{pkgname}-{SUFFIX}'
    return pkgname, freeworldname


def welcome(what, pkgname, freeworldname):
    line = f'{what} for '
    line += click.style(pkgname, bold=True, fg='blue')
    line += ' and '
    line += click.style(freeworldname, bold=True, fg='magenta')
    click.echo(line)


@click.group()
@click.option('-p', '--pkgname', default=FEDORA_PKGNAME, metavar='NAME',
              help=f'Name of the Fedora package (default: {FEDORA_PKGNAME})')
@click.option('-f', '--freeworldname', default=None, metavar='NAME',
              help=f'Name of the RPM Fusion package '
                   f'(default: <pkgname>-{SUFFIX})')
@click.pass_context
def fsyncer(ctx, pkgname, freeworldname):
    """Compare package across Fedora and RPM Fusion"""
    ctx.obj['pkgname'] = pkgname
    ctx.obj['freeworldname'] = freeworldname


@fsyncer.command()
@click.pass_context
def koji(ctx):
    """Show sync status on Koji builds"""
    pkgname, freeworldname = pkgname_freeworldname(ctx)
    welcome('Koji check', pkgname, freeworldname)

    fedora_builds = latest_complete_builds(
        koji_builds(FEDORA_KOJI, pkgname))
    fusion_builds = latest_complete_builds(
        koji_builds(FUSION_KOJI, freeworldname))

    exitcode = 0

    for dist in reversed(sorted(fedora_builds.keys())):
        line = click.style(f'{dist}: ', bold=True)

        fedora_build = fedora_builds[dist]
        fusion_build = fusion_builds.get(dist)

        if compare_evr(fedora_build, fusion_build):
            fg = 'green'
        else:
            fg = 'red'
            exitcode = 1

        line += click.style(f'{fedora_build} {fusion_build}', fg=fg)
        click.echo(line)

    sys.exit(exitcode)


def yellow(text):
    return click.echo(click.style(text, fg='yellow'))


@fsyncer.command()
@click.option('-b', '--branch', default='master', metavar='BRANCH',
              help=f'git branch (default: master)')
@click.option('-n', '--namespace', default='free',
              type=click.Choice(['free', 'nonfree']),
              help='RPM Fusion namespace (default: free)')
@click.pass_context
def git(ctx, branch, namespace):
    """Merge Fedora git to RPMFusion (does not push)"""
    pkgname, freeworldname = pkgname_freeworldname(ctx)
    welcome('Git sync', pkgname, freeworldname)

    yellow('\nSetting up git-scm in ./scm...')
    clone_or_reset(pkgname, freeworldname, rffree=namespace == 'free')

    yellow(f'Merging {branch} from Fedora to RPM Fusion...')
    git_merge(pkgname, freeworldname, branch)

    yellow('Getting sources...')
    sources_magic(pkgname, freeworldname, branch)

    yellow('Squashing source change to merge commit...')
    squash(pkgname, freeworldname, branch)

    yellow(f'\nReady in ./scm/{freeworldname}')
    yellow('Inspect the commit and push manually at will')


if __name__ == '__main__':
    fsyncer(obj={})
