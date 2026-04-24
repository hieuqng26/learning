#from distutils.filelist import FileList
#from msilib.schema import File
import os
import pandas as pd
import numpy as np
import concurrent.futures
import cProfile
def clean_str_columns(df):
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
    return df

# return an array of dataframes
#def readData(filename, mode = "r", outputText = False, removeHeader = False):
#    extension = os.path.splitext(filename)[1][1:].upper()
#    if extension == "XLSX":
#        dfs = []
#        # detect empty rows
#        entire_sheet = pd.read_excel(filename, header=None)
#        nonEmptyCellsPerRow = (~entire_sheet.isnull()).sum(axis=1).values
#        emptyRowIndices = np.where(nonEmptyCellsPerRow == 0)[0]
#        # first table
#        firstDf = pd.read_excel(filename, header=0, nrows=emptyRowIndices[0]-1 if np.any(emptyRowIndices) else None) # -1 for data values because one row is used for header
#        # truncate trailing na columns\
#        firstDf = firstDf.loc[:, ~firstDf.columns.str.match("Unnamed")]
#        #nonEmptyColumns = (~firstDf.isnull()).sum(axis=0).values
#        #lastNonEmptyColumIndex = np.max(np.nonzero(nonEmptyColumns))
#        ##lastNonEmptyColumNameIndex = np.max(np.nonzero(~firstDf.Columns.isnull()))
#        #if lastNonEmptyColumIndex < len(firstDf.columns):
#        #    firstDf = firstDf.drop(firstDf.columns[(lastNonEmptyColumIndex+1):], axis=1)
#        firstDf = clean_str_columns(firstDf)
#        dfs.append(firstDf)
#        # subsequent tables
#        for i in range(len(emptyRowIndices)):
#            df = pd.read_excel(filename, skiprows=range(emptyRowIndices[i]+1), nrows=None if i == len(emptyRowIndices)-1 else emptyRowIndices[i+1]-emptyRowIndices[i]-1-1) # -1 for data values because one row is used for header, another -1 is to exclude the final empty row
#            # truncate trailing na columns
#            df = df.loc[:, ~df.columns.str.match("Unnamed")]
#            #nonEmptyColumns = (~df.isnull()).sum(axis=0).values
#            #lastNonEmptyColumIndex = np.max(np.nonzero(nonEmptyColumns))
#            #if lastNonEmptyColumIndex < len(df.columns):
#            #    df = df.drop(df.columns[(lastNonEmptyColumIndex+1):], axis=1)
#            df = clean_str_columns(df)
#            dfs.append(df)

#        if not outputText:
#            return dfs
#        else:
#            raise NotImplementedError();
#            texts = [df.to_csv(header = not removeHeader, index = False) for df in dfs]
#            return texts
#    else:
#        raise NotImplementedError();
#        if not outputText:
#            return pd.read_csv(filename, header = None, index = None)
#        else:
#            return open(filename, mode).read()

#    return None



#def readData(filename, mode="r", outputText=False, removeHeader=False):
#    extension = os.path.splitext(filename)[1][1:].upper()
#    if extension == "XLSX":
#        dfs = []
#        entire_sheet =  pd.io.excel.read_excel(filename, header=None)
#        nonEmptyCellsPerRow = (~entire_sheet.isnull()).sum(axis=1).values
#        emptyRowIndices = np.where(nonEmptyCellsPerRow == 0)[0]
#        start_row = 0
#        for end_row in emptyRowIndices:
#            if end_row > start_row:
#                table = entire_sheet.iloc[start_row:end_row, :].copy()  # Create a new DataFrame with .copy()
#                table.dropna(axis=1, how='all', inplace=True)
#                table = table.dropna(axis=0, how='all')
#                if not removeHeader:
#                    table_header = table.iloc[0]
#                    table = table[1:]
#                    table.columns = table_header
#                table.reset_index(drop=True, inplace=True)
#                table = clean_str_columns(table)
#                dfs.append(table)
#            start_row = end_row + 1
#        if start_row < len(entire_sheet):
#            table = entire_sheet.iloc[start_row:, :].copy()
#            table.dropna(axis=1, how='all', inplace=True)
#            table = table.dropna(axis=0, how='all')
#            if not removeHeader:
#                table_header = table.iloc[0]
#                table = table[1:]
#                table.columns = table_header
#            table.reset_index(drop=True, inplace=True)
#            table = clean_str_columns(table)
#            dfs.append(table)
#        if not outputText:
#            return dfs
#        else:
#            # Output text functionality 
#            raise NotImplementedError()
#    else:
#        # Handling for non-XLSC files 
#        raise NotImplementedError();
#    return None
        



