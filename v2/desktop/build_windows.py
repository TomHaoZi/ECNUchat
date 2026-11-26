"""Build a portable Windows ZIP with the locally installed JDK. No network or package manager."""
import argparse
import io
import os
import shutil
import struct
import subprocess
import tempfile
import zipfile
from pathlib import Path

DESKTOP = Path(__file__).resolve().parent
PWA = DESKTOP.parent / "pwa"
ROOT = DESKTOP.parents[1]
NAME = "ECNUchat-v2"


def client_bundle():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as bundle:
        for source in sorted(PWA.rglob("*")):
            if source.is_file():
                data = source.read_bytes()
                if source == PWA / "index.html":
                    if data.count(b"</head>") != 1:
                        raise ValueError("PWA index must have one </head> for desktop configuration")
                    data = data.replace(b"</head>", b'<script src="desktop-bridge.js"></script>\n</head>')
                bundle.writestr(source.relative_to(PWA).as_posix(), data)
    return stream.getvalue()


def build(output):
    if os.name != "nt":
        raise SystemExit("Build this Windows image on Windows with JDK 21 or newer.")
    for binary in ("javac", "jpackage"):
        if not shutil.which(binary):
            raise SystemExit(f"{binary} is required on PATH (local JDK 21 or newer).")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as temp:
        work = Path(temp)
        classes = work / "classes"
        jars = work / "jars"
        classes.mkdir()
        jars.mkdir()
        subprocess.run(["javac", "--release", "21", "-encoding", "UTF-8", "-d", classes,
                        DESKTOP / "Desktop.java"], check=True)
        with zipfile.ZipFile(jars / "desktop.jar", "w", zipfile.ZIP_DEFLATED) as jar:
            for compiled in classes.rglob("*.class"):
                jar.write(compiled, compiled.relative_to(classes))
            jar.write(DESKTOP / "config.js", "config.js")
            jar.writestr("pwa.zip", client_bundle())
        # Windows ICO containers accept PNG images directly.
        png = (PWA / "icon-192.png").read_bytes()
        icon = work / "desktop.ico"
        icon.write_bytes(struct.pack("<HHHBBBBHHII", 0, 1, 1, 192, 192, 0, 0, 1, 32, len(png), 22) + png)
        subprocess.run(["jpackage", "--type", "app-image", "--name", NAME, "--app-version", "2.0",
                        "--input", jars, "--main-jar", "desktop.jar", "--main-class", "Desktop",
                        "--add-modules", "jdk.httpserver,java.desktop", "--icon", icon,
                        "--vendor", "ECNUchat", "--dest", work], check=True)
        image = work / NAME
        jdk = Path(shutil.which("jpackage")).resolve().parents[1]
        if (jdk / "NOTICE").is_file():
            shutil.copy2(jdk / "NOTICE", image / "runtime")
        if (jdk / "release").is_file():
            shutil.copy2(jdk / "release", image / "runtime" / "build-source.txt")
        shutil.copy2(DESKTOP / "README.md", image)
        shutil.copy2(DESKTOP.parent / "relay" / "relay.py", image)
        shutil.copy2(ROOT / "LICENSE", image)
        archive = shutil.make_archive(str(work / "release"), "zip", work, NAME)
        os.replace(archive, output)
    print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / (NAME + "-Windows.zip"))
    build(parser.parse_args().output.resolve())
