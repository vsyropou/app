from abc import ABC, abstractmethod


class IDependency(ABC):
    @abstractmethod
    async def method(self) -> bool:
        pass
