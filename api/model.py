from datetime import date
from enum import Enum
from typing import Optional
import prefixdate
from pydantic import BaseModel, Field, validator, root_validator
from prefixdate import parse, normalize_date, Precision, DatePrefix


class Author(BaseModel):
    # some source might assign id to authors which can be useful to disambiguate
    id: Optional[str]
    firstname: Optional[str]
    lastname: Optional[str]
    fullname: str
    institution: Optional[str]

    @root_validator(pre=True)
    def fullname_from_firstname_lastname(cls, values):
        if 'fullname' in values and values["fullname"] != "":
            return values
        elif 'lastname' in values:
            values["fullname"] = (
                f"{values['firstname']} " if 'firstname' in values else '') + values['lastname']
            return values
        else:
            raise ValueError("fullname or lastname is mandatory")


class Journal(BaseModel):
    # some source might assign id to authors which can be useful to disambiguate
    id: Optional[str]
    name: str
    editor: Optional[str]


class Paper(BaseModel):
    """
    Paper objects store paper information
    """
    id: str
    title: str
    date: Optional[DatePrefix] = Field(
        title='date',
        description='publication date as YYYY, YYYY-MM or YYYY-MM-DD',
        # regex=r"\d{4}(-\d{2}(-\d{2})?)?"
    )
    authors: Optional[list[Author]] = Field(label="Author")
    keywords: Optional[list[str]]
    abstract: Optional[str]
    journal: Optional[Journal]

    @validator('date', pre=True)
    def year_validation(cls, v):
        date = prefixdate.parse(v)
        if not date:
            raise ValueError(f'{v} Date format invalid')
        else:
            return date

    class Config:
        title = 'Research Paper'
        arbitrary_types_allowed = True
        extra = 'allow'
        json_encoders = {
            DatePrefix: lambda d: d.text
        }


# this is equivalent to json.dumps(MainModel.schema(), indent=2):
# print(Paper.schema_json(indent=2))
if __name__ == "__main__":
    paper = {
        "id": "lpoip",
        "date": "2002-05",
        "title": "aozpeizapeoi",
        "authors": [{"lastname": "Girard"}],
        "extrafield": "oiuoiu"}
    paper = {
        "id": "arXiv:2109.09709",
        "title": "Information Dynamics and The Arrow of Time",
        "date": "2021-09-16",
        "authors": [
            {
                "fullname": "Aram Ebtekar"
            }
        ],
        "keywords": [
            "cond-mat.stat-mech",
            "cs.IT",
            "nlin.CG"
        ],
        "extrafield": 5,
        "abstract": "Time appears to pass irreversibly. In light of CPT symmetry, the Universe's initial condition is thought to be somehow responsible. We propose a model, the stochastic partitioned cellular automaton (SPCA), in which to study the mechanisms and consequences of emergent irreversibility. While their most natural definition is probabilistic, we show that SPCA dynamics can be made deterministic and reversible, by attaching randomly initialized degrees of freedom. This property motivates analogies to classical field theories. We develop the foundations of non-equilibrium statistical mechanics on SPCAs. Of particular interest are the second law of thermodynamics, and a mutual information law which proves fundamental in non-equilibrium settings. We believe that studying the dynamics of information on SPCAs will yield insights on foundational topics in computer engineering, the sciences, and the philosophy of mind. As evidence of this, we discuss several such applications, including an extension of Landauer's principle, and sketch a physical justification of the causal decision theory that underlies the so-called psychological arrow of time."

    }

    Paper.validate(paper)
    o = Paper.parse_obj(paper)
    print(o.date, o.date.precision, o.extrafield)
    print(o.authors)
