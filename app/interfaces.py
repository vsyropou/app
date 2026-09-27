from abc import ABC, abstractmethod


class IDependency(ABC):
    @abstractmethod
    async def method() -> bool:
        pass
