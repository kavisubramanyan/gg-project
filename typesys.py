"""
Schema from lecture 3 slides:

(Award-Ceremony
    Name (Golden Globes)
    Year (year) [+ type constraints]
    Host (host) [+ type constraints]
    Awards (
        Award (
            Award-name (award-name) [+ type constraints]
            Presenters (
                {p1, p2}
            ) [+ type constraints]
            Nominees (
                {n1, n2, n3, …}
            ) [+ type constraints]
            Winner (
                winner
            ) [+ type, relational constraints]
            … )
        Award ( …
        …
    )
)

"""

from dataclasses import dataclass, field
from typing import List, Type, Optional

class Entity:
    def __init__(self, id: int, name: str) -> None:
        self.id = id
        self.name = name

    def __str__(self):
        return self.name

class Person(Entity):
    pass

class Film(Entity):
    pass


@dataclass
class Award:
    awardName: str
    presenters: List[Person] = field(default_factory=list)
    nominees: List[Entity] = field(default_factory=list)
    winner: Optional[Entity] = None

    _type: Optional[Type[Entity]] = field(default=None, init=False, repr=False)

    def _type_check(self, e: Entity) -> None:
        if type(e) is not self._type:
            raise TypeError(f"Award is of type {self._type.__name__}\n Arg is of type: {type(e).__name__}")

    def add_presenter(self, p: Person) -> None:
        if not isinstance(p, Person):
            raise TypeError("Presenter must be a person")
        self.presenters.append(p)

    def add_nominee(self, e: Entity) -> None:
        if self._type is None:
            self._type = type(e)

        self._type_check(e)

        self.nominees.append(e)

    def set_winner(self, e: Entity) -> None:
        if self._type is None:
            self._type = type(e)
        
        self._type_check(e)

        noms = [n.id for n in self.nominees]

        if e.id not in noms:
            raise ValueError("Winner must be a nominee")
        
        self.winner = e

    def __str__(self) -> str:
        presenters = ", ".join(str(p) for p in self.presenters)
        nominees = ", ".join(str(e) for e in self.nominees)
        winner = str(self.winner) if self.winner else ""

        return (
            "\t\tAward (\n"
            f"\t\t\tAward-Name ({self.awardName})\n"
            f"\t\t\tPresenters (\n"
            f"\t\t\t\t{presenters}\n"
            f"\t\t\t)\n"
            f"\t\t\tNominees (\n"
            f"\t\t\t\t{nominees}\n"
            f"\t\t\t)\n"
            f"\t\t\tWinner ({winner})\n"
            f"\t\t)"
        )



@dataclass
class AwardCeremony:

    name: Optional[str] = None
    year: Optional[int] = None
    host: Optional[Person] = None
    awards: List[Award] = field(default_factory=list)

    def set_name(self, name: str) -> None:
        if not isinstance(name, str):
            raise TypeError("Award name must be a string")
        self.name = name
    
    def set_year(self, year: int) -> None:
        if not isinstance(year, int):
            raise TypeError("Year must be an int")
        self.year = year
    
    def set_host(self, p: Person) -> None:
        if not isinstance(p, Person):
            raise TypeError("Host must be a person")
        self.host = p
    
    def award_exists(self, name: str) -> bool:
        return any(a.awardName == name for a in self.awards)
    
    def get_award(self, name: str) -> Award:
        for a in self.awards:
            if a.awardName == name:
                return a
        
        raise ValueError(f"Award(f{name}) does not exist")

    def add_award(self, *args, **kwargs) -> Award:
        award = Award(*args, **kwargs)

        if self.award_exists(award.awardName):
            raise ValueError(f"Award(f{award.awardName}) already exists")

        self.awards.append(award)
        return award
    
    def __str__(self) -> str:
        host = str(self.host) if self.host else ""
        awards = "\n".join(str(a) for a in self.awards)

        return (
            "(Award-Ceremony\n"
            f"\tName ({self.name})\n"
            f"\tYear ({self.year})\n"
            f"\tHost ({host})\n"
            "\tAwards (\n"
            f"{awards}\n"
            "\t)\n"
            ")"
        )




if __name__ == "__main__":

    host = Person(1, "John Doe")
    actor = Person(2, "Some Actor")
    film = Film(3, "Some Film")

    ceremony = AwardCeremony("Golden Globes", 2025, host=host)

    award1 = ceremony.add_award("Best Actor")
    award1.add_presenter(host)
    award1.add_nominee(actor)
    award1.set_winner(actor)

    award2 = ceremony.add_award(
        awardName="Best Picture", 
        presenters=[host], 
        nominees=[film],
        winner=film
    )

    print(ceremony)
