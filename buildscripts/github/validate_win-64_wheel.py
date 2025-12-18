import lief
import pathlib

for path in pathlib.Path(".").rglob("**/*.dll"):
    print("path", path)
    dll = lief.PE.parse(str(path))

    if path.name.lower().startswith("msvcp140"):
        continue

    if hasattr(dll, "delay_imports"):
        delay_imports = {x.name for x in dll.delay_imports}
        print("Delay imports:", delay_imports)
        expected_delay_imports = {"SHELL32.dll", "ole32.dll"}
        assert (
            delay_imports == expected_delay_imports
        ), f"Unexpected delay imports: {delay_imports}"

    imports = {x.name for x in dll.imports}
    print("Regular imports:", imports)
    # Normalize delvewheel-mangled MSVCP import (e.g. msvcp140-<hash>.dll)
    imports = {
        ("MSVCP140.dll" if name.lower().startswith("msvcp140") else name)
        for name in imports
    }
    expected_imports = {
        "ADVAPI32.dll",
        "KERNEL32.dll",
        "MSVCP140.dll",
        "VCRUNTIME140.dll",
        "VCRUNTIME140_1.dll",
        "api-ms-win-crt-convert-l1-1-0.dll",
        "api-ms-win-crt-environment-l1-1-0.dll",
        "api-ms-win-crt-heap-l1-1-0.dll",
        "api-ms-win-crt-locale-l1-1-0.dll",
        "api-ms-win-crt-math-l1-1-0.dll",
        "api-ms-win-crt-runtime-l1-1-0.dll",
        "api-ms-win-crt-stdio-l1-1-0.dll",
        "api-ms-win-crt-string-l1-1-0.dll",
        "api-ms-win-crt-time-l1-1-0.dll",
        "api-ms-win-crt-utility-l1-1-0.dll",
        "ntdll.dll",
    }
    assert imports == expected_imports, (
        f"Unexpected imports: {imports - expected_imports}\n"
        f"Missing imports: {expected_imports - imports}"
    )
