"""
Component Geometry Validation

Provides validation checks for CadQuery geometry to catch issues early:
- Shape validity (OCC validation)
- Bounding box sanity checks
- Solid/face counts
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import cadquery as cq


class IssueSeverity(Enum):
    """Severity level for validation issues."""
    ERROR = "error"      # Geometry likely won't work
    WARNING = "warning"  # Potential issues
    INFO = "info"        # Informational only


@dataclass
class ValidationIssue:
    """A single validation issue found during geometry checks."""
    severity: IssueSeverity
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of validating a component's geometry."""
    component_name: str
    is_valid: bool  # True if no errors
    issues: list[ValidationIssue] = field(default_factory=list)
    # Geometry metrics
    bbox_size: tuple[float, float, float] | None = None
    solid_count: int = 0
    face_count: int = 0

    @property
    def has_errors(self) -> bool:
        """Check if any error-level issues exist."""
        return any(i.severity == IssueSeverity.ERROR for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        """Check if any warning-level issues exist."""
        return any(i.severity == IssueSeverity.WARNING for i in self.issues)

    @property
    def error_count(self) -> int:
        """Count of error-level issues."""
        return sum(1 for i in self.issues if i.severity == IssueSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        """Count of warning-level issues."""
        return sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING)


# Validation thresholds (in mm)
MAX_DIMENSION = 2000.0  # Maximum reasonable dimension
MIN_DIMENSION = 0.01    # Minimum reasonable dimension


def validate_geometry(
    geometry: "cq.Workplane",
    name: str = "component",
    max_dimension: float = MAX_DIMENSION,
    min_dimension: float = MIN_DIMENSION,
) -> ValidationResult:
    """
    Validate a CadQuery geometry.

    Performs the following checks:
    - Geometry contains shapes (not empty)
    - Geometry contains solid bodies
    - OCC shape validity (if available)
    - Bounding box within reasonable limits

    Args:
        geometry: CadQuery Workplane to validate
        name: Component name for reporting
        max_dimension: Maximum allowed dimension in mm
        min_dimension: Minimum allowed dimension in mm

    Returns:
        ValidationResult with issues and metrics
    """
    issues: list[ValidationIssue] = []
    bbox_size = None
    solid_count = 0
    face_count = 0

    # Check 1: Get underlying shapes
    try:
        vals = geometry.vals()
        if not vals:
            issues.append(ValidationIssue(
                severity=IssueSeverity.ERROR,
                code="EMPTY_GEOMETRY",
                message="Geometry contains no shapes",
            ))
            return ValidationResult(
                component_name=name,
                is_valid=False,
                issues=issues,
            )

        # Get the compound/solid for further analysis
        shape = geometry.val()
    except Exception as e:
        issues.append(ValidationIssue(
            severity=IssueSeverity.ERROR,
            code="GEOMETRY_ACCESS_FAILED",
            message=f"Failed to access geometry: {e}",
        ))
        return ValidationResult(
            component_name=name,
            is_valid=False,
            issues=issues,
        )

    # Check 2: Count solids
    try:
        solids = shape.Solids()  # type: ignore[union-attr]
        solid_count = len(solids)
        if solid_count == 0:
            issues.append(ValidationIssue(
                severity=IssueSeverity.ERROR,
                code="NO_SOLIDS",
                message="Geometry has no solid bodies",
            ))
    except Exception:
        # Some shapes may not support Solids() - not necessarily an error
        pass

    # Check 3: Count faces
    try:
        faces = shape.Faces()  # type: ignore[union-attr]
        face_count = len(faces)
        if face_count == 0 and solid_count > 0:
            issues.append(ValidationIssue(
                severity=IssueSeverity.WARNING,
                code="NO_FACES",
                message="Solid has no faces",
            ))
    except Exception:
        pass

    # Check 4: Multiple solids (informational)
    if solid_count > 1:
        issues.append(ValidationIssue(
            severity=IssueSeverity.INFO,
            code="MULTIPLE_SOLIDS",
            message=f"Geometry contains {solid_count} separate solids",
            details={"solid_count": solid_count},
        ))

    # Check 5: Bounding box
    try:
        bbox = shape.BoundingBox()  # type: ignore[union-attr]
        bbox_size = (bbox.xlen, bbox.ylen, bbox.zlen)

        # Check for oversized dimensions
        max_dim = max(bbox_size)
        if max_dim > max_dimension:
            issues.append(ValidationIssue(
                severity=IssueSeverity.WARNING,
                code="OVERSIZED",
                message=f"Bounding box dimension ({max_dim:.1f}mm) exceeds {max_dimension}mm",
                details={"max_dimension": max_dim, "threshold": max_dimension},
            ))

        # Check for undersized dimensions
        min_dim = min(bbox_size)
        if min_dim < min_dimension:
            issues.append(ValidationIssue(
                severity=IssueSeverity.WARNING,
                code="UNDERSIZED",
                message=f"Bounding box dimension ({min_dim:.4f}mm) below {min_dimension}mm",
                details={"min_dimension": min_dim, "threshold": min_dimension},
            ))
    except Exception as e:
        issues.append(ValidationIssue(
            severity=IssueSeverity.WARNING,
            code="BBOX_FAILED",
            message=f"Could not compute bounding box: {e}",
        ))

    # Check 6: OCC shape validity
    try:
        occ_shape = shape.wrapped  # type: ignore[union-attr]
        from OCC.Core.BRepCheck import BRepCheck_Analyzer
        analyzer = BRepCheck_Analyzer(occ_shape)
        if not analyzer.IsValid():
            issues.append(ValidationIssue(
                severity=IssueSeverity.ERROR,
                code="INVALID_SHAPE",
                message="OCC reports shape is invalid (may have self-intersections or other issues)",
            ))
    except ImportError:
        # OCC not available for direct import - skip this check
        pass
    except Exception as e:
        issues.append(ValidationIssue(
            severity=IssueSeverity.WARNING,
            code="OCC_CHECK_FAILED",
            message=f"Could not perform OCC validity check: {e}",
        ))

    # Determine overall validity (no errors = valid)
    is_valid = not any(i.severity == IssueSeverity.ERROR for i in issues)

    return ValidationResult(
        component_name=name,
        is_valid=is_valid,
        issues=issues,
        bbox_size=bbox_size,
        solid_count=solid_count,
        face_count=face_count,
    )
