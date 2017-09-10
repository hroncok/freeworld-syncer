import pytest
import re
import requests

# General config
FEDORA_PKGNAME = 'chromium'
FUSION_PKGNAME = FEDORA_PKGNAME + '-freeworld'

FEDORA_KOJI = 'https://koji.fedoraproject.org/koji/'
FUSION_KOJI = 'http://koji.rpmfusion.org/koji/'


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


def koji_builds(koji, pkgname):
    html = koji_search_package(koji, pkgname)
    builds = RE_BUILDS.findall(html)
    statuses = RE_STATUS.findall(html)
    for idx, build in enumerate(builds):
        yield build[1], int(build[0]), statuses[idx]


def test_koji_builds(koji_pkgname):
    koji, pkgname = koji_pkgname
    builds = list(koji_builds(koji, pkgname))
    for build in builds:
        assert build[0].startswith(pkgname)
        assert isinstance(build[1], int)
        assert build[2] in ('complete', 'deleted', 'canceled', 'free',
                            'open', 'failed', 'closed')


if __name__ == '__main__':
    for build in koji_builds(FEDORA_KOJI, FEDORA_PKGNAME):
        print(build)

    for build in koji_builds(FUSION_KOJI, FUSION_PKGNAME):
        print(build)
