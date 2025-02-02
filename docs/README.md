# DNSSEC KSK Management Tools - Documentation

The following documents are contained in this sub-directory:

[User Documentation:](usage.md) Describes how to execute each command (i.e. KSR Signer; KSR Received; Keymaster; Trust Anchor Exporter; SHA-256 PGP Word calculator) on the command line.

[Test Documentation:](aep-keyper-test.md) Describes how to test the KSR Signer using the AEP Keyper HSM.

[Assurance Cases:](assurance-cases.md) Documents the security claims about the system software and shows they are valid using a Claims-Arguments-Evidence notation.

[Architectural Design and Functional Specification:](design-specifications.md)
Describes the high-level architectural design of the KSR Signer software, describing the security domains and functions maintained by the software.

[Test Framework:](test.md) Describes the scope and method for unit testing.

## Source Code Review

The kskm-0.0.1 source code audit has been performed by No Hats Corporation. 

- No Hats Corporation's audit report is available at [NoHatsAudit-KSKM-Tools-v1.01.pdf](./reports/NoHatsAudit-KSKM-Tools-v1.01.pdf)
- The audit report's PGP signature is available at [NoHatsAudit-KSKM-Tools-v1.01.sig](./reports/NoHatsAudit-KSKM-Tools-v1.01.sig)