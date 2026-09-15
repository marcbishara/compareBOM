import pandas as pd
from tkinter import *
from tkinter import filedialog
from tkinter import simpledialog
from tkinter import messagebox
import os
import re
import traceback

parameter = 'RYSE part number'
description_parameter = 'Description'
curLng = 'EN'
path1 = ''
path2 = ''


# --------------------------------------------------------------------------
# Normalization helpers
# --------------------------------------------------------------------------

def norm_text(value):
    """Loose key/column name: trimmed, internal whitespace collapsed, lower case."""
    if value is None:
        return ''
    text = str(value).replace(' ', ' ')
    return re.sub(r'\s+', ' ', text).strip().lower()


def is_blank(value):
    """True for None, NaN, empty strings and the literal text 'nan'."""
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return str(value).strip().lower() in ('', 'nan', 'none')


def norm_value(value):
    """Comparison form of a cell: blanks collapse to None, numbers compare
    numerically ('1' == '1.0' == 1), text ignores case and extra spaces."""
    if is_blank(value):
        return None
    text = re.sub(r'\s+', ' ', str(value).replace(' ', ' ')).strip()
    try:
        return float(text.replace(',', '')) if re.fullmatch(r'[-+]?[\d,]*\.?\d+', text) else text.lower()
    except ValueError:
        return text.lower()


def display(value):
    """Printable form of a cell; trims whitespace and drops trailing '.0'."""
    if is_blank(value):
        return '(blank)'
    text = str(value).strip()
    match = re.fullmatch(r'([-+]?\d+)\.0+', text)
    return match.group(1) if match else text


def find_column(df, name):
    """Return the real column matching `name`, tolerating case/spacing differences."""
    if name is None or df is None:
        return None
    if name in df.columns:
        return name
    target = norm_text(name)
    if not target:
        return None
    for column in df.columns:
        if norm_text(column) == target:
            return column
    return None


def read_bom(path):
    """Read a BOM CSV as text, with trimmed headers and trimmed cell values.
    The frame index is the line number in the CSV file (the header is line 1),
    so anything reported can be found again in the original file."""
    try:
        df = pd.read_csv(path, sep=',', dtype=str, encoding='utf-8-sig',
                         skip_blank_lines=False)
    except UnicodeDecodeError:
        df = pd.read_csv(path, sep=',', dtype=str, encoding='latin-1',
                         skip_blank_lines=False)
    df.columns = [str(c).replace(' ', ' ').strip() for c in df.columns]
    for column in df.columns:
        df[column] = df[column].map(lambda v: v.replace(' ', ' ').strip() if isinstance(v, str) else v)
    df.index = pd.RangeIndex(start=2, stop=len(df) + 2)
    # Drop lines that are entirely empty; everything else keeps its line number
    keep = [not all(is_blank(v) for v in row) for row in df.itertuples(index=False)]
    return df.loc[keep]


def row_summary(df, row):
    """Every populated field of a row, so an unidentified line can be found
    again in the source CSV."""
    parts = []
    for column in df.columns:
        value = df[column].iat[row]
        if not is_blank(value):
            parts.append('%s: %s' % (column, str(value).strip()))
    return ' | '.join(parts) if parts else '(no data on this line)'


def blank_key_rows(df, key_column):
    """Lines that carry data but no entry in the key column - typically line
    items the factory added to the BOM without a part number."""
    found = []
    for row, value in enumerate(df[key_column]):
        if is_blank(value):
            found.append((df.index[row], row_summary(df, row)))
    return found


