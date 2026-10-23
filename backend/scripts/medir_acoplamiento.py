"""
Mide Ca (acoplamiento aferente), Ce (acoplamiento eferente) y I (inestabilidad)
por paquete, analizando los imports reales de backend/src con el modulo ast
(sin dependencias externas: no hace falta jdeps/pydeps, que son para otros
lenguajes). Equivalente real para Python a lo que jdeps hace en Java.

I = Ce / (Ca + Ce). Cerca de 0 = estable (del que dependen, no depende de
nadie). Cerca de 1 = inestable (depende de todos, nadie depende de el).
"""
import ast
import os
from collections import defaultdict

ROOT = os.path.join(os.path.dirname(__file__), "..", "src")
ROOT = os.path.normpath(ROOT)


def paquete_de(path: str) -> str:
    """backend/src/modules/queues/domain/puertos.py -> modules.queues.domain"""
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    parts = rel.split("/")[:-1]  # sin el archivo .py
    return ".".join(parts) if parts else "src"


def resolver_import(modulo_actual: str, nodo) -> list[str]:
    """Devuelve los paquetes (no el archivo final) a los que apunta un import,
    relativo o absoluto, dentro de src/."""
    objetivos = []
    if isinstance(nodo, ast.Import):
        for alias in nodo.names:
            objetivos.append(alias.name)
    elif isinstance(nodo, ast.ImportFrom):
        if nodo.level and nodo.level > 0:
            # import relativo: sube `level` paquetes desde el actual
            partes_actual = modulo_actual.split(".")
            base = partes_actual[: len(partes_actual) - (nodo.level - 1)] if nodo.level > 1 else partes_actual
            if nodo.module:
                objetivos.append(".".join(base + [nodo.module]))
            else:
                objetivos.append(".".join(base))
        elif nodo.module:
            objetivos.append(nodo.module)
    return objetivos


def es_paquete_propio(nombre: str) -> bool:
    return nombre.startswith("modules.") or nombre.startswith("shared.") or nombre in ("modules", "shared")


def main():
    deps = defaultdict(set)  # paquete -> set(paquetes de los que depende)
    paquetes = set()

    for dirpath, _, filenames in os.walk(ROOT):
        if "__pycache__" in dirpath:
            continue
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            full = os.path.join(dirpath, fn)
            pkg = paquete_de(full)
            paquetes.add(pkg)
            with open(full, encoding="utf-8") as f:
                try:
                    tree = ast.parse(f.read(), filename=full)
                except SyntaxError:
                    continue
            for nodo in ast.walk(tree):
                if isinstance(nodo, (ast.Import, ast.ImportFrom)):
                    for objetivo in resolver_import(pkg, nodo):
                        if es_paquete_propio(objetivo) or objetivo.split(".")[0] == pkg.split(".")[0]:
                            # nos quedamos solo con paquetes de primer/segundo nivel
                            # (modules.X o modules.queues.Y), no el archivo exacto
                            piezas = objetivo.split(".")
                            if piezas[0] in ("modules", "shared"):
                                destino = ".".join(piezas[:3]) if len(piezas) >= 3 else ".".join(piezas)
                            else:
                                continue
                            if destino != pkg:
                                deps[pkg].add(destino)

    # Nivel 1: por modulo de negocio (modules.auth, modules.queues, ... , shared)
    def nivel1(pkg):
        piezas = pkg.split(".")
        if piezas[0] == "modules" and len(piezas) >= 2:
            return f"modules.{piezas[1]}"
        return piezas[0]

    deps_n1 = defaultdict(set)
    for origen, destinos in deps.items():
        for d in destinos:
            o1, d1 = nivel1(origen), nivel1(d)
            if o1 != d1:
                deps_n1[o1].add(d1)

    todos_n1 = sorted(set(deps_n1.keys()) | {d for s in deps_n1.values() for d in s})

    print("# Acoplamiento por modulo (nivel 1) — backend/src/modules/* y shared")
    print()
    print("Comando real usado: python backend/scripts/medir_acoplamiento.py")
    print("(analizador propio con el modulo ast de Python, equivalente a jdeps para este stack;")
    print(" ver docs/acoplamiento/2026-10-17.md sobre por que no pydeps/import-linter para esto)")
    print()
    print("Dependencias (quien -> de quien depende), nivel modulo:")
    for o in todos_n1:
        for d in sorted(deps_n1.get(o, [])):
            print(f"  {o} -> {d}")
    print()

    print("| Paquete | Ca | Ce | I |")
    print("|---|---|---|---|")
    for pkg in todos_n1:
        ce = len(deps_n1.get(pkg, set()))
        ca = sum(1 for o, ds in deps_n1.items() if pkg in ds)
        i = ce / (ca + ce) if (ca + ce) else 0.0
        print(f"| {pkg} | {ca} | {ce} | {i:.2f} |")

    # Nivel 2 especial: queues.domain vs queues.infraestructura (el limite que
    # ya vigila .importlinter) — igual que el ejemplo de la clase con reservas.*
    print()
    print("## Foco: backend/src/modules/queues/* (el paquete con la rodaja hexagonal)")
    print()
    sub_deps = defaultdict(set)
    for origen, destinos in deps.items():
        if origen.startswith("modules.queues"):
            for d in destinos:
                if d.startswith("modules.queues") and d != origen:
                    sub_deps[origen].add(d)
    subpaquetes = sorted(set(sub_deps.keys()) | {d for s in sub_deps.values() for d in s})
    print("| Paquete | Ca | Ce | I |")
    print("|---|---|---|---|")
    for pkg in subpaquetes:
        ce = len(sub_deps.get(pkg, set()))
        ca = sum(1 for o, ds in sub_deps.items() if pkg in ds)
        i = ce / (ca + ce) if (ca + ce) else 0.0
        print(f"| {pkg} | {ca} | {ce} | {i:.2f} |")


if __name__ == "__main__":
    main()
