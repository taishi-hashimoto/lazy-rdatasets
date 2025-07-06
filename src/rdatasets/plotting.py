"Quicklook utilities."
import math
from collections import Counter
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


def plot_categorical(df: pd.DataFrame, maxcols: int = 10, maxlen: int = 32):
    """Summarize categorical variables by bar plots."""
    cat_cols = df.select_dtypes(include=["bool", "object", "category"]).columns
    ncats_plotted = min(len(cat_cols), maxcols)
    ncats_omitted = max(0, len(cat_cols) - maxcols)
    cat_cols = cat_cols[:ncats_plotted]
    ncats = len(cat_cols)
    if ncats == 0:
        raise ValueError("No categorical data found")
    nrows = max(math.floor(math.sqrt(ncats)-1), 1)
    ncols = max(math.floor(ncats / nrows), 1)
    if nrows*ncols < ncats:
        ncols += 1

    fig, axes = plt.subplots(nrows, ncols, figsize=(max(ncols*3, 8), max(nrows*3, 6)), squeeze=False)
    for ax, col in zip(axes.flat, cat_cols):
        counter = Counter(df[col].astype(str))
        c = ax.bar(range(len(counter)), counter.values(), alpha=0.5)
        ax.bar_label(
            c,
            [text if len(text) <= maxlen else (text[:maxlen-4] + " ...") for text in counter.keys()],
            label_type="center", rotation=90)
        ax.set_title(col)
        ax.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
    for ax in axes.flat[len(cat_cols):]:
        ax.set_visible(False)
    title = "Categorical Variables"
    if ncats_omitted != 0:
        title += f"(first {ncats_plotted} cols, {ncats_omitted} more cols omitted)"
    fig.suptitle(title)
    fig.tight_layout()

    return fig


def plot_missing(df: pd.DataFrame):
    "Visualize missing values."
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.imshow(df.isnull(), aspect='auto', origin="lower", cmap='binary', interpolation='nearest')
    ax.set_xticks(range(len(df.columns)), df.columns)
    ax.tick_params(axis='x', labelrotation=90)
    ax.set_title("Missing Values")
    fig.tight_layout()
    return fig


def plot_numeric(df: pd.DataFrame, maxcols: int = 10):
    """Summarize numeric variables by scatter matrix or histogram."""
    numeric_cols = df.select_dtypes(include="number", exclude="bool").columns.tolist()
    nplotted = min(len(numeric_cols), maxcols)
    nomitted = max(0, len(numeric_cols) - maxcols)
    title = "Numeric Variables"
    if len(numeric_cols) >= 2:
        fig, axes = plt.subplots(nplotted, nplotted, figsize=(nplotted*3, nplotted*3))
        pd.plotting.scatter_matrix(df[numeric_cols[:maxcols]].dropna(), ax=axes, )
        if nomitted != 0:
            title += f"(first {nplotted} cols, {nomitted} more cols omitted)"
        plt.suptitle(title)
        plt.tight_layout()
    elif len(numeric_cols) == 1:
        fig, ax = plt.subplots(1, 1, figsize=(3, 3))
        df[numeric_cols[0]].hist(ax=ax)
        fig.suptitle(title + ": " + numeric_cols[0])
        fig.tight_layout()


def plot_pca(df: pd.DataFrame):
    numeric_cols = df.select_dtypes(include="number", exclude="bool").columns.tolist()
    X = df[numeric_cols].dropna()
    if len(X) > 5:
        X_scaled = StandardScaler().fit_transform(X)
        pca = PCA(n_components=2)
        components = pca.fit_transform(X_scaled)

        plt.figure()
        plt.scatter(components[:, 0], components[:, 1], alpha=0.6)
        plt.title("PCA Projection")
        plt.tight_layout()


def quicklook_dataframe(df: pd.DataFrame, maxcols: int = 10):
    numeric_cols: list[str] = df.select_dtypes(include="number", exclude="bool").columns.tolist()
    categorical_cols: list[str] = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Missing values.
    if df.isnull().sum().sum() > 0:
        plot_missing(df)

    df = df.dropna()

    if len(categorical_cols) > 0:
        plot_categorical(df, maxcols=maxcols)

    if numeric_cols != 0:
        plot_numeric(df, maxcols=maxcols)

    if len(numeric_cols) >= 3:
        plot_pca(df)
