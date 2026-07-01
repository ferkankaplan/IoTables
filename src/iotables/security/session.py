from iotables.security.context import ActorContext


class NullSessionResolver:
    async def resolve(self, session_token: str) -> ActorContext | None:
        return None
