import pandas as pd
import numpy
from tkinter import *
from tkinter import filedialog
from tkinter import simpledialog

parameter = 'REFDES'
description_parameter = 'Description'
curLng = 'EN'
class CompareFrame(Frame):
    file1_path = ''
    file2_path = ''



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
        global parameter
        global description_parameter
        print("Default search key: " + parameter)
        print("Default description key" + description_parameter)
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
        global path1
        path1 = file1_path
        self.button1['text'] = 'From: ' + path1.split('/')[-1]
    
    def load_file2(self):
        file2_path = filedialog.askopenfilename(filetypes = (("CSV files", "*.csv")
                                                           ,("All files", "*.*") ))
        global path2
        path2 = file2_path
        self.button5['text'] = 'To: ' + path2.split('/')[-1]

    def add_description(self):
        answer = simpledialog.askstring('Description key', 'Which column contains the part description?')
        global description_parameter
        description_parameter = answer

    def search_for(self):
        answer = simpledialog.askstring('Compare', 'Which column do you want to compare?')
        global parameter
        parameter = answer

    def compare_files(self):
        bomDiffFileName = 'BOM differences '
        print(parameter)        
        path_l1 = []
        path_l2 = []
        path_l1 = path1.split('/')   #find just filename
        path_l2 = path2.split('/')   #find just filename
        file1 = open(path1, 'r')
        file2 = open(path2, 'r')
        my_csv_f1 = pd.read_csv(file1, sep = ',')
        refdes1 = my_csv_f1[parameter]
        my_csv_f2 = pd.read_csv(file2, sep = ',')
        refdes2 = my_csv_f2[parameter]

        bomDiffFileName += path_l1[-1] + ' to ' + path_l2[-1] + '.txt'

        with open(bomDiffFileName, 'w') as output:
            output.write('BOM change notification:\n')
            output.write('From: ' + path_l1[-1] + '\n')
            output.write('To: ' + path_l2[-1] + '\n')

        # to add component value check
        list_f1 = []
        list_f2 = []
        list_comp = []

        for line in refdes1:
            list_f1.append(line)
        for line in refdes2:
            list_f2.append(line)
        for i in list_f1:
            if i not in list_f2:
                list_comp.append(i)
        if len(list_comp) > 0:
            with open(bomDiffFileName, 'a') as output:
                output.write('\n=====================================================================\n')
                output.write('REMOVE from ' + path_l1[-1] + ': ' + '\n')
                for each in list_comp:
                    output.write(each + ": " + str(my_csv_f1[description_parameter][my_csv_f1[parameter] == each].iloc[0]) + '\n')

        list_comp = []
        for i in list_f2:
            if i not in list_f1:
                list_comp.append(i)
        if len(list_comp) > 0:
            with open(bomDiffFileName, 'a') as output:
                output.write('\n=====================================================================\n')
                output.write('ADD to ' + path_l1[-1] + ': ' + '\n')
                for each in list_comp:
                    output.write(each + ": " + str(my_csv_f2[description_parameter][my_csv_f2[parameter] == each].iloc[0]) + '\n')
        
        # compare the columns for the parts that are in both files
        with open(bomDiffFileName, 'a') as output:
            output.write('\n=====================================================================\n')
        list_comp = []
        # for each column in the file compare the values
        coumnIndx = 0
        for column in my_csv_f1.columns:
            if column == parameter or column == description_parameter:
                continue
            for i in list_f1:
                if i in list_f2:
                        # if i is not a string or is null, skip it
                        if type(i) != str or pd.isnull(i) or i == 'nan':
                            continue
                        # if the part has already been compared, skip it
                        if i in list_comp:
                            continue
                        # check if there are multiple occurances of i in either file
                        iOccurF1 = []
                        iOccurF2 = []
                        # for each time i occurs in list_f1 append the index of i into iOccurF1
                        for index, value in enumerate(list_f1):
                            if value == i:
                                iOccurF1.append(index)
                        for index, value in enumerate(list_f2):
                            if value == i:
                                iOccurF2.append(index)
                        
                        for i_indxF1 in iOccurF1:
                            # find closest i_indxF2 to i_indxF1
                            i_indxF2 = 0
                            minDiff = 1000000
                            for i_indxF2_temp in iOccurF2:
                                diff = abs(i_indxF1 - i_indxF2_temp)
                                if diff < minDiff:
                                    minDiff = diff
                                    i_indxF2 = i_indxF2_temp

                            # if iOccurF1 has more than one entry, print the index being compared
                            if len(iOccurF1) > 1:
                                print('Comparing ' + column + ' for ' + i + ' at index ' + str(i_indxF1) + ' with ' + str(i_indxF2))

                            valF1 = my_csv_f1[column][i_indxF1]
                            valF2 = my_csv_f2[column][i_indxF2]

                            print('Comparing ' + column + ' for ' + i)
                            print(valF1)
                            print(valF2)
                            if valF1 != valF2:
                                #if both values are nan or null skip
                                if pd.isnull(valF1) and pd.isnull(valF2):
                                    continue
                                else:
                                    print('Add to diff')
                                    list_comp.append(i)
            # if there are any differences write them to the file
            if len(list_comp) > 0:
                coumnIndx += 1
                with open(bomDiffFileName, 'a') as output:
                    output.write('\nMODIFY-' + str(coumnIndx) + ' ' + column + ':\n')
                    output.write(path_l1[-1] + ' ===> ' + path_l2[-1] + '\n')
                    for each in list_comp:
                        valF1 = my_csv_f1[column][my_csv_f1[parameter] == each].iloc[0]
                        valF2 = my_csv_f2[column][my_csv_f2[parameter] == each].iloc[0]
                        # if value is float convert it to an int
                        if type(valF1) == numpy.float64:
                            valF1 = int(valF1)
                        if type(valF2) == numpy.float64:
                            valF2 = int(valF2)
                        # Write it to file
                        output.write(each + ": " + str(valF1) + ' ===> ' + str(valF2) + '\n')
            #clear list_comp
            list_comp = []

if __name__ == "__main__":
    CompareFrame().mainloop()
