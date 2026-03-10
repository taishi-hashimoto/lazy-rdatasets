"""Convenience interface of Reatasets for lazy data scientists.

Rdatasets:
  https://vincentarelbundock.github.io/Rdatasets/index.html
"""

import random
from io import BytesIO
import requests_cache
import pandas as pd
from os.path import expanduser
from IPython.display import HTML, display
from .plotting import quicklook_dataframe


META_URL = "https://vincentarelbundock.github.io/Rdatasets/datasets.csv"
"Metadata of Rdatasets."

CACHE_PATH = expanduser("~/.pda/rdatasets.sqlite3")
"Path to the cache file."


class LazyRdatasets:
    "Convenience interface of Reatasets for lazy data scientists."

    class Dataset:
        "Single dataset, i.e., a csv file."

        def __init__(self, parent: "LazyRdatasets", index: int):
            self.parent = parent
            self.index = index
            with self.parent.session:
                self.doc = self.parent.session.get(self.doc_url).text
                self.data = pd.read_csv(
                    BytesIO(self.parent.session.get(self.csv_url).content),
                    encoding_errors="ignore",
                )

        @property
        def catalog(self) -> pd.DataFrame:
            return self.parent.catalog

        @property
        def info(self) -> pd.DataFrame:
            return self.catalog.loc[self.index]

        @property
        def package(self) -> str:
            "Package name."
            return self.info["Package"]

        @property
        def item(self) -> str:
            "Item name."
            return self.info["Item"]

        @property
        def title(self) -> str:
            "Title of the dataset."
            return self.info["Title"]

        @property
        def csv_url(self) -> str:
            "URL of the CSV file."
            return self.info["CSV"]

        @property
        def doc_url(self) -> str:
            "URL of the documentation."
            return self.info["Doc"]

        @property
        def shape(self) -> tuple[int, int]:
            "Shape of the dataset (nrows, ncols), or (nsamples, nparameters/nfeatures)"
            return self.data.shape

        @property
        def n_binary(self) -> int:
            "The number of binary variables (yes/no, 0/1, ...)"
            return self.info["n_binary"]

        @property
        def n_character(self) -> int:
            "The number of character variables."
            return self.info["n_character"]

        @property
        def n_factor(self) -> int:
            "The number of factor variables."
            return self.info["n_factor"]

        @property
        def n_logical(self) -> int:
            "The number of logical variables (True/False)."
            return self.info["n_logical"]

        @property
        def n_numeric(self) -> int:
            "The number of numeric variables."
            return self.info["n_numeric"]

        def quicklook(self, pmax: int = 10):
            quicklook_dataframe(self.data, maxcols=pmax)

        def __str__(self):
            return "\n".join(
                [
                    f"#️⃣ Index  : {self.index}",
                    f"📦 Package: {self.package}",
                    f"📄 Item   : {self.item}",
                    f"📚 Title  : {self.title}",
                    f"📐 Shape  : {self.shape}",
                    f"  ⚖️ Binary   : {self.n_binary}",
                    f"  🔤 Character: {self.n_character}",
                    f"  🧮 Factor   : {self.n_factor}",
                    f"  🔘 Logical  : {self.n_logical}",
                    f"  🔢 Numeric  : {self.n_numeric}",
                    f"🔗 CSV: {self.csv_url}",
                    f"🔗 Doc: {self.doc_url}",
                ]
            )

        def __repr__(self):
            return self.__str__()

        def show(self):
            display(HTML(self.doc))
            display(self.data)

    def __init__(self, url=META_URL, catalog=None):
        self.session = requests_cache.CachedSession(
            CACHE_PATH,
        )
        if catalog is None:
            with self.session:
                catalog = pd.read_csv(
                    BytesIO(self.session.get(url).content), encoding_errors="ignore"
                )
        self.catalog = catalog

    @staticmethod
    def find(*args, **kwargs) -> "LazyRdatasets":
        """Find datasets based on conditions.

        Parameters
        ==========
        args, kwargs: passed to `filter()`

        Returns
        =======
        Rdatasets
            Filtered RDatasets object.
        """
        return LazyRdatasets().filter(*args, **kwargs)

    def filter(
        self,
        package: str | None = None,
        item: str | None = None,
        title: str | None = None,
        minrows: int | None = None,
        maxrows: int | None = None,
        mincols: int | None = None,
        maxcols: int | None = None,
        nmin=None,
        nmax=None,
        pmin=None,
        pmax=None,
        binary=None,
        character=None,
        factor=None,
        logical=None,
        numeric=None,
        categorical=None,
        pred=None,
        exact: bool = False,
    ) -> "LazyRdatasets":
        """Filter datasets based on conditions.

        Parameters
        ==========
        package: str
            A text or pattern to be searched from the package name of each dataset.
            Cases are ignored.
        item: str
            A text or pattern to be searched from the item name of each dataset.
            Cases are ignored.
        title: str
            A text or pattern to be searched from the title of each dataset.
            Cases are ignored.
        nmin, nmax: int
            The minimum and maximum numbers of samples, i.e., rows.
        pmin, pmax: int
            The minimum and maximum numbers of parameters, i.e., columns.
        binary, character, factor, logical, numeric: bool
            If specified, datasets that only contains (True) or does not
            contain (False) the specified type are returned.
            Types are based on the document of each dataset.
        categorical: bool
            Composite data type: binary + character + factor + logical.
            Maybe the same as `numeric=False`...
        pred: a functor that takes one argument and returns indices
            Custom selector predicate.
            The argument is RDatasets catalog in DataFrame.

        Returns
        =======
        RDatasets
            Filtered RDatasets object.
        """
        found = self.catalog

        # Text comparison.

        if exact:
            if package is not None:
                found = found[found.Package == package]
            if item is not None:
                found = found[found.Item == item]
            if title is not None:
                found = found[found.Title == title]
        else:
            if package is not None:
                found = found[found.Package.str.lower().str.contains(package.lower())]
            if item is not None:
                found = found[found.Item.str.lower().str.contains(item.lower())]
            if title is not None:
                found = found[found.Title.str.lower().str.contains(title.lower())]

        # Custom selector function.

        if pred is not None:
            found = found[pred(found)]

        # Categorical data: binary, character, factor, logical.

        if categorical is not None:
            is_categorical = (
                (found.n_binary > 0)
                | (found.n_character > 0)
                | (found.n_factor > 0)
                | (found.n_logical > 0)
            )
            if categorical:
                found = found[is_categorical]
            else:
                found = found[~is_categorical]

        # Data types based on documents.

        for key in ["binary", "character", "factor", "logical", "numeric"]:
            val = locals()[key]
            if val is not None:
                is_key = found[f"n_{key}"] > 0
                if val:
                    found = found[is_key]
                else:
                    found = found[~is_key]

        # The sizes of the datasets.

        if nmin is None and minrows is not None:
            nmin = minrows
        if nmax is None and maxrows is not None:
            nmax = maxrows
        if pmin is None and mincols is not None:
            pmin = mincols
        if pmax is None and maxcols is not None:
            pmax = maxcols

        if nmin is not None:
            found = found[(found.Rows >= nmin)]
        if pmin is not None:
            found = found[(found.Cols >= pmin)]
        if nmax is not None:
            found = found[(found.Rows <= nmax)]
        if pmax is not None:
            found = found[(found.Cols <= pmax)]

        return LazyRdatasets(catalog=found)

    def sample(self) -> "LazyRdatasets.Dataset":
        "Randomly choose a dataset from the catalog and load it."
        index = random.choice(self.catalog.index)
        return self[index]

    @property
    def first(self) -> "LazyRdatasets.Dataset":
        "Get the first dataset in the catalog."
        return self.at(0)

    def __getitem__(self, index) -> "LazyRdatasets.Dataset":
        "Get dataset from index number (loc)."
        return self.Dataset(self, index)

    def at(self, i) -> "LazyRdatasets.Dataset":
        "Get dataset from its position (iloc)."
        return self.Dataset(self, self.catalog.index[i])

    def __repr__(self):
        return f"Rdatasets(len={len(self.catalog)})"

    def _repr_html_(self):
        return self.catalog._repr_html_()
