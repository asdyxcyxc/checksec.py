from collections import namedtuple
from pathlib import Path

import lief
from lief.PE import DLL_CHARACTERISTICS, HEADER_CHARACTERISTICS, MACHINE_TYPES

from .binary import BinarySecurity

PEChecksecData = namedtuple(
    "PEChecksecData",
    [
        "machine",
        "nx",
        "pie",
        "canary",
        "aslr",
        "dynamic_base",
        "high_entropy_va",
        "isolation",
        "seh",
        "safe_seh",
        "guard_cf",
        "force_integrity",
    ],
)


def is_pe(filepath: Path) -> bool:
    """Tests whether given file is a Portable Executable"""
    return lief.is_pe(str(filepath))


class PESecurity(BinarySecurity):
    """This class allows to get the security state of a PE from a Path object"""

    def __init__(self, pe_path: Path):
        super().__init__(pe_path)

    @property
    def has_pie(self) -> bool:
        """Whether PIE is enabled"""
        return self.bin.is_pie

    @property
    def has_canary(self) -> bool:
        """Whether Security Cookie (/GS) is enabled"""
        return True if self.bin.load_configuration.security_cookie != 0 else False

    @property
    def has_dynamic_base(self) -> bool:
        """Whether DYNAMIC_BASE is enabled"""
        return self.bin.optional_header.has(DLL_CHARACTERISTICS.DYNAMIC_BASE)

    @property
    def is_aslr(self) -> bool:
        """Checks whether ASLR is compatible"""
        # https://github.com/trailofbits/winchecksec/blob/v2.0.0/checksec.cpp#L172
        return not self.bin.header.has_characteristic(HEADER_CHARACTERISTICS.RELOCS_STRIPPED) and self.has_dynamic_base

    @property
    def has_high_entropy_va(self) -> bool:
        """Whether HIGH_ENTROPY_VA is enabled"""
        return self.bin.optional_header.has(DLL_CHARACTERISTICS.HIGH_ENTROPY_VA)

    @property
    def has_guard_cf(self) -> bool:
        """Whether GUARD:CF is enabled"""
        return self.bin.optional_header.has(DLL_CHARACTERISTICS.GUARD_CF)

    @property
    def has_force_integrity(self) -> bool:
        """Whether FORCE_INTEGRITY is enabled"""
        return self.bin.optional_header.has(DLL_CHARACTERISTICS.FORCE_INTEGRITY)

    @property
    def has_isolation(self) -> bool:
        """Whether the binary has NO_ISOLATION disabled"""
        return not self.bin.optional_header.has(DLL_CHARACTERISTICS.NO_ISOLATION)

    @property
    def has_seh(self) -> bool:
        return not self.bin.optional_header.has(DLL_CHARACTERISTICS.NO_SEH)

    @property
    def has_safe_seh(self) -> bool:
        """Whether the binary has SafeSEH mitigations"""
        # SafeSEH only applies to 32 bits
        # winchecksec implementation:
        # https://github.com/trailofbits/winchecksec/blob/v2.0.0/checksec.cpp#L280
        if not self.bin.header.machine == MACHINE_TYPES.I386:
            return False
        return (
            self.has_seh
            and self.bin.load_configuration.se_handler_table != 0
            and self.bin.load_configuration.se_handler_count != 0
        )

    @property
    def checksec_state(self) -> PEChecksecData:
        return PEChecksecData(
            self.bin.header.machine,
            self.has_nx,
            self.has_pie,
            self.has_canary,
            self.is_aslr,
            self.has_dynamic_base,
            self.has_high_entropy_va,
            self.has_isolation,
            self.has_seh,
            self.has_safe_seh,
            self.has_guard_cf,
            self.has_force_integrity,
        )