class CompareFrame(Frame):

    def __init__(self):
        Frame.__init__(self)
        self.master.title('BOM Compare')
        self.master.rowconfigure(3, weight=1)
        self.master.columnconfigure(3, weight=1)
        self.grid(sticky=W+E+N+S)

        self.button1 = Button(self, text = 'Load "From" file (the old BOM)', command=self.load_file1, width=40)
        self.button1.grid(row=0, column=0, sticky=W)
        self.button5 = Button(self, text = 'Load "To" file (the new BOM)', command=self.load_file2, width=40)
        self.button5.grid(row=0, column=3, sticky=W)

        self.button6 = Button(self, text = 'EN/PL', command=self.chngLanguage, width=0)
        self.button6.grid(row=0, column=1)

        self.button2 = Button(self, text = 'Search key', command=self.search_for, width=25)
        self.button2.grid(row=1, column=0, sticky=E)
        self.button3 = Button(self, text = 'Compare', command=self.compare_files, width=10, padx=10)
        self.button3.grid(row=2, column=1)
        # Add a button to choose a description column
        self.button4 = Button(self, text = 'Description key', command=self.add_description, width=25)
        self.button4.grid(row=1, column=1)
        print("Default search key: " + parameter)
        print("Default description key: " + description_parameter)

    def chngLanguage(self):
        global curLng
        if curLng == 'EN':
            # translate the buttons to polish
            self.button1['text'] = 'Wczytaj plik "Z" (stary BOM)'
            self.button5['text'] = 'Wczytaj plik "Do" (nowy BOM)'
            self.button2['text'] = 'Szukaj po'
            self.button3['text'] = 'Porównaj'
            self.button4['text'] = 'Klucz opisu'
            curLng = 'PL'
        else:
            # translate the buttons to english
            self.button1['text'] = 'Load "From" file (the old BOM)'
            self.button5['text'] = 'Load "To" file (the new BOM)'
            self.button2['text'] = 'Search key'
            self.button3['text'] = 'Compare'
            self.button4['text'] = 'Description key'
            curLng = 'EN'

    def load_file1(self):
        file1_path = filedialog.askopenfilename(filetypes = (("CSV files", "*.csv")
                                                           ,("All files", "*.*") ))
        if not file1_path:
            return
        global path1
        path1 = file1_path
        self.button1['text'] = 'From: ' + os.path.basename(path1)

    def load_file2(self):
        file2_path = filedialog.askopenfilename(filetypes = (("CSV files", "*.csv")
                                                           ,("All files", "*.*") ))
        if not file2_path:
            return
        global path2
        path2 = file2_path
        self.button5['text'] = 'To: ' + os.path.basename(path2)

    def add_description(self):
        answer = simpledialog.askstring('Description key', 'Which column contains the part description?')
        if not answer or not answer.strip():
            return
        global description_parameter
        description_parameter = answer.strip()
        print('Description key: ' + description_parameter)

    def search_for(self):
        answer = simpledialog.askstring('Compare', 'Which column do you want to compare?')
        if not answer or not answer.strip():
            return
        global parameter
        parameter = answer.strip()
        print('Search key: ' + parameter)

    def compare_files(self):
        """Wrapper so an unexpected failure shows a dialog instead of a traceback
        swallowed by the Tk callback."""
        try:
            self.run_compare()
        except Exception as exc:
            traceback.print_exc()
            messagebox.showerror('Compare failed', '%s: %s' % (type(exc).__name__, exc))

    def run_compare(self):
        print(parameter)
        if not path1 or not path2:
            messagebox.showerror('Compare', 'Load both the "From" and the "To" file first.')
            return

        try:
            my_csv_f1 = read_bom(path1)
            my_csv_f2 = read_bom(path2)
        except Exception as exc:
            traceback.print_exc()
            messagebox.showerror('Compare', 'Could not read the CSV files:\n%s' % exc)
            return

        # Locate the key column in each file, tolerating case/spacing differences
        key_f1 = find_column(my_csv_f1, parameter)
        key_f2 = find_column(my_csv_f2, parameter)
        missing_in = [name for name, key in ((os.path.basename(path1), key_f1),
                                             (os.path.basename(path2), key_f2)) if key is None]
        if missing_in:
            messagebox.showerror(
                'Compare',
                'Search key column "%s" was not found in: %s\n\n%s has:\n%s\n\n%s has:\n%s' % (
                    parameter, ', '.join(missing_in),
                    os.path.basename(path1), ', '.join(my_csv_f1.columns),
                    os.path.basename(path2), ', '.join(my_csv_f2.columns)))
            return

        # The description column is optional - note it and carry on without it
        desc_f1 = find_column(my_csv_f1, description_parameter)
        desc_f2 = find_column(my_csv_f2, description_parameter)
        notes = []
        if desc_f1 is None or desc_f2 is None:
            notes.append('NOTE: description column "%s" not found in %s - descriptions omitted.' % (
                description_parameter,
                ' and '.join(n for n, d in ((os.path.basename(path1), desc_f1),
                                            (os.path.basename(path2), desc_f2)) if d is None)))

        path_l1 = os.path.basename(path1)
        path_l2 = os.path.basename(path2)
        bomDiffFileName = 'BOM differences ' + path_l1 + ' to ' + path_l2 + '.txt'

        # Normalized key -> row positions, in file order
        occ_f1 = key_positions(my_csv_f1, key_f1)
        occ_f2 = key_positions(my_csv_f2, key_f2)

        # Only columns present in BOTH files can be compared. Anything else is
        # reported as an added/removed column instead of crashing.
        pairs = []
        only_f1 = []
        for column in my_csv_f1.columns:
            if column in (key_f1, desc_f1):
                continue
            match = find_column(my_csv_f2, column)
            if match is None:
                only_f1.append(column)
            else:
                pairs.append((column, match))
        only_f2 = [c for c in my_csv_f2.columns
                   if c not in (key_f2, desc_f2) and find_column(my_csv_f1, c) is None]
        if only_f1:
            notes.append('Columns only in %s (not compared): %s' % (path_l1, ', '.join(only_f1)))
        if only_f2:
            notes.append('Columns only in %s (not compared): %s' % (path_l2, ', '.join(only_f2)))
        for note in notes:
            print(note)

        with open(bomDiffFileName, 'w', encoding='utf-8') as output:
            output.write('BOM change notification:\n')
            output.write('From: ' + path_l1 + '\n')
            output.write('To: ' + path_l2 + '\n')
            for note in notes:
                output.write(note + '\n')

        # ---- lines with no part number ----------------------------------
        # e.g. line items the factory added to the BOM. They cannot be matched
        # up, so they are listed in full rather than compared.
        for label, df, key_column in ((path_l1, my_csv_f1, key_f1),
                                      (path_l2, my_csv_f2, key_f2)):
            unidentified = blank_key_rows(df, key_column)
            if not unidentified:
                continue
            with open(bomDiffFileName, 'a', encoding='utf-8') as output:
                output.write('\n=====================================================================\n')
                output.write('NO %s in %s (%d line%s, not compared):\n' % (
                    key_column, label, len(unidentified), '' if len(unidentified) == 1 else 's'))
                for line_no, summary in unidentified:
                    print('%s line %d has no %s: %s' % (label, line_no, key_column, summary))
                    output.write('line %d: %s\n' % (line_no, summary))

        # ---- parts that disappeared -------------------------------------
        removed = [key for key in occ_f1 if key not in occ_f2]
        if removed:
            with open(bomDiffFileName, 'a', encoding='utf-8') as output:
                output.write('\n=====================================================================\n')
                output.write('REMOVE from ' + path_l1 + ': ' + '\n')
                for key in removed:
                    row = occ_f1[key][0]
                    label = display(my_csv_f1[key_f1].iat[row])
                    desc = display(my_csv_f1[desc_f1].iat[row]) if desc_f1 else ''
                    print(label + ': ' + desc)
                    output.write(label + ': ' + desc + '\n')

        # ---- parts that appeared ----------------------------------------
        added = [key for key in occ_f2 if key not in occ_f1]
        if added:
            with open(bomDiffFileName, 'a', encoding='utf-8') as output:
                output.write('\n=====================================================================\n')
                output.write('ADD to ' + path_l1 + ': ' + '\n')
                for key in added:
                    row = occ_f2[key][0]
                    label = display(my_csv_f2[key_f2].iat[row])
                    desc = display(my_csv_f2[desc_f2].iat[row]) if desc_f2 else ''
                    print(label + ': ' + desc)
                    output.write(label + ': ' + desc + '\n')

        # ---- parts that moved onto a different number of lines ----------
        # Reported once here, rather than showing up as a bogus change in every
        # column below (column_values() drops the repeats).
        relined = [key for key in occ_f1
                   if key in occ_f2 and len(occ_f1[key]) != len(occ_f2[key])]
        if relined:
            with open(bomDiffFileName, 'a', encoding='utf-8') as output:
                output.write('\n=====================================================================\n')
                output.write('NUMBER OF LINES CHANGED, ' + path_l1 + ' ===> ' + path_l2 + ':\n')
                for key in relined:
                    label = display(my_csv_f1[key_f1].iat[occ_f1[key][0]])
                    n1, n2 = len(occ_f1[key]), len(occ_f2[key])
                    print('%s is on %d line(s), then %d' % (label, n1, n2))
                    output.write('%s: %d line%s ===> %d line%s\n' % (
                        label, n1, '' if n1 == 1 else 's', n2, '' if n2 == 1 else 's'))

        # ---- compare the columns for the parts that are in both files ----
        with open(bomDiffFileName, 'a', encoding='utf-8') as output:
            output.write('\n=====================================================================\n')

        shared = [key for key in occ_f1 if key in occ_f2]
        coumnIndx = 0
        for col_f1, col_f2 in pairs:
            diffs = []
            for key in shared:
                # A part number can legitimately sit on several lines - the same
                # component used in different sub-assemblies. Those lines cannot
                # be paired up one to one: their order differs between the files,
                # so any positional pairing reports imaginary changes. Compare
                # the whole set of values for the part instead, and report only
                # when the sets themselves differ.
                valsF1 = column_values(my_csv_f1, col_f1, occ_f1[key])
                valsF2 = column_values(my_csv_f2, col_f2, occ_f2[key])
                if [compare_value(v) for v in valsF1] == [compare_value(v) for v in valsF2]:
                    continue

                label = display(my_csv_f1[key_f1].iat[occ_f1[key][0]])
                textF1 = ', '.join(display_cell(v) for v in valsF1)
                textF2 = ', '.join(display_cell(v) for v in valsF2)
                print('%s differs for %s: %s ===> %s' % (col_f1, label, textF1, textF2))
                diffs.append((label, textF1, textF2))

            if diffs:
                coumnIndx += 1
                header = col_f1 if col_f1 == col_f2 else '%s ===> %s' % (col_f1, col_f2)
                with open(bomDiffFileName, 'a', encoding='utf-8') as output:
                    output.write('\nMODIFY-' + str(coumnIndx) + ' ' + header + ':\n')
                    output.write(path_l1 + ' ===> ' + path_l2 + '\n')
                    for label, textF1, textF2 in diffs:
                        output.write(label + ': ' + textF1 + ' ===> ' + textF2 + '\n')

        print('Done. If in windows, open the compare file')
        # open the file if on windows
        if os.name == 'nt':
            os.startfile(bomDiffFileName)


