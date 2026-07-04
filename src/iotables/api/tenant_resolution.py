from fastapi import Request


def tenant_subdomain_from_request(request: Request) -> str | None:
    explicit = request.headers.get("X-Tenant-Subdomain")
    if explicit and explicit.strip():
        return explicit.strip().lower()

    host = request.headers.get("host", "").split(":", maxsplit=1)[0].lower()
    suffix = ".iotables.net"
    if host.endswith(suffix) and host != f"platform{suffix}":
        return host.removesuffix(suffix)
    return None
