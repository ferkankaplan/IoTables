from fastapi import Request


def tenant_root_domains_from_request(request: Request) -> list[str]:
    settings = getattr(request.app.state, "settings", None)
    domains = getattr(settings, "tenant_root_domains", ["iotables.net"])
    return [domain.strip().lower().removeprefix(".") for domain in domains if domain.strip()]


def tenant_subdomain_from_request(request: Request) -> str | None:
    explicit = request.headers.get("X-Tenant-Subdomain")
    if explicit and explicit.strip():
        return explicit.strip().lower()

    host = request.headers.get("host", "").split(":", maxsplit=1)[0].lower()
    for root_domain in tenant_root_domains_from_request(request):
        suffix = f".{root_domain}"
        if host.endswith(suffix) and host != f"platform{suffix}":
            return host.removesuffix(suffix)
    return None
