from app.interfaces import IDependency


class _PlaceholderDependency(IDependency):
    async def method(self) -> bool:
        return True


def get_method() -> IDependency:
    return _PlaceholderDependency()