#def readData(filename, mode="r", output_text=False, remove_header=False):
#   extension = os.path.splitext(filename)[1][1:].upper()
#   if extension == "XLSX":
#       dfs = []
#       entire_sheet = pd.read_excel(filename, header=None)
#       def clean_and_append_table(start, end):
#           table = entire_sheet.iloc[start:end, :].copy()
#           table.dropna(axis=1, how='all', inplace=True)
#           table = table.dropna(axis=0, how='all')
#           if not remove_header:
#               table_header = table.iloc[0]
#               table = table[1:]
#               table.columns = table_header
#           table.reset_index(drop=True, inplace=True)
#           table = clean_str_columns(table) 
#           dfs.append(table)
#       start_row = 0
#       for end_row in np.append(np.where(entire_sheet.isnull().all(axis=1))[0], len(entire_sheet)):
#           if end_row > start_row:
#               clean_and_append_table(start_row, end_row)
#           start_row = end_row + 1
#       if not output_text:
#           return dfs
#       else:
#           # Output text functionality 
#           raise NotImplementedError

#   else:
#       # Handling for non-XLSX files 
#       raise NotImplementedError

def readData(filename, mode="r", outputText=False, removeHeader=False):
    extension = os.path.splitext(filename)[1][1:].upper()

    if extension == "XLSX":
        entire_sheet = pd.read_excel(filename, header=None, engine='openpyxl')

        non_empty_cells_per_row = (~entire_sheet.isnull()).sum(axis=1).values
        empty_row_indices = np.where(non_empty_cells_per_row == 0)[0]

        dfs = []
        start_row = 0

        for end_row in empty_row_indices:
            if end_row > start_row:
                table = entire_sheet.iloc[start_row:end_row, :].copy()
                table.dropna(axis=1, how='all', inplace=True)
                table = table.dropna(axis=0, how='all')
                if not removeHeader:
                    table_header = table.iloc[0]
                    table = table[1:]
                    table.columns = table_header
                table.reset_index(drop=True, inplace=True)
                table = clean_str_columns(table)
                dfs.append(table)
            start_row = end_row + 1

        if start_row < len(entire_sheet):
            table = entire_sheet.iloc[start_row:, :].copy()
            table.dropna(axis=1, how='all', inplace=True)
            table = table.dropna(axis=0, how='all')
            if not removeHeader:
                table_header = table.iloc[0]
                table = table[1:]
                table.columns = table_header
            table.reset_index(drop=True, inplace=True)
            table = clean_str_columns(table)
            dfs.append(table)

        if not outputText:
            return dfs
        else:
            # Output text functionality
            raise NotImplementedError()
    else:
        # Handling for non-XLSX files
        raise NotImplementedError()

    return None

#def readDirectory(path, mode = "r", outputText = False, removeHeader = False):
#    fileList = os.scandir(path)
#    fileDataFrameDictionary = {}
#    for f in fileList:
#        if not f.is_dir() and not f.name.startswith("~$"): # skipping directories and windows temporary files
#            fileDataFrameDictionary[f.name] = readData(path + "/" + f.name, mode, outputText, removeHeader)
#    return fileDataFrameDictionary