DESIGNATOR = re.compile(r'^([A-Za-z]+)(\d+)$')
DESIGNATOR_RANGE = re.compile(r'^([A-Za-z]+)(\d+)-([A-Za-z]*)(\d+)$')


def designator_set(value):
    """The individual reference designators a cell names, or None when the cell
    is not a designator list.

    The same set of parts gets written many ways - 'Q4-5 Q8-10' from Aligni and
    'Q4,Q5,Q8,Q9,Q10' from the factory mean exactly the same thing - so ranges
    are expanded and separators dropped before anything is compared. Any cell
    that is not wholly made of designators (free text in the column, say) gives
    None, and is then compared as plain text exactly as before."""
    if is_blank(value):
        return None
    found = set()
    for token in re.split(r'[,;\s]+', str(value).strip()):
        if not token:
            continue
        single = DESIGNATOR.match(token)
        if single:
            found.add((single.group(1).upper(), int(single.group(2))))
            continue
        spread = DESIGNATOR_RANGE.match(token)
        if not spread:
            return None
        prefix, first, last_prefix, last = spread.groups()
        prefix = prefix.upper()
        # 'C15-16' and 'U1-U3' are both ranges; 'Q4-R5' is not one we understand
        if last_prefix and last_prefix.upper() != prefix:
            return None
        first, last = int(first), int(last)
        if not 0 <= last - first <= 1000:
            return None
        found.update((prefix, number) for number in range(first, last + 1))
    return found or None


