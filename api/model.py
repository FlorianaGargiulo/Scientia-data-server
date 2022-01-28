from __future__ import annotations

from datetime import date
from enum import Enum
import pathlib
from tokenize import Number
from typing import Optional
from flask import current_app
import prefixdate
from pydantic import AnyUrl, BaseModel, Field, validator, root_validator
from prefixdate import parse, normalize_date, Precision, DatePrefix
from pydantic.types import Json
from pathlib import Path

from pydantic.utils import path_type
from datetime import datetime
import os


class IndexationReport(BaseModel):
    """
    Indexation task report
    """
    date: datetime
    nb_document_inserted: int
    nb_citations_inserted: Optional[int]
    validation_errors: Optional[list[str]]


class PaperDataSet(BaseModel):
    """
    Paper Data Set configuration
    """
    corpus: str
    source: str
    papers_filepath: str
    basePath: Optional[str]
    nb_papers: Optional[int]
    citations_filepath: Optional[str]
    elasticsearch_settings: Optional[dict]
    elasticsearch_mappings: Optional[dict]
    indexation_reports: Optional[list[IndexationReport]]

    @root_validator()
    def validate_filepaths(cls, values):

        def validate_datafilepath(field):
            # common validation method for papers and citation data filepath
            pathToData = Path(values[field])
            # checking absolute/relative path
            newAbsolutePath = None
            if not pathToData.is_absolute() and "basePath" in values and values['basePath']:
                # make path absolute
                newAbsolutePath = os.path.join(
                    values['basePath'], values[field])
                pathToData = Path(newAbsolutePath)

            # check existence and type
            assert path_type(pathToData) in [
                'file', 'symlink'], 'papers_filepath must point to a file'
            # store the absolute path
            if newAbsolutePath:
                values[field] = newAbsolutePath

        if values["basePath"]:
            assert path_type(Path(values["basePath"])) == 'directory'
        validate_datafilepath("papers_filepath")
        if values['citations_filepath']:
            validate_datafilepath("citations_filepath")

        return values


class Affiliation(BaseModel):
    id: Optional[str]
    name: str
    homepage: Optional[AnyUrl]

    class Config:
        extra = 'allow'


class Author(BaseModel):
    """
    Academic Papers's author metadata object
    """

    # some source might assign id to authors which can be useful to disambiguate
    id: Optional[str]
    firstname: Optional[str]
    lastname: Optional[str]
    fullname: str
    institution: Optional[Affiliation]
    queryLevel: Optional[str]

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
    """
    Academic Journal metadata object
    """
    # some source might assign id to authors which can be useful to disambiguate
    id: Optional[str]
    name: str
    publisher: Optional[str]
    ISSN: Optional[str]


class Paper(BaseModel):
    """
    Academic Paper metadata object
    """
    id: Optional[str]
    title: Optional[str]
    date: Optional[DatePrefix] = Field(
        title='date',
        description='publication date as YYYY, YYYY-MM or YYYY-MM-DD',
        # regex=r"\d{4}(-\d{2}(-\d{2})?)?"
    )
    authors: Optional[list[Author]] = Field(label="Author")
    keywords: Optional[list[str]]
    abstract: Optional[str]
    journal: Optional[Journal]
    publisher: Optional[str]
    doi: Optional[str]

    @validator('date', pre=True)
    def date_validation(cls, v):
        date = prefixdate.parse(v)
        if not date:
            raise ValueError(f'{v} Date format invalid')
        else:
            return date

    def to_elasticsearch(self):
        document = self.dict(exclude_none=True)
        if self.date:
            precision = None
            if self.date.precision in [Precision.DAY, Precision.HOUR, Precision.MINUTE, Precision.FULL]:
                precision = "day"
            if self.date.precision == Precision.MONTH:
                precision = "month"
            if self.date.precision == Precision.YEAR:
                precision = "year"

            if precision:
                document["date"] = {
                    "date": self.date.dt, "precision": precision}
        return document

    @classmethod
    def from_elasticsearch(cls, source_obj: dict) -> Paper:

        if "date" in source_obj:
            precision = None
            if source_obj['date']['precision'] == "day":
                precision = Precision.DAY
            if source_obj['date']['precision'] == "month":
                precision = Precision.MONTH
            if source_obj['date']['precision'] == "year":
                precision = Precision.YEAR

            return Paper.parse_obj(source_obj | {'date': prefixdate.DatePrefix(source_obj['date']['date'], precision)})
        else:
            return Paper.parse_obj(source_obj)

    class Config:
        title = 'Research Paper'
        arbitrary_types_allowed = True
        extra = 'allow'
        json_encoders = {
            DatePrefix: lambda d: d.text
        }


class Citation(BaseModel):
    citing: str
    cited: str
