import numpy as np
import math
def isclose(a, b, rel_tol = np.finfo(float).eps):
    return math.isclose(a, b, rel_tol = rel_tol)

def QLD_DATAFRAME_CLOSE(df, dfExpected, reltolfloat):
    nrows = len(df)
    nrowse = len(dfExpected)
    if nrows != nrowse:
        raise ValueError("Row size (" + nrows + ") of result is different from expected result (" + nrowse + ").")
    else:
        dfCols = df.columns
        dfColse = dfExpected.columns
        ncols = len(dfCols)
        ncolse = len(dfExpected.columns)
        if ncols != ncolse:
            raise ValueError("Column size (" + ncols + ") of result is different from expected result (" + ncolse + ").")
        else:
            if (dfCols != dfColse).all():
                for i in range(ncols):
                    if dfCols[i] != dfColse[i]:
                        raise ValueError("Column #" + str(i) + " (" + dfCols[i] + ") of result is different from expected result (" + dfColse[i] + ")")
                raise ValueError("Should not be reached")
            else:
                for j in range(ncols):
                    dfDataCol = df[dfCols[j]]
                    dfDataCole = dfExpected[dfColse[j]]
                    for i in range(nrows):
                        dfValue = dfDataCol[i]
                        dfValuee = dfDataCole[i]

                        if dfValue != dfValuee and not(math.isnan(dfValue) and math.isnan(dfValuee)):
                            if not(isinstance(dfValue, float) and isinstance(dfValuee, float) and isclose(dfValue, dfValuee, reltolfloat)):
                                raise ValueError("Value (" + str(dfValue) + ", type: " + str(type(dfValue)) + ") at [row: " + str(i) + ", col: " + str(j) + "] is different from expected result (" + str(dfValuee) + ", type: " + str(type(dfValuee)) + ").")
    return True


