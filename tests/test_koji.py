import pytest

from syncer.koji import FEDORA_KOJI, FUSION_KOJI
from syncer.koji import Build, compare_evr, guess_dist, koji_builds
from syncer.koji import koji_search_package, latest_complete_builds
from syncer.koji import split_nevr


@pytest.fixture(params=('fedora', 'rpmfusion', 'centos'))
def koji_pkgname(request):
    d = {
        'fedora': (FEDORA_KOJI, 'fedora-release'),
        'rpmfusion': (FUSION_KOJI, 'rpmfusion-free-release'),
        'centos': ('https://cbs.centos.org/koji/', 'centos-release-docker')
    }
    return d[request.param]


def test_koji_search_package(koji_pkgname):
    koji, pkgname = koji_pkgname
    html = koji_search_package(koji, pkgname)
    assert 'Information for package' in html
    assert pkgname in html


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


@pytest.mark.parametrize('release', ['399.fc28', '1.fc28.8',
                                     '12.20170309git3300eb5.fc28'])
def test_guess_dist_fc28(release):
    assert guess_dist(release) == 'fc28'


@pytest.mark.parametrize('release', ['399.epel7', '1.epel7.8',
                                     '12.20170309git3300eb5.epel7'])
def test_guess_dist_epel7(release):
    assert guess_dist(release) == 'epel7'


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


def test_koji_builds(koji_pkgname):
    koji, pkgname = koji_pkgname
    builds = list(koji_builds(koji, pkgname))
    for build in builds:
        assert build.nevr.startswith(pkgname)
        assert isinstance(build.koji_id, int)
        assert build.status in ('complete', 'deleted', 'canceled', 'free',
                                'open', 'failed', 'closed')


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