def format_designators(designators):
    """Write a designator set out compactly, and the same way for both files:
    sorted, with consecutive numbers collapsed back into ranges so that long
    lists stay as short as the factory writes them."""
    runs = []
    for prefix, number in sorted(designators):
        if runs and runs[-1][0] == prefix and runs[-1][2] == number - 1:
            runs[-1][2] = number
        else:
            runs.append([prefix, number, number])
    return ' '.join('%s%d' % (prefix, first) if first == last
                    else '%s%d-%d' % (prefix, first, last)
                    for prefix, first, last in runs)


def compare_value(value):
    """The form of a cell used to decide whether it changed: a reference
    designator list becomes the designators themselves, so that separators,
    ranges and ordering cannot masquerade as a change. Everything else is
    compared as before."""
    designators = designator_set(value)
    return norm_value(value) if designators is None else sorted(designators)


def display_cell(value):
    """Printable form of a cell being compared. Designator lists are written
    out one way - sorted, space separated - so that the two sides of a report
    line can be read against each other."""
    designators = designator_set(value)
    if designators is None:
        return display(value)
    return format_designators(designators)


def sort_key(value):
    """Order values so both files present them the same way: blanks first, then
    numbers in numeric order, then text alphabetically."""
    comparable = compare_value(value)
    if comparable is None:
        return (0, 0.0, '')
    if isinstance(comparable, float):
        return (1, comparable, '')
    if isinstance(comparable, list):
        return (2, 0.0, display_cell(value))
    return (2, 0.0, comparable)


def column_values(df, column, rows):
    """The distinct values a column takes across every line of one part.

    A part can legitimately sit on several lines - the same component used in
    different sub-assemblies - and those lines repeat the description, the
    manufacturer and so on. Repeats are dropped so that a part landing on a
    different number of lines does not report a change in every column; that
    is reported once, on its own, as a line-count change."""
    distinct = {}
    for row in rows:
        distinct.setdefault(str(compare_value(df[column].iat[row])), df[column].iat[row])
    return sorted(distinct.values(), key=sort_key)


def key_positions(df, key_column):
    """Map each normalized key to the row positions where it occurs, in file order.
    Blank keys are skipped."""
    positions = {}
    for row, value in enumerate(df[key_column]):
        if is_blank(value):
            continue  # reported separately by blank_key_rows()
        positions.setdefault(norm_value(value), []).append(row)
    return positions


if __name__ == "__main__":
    CompareFrame().mainloop()
