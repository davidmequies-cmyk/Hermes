"""Zip compatible avec l'hébergement Wix : les noms de fichiers sont stockés en CP437
(c'est ainsi que Wix les relit), ce qui garde les accents des adresses (é, è, à…)."""
import sys, zipfile, pathlib

class CP437Info(zipfile.ZipInfo):
    def _encodeFilenameFlags(self):
        try:
            return self.filename.encode("cp437"), self.flag_bits & ~0x800
        except UnicodeEncodeError:
            return self.filename.encode("utf-8"), self.flag_bits | 0x800

def make(src, dest):
    src = pathlib.Path(src)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(src.rglob("*")):
            if f.is_file():
                info = CP437Info(f.relative_to(src).as_posix(), date_time=(2026, 10, 21, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, f.read_bytes())

if __name__ == "__main__":
    make(sys.argv[1], sys.argv[2])
