import click
import pytest
import re
import requests
import sys

# General config
FEDORA_PKGNAME = 'chromium'
SUFFIX = 'freeworld'
FUSION_PKGNAME = f'{FEDORA_PKGNAME}-{SUFFIX}'

FEDORA_KOJI = 'https://koji.fedoraproject.org/koji/'
FUSION_KOJI = 'http://koji.rpmfusion.org/koji/'

FEDORA_PREFIX = 'fc'
FEDORA_EOL = 24


# Global constants
RE_BUILDS = re.compile(r'<td><a href="buildinfo\?buildID=(\d+)">([^<]+)</a>'
                       r'</td>', re.ASCII)
RE_STATUS = re.compile(r'<img class="stateimg" src="/koji-static/images/\w+.'
                       r'png" title="(\w+)" alt="\w+"/>', re.ASCII)


@pytest.fixture(params=('fedora', 'rpmfusion', 'centos'))
def koji_pkgname(request):
    d = {
        'fedora': (FEDORA_KOJI, 'fedora-release'),
        'rpmfusion': (FUSION_KOJI, 'rpmfusion-free-release'),
        'centos': ('https://cbs.centos.org/koji/', 'centos-release-docker')
    }
    return d[request.param]


def koji_search_package(koji, pkgname):
    url = koji + 'search'
    r = requests.post(url, data={
        'match': 'glob',
        'type': 'package',
        'terms': pkgname,
    })
    r.raise_for_status()
    return r.text  # HTML


def test_koji_search_package(koji_pkgname):
    koji, pkgname = koji_pkgname
    html = koji_search_package(koji, pkgname)
    assert 'Information for package' in html
    assert pkgname in html


def split_nevr(nevr):
    nev, _, release = nevr.rpartition('-')
    name, _, ev = nev.rpartition('-')
    if ':' in ev:
        epoch, _, version = ev.partition(':')
    else:
        epoch, version = None, ev
    return name, epoch, version, release


@pytest.mark.parametrize('nevr', ['perl-1:5.26.0-399.fc28',
                                  'perl-5.26.0-399.fc28'])
def test_split_nevr(nevr):
    name, epoch, version, release = split_nevr(nevr)
    assert name == 'perl'
    if ':' in nevr:
        assert epoch == '1'
    else:
        assert epoch is None
    assert version == '5.26.0'
    assert release == '399.fc28'


def guess_dist(release):
    parts = release.split('.')
    for part in parts:
        if part.startswith(('fc', 'el', 'epel')):
            return part


@pytest.mark.parametrize('release', ['399.fc28', '1.fc28.8',
                                     '12.20170309git3300eb5.fc28'])
def test_guess_dist_fc28(release):
    assert guess_dist(release) == 'fc28'


@pytest.mark.parametrize('release', ['399.epel7', '1.epel7.8',
                                     '12.20170309git3300eb5.epel7'])
def test_guess_dist_epel7(release):
    assert guess_dist(release) == 'epel7'


class Build:
    def __init__(self, nevr, koji_id, status):
        self.nevr = nevr
        self.koji_id = int(koji_id)
        self.status = status

    def __repr__(self):
        return self.nevr

    def _attrs(self):
        if not hasattr(self, '_name'):
            (self._name, self._epoch,
             self._version, self._release) = split_nevr(self.nevr)
            self._dist = guess_dist(self._release)

    def __getattr__(self, name):
        if name in ('name', 'epoch', 'version', 'release', 'dist'):
            self._attrs()
            return getattr(self, '_' + name)
        raise AttributeError()


def test_build_class():
    build = Build('chromium-freeworld-60.0.3112.113-1.fc27', '123', 'complete')
    assert build.nevr == 'chromium-freeworld-60.0.3112.113-1.fc27'
    assert build.koji_id == 123
    assert build.status == 'complete'
    assert build.name == 'chromium-freeworld'
    assert build.epoch is None
    assert build.version == '60.0.3112.113'
    assert build.release == '1.fc27'
    assert build.dist == 'fc27'


def koji_builds(koji, pkgname):
    html = koji_search_package(koji, pkgname)
    builds = RE_BUILDS.findall(html)
    statuses = RE_STATUS.findall(html)
    for idx, build in enumerate(builds):
        yield Build(build[1], build[0], statuses[idx])


def test_koji_builds(koji_pkgname):
    koji, pkgname = koji_pkgname
    builds = list(koji_builds(koji, pkgname))
    for build in builds:
        assert build.nevr.startswith(pkgname)
        assert isinstance(build.koji_id, int)
        assert build.status in ('complete', 'deleted', 'canceled', 'free',
                                'open', 'failed', 'closed')


def eol(dist):
    if dist.startswith(FEDORA_PREFIX):
        num = int(dist.lstrip(FEDORA_PREFIX))
        if num <= FEDORA_EOL:
            return True
    return False


def latest_complete_builds(builds):
    latest = {}
    for build in builds:
        if (build.dist not in latest and
                build.status in ('complete', 'closed') and
                not eol(build.dist)):
            latest[build.dist] = build
    return latest


def test_latest_complete_builds():
    builds = [
        Build('a-123-2.fc28', '123', 'failed'),
        Build('a-123-2.fc27', '123', 'failed'),
        Build('a-123-1.fc28', '123', 'complete'),
        Build('a-123-1.fc20', '123', 'complete'),
        Build('a-123-1.epel7', '123', 'complete'),
        Build('a-122-1.epel7', '123', 'complete'),
    ]
    latest = latest_complete_builds(builds)
    assert len(latest) == 2
    assert latest['fc28'].nevr == 'a-123-1.fc28'
    assert latest['epel7'].nevr == 'a-123-1.epel7'


def compare_evr(build1, build2):
    return (build1 is not None and
            build2 is not None and
            build1.epoch == build2.epoch and
            build1.version == build2.version and
            build1.release == build2.release)


def test_compare_evr_ok():
    evr = '60.0.3112.113-1.fc28'
    assert compare_evr(
        Build(f'foo-{evr}', '1', 'complete'),
        Build(f'bar-{evr}', '1', 'complete')
    )


def test_compare_evr_fail():
    assert not compare_evr(
        Build('foo-123-2.fc28', '1', 'complete'),
        Build('foo-123-2.fc27', '1', 'complete')
    )


def test_compare_evr_none():
    assert not compare_evr(
        Build('foo-123-2.fc28', '1', 'complete'),
        None
    )


@click.group()
def fsyncer():
    """Compare package across Fedora and RPM Fusion"""
    pass


@fsyncer.command()
@click.option('-p', '--pkgname', default=FEDORA_PKGNAME, metavar='NAME',
              help=f'Name of the Fedora package (default: {FEDORA_PKGNAME})')
@click.option('-f', '--freeworldname', default=None, metavar='NAME',
              help=f'Name of the RPM Fusion package '
                   f'(default: <pkgname>-{SUFFIX})')
def koji(pkgname, freeworldname):
    """how sync status on Koji builds"""
    freeworldname = freeworldname or f'{pkgname}-{SUFFIX}'

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
    fsyncer()