#def readDirectory(path, mode="r", outputText=False, removeHeader=False):
#   # Using a dictionary comprehension for efficiency
#   return {
#       f.name: readData(os.path.join(path, f.name), mode, outputText, removeHeader)
#       for f in os.scandir(path)
#       if f.is_file() and not f.name.startswith("~$")
#   }

#def readDirectory(path, mode="r", outputText=False, removeHeader=False):
#    def clean_and_append_table(entire_sheet, dfs, start, end):
#        table = entire_sheet.iloc[start:end, :].copy()
#        table.dropna(axis=1, how='all', inplace=True)
#        table = table.dropna(axis=0, how='all')
#        if not removeHeader:
#            table_header = table.iloc[0]
#            table = table[1:]
#            table.columns = table_header
#        table.reset_index(drop=True, inplace=True)
#        dfs.append(table)

#    result = {}

#    for f in os.scandir(path):
#        if f.is_file() and not f.name.startswith("~$"):
#            filename = os.path.join(path, f.name)
#            extension = os.path.splitext(filename)[1][1:].upper()
#            if extension == "XLSX":
#                dfs = []

#                entire_sheet = pd.io.excel.read_excel(filename, header=None)
#                start_row = 0
#                for end_row in np.append(np.where(entire_sheet.isnull().all(axis=1))[0], len(entire_sheet)):
#                    if end_row > start_row:
#                        clean_and_append_table(entire_sheet, dfs, start_row, end_row)
#                    start_row = end_row + 1
#                if not outputText:
#                    result[f.name] = dfs
#                else:
#                    # Add code to handle outputText functionality
#                    pass
#            else:
#                # Handling for non-XLSX files
#                raise NotImplementedError
#    return (result)

def clean_and_append_table(entire_sheet, dfs, start, end, removeHeader):
    table = entire_sheet.iloc[start:end, :].copy()
    table.dropna(axis=1, how='all', inplace=True)
    table = table.dropna(axis=0, how='all')
    if not removeHeader:
        table_header = table.iloc[0]
        table = table[1:]
        table.columns = table_header
    table.reset_index(drop=True, inplace=True)
    dfs.append(table)

def readDirectory(path, mode="r", outputText=False, removeHeader=False):
    result = {}

    for f in os.scandir(path):
        if f.is_file() and not f.name.startswith("~$"):
            filename = os.path.join(path, f.name)
            extension = os.path.splitext(filename)[1][1:].upper()

            if extension == "XLSX":
                try:
                    with pd.ExcelFile(filename) as xls:
                        dfs = []
                        entire_sheet = pd.read_excel(xls, header=None)
                        
                        start_row = 0
                        end_rows = [end_row for end_row in np.where(entire_sheet.isnull().all(axis=1))[0]]
                        end_rows.append(len(entire_sheet))

                        for end_row in end_rows:
                            if end_row > start_row:
                                clean_and_append_table(entire_sheet, dfs, start_row, end_row, removeHeader)
                            start_row = end_row + 1

                        if not outputText:
                            result[f.name] = dfs
                        else:
                            # Add code to handle outputText functionality
                            pass

                except pd.errors.EmptyDataError:
                    # Handle the case where the Excel file is empty
                    pass

    return result

#a = readDirectory("../QLD-Python-Test/P202310/pricingInput.20210930.USD")
#print(a)



#def readDictionary(filename, mode = "r", removeHeader = False):
#    df = readData(filename, mode, removeHeader)
#    return df.set_index("Key").to_dict()["Value"]

#def removeLastSlash(path):
#    if path.endswith("/"):
#        path = path[:-1]
#    return path

def removeLastSlash(path):
    return path.rstrip('/')

def writeData(dataframe, filename, sheetname = "Sheet1"):
    #return dataframe.to_excel(filename, sheet_name = sheetname)
    return dataframe.to_csv(filename, sheet_name = sheetname)
