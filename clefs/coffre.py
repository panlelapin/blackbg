"""Sauvegarde initiale et restauration BlackBG. Voir paire/howto.md."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
from urllib.parse import quote


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PAIR = HERE / "paire/paire.tar.gz.age"
PUBLIC = HERE / "paire/publique.txt"
RELEASE = HERE / "release.tar.gz.age"
SESSIONS = HERE / "discussions.tar.gz.age"
SIGNING = Path.home() / ".android/blackbg-release"
SIGNER = "d7f02e4701a55950eba482d631b4df25d9fd8100c21f18f99e8897f1aab2ec5e"


def run(*args, data=None):
    return subprocess.run(args, input=data, stdout=subprocess.PIPE, check=True).stdout


def digest(data):
    return hashlib.sha256(data).hexdigest()


def archive(files):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, data in files.items():
            entry = tarfile.TarInfo(name)
            entry.size, entry.mode = len(data), 0o600
            tar.addfile(entry, io.BytesIO(data))
    return buf.getvalue()


def unpack(data):
    files = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        for entry in tar:
            if not entry.isfile() or entry.name in files:
                raise ValueError("Entrée d’archive inattendue")
            files[entry.name] = tar.extractfile(entry).read()
    return files


def export_sessions():
    def api(route):
        return json.loads(run("opencode", "api", "get", route))

    project = api("/api/location?location%5Bdirectory%5D=" + quote(str(ROOT), safe=""))["project"]["id"]
    route = "/api/session?limit=100&project=" + quote(project, safe="")
    sessions, files, manifest = {}, {}, []
    while route:
        page = api(route)
        if not page["data"]:
            break
        for session in page["data"]:
            sid = session["id"]
            if session["projectID"] != project or sid in sessions:
                raise ValueError("Liste des sessions incohérente ; relancer la sauvegarde")
            sessions[sid] = session
        cursor = page["cursor"].get("next")
        route = "/api/session?cursor=" + quote(cursor, safe="") if cursor else None
    if not sessions:
        raise ValueError("Aucune session pour ce projet")
    done = set()
    while len(done) < len(sessions):
        layer = [s for k, s in sessions.items() if k not in done
                 and (not s.get("parentID") or s["parentID"] in done)]
        if not layer:
            raise ValueError("Parent de session absent ou cycle")
        for s in layer:
            sid = s["id"]
            name = f"sessions/{sid}.json"
            data = run("opencode", "session", "export", sid)
            transcript = json.loads(data)
            if transcript["info"]["id"] != sid or not isinstance(transcript["messages"], list):
                raise ValueError("Export OpenCode invalide")
            files[name] = data
            manifest.append(dict(id=sid, file=name, parentID=s.get("parentID"), sha256=digest(data)))
            done.add(sid)
    files["manifest.json"] = json.dumps(dict(project=project, sessions=manifest)).encode()
    print(f"{len(manifest)} discussions exportées.", flush=True)
    return archive(files)


def release_files():
    names = ("release.p12", "password")
    if SIGNING.is_symlink() or any(not (SIGNING / n).is_file() or (SIGNING / n).is_symlink() for n in names):
        raise ValueError("Paire de signature absente ou inattendue")
    java = Path(os.environ.get("JAVA_HOME", "/Applications/Android Studio.app/Contents/jbr/Contents/Home"))
    keytool = java / "bin/keytool"
    cert = run(keytool if keytool.exists() else "keytool", "-exportcert", "-alias", "blackbg",
               "-storetype", "PKCS12", "-keystore", SIGNING / names[0], "-storepass:file", SIGNING / names[1])
    if digest(cert) != SIGNER:
        raise ValueError("Le certificat ne correspond pas au signataire officiel")
    return {n: (SIGNING / n).read_bytes() for n in names}


def create():
    targets = [PAIR, PUBLIC, RELEASE, SESSIONS]
    if any(os.path.lexists(f) for f in targets):
        raise SystemExit("Coffre déjà présent : aucun fichier remplacé.")
    if not sys.stdin.isatty():
        raise SystemExit("Lancer la création dans un terminal interactif personnel.")
    release = archive(release_files())
    sessions = export_sessions()
    identity = run("age-keygen")
    public = run("age-keygen", "-y", data=identity)
    pair = archive({"publique.txt": public, "privee.txt": identity})
    print("Choisis la passphrase du coffre dans l’invite age.", flush=True)
    encrypted = run("age", "-p", data=pair)
    print("Vérification : retape ta passphrase avant l’enregistrement.", flush=True)
    if run("age", "-d", data=encrypted) != pair:
        raise ValueError("Échec de vérification de la paire")
    with tempfile.TemporaryDirectory(dir=HERE) as tmp:
        tmp = Path(tmp)
        staged = {PAIR: encrypted, PUBLIC: public}
        for target, plaintext in ((RELEASE, release), (SESSIONS, sessions)):
            enc = run("age", "-r", public.decode().strip(), data=plaintext)
            f = tmp / target.name
            f.write_bytes(enc)
            if run("age", "-d", "-i", "-", f, data=identity) != plaintext:
                raise ValueError("Échec de vérification : " + target.name)
            staged[target] = enc
        for target, data in staged.items():
            (tmp / target.name).write_bytes(data)
        for target in targets:
            os.link(tmp / target.name, target)
    print("Coffre créé. Les trois archives ont été déchiffrées et comparées aux originaux.")


def restore(mode):
    pair = unpack(run("age", "-d", PAIR))
    identity = pair["privee.txt"]
    if run("age-keygen", "-y", data=identity) != PUBLIC.read_bytes() or pair["publique.txt"] != PUBLIC.read_bytes():
        raise ValueError("Clé publique incohérente")
    if mode == "restaurer-release":
        files = unpack(run("age", "-d", "-i", "-", RELEASE, data=identity))
        if set(files) != {"release.p12", "password"}:
            raise ValueError("Archive de signature inattendue")
        SIGNING.parent.mkdir(mode=0o700, exist_ok=True)
        SIGNING.mkdir(mode=0o700)  # Refuser tout écrasement.
        for name, data in files.items():
            (SIGNING / name).write_bytes(data)
        release_files()
    else:
        files = unpack(run("age", "-d", "-i", "-", SESSIONS, data=identity))
        entries = json.loads(files["manifest.json"])["sessions"]
        for s in entries:
            if digest(files[s["file"]]) != s["sha256"]:
                raise ValueError("Empreinte de session incorrecte")
        # Un seul JSON temporaire, privé et hors de la copie de travail.
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "session.json"
            for s in entries:
                f.write_bytes(files[s["file"]])
                run("opencode", "session", "import", "--directory", ROOT, f)
        print(f"{len(entries)} sessions importées dans {ROOT}.")


if __name__ == "__main__":
    os.umask(0o077)
    if sys.argv[1:] == ["creer"]:
        create()
    elif sys.argv[1:] in (["restaurer-release"], ["restaurer-discussions"]):
        restore(sys.argv[1])
    else:
        sys.exit("Usage : coffre.py creer | restaurer-release | restaurer-discussions")
