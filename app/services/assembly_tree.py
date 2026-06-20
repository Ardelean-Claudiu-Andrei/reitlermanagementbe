from sqlalchemy.orm import Session
from app.models.assembly import Assembly
from app.models.part import Part


def iter_assembly_parts(asm_id, db: Session, multiplier: int = 1, _visited=None):
    """Yield (Part, effective_qty) for every part in the assembly, recursively into child_assemblies. Cycle-safe."""
    _visited = _visited or frozenset()
    if not asm_id or asm_id in _visited:
        return
    _visited = _visited | {asm_id}
    asm = db.query(Assembly).filter(Assembly.id == asm_id).first()
    if not asm:
        return
    for ap in (asm.parts or []):
        pid = ap.get("partId")
        if not pid:
            continue
        part = db.query(Part).filter(Part.id == pid).first()
        if part:
            yield part, ap.get("quantity", 1) * multiplier
    for ca in (asm.child_assemblies or []):
        yield from iter_assembly_parts(
            ca.get("assemblyId"), db, multiplier * ca.get("quantity", 1), _visited
        )


def iter_assembly_nodes(asm_id, db: Session, depth: int = 0, _visited=None):
    """Yield (Assembly, depth) for the assembly and all descendants, recursively. Cycle-safe."""
    _visited = _visited or frozenset()
    if not asm_id or asm_id in _visited:
        return
    _visited = _visited | {asm_id}
    asm = db.query(Assembly).filter(Assembly.id == asm_id).first()
    if not asm:
        return
    yield asm, depth
    for ca in (asm.child_assemblies or []):
        yield from iter_assembly_nodes(ca.get("assemblyId"), db, depth + 1, _visited)


def assembly_requires_laser(asm_id, db: Session, _visited=None) -> bool:
    """Return True if any part in this assembly or its descendants requires laser cutting. Cycle-safe."""
    _visited = _visited or frozenset()
    if not asm_id or asm_id in _visited:
        return False
    _visited = _visited | {asm_id}
    asm = db.query(Assembly).filter(Assembly.id == asm_id).first()
    if not asm:
        return False
    for ap in (asm.parts or []):
        part = db.query(Part).filter(Part.id == ap.get("partId")).first()
        if part and part.requires_laser_cutting:
            return True
    return any(
        assembly_requires_laser(ca.get("assemblyId"), db, _visited)
        for ca in (asm.child_assemblies or [])
    )
