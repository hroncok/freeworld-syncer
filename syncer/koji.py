import re
import requests


FEDORA_KOJI = 'https://koji.fedoraproject.org/koji/'
FUSION_KOJI = 'http://koji.rpmfusion.org/koji/'

FEDORA_PREFIX = 'fc'
FEDORA_EOL = 25


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


def split_nevr(nevr):
    nev, _, release = nevr.rpartition('-')
    name, _, ev = nev.rpartition('-')
    if ':' in ev:
        epoch, _, version = ev.partition(':')
    else:
        epoch, version = None, ev
    return name, epoch, version, release


def guess_dist(release):
    parts = release.split('.')
    for part in parts:
        if part.startswith(('fc', 'el', 'epel')):
            return part


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


def koji_builds(koji, pkgname):
    html = koji_search_package(koji, pkgname)
    builds = RE_BUILDS.findall(html)
    statuses = RE_STATUS.findall(html)
    for idx, build in enumerate(builds):
        yield Build(build[1], build[0], statuses[idx])


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


def compare_evr(build1, build2):
    return (build1 is not None and
            build2 is not None and
            build1.epoch == build2.epoch and
            build1.version == build2.version and
            build1.release == build2.release)
