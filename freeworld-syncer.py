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


def koji_search_package(koji, pkgname):
    url = koji + 'search'
    r = requests.post(url, data={
        'match': 'glob',
        'type': 'package',
        'terms': pkgname,
    })
    r.raise_for_status()
    return r.text  # HTML


def koji_builds(koji, pkgname):
    html = koji_search_package(koji, pkgname)
    builds = RE_BUILDS.findall(html)
    statuses = RE_STATUS.findall(html)
    for idx, build in enumerate(builds):
        yield build[1], int(build[0]), statuses[idx]


for build in koji_builds(FEDORA_KOJI, FEDORA_PKGNAME):
    print(build)

for build in koji_builds(FUSION_KOJI, FUSION_PKGNAME):
    print(build)
