############
# Author: Leon Trieu
# Date: 03/16/2021
# Purpose: Nasdaq (Quandl) Exercise Submission for Summer 2021 Internship
############

import os
import csv
import glob
from typing import List

def calculateProfit(prices: List[int]) -> int:
    """
    Kadane's Algorithm to calculate the maximum profit given one complete transcation (1 buy and 1 sell), we keep track of the minimum and compare the differences from the current price
    """ 
    currentMax = 0
    currentMin = float('inf')

    for price in prices:
        currentMin = min(currentMin, price)
        currentMax = max(currentMax, price-currentMin)

    return currentMax

class Datastore:
    """
    Datastore class that holds the tickers and sectors data, as well as provides the data loading and data aggregation functions.
    The function to calcuate the max profit is calculateProfits() where it uses the Kadanes Algorithm to solve for the max profit given one complete transaction within a day.
    """
    def __init__(self):
        self.tickers = dict()
        self.sectors = dict()
        self.dataSetProfits = dict()
        self.dataSetNames = []

    def loadMappingFromCSV(self, fileName: str):
        """
        Consumes the given CSV file for the ticker to sector mapping. This is run first as it initializes the Ticker and Sector objects.
        """
        print("Loading the mapping using", fileName, "...")
        try:
            with open(fileName, newline='') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=',', quotechar='|')
                for dataRow in csvreader:
                    tickerName = dataRow[0]
                    sectorName = dataRow[1]

                    if sectorName not in self.sectors:
                        self.sectors[sectorName] = Sector(sectorName)
                    
                    if tickerName not in self.tickers:
                        newTicker = Ticker(tickerName, self.sectors[sectorName])
                        self.tickers[tickerName] = newTicker
                        self.sectors[sectorName].addTicker(newTicker)
                    else:
                        print("WARNING: More than one mapping found for ticker:", tickerName)
        except Exception as err:
            print("ERROR: with loading mapping from csv file '" + fileName + "'. Please verify the file name, contents and delimiters.")
            print(err)
        else:
            print("Successfully loaded mapping\n")

    def loadDatafromCSV(self):
        """
        Consumes all CSV data files from the data directory and loads the datastore for each file.
        """
        self.dataSetNames = glob.glob("data/*.csv")

        for fileName in self.dataSetNames:
            print("Processing file", fileName, "...")
            
            #Initialize dataSetProfits using the fileName as key. We strip the fileName from any path prefixes to be used as the key.
            strippedFileName = os.path.basename(fileName)
            self.dataSetProfits[strippedFileName] = dict()

            # Parse CSV and create Ticker/Sector object and save to self.tickers and self.sectors
            try:
                with open(fileName, newline='') as csvfile:
                    csvreader = csv.reader(csvfile, delimiter=',', quotechar='|')

                    for dataRow in csvreader:
                        tickerName = dataRow[0]
                        stockPrices = list()
                        for price in dataRow[1:]:
                            stockPrices.append(int(price.strip("[]")))

                        if tickerName in self.tickers:
                            self.tickers[tickerName].addDataSet(strippedFileName, stockPrices)
                        else:
                            print("WARNING: Ticker", tickerName, "is not associated with a sector in the loaded mapping")

                            # Add the ticker to the list with an undefined sector
                            newTicker = Ticker(tickerName, None)
                            self.tickers[tickerName] = newTicker
            except Exception as err:
                print("Failed to load data set", fileName, err)
            else:
                print("Successfully loaded data set", fileName)

    def exportDataToCSV(self):
        """
        Exports the Ticker and Sector profit data into a CSV
        """
        print("Exporting ticker and sector data as CSV...")
        try:
            with open('output_profits.csv', 'w', newline='') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=',', quotechar='|')

                ### Sectors Data
                csvwriter.writerow(["Sector", "Total Profit"])
                for sectorObj in self.sectors.values():
                    csvwriter.writerow([sectorObj.name, sectorObj.profits])

                csvwriter.writerow([])

                ### Tickers Data
                csvwriter.writerow(["Ticker", "Sector", "Total Profit"]+list(self.dataSetProfits.keys()))
                for tickerObj in self.tickers.values():
                    csvwriter.writerow([tickerObj.name, tickerObj.sector.name, tickerObj.totalProfits]+list(tickerObj.profits.values()))
        except Exception as err:
            print("ERROR: Failed to export ticker and sector data as 'outputs_profits.csv' - ",err)
        else:
            print("Successfully exported ticker and sector data as 'outputs_profits.csv'")

    def compileData(self):
        """
        Iterates through the list of tickers and calculates their profits for each of their data sets. The profits are then saved to the respective sector.
        All profits for a given dataSet is aggregated into dataSetProfits
        """
        for tickerKey, tickerObj in self.tickers.items():
            for dataSetKey, dataSet in tickerObj.dataSets.items():
                maxProfit = calculateProfit(dataSet)
                tickerObj.profits[dataSetKey] = maxProfit
                tickerObj.addTotalProfit(maxProfit)
                tickerObj.sector.addProfit(maxProfit)

                # Set profit for a Ticker in the store's corresponding data set so we can easily aggregate maximums and minimums
                self.dataSetProfits[dataSetKey][tickerKey] = maxProfit

    def displayMaximizeProfit(self):
        """
        Print function to display the maximum profits for each dataset, overall max profit, and best performing sector.
        """
        print("\n#################################\nRESULTS\n#################################\n")

        ### Maximum Profit for Each Data Set
        print("Maximum profit on the given day:")
        for dataSetKey, profits in self.dataSetProfits.items():
            # We find the maximum in the list of profits, and then find any matching keys to the maximum value since there can be more than one maximum
            maximumProfit = max(profits.values())
            maximumTickers = [tickerName for tickerName, tickerProfit in profits.items() if tickerProfit == maximumProfit]
            print(dataSetKey, '-', maximumTickers, '= $'+str(maximumProfit))

        ### Overall Max Profit
        print("\n--------------\n")
        print("Best performing ticker:")
        # We find the total profit maximum in the list of tickers, and then find any matching ticker keys to the maximum value since there can ties for the maximum
        maximumTotalTickerProfit = 0
        for tickerKey, tickerObj in self.tickers.items():
            maximumTotalTickerProfit = max(tickerObj.totalProfits, maximumTotalTickerProfit)
        bestPerformingTickers = [tickerName for tickerName, tickerObj in self.tickers.items() if tickerObj.totalProfits == maximumTotalTickerProfit]
        print(bestPerformingTickers, '= $'+str(maximumTotalTickerProfit))

        ### Best Performing Sector
        print("\n--------------\n")
        print("Best performing sector:")
        # We find the overall maximum in the list of sectors, and then find any matching sector keys to the maximum value since there can ties for the maximum
        maximumSectorProfit = 0
        for sectorKey, sectorObj in self.sectors.items():
            maximumSectorProfit = max(sectorObj.profits, maximumSectorProfit)
        bestPerformingSectors = [sectorName for sectorName, sectorObj in self.sectors.items() if sectorObj.profits == maximumSectorProfit]
        print(bestPerformingSectors, '= $'+str(maximumSectorProfit))

        print("\n--------------\n")

class Sector:
    def __init__(self, name: str):
        self.name = name
        self.tickerList = list()
        self.profits = 0
    
    def addTicker(self, Ticker):
        self.tickerList.append(Ticker)

    def addProfit(self, profit):
        self.profits+=profit

class Ticker:
    def __init__(self, name: str, sector: Sector):
        self.name = name
        self.sector = sector
        self.totalProfits = 0
        self.profits = dict()
        self.dataSets = dict()
    
    def addDataSet(self, dataSetName: str, dataSetPrices: List[int]):
        if dataSetName in self.dataSets:
            print("WARNING: There exists duplicate or conflicting data entries for", self.name, "in", dataSetName)
        else:
            self.dataSets[dataSetName] = dataSetPrices
    
    def addTotalProfit(self, profit: int):
        self.totalProfits+=profit

if __name__ == "__main__":
    main = Datastore()
    main.loadMappingFromCSV("tickers_sectors.csv")
    main.loadDatafromCSV()
    main.compileData()
    main.displayMaximizeProfit()
    main.exportDataToCSV()
