import sys

import click

from syncer.koji import koji_builds, latest_complete_builds, compare_evr
from syncer.koji import FEDORA_KOJI, FUSION_KOJI


FEDORA_PKGNAME = 'chromium'
SUFFIX = 'freeworld'
FUSION_PKGNAME = f'{FEDORA_PKGNAME}-{SUFFIX}'


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
    """how sync status on Koji builds"""
    pkgname = ctx.obj['pkgname']
    freeworldname = ctx.obj['freeworldname'] or f'{pkgname}-{SUFFIX}'

    line = 'Koji check for '
    line += click.style(pkgname, bold=True, fg='blue')
    line += ' and '
    line += click.style(freeworldname, bold=True, fg='magenta')
    click.echo(line)

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


if __name__ == '__main__':
    fsyncer(obj={})
